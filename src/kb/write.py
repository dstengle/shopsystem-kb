"""The write path: a set of operations applied in order to a draft of the store and checked there, against the store
as the operations before it left it; only when every one passes is anything written, each artifact saved, one journal
entry per operation naming the set, and one commit. A fault anywhere refuses the whole set with every fault found,
and nothing is written. Starting a store and recording a snapshot write and commit here too."""
from pathlib import Path
from typing import NamedTuple

from kb import canonical, edits, journal, refusals, requests
from kb.metaschema import METASCHEMA
from kb.edits import Change
from kb.store import Draft, Store
from kb.values import Actor, ArtifactId, Kind, Refused, Signed

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
    """A change as it will be written: its canonical text, None for a removal, and the versions its entry records."""
    change: Change
    text: str | None
    revision: int
    schema_version: int


def start(root: Path, actor: Actor) -> None:
    """A new store at root, holding the type of types, its start in the journal and in one commit."""
    store, signed = Store(root), Signed(actor, "initialise store")
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
    draft, changes = _drafted(store, operations)
    return _written(store, _serialised(draft, changes), signed)


def record(store: Store, read: list[dict], signed: Signed) -> str:
    """One journal entry listing what a piece of work read, in a commit of its own. Returns the entry's id."""
    entry = journal.snapshot(store.dir, signed=signed, read=read)
    store.commit([entry], signed)
    return entry.stem


def _drafted(store: Store, operations: list) -> tuple[Draft, list[Change]]:
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
    return draft, changes


def _serialised(draft: Draft, changes: list[Change]) -> list[Landing]:
    """Each change as it will be written, settled from the draft; refused if any cannot be written."""
    landings, found = [], []
    for change in changes:
        if change.op == "delete":
            landings.append(Landing(change, None, change.revision, change.schema_version))
            continue
        artifact = draft.load(change.artifact_id)
        try:
            landings.append(Landing(change, canonical.dump(artifact), artifact["revision"], artifact["schema_version"]))
        except canonical.NotCanonical as fault:
            found.append(refusals.unwritable(change.artifact_id, str(fault)))
    if found:
        raise Refused(found)
    return landings


def _written(store: Store, landings: list[Landing], signed: Signed) -> Landed:
    """Each file saved or removed, its journal entry written naming the set, and all of it in one commit. Reads
    nothing: everything written was settled before."""
    written, results, batch = [], [], ""
    for seq, (change, text, revision, schema_version) in enumerate(landings, start=1):
        if text is None:
            path = store.remove(change.artifact_id)
        else:
            path = store.save(change.artifact_id, text)
        entry = journal.write(
            store.dir, signed=signed, op=change.op, artifact=str(change.artifact_id), path=change.path,
            revision=revision, schema_version=schema_version, text=text, seq=seq, batch=batch,
        )
        batch = batch or entry.stem
        written += [path, entry]
        results.append(Result(change.artifact_id, revision, change.item))
    store.commit(written, signed)
    return Landed(batch, results)
