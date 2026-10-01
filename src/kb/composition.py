"""A type read through what it is built on: the schemas of its composition, base first, the type a kb: reference
names, and the type a kind names. kb's own keywords are read through the composition, so a type built on a base
carries the base's first."""
from typing import NamedTuple

from referencing.exceptions import NoSuchResource

from kb import names, refusals, values


def composition(schema: dict, corpus) -> list[dict]:
    """The schema and every schema it is built on, base first: its allOf members in order, a whole type it names by
    $ref followed to that type's schema, and last the schema itself. kb's keywords are read through this list."""
    built_on = []
    for member in schema.get("allOf", []):
        built_on += composition(member, corpus)
    ref = schema.get("$ref")
    referred = reference(ref) if isinstance(ref, str) else None
    if referred is not None and referred.whole:
        built_on += composition(type_schema(ref, corpus), corpus)
    return [*built_on, schema]


class Reference(NamedTuple):
    """What a kb: reference names: the type, None when it names no type at all, and whether it is to the whole type
    rather than to a shape inside it."""
    type_id: values.ArtifactId | None
    whole: bool


def reference(ref: str) -> Reference | None:
    """What a kb: reference names, the type's name checked as any other name is. None for a reference that is not
    kb's."""
    referred = names.referred(ref)
    if referred is None:
        return None
    name, fragment = referred
    try:
        type_id = values.artifact_id(name)
    except values.Refused:
        type_id = None
    if type_id is not None and type_id.kind != values.TYPE_KIND:
        type_id = None
    return Reference(type_id, not fragment)


def type_schema(uri: str, corpus) -> dict:
    """The JSON Schema of the type a kb: URI names. NoSuchResource if it names none the corpus holds."""
    referred = reference(uri)
    if referred is None or referred.type_id is None or not corpus.holds(referred.type_id):
        raise NoSuchResource(ref=uri)
    return corpus.artifact(referred.type_id)["schema"]


def declared(schema: dict, corpus) -> dict:
    """kb's own keywords as a type declares them together with everything it is built on, base first: its fields
    (`properties`), its collections (`parts`) and the fields shown at a glance (`summary`). A type naming a field or
    a collection its base names too has its own."""
    whole = {"properties": {}, "parts": {}, "summary": []}
    for part in composition(schema, corpus):
        whole["properties"].update(part.get("properties", {}))
        whole["parts"].update(part.get("parts", {}))
        whole["summary"] += [name for name in part.get("summary", []) if name not in whole["summary"]]
    return whole


def kind_type(kind: values.Kind, corpus) -> values.ArtifactId:
    """The type a kind names. Raises Refused when the corpus holds none, since a kind must name a type the store
    holds, wherever it is given."""
    type_id = values.type_of(kind)
    if not corpus.holds(type_id):
        raise values.Refused([refusals.no_type(kind.name)])
    return type_id


def kind_schema(kind: values.Kind, corpus) -> dict:
    """The type a kind names, as the corpus holds it, its JSON Schema under `schema`. Raises Refused when the corpus
    holds none."""
    return corpus.artifact(kind_type(kind, corpus))


def reading(changed: set[values.ArtifactId], types: list[values.ArtifactId], corpus) -> list[values.Kind]:
    """The kinds whose type, of those given, reads a changed type: is one, or refers by a kb: reference anywhere in
    its schema to a type that reads one. What an artifact's links are read through can change only for these."""
    def reads(type_id: values.ArtifactId, seen: frozenset) -> bool:
        if type_id in changed:
            return True
        if type_id in seen or not corpus.holds(type_id):
            return False
        return any(reads(each, seen | {type_id}) for each in referred(corpus.artifact(type_id).get("schema")))
    return [values.Kind(type_id.slug) for type_id in types if reads(type_id, frozenset())]


def referred(node):
    """Every type a kb: reference anywhere in a schema names."""
    if isinstance(node, dict):
        for key, value in node.items():
            named = reference(value) if key == "$ref" and isinstance(value, str) else None
            if named is not None and named.type_id is not None:
                yield named.type_id
            yield from referred(value)
    elif isinstance(node, list):
        for value in node:
            yield from referred(value)
