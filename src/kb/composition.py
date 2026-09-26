"""A type read through what it is built on: the schemas of its composition, base first, and the type a kb: reference
names. kb's own keywords are read through the composition, so a type built on a base carries the base's first."""
from referencing.exceptions import NoSuchResource

from kb import values
from kb.values import Kind

TYPE_URI = "kb:"


def composition(schema: dict, corpus) -> list[dict]:
    """The schema and every schema it is built on, base first: its allOf members in order, a whole type it names by
    $ref followed to that type's schema, and last the schema itself. kb's keywords are read through this list."""
    built_on = []
    for member in schema.get("allOf", []):
        built_on += composition(member, corpus)
    ref = schema.get("$ref")
    if isinstance(ref, str) and ref.startswith(TYPE_URI) and "#" not in ref:
        built_on += composition(type_schema(ref, corpus), corpus)
    return [*built_on, schema]


def type_schema(uri: str, corpus) -> dict:
    """The JSON Schema of the type a kb: URI names, its name checked as any other name is. NoSuchResource if none."""
    try:
        schema_id = values.artifact_id(uri.removeprefix(TYPE_URI)) if uri.startswith(TYPE_URI) else None
    except values.Refused:
        schema_id = None
    if schema_id is None or schema_id.kind != Kind("schema") or not corpus.holds(schema_id):
        raise NoSuchResource(ref=uri)
    return corpus.artifact(schema_id)["schema"]


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
