"""The refusals the domain makes of what a store holds, each with its rule and its message. Conversions refuse in
kb.values and type checks in kb.validation; what neither owns is made here, so no domain module names a contract type."""
from kb.contract import kb_pb2
from kb.names import Misnamed
from kb.values import ArtifactId, Locator


def not_found(artifact_id: ArtifactId) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(artifact_id), rule="not-found", message=f"the store holds nothing by the name {str(artifact_id)!r}",
    )


def no_type(kind_name: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        rule="kind", message=f"a kind must name a type the store holds; the store holds no type called {kind_name!r}",
    )


def not_a_collection(locator: Locator) -> kb_pb2.Fault:
    place = "/".join(locator.place)
    return kb_pb2.Fault(
        artifact=str(locator.id), path=place, rule="collection",
        message=f"an item is added to a collection, and {place!r} in {str(locator.id)!r} is not one",
    )


def nothing_at(locator: Locator) -> kb_pb2.Fault:
    place = "/".join(locator.place)
    return kb_pb2.Fault(
        artifact=str(locator.id), path=place, rule="not-found",
        message=f"{str(locator.id)!r} holds nothing at {place!r}",
    )


def settled_place(locator: Locator) -> kb_pb2.Fault:
    place = "/".join(locator.place)
    return kb_pb2.Fault(
        artifact=str(locator.id), path=place, rule="identity",
        message=f"a place inside an artifact never names what only the store settles; {place!r} begins at {locator.place[0]!r}",
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


def unreadable(artifact_id: ArtifactId, file, problem: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(artifact_id), rule="unreadable", message=f"the stored file {file} cannot be read: {problem}",
    )


MISNAMED = {
    "not-plain": "a name is a plain name of lower-case letters, digits and single hyphens; {name!r} is not",
    "repeated": "the items of a collection each have a name of their own; {name!r} is on more than one",
    "unknown": "a name on an item names an item already in that collection; {collection!r} held no item named {name!r}",
}


def misnamed(artifact_id: ArtifactId, found: Misnamed) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(artifact_id), path=f"{found.collection}/{found.index}/id", rule="item-name",
        message=MISNAMED[found.why].format(name=found.name, collection=found.collection),
    )


def no_such_shape(type_id: ArtifactId, place: str, ref: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(type_id), path=place, rule="shape",
        message=f"a shape a type refers to must belong to a type the store holds; {ref!r} does not",
    )


def built_on_itself(type_id: ArtifactId, place: str, ref: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(type_id), path=place, rule="built-on",
        message=f"a type cannot be built on itself; {str(type_id)!r} names {ref!r}",
    )


def no_targets(type_id: ArtifactId, place: str, field: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(type_id), path=place, rule="targets",
        message=f"a link field says which kinds it may point at; {field!r} does not",
    )


def unwritable(artifact_id: ArtifactId, problem: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(artifact=str(artifact_id), rule="content", message=problem)



def no_section(artifact_id: ArtifactId, title: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(artifact_id), path="sections", rule="not-found",
        message=f"{str(artifact_id)!r} holds no section titled {title!r}",
    )
