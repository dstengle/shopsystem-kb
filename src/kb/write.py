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
ROUNDS = 10  # times a set is drafted and landed while other changes keep landing first


class Result(NamedTuple):
    """What a set did to one artifact: its version now, and, for an item added, the item's name."""
    artifact_id: ArtifactId
    revision: int
    item: str


class Drafted(NamedTuple):
    """A set drafted against the store as it stood: the draft, its changes, their texts, the changes as the port takes
    them, and the links read again of what the set leaves as it is."""
    draft: Draft
    changes: list[Change]
    texts: list[str | None]
    handed: list[port.Change]
    relinks: list[port.Relink]


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
    """The set drafted against the store as it stands, each entry's moment read once from the clock, then landed. When
    another change lands between the draft and the landing, the set is drafted again against what that change left,
    its moments kept and its entries' ids minted again, up to ROUNDS times. Raises Refused with every fault, having
    written nothing."""
    moments = None
    for round_ in range(1, ROUNDS + 1):
        drafted = _drafting(held, operations)
        moments = journal.moments(len(drafted.changes), clock) if moments is None else moments
        try:
            return _landing(held, drafted, signed, moments)
        except port.Conflict:
            if round_ == ROUNDS:
                raise


def _drafting(held: port.Port, operations: list) -> Drafted:
    """The set drafted and serialised against the store as it stands, each change as the port takes it, and the
    links of what it leaves as it is read again."""
    draft = Draft(held)
    changes = _drafted(draft, operations)
    texts = _serialised(changes)
    last = {change.artifact_id: index for index, change in enumerate(changes)}
    handed = [_handed(draft, change, last[change.artifact_id] == index) for index, change in enumerate(changes)]
    relinks = [
        port.Relink(each, tuple(links.handed(each, draft.artifact(each), draft)), draft.artifact(each)["revision"])
        for each in draft.stale()
    ]
    return Drafted(draft, changes, texts, handed, relinks)


def _landing(held: port.Port, drafted: Drafted, signed: Signed, moments: list) -> Landed:
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
    _landed(held, drafted.draft, drafted.handed, entries, drafted.relinks)
    return Landed(batch, [Result(change.artifact_id, change.revision, change.item) for change in drafted.changes])


def _landed(held: port.Port, draft: Draft, handed: list[port.Change], entries: list, relinks: list) -> None:
    """The set handed to the port; a link the port finds into what the set takes out is refused, one fault for each,
    the item named for a part dropped and the artifact for one removed; a link the set hands that the port finds
    landing on nothing it may land on is refused as validation refuses it."""
    try:
        held.land(handed, entries, relinks)
    except port.Linked as linked:
        raise Refused([
            refusals.still_linked(_named(draft, each), each.source, each.place) for each in linked.links
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
    at what it removed; for a change, those it found as it acted, then what it left against its type as the set leaves
    it, and, for the last the set makes to a type, that type checked as a type."""
    if not isinstance(outcome, Change):
        return outcome
    if outcome.left is None:
        return [
            refusals.still_linked(str(outcome.artifact_id), each.source, each.place)
            for each in draft.links_in(outcome.artifact_id) if each.source != outcome.artifact_id
        ]
    faults = [*outcome.faults, *_fits(draft, outcome)]
    if not faults and last[outcome.artifact_id] is outcome and outcome.artifact_id.kind == values.TYPE_KIND:
        faults = definitions.faults(outcome.artifact_id, settled.checked(outcome.left), draft)
    return faults


def _fits(draft: Draft, change: Change) -> list:
    """Every fault of what a change left against its type, its links landing, both as the set leaves them."""
    try:
        schema = _typed(draft, change)
    except Refused as refused:
        return list(refused.faults)
    return validation.validate(str(change.artifact_id), settled.checked(change.left), schema["schema"], draft)


def _typed(draft: Draft, change: Change) -> dict:
    """The type a change is checked against: its kind's as the set leaves it, or, for an artifact the set later removes
    when it leaves no such type, as the change acted on it. Raises Refused when an artifact the set leaves has no
    type."""
    if not draft.holds(change.artifact_id) and not draft.holds(values.type_of(change.artifact_id.kind)):
        return change.acted
    return composition.kind_schema(change.artifact_id.kind, draft)


def _versioned(draft: Draft, change: Change, last: bool) -> Change:
    """A change recording the version of the type it was checked against, its entries in the order that type
    declares; the last the set makes to an artifact put in the draft so."""
    if change.left is None:
        return change
    schema = _typed(draft, change)
    left = settled.order(
        {**change.left, "schema_version": schema["version"]}, composition.declared(schema["schema"], draft),
    )
    if last:
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
