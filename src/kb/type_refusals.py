"""The refusals of a type as it is written, each with its rule and its message, from plain values: a shape it refers
to that no held type has, a type built on itself, a link field that does not say what it may point at, a version
kept while the type changed."""
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
