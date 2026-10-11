"""The refusals the domain makes of what a store holds, each with its rule and its message. Conversions refuse in
kb.values and type checks in kb.validation; what neither owns is made here, so no domain module names a contract type."""
from kb import names, rules
from kb.contract import kb_pb2
from kb.item_names import Misnamed
from kb.values import ArtifactId, Locator


def not_found(artifact_id: ArtifactId) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(artifact_id), rule=rules.NOT_FOUND, message=f"the store holds nothing by the name {str(artifact_id)!r}",
    )


def no_type(kind_name: str) -> kb_pb2.Fault:
    """A kind the store holds no type for."""
    return kb_pb2.Fault(
        rule=rules.KIND,
        message=f"a kind must name a type the store holds; the store holds no type called {kind_name!r}",
    )


def no_version(version: str) -> kb_pb2.Fault:
    """A type version the store does not hold, named by a create."""
    return kb_pb2.Fault(
        rule=rules.VERSION,
        message=f"a create names a version of a type the store holds; the store holds no version {version!r}",
    )


def not_later(artifact_id: ArtifactId, version: str, conforms: str) -> kb_pb2.Fault:
    """A replacement naming a version its artifact cannot move to: an earlier one, another type's, or one not held."""
    return kb_pb2.Fault(
        artifact=str(artifact_id), rule=rules.VERSION,
        message=f"an artifact moves only to a later version of its own type that the store holds; {version!r} is "
        f"not one for an artifact conforming to {conforms!r}",
    )


def not_under(artifact_id: ArtifactId, type_id: ArtifactId) -> kb_pb2.Fault:
    """A create at an IRI that does not belong to the type it names: the nearest held type it sits under is another,
    or none."""
    return kb_pb2.Fault(
        artifact=str(artifact_id), rule=rules.IDENTITY,
        message=f"an artifact's IRI sits under its type's IRI; {str(artifact_id)!r} is not an IRI of {str(type_id)!r}",
    )


def belongs(type_id: ArtifactId, sitting: ArtifactId, other: ArtifactId) -> kb_pb2.Fault:
    """A define of a type at an IRI under another type's, under which an artifact of that other type is held, or
    a link waits on an IRI not held: the IRI that sits there."""
    return kb_pb2.Fault(
        artifact=str(type_id), rule=rules.IDENTITY,
        message=f"an IRI keeps the type it was written or linked under; {str(sitting)!r} belongs to {str(other)!r}",
    )


def already_held(artifact_id: ArtifactId) -> kb_pb2.Fault:
    """A create at an IRI the store already holds something at."""
    return kb_pb2.Fault(
        artifact=str(artifact_id), rule=rules.IDENTITY,
        message=f"an IRI names one artifact; the store already holds one at {str(artifact_id)!r}",
    )


def carried_twice(artifact_id: ArtifactId) -> kb_pb2.Fault:
    """A create at an IRI a create before it in its set carries."""
    return kb_pb2.Fault(
        artifact=str(artifact_id), rule=rules.IDENTITY,
        message=f"an IRI names one artifact; the set carries {str(artifact_id)!r} on more than one create",
    )


def not_a_collection(locator: Locator) -> kb_pb2.Fault:
    place = names.placed(locator.place)
    return kb_pb2.Fault(
        artifact=str(locator.id), place=place, rule=rules.COLLECTION,
        message=f"an item is added to a collection, and {place!r} in {str(locator.id)!r} is not one",
    )


def nothing_at(locator: Locator) -> kb_pb2.Fault:
    place = names.placed(locator.place)
    return kb_pb2.Fault(
        artifact=str(locator.id), place=place, rule=rules.NOT_FOUND,
        message=f"{str(locator.id)!r} holds nothing at {place!r}",
    )


def settled_place(locator: Locator) -> kb_pb2.Fault:
    place = names.placed(locator.place)
    return kb_pb2.Fault(
        artifact=str(locator.id), place=place, rule=rules.IDENTITY,
        message=f"a place inside an artifact never names what only the store settles; {place!r} begins at {locator.place[0]!r}",
    )


def moved(artifact_id: ArtifactId, revision: int) -> kb_pb2.Fault:
    """A change that said the revision its artifact was read at, which the artifact no longer stands at."""
    return kb_pb2.Fault(
        artifact=str(artifact_id), rule=rules.REVISION,
        message=f"the artifact moved since it was read; {str(artifact_id)!r} stands at revision {revision}",
    )


def whole_only(locator: Locator) -> kb_pb2.Fault:
    place = names.placed(locator.place)
    return kb_pb2.Fault(
        artifact=str(locator.id), place=place, rule=rules.LOCATOR,
        message=f"a removal takes out a whole artifact; {place!r} is a place inside {str(locator.id)!r}",
    )


def still_linked(removed: str, other: ArtifactId, place: str) -> kb_pb2.Fault:
    """One link that still points at what would go: a whole artifact, or an item written `<artifact>#<place>`."""
    where = f" at {place!r}" if place else ""
    return kb_pb2.Fault(
        artifact=str(other), place=place, rule=rules.ON_DELETE,
        message=f"{removed!r} cannot be removed while {str(other)!r} points at it{where}",
    )


def unlanded(artifact: str, place: str, target: str) -> kb_pb2.Fault:
    """A link that lands on nothing the store holds, or on a node of a kind its type does not allow."""
    return kb_pb2.Fault(
        artifact=artifact, place=place, rule=rules.REF,
        message=f"a link must land on a node of a kind the type allows; {target!r} does not",
    )


MISNAMED = {
    "not-plain": "a name is a plain name of lower-case letters, digits and single hyphens; {unfit}",
    "repeated": "the items of a collection each have a name of their own; {name!r} is on more than one",
    "unknown": "a name on an item names an item already in that collection; {collection!r} held no item named {name!r}",
}


def misnamed(artifact_id: ArtifactId, found: Misnamed) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(artifact_id), place=f"{found.collection}/{found.index}/id", rule=rules.ITEM_NAME,
        message=MISNAMED[found.why].format(name=found.name, collection=found.collection, unfit=_unfit(found.name)),
    )


def _unfit(name) -> str:
    """What is said of a name given that is not a plain name: text as it was given, and anything else, which has no
    one way of being written, as not text."""
    return f"{name!r} is not" if isinstance(name, str) else "a name is text, and what was given is not"


PART_MISNAMED = {
    "not-plain": "a part's name is a plain name of lower-case letters, digits and single hyphens; {unfit}",
    "repeated": "a part's name is unique in its collection; {name!r} is on more than one",
}


def misnamed_part(artifact_id: ArtifactId, found: Misnamed) -> kb_pb2.Fault:
    """A name a create gives a part that the part may not carry, at the part's place in what the create carried."""
    return kb_pb2.Fault(
        artifact=str(artifact_id), place=f"{found.collection}/{found.index}/id", rule=rules.ITEM_NAME,
        message=PART_MISNAMED[found.why].format(name=found.name, unfit=_unfit(found.name)),
    )


def unwritable(artifact_id: ArtifactId, problem: str, place: str = "") -> kb_pb2.Fault:
    return kb_pb2.Fault(artifact=str(artifact_id), place=place, rule=rules.CONTENT, message=problem)


def no_section(artifact_id: ArtifactId, title: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(artifact_id), place="sections", rule=rules.NOT_FOUND,
        message=f"{str(artifact_id)!r} holds no section titled {title!r}",
    )


def clock_failed(problem: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(rule=rules.CLOCK, message=f"the clock failed when it was asked the time: {problem}")


def unreadable(problem: str) -> kb_pb2.Fault:
    """A store whose database cannot be read, the problem naming the database."""
    return kb_pb2.Fault(rule=rules.UNREADABLE, message=f"the store's database cannot be read: {problem}")


def earlier_kb(root: str) -> kb_pb2.Fault:
    """A store an earlier kb made, which this kb can neither read nor move."""
    return kb_pb2.Fault(rule=rules.UNREADABLE, message=(
        f"the store at {root} was made by an earlier version of kb, which this kb cannot read or move"
    ))


def later_kb(root: str) -> kb_pb2.Fault:
    """A store whose marker names a form of store this kb does not know, or cannot be read at all."""
    return kb_pb2.Fault(rule=rules.UNREADABLE, message=(
        f"the store at {root} was made by a later version of kb, which is needed to read it; this kb does not know "
        f"the form of store its marker names"
    ))


def busy() -> kb_pb2.Fault:
    return kb_pb2.Fault(rule=rules.BUSY, message=(
        "the store was busy with another change for longer than it waits, and nothing was written; the same change "
        "may be made again"
    ))


def served(address: str) -> kb_pb2.Fault:
    """A change asked of a store directly while a server owns it, naming the address the server serves at."""
    return kb_pb2.Fault(rule=rules.SERVED, message=(
        f"the store is served, and every change goes through its server, at {address}; nothing was written"
    ))


def clock_with_a_server() -> kb_pb2.Fault:
    """A change asked of a server by a client readied with a clock: the clock is for a store reached in process."""
    return kb_pb2.Fault(rule=rules.CLOCK, message=(
        "the clock belongs to a client that reaches its store in process, and a server stamps each change with its "
        "own; nothing was written"
    ))


def connection(path: str) -> kb_pb2.Fault:
    """The connection to a server that cannot be read, or names no address: the file it is, named."""
    return kb_pb2.Fault(rule=rules.CONNECTION, message=(
        f"the connection to a server cannot be read or names no address `host:port`: {path}"
    ))


def unreachable(address: str) -> kb_pb2.Fault:
    """A server the connection names that cannot be reached, never there or gone since, naming the address."""
    return kb_pb2.Fault(
        rule=rules.UNREACHABLE, message=f"the server the connection names, at {address}, cannot be reached",
    )


def escaped(problem: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(rule=rules.STORE, message=f"the store could not answer, and nothing was written: {problem}")
