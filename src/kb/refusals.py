"""The refusals the domain makes of what a store holds, each with its rule and its message. Conversions refuse in
kb.values and type checks in kb.validation; what neither owns is made here, so no domain module names a contract type."""
from kb.contract import kb_pb2
from kb.values import ArtifactId, Locator


def not_found(artifact_id: ArtifactId) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(artifact_id), rule="not-found", message=f"the store holds nothing by the name {str(artifact_id)!r}",
    )


def no_type(kind_name: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        rule="kind", message=f"a kind must name a type the store holds; the store holds no type called {kind_name!r}",
    )


def no_collection(artifact_id: ArtifactId, collection: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(artifact_id), path=collection, rule="not-found",
        message=f"{str(artifact_id)!r} holds no collection called {collection!r}",
    )


def nothing_at(locator: Locator) -> kb_pb2.Fault:
    place = "/".join(locator.place)
    return kb_pb2.Fault(
        artifact=str(locator.id), path=place, rule="not-found",
        message=f"{str(locator.id)!r} holds nothing at {place!r}",
    )


def whole_only(locator: Locator) -> kb_pb2.Fault:
    place = "/".join(locator.place)
    return kb_pb2.Fault(
        artifact=str(locator.id), path=place, rule="locator",
        message=f"a removal takes out a whole artifact; {place!r} is a place inside {str(locator.id)!r}",
    )


def still_linked(removed: ArtifactId, other: ArtifactId, place: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(other), path=place, rule="on_delete",
        message=f"{str(removed)!r} cannot be removed while {str(other)!r} points at it at {place!r}",
    )


def unwritable(artifact_id: ArtifactId, problem: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(artifact=str(artifact_id), rule="content", message=problem)

