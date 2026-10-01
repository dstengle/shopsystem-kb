"""The write path: a set of operations applied in order to a draft of the store and checked there, against the store
as the operations before it left it; only when every one passes is each entry's stamp settled by the clock and the
set handed to the port, which lands every change and one entry per operation naming the set in one transaction. A
fault anywhere refuses the whole set with every fault found, and nothing is written. Starting a store and recording
a snapshot land through the port too."""
from typing import NamedTuple

from kb import canonical, edits, journal, links, places, port, query, refusals, requests, settled, store, values
from kb.draft import Draft
from kb.edits import Change
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
    created = port.Change(METASCHEMA_ID, metaschema, revision=1)
    store.start(root, lambda made: made.land([created], [entry]))


def land(held: port.Port, operations: list, signed: Signed, clock: journal.Clock | None = None) -> Landed:
    """The set drafted and serialised, each entry's stamp settled by the clock, then landed. Raises Refused with
    every fault, having written nothing."""
    draft = Draft(held)
    changes = _drafted(draft, operations)
    texts = _serialised(changes)
    handed = [_handed(draft, change) for change in changes]
    stamps = journal.stamps(held, len(changes), clock)
    batch = stamps[0].id
    entries = [
        journal.change(
            signed=signed, op=change.op, artifact=str(change.artifact_id), path=change.path, revision=change.revision,
            schema_version=change.schema_version, text=text, stamp=stamp, batch=batch,
        )
        for change, text, stamp in zip(changes, texts, stamps, strict=True)
    ]
    held.land(handed, entries)
    return Landed(batch, [Result(change.artifact_id, change.revision, change.item) for change in changes])


def record(held: port.Port, named: list, signed: Signed, clock: journal.Clock | None = None) -> str:
    """One history entry listing each artifact named as it stands now, stamped by the clock, landed as a set of its
    own. Returns the entry's id; raises Refused, having written nothing, when a name did not convert or the store
    lacks it."""
    read = query.snapshotted(held, named)
    [stamp] = journal.stamps(held, 1, clock)
    entry = journal.snapshot(signed=signed, read=read, stamp=stamp)
    held.land([], [entry])
    return entry.id


def _drafted(draft: Draft, operations: list) -> list[Change]:
    """Every operation applied in order to a draft; refused with the faults of every operation that fails."""
    changes, faults = [], []
    for operation in operations:
        if isinstance(operation, requests.Refusal):
            faults += operation.faults
            continue
        try:
            changes.append(edits.apply(draft, operation))
        except Refused as refused:
            faults += refused.faults
    if faults:
        raise Refused(faults)
    return changes


def _serialised(changes: list[Change]) -> list[str | None]:
    """Each change's canonical text as the change left its artifact, None for a removal; refused if any cannot be
    written."""
    texts, found = [], []
    for change in changes:
        try:
            texts.append(None if change.left is None else canonical.dump(change.left))
        except canonical.NotCanonical as fault:
            found.append(refusals.unwritable(change.artifact_id, str(fault)))
    if found:
        raise Refused(found)
    return texts


def _handed(draft: Draft, change: Change) -> port.Change:
    """A change as the port takes it: its content, its links and the places of its parts as it left the artifact,
    read at the revision before the one it leaves."""
    if change.left is None:
        return port.Change(change.artifact_id, None, read=change.revision - 1, revision=change.revision)
    return port.Change(
        change.artifact_id, change.left, tuple(links.handed(change.artifact_id, change.left, draft)),
        tuple(places.parts(change.left)), change.revision - 1, change.revision,
    )
