"""A type checked as it is written, as the whole set leaves the types: every shape it refers to belongs to a type the
store holds, it is not built on itself, every link field says which kinds it may point at; and, for each change to it,
that its version moves on from the version it changed. What a type could never check an artifact against is refused
here, once, rather than by every create that uses it."""
from kb import composition, refusals
from kb.contract import kb_pb2
from kb.values import ArtifactId


def faults(type_id: ArtifactId, content: dict, draft) -> list[kb_pb2.Fault]:
    """Every way the type's schema could never be checked against, each at its place in the type."""
    schema = content.get("schema")
    found = []
    for place, ref in _refs(schema, "schema"):
        named = composition.reference(ref)
        if named is None:
            continue
        if named.type_id == type_id and named.whole:
            found.append(refusals.built_on_itself(type_id, place, ref))
        elif named.type_id is None or not draft.holds(named.type_id):
            found.append(refusals.no_such_shape(type_id, place, ref))
    for place, name, field in _link_fields(schema, "schema"):
        if not isinstance(field["ref"], dict) or "targets" not in field["ref"]:
            found.append(refusals.no_targets(type_id, place, name))
    return found


def version_kept(type_id: ArtifactId, content: dict, held: dict) -> list[kb_pb2.Fault]:
    """The fault of a type whose schema changed from the one held while its version did not go up from the held
    version; nothing when the version given is not a number, which the type of types refuses."""
    version = content.get("version")
    if isinstance(version, bool) or not isinstance(version, int):
        return []
    if content.get("schema") == held["schema"] or version > held["version"]:
        return []
    return [refusals.version_kept(type_id, held["version"])]


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
