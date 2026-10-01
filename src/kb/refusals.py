"""The refusals the domain makes of what a store holds, each with its rule and its message. Conversions refuse in
kb.values and type checks in kb.validation; what neither owns is made here, so no domain module names a contract type."""
from kb import names, rules
from kb.contract import kb_pb2
from kb.names import Misnamed
from kb.values import ArtifactId, Locator


def not_found(artifact_id: ArtifactId) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(artifact_id), rule=rules.NOT_FOUND, message=f"the store holds nothing by the name {str(artifact_id)!r}",
    )


def no_type(kind_name: str, artifact: str = "") -> kb_pb2.Fault:
    """A kind the store holds no type for: asked for, or claimed by the artifact named."""
    return kb_pb2.Fault(
        artifact=artifact, rule=rules.KIND,
        message=f"a kind must name a type the store holds; the store holds no type called {kind_name!r}",
    )


def not_a_collection(locator: Locator) -> kb_pb2.Fault:
    place = names.placed(locator.place)
    return kb_pb2.Fault(
        artifact=str(locator.id), path=place, rule=rules.COLLECTION,
        message=f"an item is added to a collection, and {place!r} in {str(locator.id)!r} is not one",
    )


def nothing_at(locator: Locator) -> kb_pb2.Fault:
    place = names.placed(locator.place)
    return kb_pb2.Fault(
        artifact=str(locator.id), path=place, rule=rules.NOT_FOUND,
        message=f"{str(locator.id)!r} holds nothing at {place!r}",
    )


def settled_place(locator: Locator) -> kb_pb2.Fault:
    place = names.placed(locator.place)
    return kb_pb2.Fault(
        artifact=str(locator.id), path=place, rule=rules.IDENTITY,
        message=f"a place inside an artifact never names what only the store settles; {place!r} begins at {locator.place[0]!r}",
    )


def whole_only(locator: Locator) -> kb_pb2.Fault:
    place = names.placed(locator.place)
    return kb_pb2.Fault(
        artifact=str(locator.id), path=place, rule=rules.LOCATOR,
        message=f"a removal takes out a whole artifact; {place!r} is a place inside {str(locator.id)!r}",
    )


def still_linked(removed: str, other: ArtifactId, place: str) -> kb_pb2.Fault:
    """One link that still points at what would go: a whole artifact, or an item written `<artifact>#<place>`."""
    where = f" at {place!r}" if place else ""
    return kb_pb2.Fault(
        artifact=str(other), path=place, rule=rules.ON_DELETE,
        message=f"{removed!r} cannot be removed while {str(other)!r} points at it{where}",
    )


MISNAMED = {
    "not-plain": "a name is a plain name of lower-case letters, digits and single hyphens; {name!r} is not",
    "repeated": "the items of a collection each have a name of their own; {name!r} is on more than one",
    "unknown": "a name on an item names an item already in that collection; {collection!r} held no item named {name!r}",
}


def misnamed(artifact_id: ArtifactId, found: Misnamed) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(artifact_id), path=f"{found.collection}/{found.index}/id", rule=rules.ITEM_NAME,
        message=MISNAMED[found.why].format(name=found.name, collection=found.collection),
    )


def no_such_shape(type_id: ArtifactId, place: str, ref: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(type_id), path=place, rule=rules.SHAPE,
        message=f"a shape a type refers to must belong to a type the store holds; {ref!r} does not",
    )


def built_on_itself(type_id: ArtifactId, place: str, ref: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(type_id), path=place, rule=rules.BUILT_ON,
        message=f"a type cannot be built on itself; {str(type_id)!r} names {ref!r}",
    )


def no_targets(type_id: ArtifactId, place: str, field: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(type_id), path=place, rule=rules.TARGETS,
        message=f"a link field says which kinds it may point at; {field!r} does not",
    )


def version_kept(type_id: ArtifactId, held: int) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(type_id), path="version", rule=rules.VERSION,
        message=f"a type's version goes up whenever the type changes; {str(type_id)!r} changed at version {held}",
    )


def unwritable(artifact_id: ArtifactId, problem: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(artifact=str(artifact_id), rule=rules.CONTENT, message=problem)


def no_section(artifact_id: ArtifactId, title: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(artifact_id), path="sections", rule=rules.NOT_FOUND,
        message=f"{str(artifact_id)!r} holds no section titled {title!r}",
    )


def clock_failed(problem: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(rule=rules.CLOCK, message=f"the clock failed when it was asked the time: {problem}")


def unreadable(problem: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(rule=rules.UNREADABLE, message=f"the store's database cannot be read: {problem}")


def escaped(problem: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(rule=rules.STORE, message=f"the store could not answer, and nothing was written: {problem}")
