"""Schema validation: the type's JSON Schema composed with kb's own structural rules, and beside it what the schema
language cannot say, checked in code: required sections in their declared order, and links that land on an artifact
the corpus holds, or a part inside it, of a kind the type allows, or wait on an IRI it does not hold, under a held
type the field allows, or already wait, as the store held them, on a part their held target lacks
(decision/a-link-that-waits-keeps-waiting), each told by what holds it, never by where it stands in a list, or are
brought by an import, which lets every such link wait as the store exported held it. Every
fault comes back together; kb's rules pass over a node JSON Schema found misshapen. kb's keywords are read through
kb.composition. What is checked, and the corpus it is checked against, are given; nothing here finds or opens a file.
"""
from jsonschema import Draft202012Validator
from jsonschema_specifications import REGISTRY as SPECIFICATIONS
from referencing import Registry
from referencing.jsonschema import DRAFT202012

from kb import links, places, refusals, rules, settled, values
from kb.composition import composition, declared, nearest_type, type_schema
from kb.contract import kb_pb2

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


def compose(schema: dict, corpus) -> dict:
    """One effective schema: the type's, with kb's structural rules and the shape of each collection it and its bases
    declare beside it under allOf.

    The type stays the root, so its own `#` references still resolve; kb's shapes sit under `$defs/kb-*`.
    """
    return {
        **schema,
        "allOf": [*schema.get("allOf", []), STRUCTURE, *_collections(schema, corpus)],
        "$defs": {**schema.get("$defs", {}), "kb-section": SECTION},
    }


def _collections(schema: dict, corpus) -> list[dict]:
    """The collections a schema and its bases declare, each a list whose items fit the item's type, and the
    collections that type declares in turn."""
    parts = declared(schema, corpus)["parts"]
    if not parts:
        return []
    return [{"properties": {
        name: {"type": "array", "items": _item(part.get("items", {}), corpus)} for name, part in parts.items()
    }}]


def _item(item_schema: dict, corpus) -> dict:
    """An item's schema with the shape of each collection it declares beside it; unchanged when it declares none."""
    collections = _collections(item_schema, corpus)
    if not collections:
        return item_schema
    return {**item_schema, "allOf": [*item_schema.get("allOf", []), *collections]}


_DIALECT = "https://json-schema.org/draft/2020-12/"
_VOCABULARIES = (
    "applicator", "content", "core", "format-annotation", "format-assertion", "meta-data", "unevaluated", "validation",
)
METASCHEMAS = Registry().with_resources(
    (uri, SPECIFICATIONS[uri]) for uri in (_DIALECT + "schema", *(_DIALECT + "meta/" + name for name in _VOCABULARIES))
)


def registry(corpus) -> Registry:
    """The 2020-12 metaschema and its vocabularies, the nine resources kb takes from the specifications package it
    declares (`METASCHEMAS`), and every type the corpus holds, found by the URI kb:<type IRI>@<n> of the version it
    stands at when a schema refers to it, and only then."""
    def retrieve(uri: str):
        return DRAFT202012.create_resource(type_schema(uri, corpus))
    return METASCHEMAS.combine(Registry(retrieve=retrieve))


def validate(artifact_id: str, content: dict, schema: dict, corpus, waited=frozenset(),
             imported: bool = False) -> list[kb_pb2.Fault]:
    """Every violation, as artifact, path, rule, message, JSON Schema's and kb's own rules' together. A
    kb:<type IRI>@<n> reference resolves against the corpus, to the version it holds. `waited` are the links the
    store held for this artifact, before what is checked, that landed on nothing held, each as
    `port_values.told` gives it: none for an artifact the store did not hold. `imported` says an import brings what
    is checked, so that each of its links into a part its held target lacks waits, whatever the store held.

    kb's own rules read a node only where JSON Schema found it in the shape they read it in.
    """
    errors = _errors(content, compose(schema, corpus), corpus)
    faults = [
        kb_pb2.Fault(artifact=artifact_id, place=_place(error), rule=error.validator, message=error.message)
        for error in errors
    ]
    if not _misread("sections", errors):
        required = [section for part in composition(schema, corpus) for section in part.get("sections", [])]
        faults += _sections(artifact_id, content.get("sections", []), required, "sections")
    found = unlanded(content, schema, corpus, waited, imported, errors)
    return faults + [refusals.unlanded(artifact_id, link.place, link.target) for link in found]


def unlanded(content: dict, schema: dict, corpus, waited=frozenset(), imported: bool = False, errors=()) -> list:
    """The links content carries that neither land in the corpus nor wait, `waited` and `imported` as `validate` takes
    them, but those JSON Schema's errors leave unread. The links are read through the schema; the corpus is where
    they would land, which an import's check gives as the store with only the files that would land (kb.examining)."""
    carried = links.carried(content, schema, corpus)
    return [
        link for link, told in zip(carried, links.told(carried))
        if not (_misread(link.place, errors) or _lands(link.target, link.ref, corpus))
        and not ((imported or told in waited) and _keeps_waiting(link, told[2], corpus))
    ]


def _errors(content: dict, composed: dict, corpus) -> list:
    """JSON Schema's every error."""
    return list(Draft202012Validator(composed, registry=registry(corpus)).iter_errors(content))


def _place(error) -> str:
    return "/".join(str(step) for step in error.absolute_path)


def _misread(place: str, errors: list) -> bool:
    """Whether JSON Schema found fault with the node at a place, or with anything inside it, or found a node holding
    it of the wrong type, so that kb's own rules cannot read it."""
    steps = place.split("/")
    for error in errors:
        at = _place(error).split("/") if error.absolute_path else []
        if at[:len(steps)] == steps or (error.validator == "type" and steps[:len(at)] == at):
            return True
    return False


def _lands(target: str, ref: dict, corpus) -> bool:
    """Whether a link lands: on an artifact of a kind the field allows that the corpus holds, and, when it names a
    place after `#` and the field allows parts, on a part that artifact holds; or on an IRI the corpus does not hold
    that waits under a held type the field allows, the part it names, if any, not checked, nothing being held there."""
    try:
        link = values.target(target)
    except values.Refused:
        return False
    if link.place and not ref.get("parts"):
        return False
    if not corpus.holds(link.id):
        return _waits(link.id, ref, corpus)
    if settled.kind(corpus.artifact(link.id)) not in ref["targets"]:
        return False
    return not link.place or places.holds_part(corpus.artifact(link.id), link.place)


def _keeps_waiting(link: links.Link, target: values.ArtifactId, corpus) -> bool:
    """Whether a link that does not land, and is the very link the store held for its artifact landing on nothing
    held (in the same field of the same thing, the artifact or the item of that name, to the same IRI and part,
    wherever it stands in a list), or one an import brings, waits: the corpus refuses it only for the part it names,
    its target held, of a kind the field allows, and lacking that part. A link into such a part that the store did
    not hold so, in a change that is no import, is new, and never waits."""
    held = bool(link.ref.get("parts")) and corpus.holds(target)
    return held and settled.kind(corpus.artifact(target)) in link.ref["targets"]


def _waits(target: values.ArtifactId, ref: dict, corpus) -> bool:
    """Whether an IRI the corpus does not hold may be linked to: the nearest held type it sits under is one the
    field allows. One under no held type may not."""
    under = nearest_type(target, corpus)
    return under is not None and str(under) in ref["targets"]


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
            artifact=artifact_id, place=place, rule=rules.SECTIONS,
            message=f"the sections the type requires must all be present, in order; {wanted['title']!r} {where}",
        ))
    return faults
