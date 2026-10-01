"""The write path: a set of operations applied in order to a draft of the store, each acting on it as the operations
before it left it, then every artifact the set touched checked once, its content, its links and a type as a type,
against the store as the whole set leaves it; only when every one passes is each entry's stamp settled by the clock
and the set handed to the port, which lands every change and one entry per operation naming the set in one
transaction. A fault anywhere refuses the whole set with every fault found, and nothing is written. Starting a store
and recording a snapshot land through the port too."""
from typing import NamedTuple

from kb import (
    canonical, composition, definitions, edits, journal, links, places, port, query, refusals, requests, settled, store,
    validation, values,
)
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
    last = {change.artifact_id: index for index, change in enumerate(changes)}
    handed = [_handed(draft, change, last[change.artifact_id] == index) for index, change in enumerate(changes)]
    relinks = [
        port.Relink(each, tuple(links.handed(each, draft.artifact(each), draft)), draft.artifact(each)["revision"])
        for each in draft.stale()
    ]
    stamps = journal.stamps(held, len(changes), clock)
    batch = stamps[0].id
    entries = [
        journal.change(
            signed=signed, op=change.op, artifact=str(change.artifact_id), path=change.path, revision=change.revision,
            schema_version=change.schema_version, text=text, stamp=stamp, batch=batch,
        )
        for change, text, stamp in zip(changes, texts, stamps, strict=True)
    ]
    _landed(held, draft, handed, entries, relinks)
    return Landed(batch, [Result(change.artifact_id, change.revision, change.item) for change in changes])


def _landed(held: port.Port, draft: Draft, handed: list[port.Change], entries: list, relinks: list) -> None:
    """The set handed to the port; a link the port finds into what the set takes out is refused, one fault for each,
    the item named for a part dropped and the artifact for one removed."""
    try:
        held.land(handed, entries, relinks)
    except port.Linked as linked:
        raise Refused([
            refusals.still_linked(
                f"{each.target}#{each.part}" if each.part and draft.holds(each.target) else str(each.target),
                each.source, each.place,
            )
            for each in linked.links
        ]) from linked


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
    """Every operation applied in order to a draft, then what the set leaves checked once; refused with every fault,
    in the order of the operations they belong to."""
    outcomes = [_acted(draft, operation) for operation in operations]
    changes = [each for each in outcomes if isinstance(each, Change)]
    last = {change.artifact_id: change for change in changes}
    faults = [fault for outcome in outcomes for fault in _faults(draft, outcome, last)]
    if faults:
        raise Refused(faults)
    return [_versioned(draft, change, last[change.artifact_id] is change) for change in changes]


def _acted(draft: Draft, operation) -> Change | list:
    """What one operation did to the draft, or the faults it was refused with as it acted."""
    if isinstance(operation, requests.Refusal):
        return list(operation.faults)
    try:
        return edits.apply(draft, operation)
    except Refused as refused:
        return list(refused.faults)


def _faults(draft: Draft, outcome: Change | list, last: dict) -> list:
    """An operation's faults: those it was refused with as it acted; for a removal, every link the set leaves pointing
    at what it removed; for a change, the names it handed back that the artifact did not hold, and, for the last the
    set makes to an artifact, the artifact as the set leaves it against its type as the set leaves it."""
    if not isinstance(outcome, Change):
        return outcome
    return [*outcome.faults, *_left(draft, outcome, last)]


def _left(draft: Draft, outcome: Change, last: dict) -> list:
    """What a change leaves refused for, judged against the state the whole set leaves."""
    if outcome.left is None:
        return [
            refusals.still_linked(str(outcome.artifact_id), each.source, each.place)
            for each in draft.links_in(outcome.artifact_id) if each.source != outcome.artifact_id
        ]
    if last[outcome.artifact_id] is not outcome:
        return []
    try:
        return _fits(draft, outcome.artifact_id)
    except Refused as refused:
        return list(refused.faults)


def _fits(draft: Draft, artifact_id: ArtifactId) -> list:
    """Every fault of an artifact against its type, both as the set leaves them; a type, once it fits the type of
    types, checked as a type too."""
    checked = settled.checked(draft.artifact(artifact_id))
    faults = validation.validate(
        str(artifact_id), checked, composition.kind_schema(artifact_id.kind, draft)["schema"], draft,
    )
    if not faults and artifact_id.kind == values.TYPE_KIND:
        faults = definitions.faults(artifact_id, checked, draft)
    return faults


def _versioned(draft: Draft, change: Change, last: bool) -> Change:
    """The last change the set makes to an artifact, recording the version of its type as the set leaves it, the one
    it was checked against, its entries in the order that type declares, and put in the draft so; any other change as
    it acted."""
    if change.left is None or not last:
        return change
    schema = composition.kind_schema(change.artifact_id.kind, draft)
    left = settled.order(
        {**change.left, "schema_version": schema["version"]}, composition.declared(schema["schema"], draft),
    )
    draft.put(change.artifact_id, left)
    return change._replace(schema_version=schema["version"], left=left)


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


def _handed(draft: Draft, change: Change, last: bool) -> port.Change:
    """A change as the port takes it, read at the revision before the one it leaves: its content as it left the
    artifact, and, for the last change the set makes to that artifact, its links and the places of its parts as the
    set leaves them, read through the types as the set leaves them."""
    if change.left is None or not last:
        return port.Change(change.artifact_id, change.left, read=change.revision - 1, revision=change.revision)
    return port.Change(
        change.artifact_id, change.left, tuple(links.handed(change.artifact_id, change.left, draft)),
        tuple(places.parts(change.left)), change.revision - 1, change.revision,
    )
