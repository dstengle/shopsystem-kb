"""The refusals of a type as it is written, each with its rule and its message, from plain values: a shape it refers
to that no held type has, a type built on itself, one of kb's keywords where kb does not read it, a link field that
leaves out part of its shape or says what kb does not know, a version kept while the type changed."""
from kb import rules
from kb.contract import kb_pb2
from kb.values import ArtifactId


def no_such_shape(type_id: ArtifactId, place: str, ref: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(type_id), place=place, rule=rules.SHAPE,
        message=f"a shape a type refers to must belong to a type the store holds; {ref!r} does not",
    )


def built_on_itself(type_id: ArtifactId, place: str, ref: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(type_id), place=place, rule=rules.BUILT_ON,
        message=f"a type cannot be built on itself; {str(type_id)!r} names {ref!r}",
    )


def no_targets(type_id: ArtifactId, place: str, field: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(type_id), place=place, rule=rules.TARGETS,
        message=f"a link field says which kinds it may point at; {field!r} does not",
    )


def version_kept(type_id: ArtifactId, held: int) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(type_id), place="version", rule=rules.VERSION,
        message=f"a type's version goes up whenever the type changes; {str(type_id)!r} changed at version {held}",
    )


def misplaced_link(type_id: ArtifactId, place: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(type_id), place=place, rule=rules.REF,
        message=f"kb does not read a link field there; {place!r} is not on a field of a type's schema, of a base it "
                f"is built on or of a collection's items",
    )


WHERE_READ = {
    "parts": "at the top of a type's schema or of a collection's items",
    "summary": "at the top of a type's schema or of a collection's items",
    "sections": "at the top of a type's schema",
}


def misplaced(type_id: ArtifactId, keyword: str, place: str) -> kb_pb2.Fault:
    """A collection, required sections or the fields shown at a glance declared where kb does not read them."""
    return kb_pb2.Fault(
        artifact=str(type_id), place=place, rule=rules.PLACEMENT,
        message=f"kb does not read {keyword!r} there; it reads {keyword!r} only {WHERE_READ[keyword]}, and {place!r} "
                f"is not",
    )


def incomplete_link(type_id: ArtifactId, place: str, field: str, left_out: list[str]) -> kb_pb2.Fault:
    """A link field that does not say whether it points at one artifact or several, whether it may point into a
    part, or what a removal does: each key of its `ref` it leaves out named."""
    return kb_pb2.Fault(
        artifact=str(type_id), place=place, rule=rules.REF,
        message=f"a link field says which kinds it may point at, whether it points at one artifact or several, "
                f"whether it may point into a part and what a removal does; {field!r} does not say "
                f"{', '.join(repr(key) for key in left_out)}",
    )


def unknown_removal(type_id: ArtifactId, place: str, field: str, rule) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(type_id), place=place, rule=rules.REF,
        message=f"refuse is the one removal rule kb knows; {field!r} says {rule!r}",
    )


def unknown_reach(type_id: ArtifactId, place: str, field: str, cardinality) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(type_id), place=place, rule=rules.REF,
        message=f"a link field points at one artifact or several, `one` or `many`; {field!r} says {cardinality!r}",
    )
