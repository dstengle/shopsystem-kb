"""A type checked as it is written, against the types the draft holds: every shape it refers to belongs to a type the
store holds, it is not built on itself, and every link field says which kinds it may point at. What a type could never
check an artifact against is refused here, once, rather than by every create that uses it."""
from kb import refusals, values
from kb.contract import kb_pb2
from kb.validation import TYPE_URI
from kb.values import ArtifactId, Kind, Refused


def faults(type_id: ArtifactId, content: dict, draft) -> list[kb_pb2.Fault]:
    """Every way the type's schema could never be checked against, each at its place in the type."""
    schema = content.get("schema")
    found = []
    for place, ref in _refs(schema, "schema"):
        named = _type_named(ref)
        if named is None:
            continue
        if named == type_id and "#" not in ref:
            found.append(refusals.built_on_itself(type_id, place, ref))
        elif named is False or not draft.holds(named):
            found.append(refusals.no_such_shape(type_id, place, ref))
    for place, name, field in _link_fields(schema, "schema"):
        if not isinstance(field["ref"], dict) or "targets" not in field["ref"]:
            found.append(refusals.no_targets(type_id, place, name))
    return found


def _type_named(ref: str) -> ArtifactId | None | bool:
    """The type a kb: reference names; None for a reference that is not kb's, False for one naming no type at all."""
    if not ref.startswith(TYPE_URI):
        return None
    try:
        named = values.artifact_id(ref.removeprefix(TYPE_URI).partition("#")[0])
    except Refused:
        return False
    return named if named.kind == Kind("schema") else False


def _refs(node, place: str):
    """Every $ref in a schema, with its place, at every depth."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "$ref" and isinstance(value, str):
                yield f"{place}/$ref", value
            else:
                yield from _refs(value, f"{place}/{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _refs(value, f"{place}/{index}")


def _link_fields(node, place: str):
    """Every field declared with a `ref`, with its place and name, at every depth: the type's own, its items', its
    bases' and its shapes'."""
    if isinstance(node, dict):
        properties = node.get("properties")
        if isinstance(properties, dict):
            for name, field in properties.items():
                if isinstance(field, dict) and "ref" in field:
                    yield f"{place}/properties/{name}", name, field
        for key, value in node.items():
            yield from _link_fields(value, f"{place}/{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _link_fields(value, f"{place}/{index}")
