"""The write path: a set drafted and checked (kb.drafting); only when every change passes is each entry's stamp
settled by the clock and the set handed to the port, which lands every change and one entry per operation naming the
set in one transaction. When another change lands between the draft and the landing, an artifact the set changes, a
type it was read through, or an artifact whose links it reads anew having moved, the port refuses it, and the set is
drafted again, stamped and landed while the port holds the write lock, so that nothing can land before it again. A
fault anywhere refuses the whole set with every fault found, and nothing is written. Starting a store and recording a
snapshot land through the port too."""
from typing import NamedTuple

from kb import canonical, drafting, journal, port, query, refusals, search, settled, store, values
from kb.draft import Draft
from kb.metaschema import METASCHEMA
from kb.signatures import Actor, Signed
from kb.values import ArtifactId, Refused, Root

METASCHEMA_ID = values.type_of(values.TYPE_KIND)


class Result(NamedTuple):
    """What a set did to one artifact: its version now, and, for an item added, the item's name."""
    artifact_id: ArtifactId
    revision: int
    item: str


class Landed(NamedTuple):
    """A set landed: the name of the set, and what it did to each artifact, in the order of its operations."""
    batch: str
    results: list[Result]


def start(root: Root, actor: Actor, clock: journal.Clock | None = None) -> None:
    """A new store at root, holding the type of types and its start in the history, stamped by the clock before
    anything is made. Raises Refused where no store can be started."""
    stamp = journal.first(clock)
    store.vacant(root)
    metaschema = settled.order(
        settled.given(
            settled.content(METASCHEMA), str(METASCHEMA_ID), METASCHEMA_ID.kind.name, 1, 1, METASCHEMA["title"],
        ),
        METASCHEMA["schema"],
    )
    entry = journal.change(
        signed=Signed(actor, "initialise store"), op="create", artifact=str(METASCHEMA_ID), path="", revision=1,
        schema_version=1, text=canonical.dump(metaschema), stamp=stamp,
    )
    created = port.Change(METASCHEMA_ID, metaschema, revision=1, searched=tuple(search.searchable(metaschema)))
    store.start(root, lambda made: made.land([created], [entry]))


def land(held: port.Port, operations: list, signed: Signed, clock: journal.Clock | None = None) -> Landed:
    """The set drafted against the store as it stands, each entry's moment read from the clock, then landed. When
    another change lands between the draft and the landing, the set is drafted, stamped and landed again while the
    port holds the write lock, where a change that says the revision it read is compared again, and refused if its
    artifact moved. Raises Refused with every fault, having written nothing."""
    try:
        return _round(held, operations, signed, clock)
    except port.Conflict:
        with held.exclusive():
            return _round(held, operations, signed, clock)


def _round(held: port.Port, operations: list, signed: Signed, clock: journal.Clock | None) -> Landed:
    """The set drafted, its moments read from the clock after the draft, and landed."""
    drafted = drafting.drafted(held, operations)
    return _landing(held, drafted, signed, journal.moments(len(drafted.changes), clock))


def _landing(held: port.Port, drafted: drafting.Drafted, signed: Signed, moments: list) -> Landed:
    """The drafted set landed, one entry per change, under ids minted at its moments now."""
    stamps = journal.minted(held, moments)
    batch = stamps[0].id
    entries = [
        journal.change(
            signed=signed, op=change.op, artifact=str(change.artifact_id), path=change.path, revision=change.revision,
            schema_version=change.schema_version, text=text, stamp=stamp, batch=batch,
        )
        for change, text, stamp in zip(drafted.changes, drafted.texts, stamps, strict=True)
    ]
    _landed(held, drafted, entries)
    return Landed(batch, [Result(change.artifact_id, change.revision, change.item) for change in drafted.changes])


def _landed(held: port.Port, drafted: drafting.Drafted, entries: list) -> None:
    """The set handed to the port; a link the port finds into what the set takes out is refused, one fault for each,
    the item named for a part dropped and the artifact for one removed; a link the set hands that the port finds
    landing on nothing it may land on is refused as validation refuses it."""
    try:
        held.land(drafted.handed, entries, drafted.relinks, drafted.kinds)
    except port.Linked as linked:
        raise Refused([
            refusals.still_linked(_named(drafted.draft, each), each.source, each.place) for each in linked.links
        ]) from linked
    except port.Unlanded as unlanded:
        raise Refused([
            refusals.unlanded(str(each.source), each.place, _landing_on(each)) for each in unlanded.links
        ]) from unlanded


def _named(draft: Draft, link: port.Linking) -> str:
    """What a link into what a set takes out lands on: the item, for a part of an artifact the set keeps, or the
    artifact."""
    return _landing_on(link) if draft.holds(link.target) else str(link.target)


def _landing_on(link: port.Linking) -> str:
    """Where a link lands, as it is written: the artifact, and the place of the part inside it after `#`."""
    return f"{link.target}#{link.part}" if link.part else str(link.target)


def record(held: port.Port, named: list, signed: Signed, clock: journal.Clock | None = None) -> str:
    """One history entry listing each artifact named as it stands now, every one read at one moment, stamped by the
    clock, and landed as a set of its own once that reading is done; stamped and landed again while the port holds
    the write lock when another entry took its id first. Returns the entry's id; raises Refused, having written
    nothing, when a name did not convert or the store lacks it."""
    with held.at_one_moment():
        read = query.snapshotted(held, named)
    try:
        return _snapshot(held, read, signed, clock)
    except port.Conflict:
        with held.exclusive():
            return _snapshot(held, read, signed, clock)


def _snapshot(held: port.Port, read: list, signed: Signed, clock: journal.Clock | None) -> str:
    [stamp] = journal.stamps(held, 1, clock)
    entry = journal.snapshot(signed=signed, read=read, stamp=stamp)
    held.land([], [entry])
    return entry.id
