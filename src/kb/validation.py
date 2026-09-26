"""Schema validation: the type's JSON Schema composed with kb's own structural rules, checked in one pass, then
what the schema language cannot say, checked in code: required sections in their declared order, and links that
land on an artifact the corpus holds, of a kind the type allows.

kb's keywords are read through the type's composition, so a type built on a base carries the base's first.
"""
from typing import NamedTuple

from jsonschema import Draft202012Validator
from referencing import Registry
from referencing.exceptions import NoSuchResource
from referencing.jsonschema import DRAFT202012

from kb import canonical, values
from kb.contract import kb_pb2
from kb.store import Damaged, Store
from kb.values import Kind

TYPE_URI = "kb:"

SECTION = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "body": {"type": "string"},
        "sections": {"type": "array", "items": {"$ref": "#/$defs/kb-section"}},
    },
    "required": ["title", "body"],
    "additionalProperties": False,
}

STRUCTURE = {"properties": {"sections": {"type": "array", "items": {"$ref": "#/$defs/kb-section"}}}}


def compose(schema: dict) -> dict:
    """One effective schema: the type's, with kb's structural rules beside it under allOf.

    The type stays the root, so its own `#` references still resolve; kb's shapes sit under `$defs/kb-*`.
    """
    return {
        **schema,
        "allOf": [*schema.get("allOf", []), STRUCTURE],
        "$defs": {**schema.get("$defs", {}), "kb-section": SECTION},
    }


def registry(corpus) -> Registry:
    """Every type the corpus holds, found by the URI kb:schema/<type> when a schema refers to it, and only then."""
    def retrieve(uri: str):
        return DRAFT202012.create_resource(_type_schema(uri, corpus))
    return Registry(retrieve=retrieve)


def _type_schema(uri: str, corpus) -> dict:
    """The JSON Schema of the type a kb: URI names, its name checked as any other name is. NoSuchResource if none."""
    try:
        schema_id = values.artifact_id(uri.removeprefix(TYPE_URI)) if uri.startswith(TYPE_URI) else None
    except values.Refused:
        schema_id = None
    if schema_id is None or schema_id.kind != Kind("schema") or not corpus.holds(schema_id):
        raise NoSuchResource(ref=uri)
    return corpus.artifact(schema_id)["schema"]


def validate(artifact_id: str, content: dict, schema: dict, corpus) -> list[kb_pb2.Fault]:
    """Every violation, as artifact, path, rule, message. A kb:schema/<type> reference resolves against the corpus.

    kb's own rules read content that fits the composed schema, so they run only when it does.
    """
    faults = [
        kb_pb2.Fault(
            artifact=artifact_id,
            path="/".join(str(step) for step in error.absolute_path),
            rule=error.validator,
            message=error.message,
        )
        for error in Draft202012Validator(compose(schema), registry=registry(corpus)).iter_errors(content)
    ]
    if faults:
        return faults
    required = [section for part in composition(schema, corpus) for section in part.get("sections", [])]
    faults = _sections(artifact_id, content.get("sections", []), required, "sections")
    for link in links(content, schema, corpus):
        if not _lands(link.target, link.ref, corpus):
            faults.append(kb_pb2.Fault(
                artifact=artifact_id, path=link.place, rule="ref",
                message=f"a link must land on a node of a kind the type allows; {link.target!r} does not",
            ))
    return faults


def check(store: Store) -> kb_pb2.ValidateResponse:
    """Every artifact checked against the current version of its type, and listed as stale when it was last
    checked against an older one; a file that cannot be read is reported and the check goes on."""
    violations, stale = [], []
    for artifact_id in store.ids():
        loaded = _with_type(store, artifact_id)
        if isinstance(loaded, Damaged):
            violations.append(loaded.fault)
            continue
        artifact, schema = loaded
        if artifact["schema_version"] < schema["version"]:
            stale.append(kb_pb2.Stale(
                artifact=str(artifact_id), schema_version=artifact["schema_version"], current=schema["version"],
            ))
        content = {key: value for key, value in artifact.items() if key not in canonical.IDENTITY[:4]}
        violations += validate(str(artifact_id), content, schema["schema"], store)
    return kb_pb2.ValidateResponse(violations=violations, stale=stale)


def _with_type(store: Store, artifact_id) -> tuple[dict, dict] | Damaged:
    """The artifact and its type as stored, or the damage of the first of them whose file cannot be read."""
    artifact = store.load(artifact_id)
    if isinstance(artifact, Damaged):
        return artifact
    schema = store.load(values.ArtifactId(Kind("schema"), artifact_id.kind.name))
    return schema if isinstance(schema, Damaged) else (artifact, schema)


def references(schema: dict, corpus) -> dict[str, dict]:
    """Every field that links to other artifacts, from every schema in the composition, base first, with its `ref`."""
    return {
        name: field["ref"]
        for part in composition(schema, corpus)
        for name, field in part.get("properties", {}).items()
        if "ref" in field
    }


class Link(NamedTuple):
    """One link an artifact carries: the field that holds it, the place of that field in the artifact, the name it
    points at, and the field's `ref`, which says what it may land on."""
    field: str
    place: str
    target: str
    ref: dict


def links(artifact: dict, schema: dict, corpus) -> list[Link]:
    """Every link an artifact carries, wherever it sits: in its own fields, and in the fields of each item of each of
    its collections, at every depth."""
    return _links_in(artifact, references(schema, corpus), schema.get("parts", {}), "", corpus)


def _links_in(node: dict, refs: dict[str, dict], parts: dict, at: str, corpus) -> list[Link]:
    """The links in one node, an artifact or an item, its place in the artifact before each of theirs."""
    found = []
    for field, ref in refs.items():
        value = node.get(field)
        if isinstance(value, list):
            found += [Link(field, f"{at}{field}/{index}", target, ref) for index, target in enumerate(value)]
        elif value is not None:
            found.append(Link(field, f"{at}{field}", value, ref))
    for collection, part in parts.items():
        items = node.get(collection)
        if not isinstance(items, list):
            continue
        item_schema = part.get("items", {})
        item_refs = references(item_schema, corpus)
        for index, item in enumerate(items):
            if isinstance(item, dict):
                found += _links_in(item, item_refs, item_schema.get("parts", {}), f"{at}{collection}/{index}/", corpus)
    return found


def points_at(target: str, artifact_id) -> bool:
    """Whether a link lands on the artifact or on a part inside it."""
    return target.partition("#")[0] == str(artifact_id)


def _lands(target: str, ref: dict, corpus) -> bool:
    """Whether a link lands: on an artifact of a kind the field allows that the corpus holds, and, when it names a
    place after `#` and the field allows parts, on a part that artifact holds."""
    try:
        link = values.target(target)
    except values.Refused:
        return False
    if link.place and not ref.get("parts"):
        return False
    if link.id.kind.name not in ref["targets"] or not corpus.holds(link.id):
        return False
    return not link.place or _holds_part(corpus.artifact(link.id), link.place)


def _holds_part(node: dict, place: tuple) -> bool:
    """Whether a place, pairs of a collection and the name of an item in it, names a part the node holds."""
    if len(place) % 2:
        return False
    for collection, name in zip(place[::2], place[1::2]):
        items = node.get(collection)
        if not isinstance(items, list):
            return False
        node = next((item for item in items if isinstance(item, dict) and item.get("id") == name), None)
        if node is None:
            return False
    return True


def composition(schema: dict, corpus) -> list[dict]:
    """The schema and every schema it is built on, base first: its allOf members in order, a whole type it names by
    $ref followed to that type's schema, and last the schema itself. kb's keywords are read through this list."""
    built_on = []
    for member in schema.get("allOf", []):
        built_on += composition(member, corpus)
    ref = schema.get("$ref")
    if isinstance(ref, str) and ref.startswith(TYPE_URI) and "#" not in ref:
        built_on += composition(_type_schema(ref, corpus), corpus)
    return [*built_on, schema]


def _sections(artifact_id: str, sections: list, required: list, place: str) -> list[kb_pb2.Fault]:
    """The required sections first, in their declared order, at every level of the tree; any others may follow.

    Each required section is looked for where the one before it left off, so one missing section is one fault.
    """
    faults, at = [], 0
    titles = [section["title"] for section in sections]
    for wanted in required:
        if titles[at:at + 1] == [wanted["title"]]:
            faults += _sections(
                artifact_id, sections[at].get("sections", []), wanted.get("sections", []), f"{place}/{at}/sections",
            )
            at += 1
            continue
        where = "is out of its place" if wanted["title"] in titles else "is missing"
        faults.append(kb_pb2.Fault(
            artifact=artifact_id, path=place, rule="sections",
            message=f"the sections the type requires must all be present, in order; {wanted['title']!r} {where}",
        ))
    return faults
