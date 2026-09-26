"""The write path: a set of operations applied in order to a draft of the store and checked there, against the store
as the operations before it left it; only when every one passes is anything written, each artifact saved, one journal
entry per operation naming the set, and one commit. A fault anywhere refuses the whole set with every fault found,
and nothing is written. Starting a store and recording a snapshot write and commit here too."""
from typing import NamedTuple

from kb import canonical, edits, journal, query, refusals, requests
from kb.metaschema import METASCHEMA
from kb.edits import Change
from kb.store import Draft, Store, vacant
from kb.values import Actor, ArtifactId, Kind, Refused, Root, Signed

METASCHEMA_ID = ArtifactId(Kind("schema"), "schema")


class Result(NamedTuple):
    """What a set did to one artifact: its version now, and, for an item added, the item's name."""
    artifact_id: ArtifactId
    revision: int
    item: str


class Landed(NamedTuple):
    """A set written: the name of the set, and what it did to each artifact, in the order of its operations."""
    batch: str
    results: list[Result]


class Landing(NamedTuple):
    """A change as it will be written: its canonical text as the change left the artifact, None for a removal, and
    whether the file is written with it, which it is only for the last change the set makes to that artifact."""
    change: Change
    text: str | None
    last: bool


def start(root: Root, actor: Actor) -> None:
    """A new store at root, holding the type of types, its start in the journal and in one commit. Raises Refused
    where no store can be started."""
    vacant(root)
    store, signed = Store(root.path), Signed(actor, "initialise store")
    store.start()
    metaschema = {"id": str(METASCHEMA_ID), "type": "schema", "schema_version": 1, "revision": 1, **METASCHEMA}
    text = canonical.dump(canonical.order(metaschema, METASCHEMA["schema"]))
    path = store.save(METASCHEMA_ID, text)
    entry = journal.write(
        store.dir, signed=signed, op="create", artifact=str(METASCHEMA_ID), path="",
        revision=1, schema_version=1, text=text,
    )
    store.commit([store.dir / "store.yaml", path, entry], signed)


def land(store: Store, operations: list, signed: Signed) -> Landed:
    """The set drafted, serialised, then written and committed. Raises Refused with every fault, having written
    nothing."""
    changes = _drafted(store, operations)
    return _written(store, _serialised(changes), signed)


def record(store: Store, named: list, signed: Signed) -> str:
    """One journal entry listing each artifact named as it stands now, in a commit of its own. Returns the entry's
    id; raises Refused, having written nothing, when a name did not convert or the store lacks it."""
    entry = journal.snapshot(store.dir, signed=signed, read=query.snapshotted(store, named))
    store.commit([entry], signed)
    return entry.stem


def _drafted(store: Store, operations: list) -> list[Change]:
    """Every operation applied in order to a draft; refused with the faults of every operation that fails."""
    draft = Draft(store)
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


def _serialised(changes: list[Change]) -> list[Landing]:
    """Each change as it will be written, settled as the change left its artifact; refused if any cannot be written."""
    last = {change.artifact_id: index for index, change in enumerate(changes)}
    landings, found = [], []
    for index, change in enumerate(changes):
        try:
            text = None if change.left is None else canonical.dump(change.left)
        except canonical.NotCanonical as fault:
            found.append(refusals.unwritable(change.artifact_id, str(fault)))
            continue
        landings.append(Landing(change, text, last[change.artifact_id] == index))
    if found:
        raise Refused(found)
    return landings


def _written(store: Store, landings: list[Landing], signed: Signed) -> Landed:
    """Each file saved or removed, its journal entry written naming the set, and all of it in one commit. Reads
    nothing: everything written was settled before."""
    written, results, batch = [], [], ""
    for seq, (change, text, last) in enumerate(landings, start=1):
        if last:
            written.append(_file(store, change.artifact_id, text))
        entry = journal.write(
            store.dir, signed=signed, op=change.op, artifact=str(change.artifact_id), path=change.path,
            revision=change.revision, schema_version=change.schema_version, text=text, seq=seq, batch=batch,
        )
        batch = batch or entry.stem
        written.append(entry)
        results.append(Result(change.artifact_id, change.revision, change.item))
    store.commit(written, signed)
    return Landed(batch, results)


def _file(store: Store, artifact_id: ArtifactId, text: str | None):
    """The artifact's file written with its text, or taken out when there is none; where it is."""
    return store.remove(artifact_id) if text is None else store.save(artifact_id, text)
