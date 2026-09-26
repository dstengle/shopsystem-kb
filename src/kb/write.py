"""The write path: a set of operations applied in order to a draft of the store and checked there, against the store
as the operations before it left it; only when every one passes is anything written, each artifact saved, one journal
entry per operation naming the set, and one commit. A fault anywhere refuses the whole set with every fault found,
and nothing is written. Starting a store and recording a snapshot write and commit here too."""
from pathlib import Path

from kb import canonical, edits, journal, requests
from kb.contract import kb_pb2
from kb.metaschema import METASCHEMA
from kb.edits import Change
from kb.store import Draft, Store
from kb.values import Actor, ArtifactId, Kind, Refused, Signed

METASCHEMA_ID = ArtifactId(Kind("schema"), "schema")


def start(root: Path, actor: Actor) -> None:
    """A new store at root, holding the type of types, its start in the journal and in one commit."""
    store, signed = Store(root), Signed(actor, "initialise store")
    store.start()
    metaschema = {"id": str(METASCHEMA_ID), "type": "schema", "schema_version": 1, "revision": 1, **METASCHEMA}
    path = store.save(METASCHEMA_ID, canonical.dump(canonical.order(metaschema, METASCHEMA["schema"])))
    entry = journal.write(
        store.dir, signed=signed, op="create", artifact=str(METASCHEMA_ID), path="",
        revision=1, schema_version=1, written=path,
    )
    store.commit([store.dir / "store.yaml", path, entry], signed)


def land(store: Store, operations: list, signed: Signed) -> kb_pb2.ApplyResponse:
    """The set drafted, serialised, then written and committed; refused with every fault before anything is written."""
    try:
        draft, changes = _drafted(store, operations)
        texts = _serialised(draft, changes)
    except Refused as refused:
        return kb_pb2.ApplyResponse(faults=refused.faults)
    return _written(store, draft, texts, signed)


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


def _serialised(draft: Draft, changes: list[Change]) -> list[tuple[Change, str | None]]:
    """Each change with the canonical text of what it leaves, None for a removal; refused if any cannot be written."""
    texts, faults = [], []
    for change in changes:
        if change.op == "delete":
            texts.append((change, None))
            continue
        try:
            texts.append((change, canonical.dump(draft.load(change.artifact_id))))
        except canonical.NotCanonical as fault:
            faults.append(kb_pb2.Fault(artifact=str(change.artifact_id), rule="content", message=str(fault)))
    if faults:
        raise Refused(faults)
    return texts


def _written(store: Store, draft: Draft, texts: list, signed: Signed) -> kb_pb2.ApplyResponse:
    """Each file saved or removed, its journal entry written naming the set, and all of it in one commit."""
    written, results, batch = [], [], ""
    for seq, (change, text) in enumerate(texts, start=1):
        if text is None:
            removed = store.load(change.artifact_id)
            revision, schema_version = removed["revision"] + 1, removed["schema_version"]
            path, saved = store.remove(change.artifact_id), None
        else:
            artifact = draft.load(change.artifact_id)
            revision, schema_version = artifact["revision"], artifact["schema_version"]
            path = saved = store.save(change.artifact_id, text)
        entry = journal.write(
            store.dir, signed=signed, op=change.op, artifact=str(change.artifact_id), path=change.path,
            revision=revision, schema_version=schema_version, written=saved, seq=seq, batch=batch,
        )
        batch = batch or entry.stem
        written += [path, entry]
        results.append(kb_pb2.Result(id=str(change.artifact_id), revision=revision, item=change.item))
    store.commit(written, signed)
    return kb_pb2.ApplyResponse(batch=batch, results=results)
