"""A type checked as it is written, as the whole set leaves the types: every shape it refers to belongs to a type the
store holds, it is not built on itself, kb's own keywords stand only where kb reads them, and every link field kb
reads states its whole shape; and, for each change to it, that its version moves on from the version it changed. What
a type could never check an artifact against is refused here, once, rather than by every create that uses it."""
from kb import composition, keywords, type_refusals
from kb.contract import kb_pb2
from kb.values import ArtifactId


def faults(type_id: ArtifactId, content: dict, draft) -> list[kb_pb2.Fault]:
    """Every way the type's schema could never be checked against, each at its place in the type."""
    schema = content.get("schema")
    return _shapes(type_id, schema, draft) + [
        fault for kept in keywords.standing(schema) for fault in _keyword(type_id, kept)
    ]


def _shapes(type_id: ArtifactId, schema, draft) -> list[kb_pb2.Fault]:
    """Every kb: reference that names no type the draft holds, or names the type itself as its base."""
    found = []
    for place, ref in _refs(schema, "schema"):
        named = composition.reference(ref)
        if named is None:
            continue
        if named.type_id == type_id and named.whole:
            found.append(type_refusals.built_on_itself(type_id, place, ref))
        elif named.type_id is None or not draft.holds(named.type_id):
            found.append(type_refusals.no_such_shape(type_id, place, ref))
    return found


def _keyword(type_id: ArtifactId, kept: keywords.Standing) -> list[kb_pb2.Fault]:
    """A keyword of kb's where kb does not read it, refused for its place alone; a link field kb reads, checked."""
    if not kept.read and kept.keyword == "ref":
        return [type_refusals.misplaced_link(type_id, kept.place)]
    if not kept.read:
        return [type_refusals.misplaced(type_id, kept.keyword, kept.place)]
    return _link_field(type_id, kept) if kept.keyword == "ref" else []


def _link_field(type_id: ArtifactId, kept: keywords.Standing) -> list[kb_pb2.Fault]:
    """What a link field kb reads leaves out of its shape or says that kb does not know, at the field's place; a `ref`
    that is not a mapping says nothing, so leaves out everything."""
    field = kept.holder.rsplit("/", 1)[-1]
    ref = kept.value if isinstance(kept.value, dict) else {}
    found = []
    left_out = _left_out(ref)
    if left_out:
        found.append(type_refusals.incomplete_link(type_id, kept.holder, field, left_out))
    if "cardinality" in ref and ref["cardinality"] not in ("one", "many"):
        found.append(type_refusals.unknown_reach(type_id, kept.holder, field, ref["cardinality"]))
    if "on_delete" in ref and ref["on_delete"] != "refuse":
        found.append(type_refusals.unknown_removal(type_id, kept.holder, field, ref["on_delete"]))
    if "targets" not in ref:
        found.append(type_refusals.no_targets(type_id, kept.holder, field))
    return found


def _left_out(ref: dict) -> list[str]:
    """Which of what a link field must say, beside its kinds, it does not say: one artifact or several, whether it
    may point into a part (yes or no), and what a removal does."""
    return [
        key for key in ("cardinality", "parts", "on_delete")
        if key not in ref or (key == "parts" and not isinstance(ref[key], bool))
    ]


def version_kept(type_id: ArtifactId, content: dict, held: dict) -> list[kb_pb2.Fault]:
    """The fault of a type whose schema changed from the one held while its version did not go up from the held
    version; nothing when either version is not a number, which the type of types refuses."""
    version, before = content.get("version"), held.get("version")
    if not _number(version) or not _number(before):
        return []
    if content.get("schema") == held.get("schema") or version > before:
        return []
    return [type_refusals.version_kept(type_id, before)]


def _number(version) -> bool:
    return isinstance(version, int) and not isinstance(version, bool)


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

