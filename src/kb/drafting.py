"""A set drafted against the store as it stands: its operations applied in order to a draft, each acting on it as
the operations before it left it, then every change checked, its content, its links and a type as a type, against the
store as the whole set leaves it, and a set with no other fault refused for every link from outside it into a part one
of its changes drops; each change then as the port takes it, with the revisions of
the types it was read through and the IRIs where a type could be defined nearer, as holding nothing (kb.standing);
and whether the set lands only as drafted while the write lock is held. The imports a set makes of one type's versions are handed one after another, in the order of
their numbers whatever order the set gave them in, each the version its file names at the revision its file gives, read
at the revision the one before it left the type at, the first at the revision the store's type stands at when
it is a version above the one that type stands at; an imported artifact is checked, and its links read, through the
version of its type its file names. Only
what the set changes is handed: a type's change restates the links of no artifact, which stay as the version it
conforms to declares them. A fault anywhere refuses the whole set with every fault found."""
from typing import NamedTuple

from kb import (
    composition, definitions, edits, fault_order, handing, names, port, port_values, refusals, requests, settled,
    standing, validation, values,
)
from kb.draft import Draft
from kb.edits import Change
from kb.values import Refused


class Drafted(NamedTuple):
    """A set drafted against the store as it stood: the draft, its changes, their texts, the changes as the port
    takes them, and whether it lands only as drafted while the write lock is held, the port comparing nothing that
    would show what landed since: a set that removes a type (a type made that reads it, a link landed that waits
    under it), one that defines a type (an artifact or a link landed under its IRI), and one that makes or links
    to something below an artifact where a type could be defined in that artifact's place (kb.standing)."""
    draft: Draft
    changes: list[Change]
    texts: list[str | None]
    handed: list[port_values.Change]
    locked: bool


def drafted(held: port.Port, operations: list) -> Drafted:
    """The set drafted and serialised against the store as it stands, each change as the port takes it."""
    draft = Draft(held)
    changes = _drafted(draft, _by_number(operations))
    texts = handing.serialised(changes)
    _kept_whole(draft, changes)
    last = {change.artifact_id: index for index, change in enumerate(changes)}
    handed = [
        handing.handed(draft, change, read, last[change.artifact_id] == index)
        for index, (change, read) in enumerate(zip(changes, _read_at(held, changes), strict=True))
    ]
    handed, below = standing.guarded(handed, draft)
    locked = below or any(standing.removes_a_type(change) or standing.defines_a_type(change) for change in changes)
    return Drafted(draft, changes, texts, handed, locked)


def _by_number(operations: list) -> list:
    """The set's operations, the imports it makes of one type's versions put in the order of their numbers, in the
    places the set gave those imports, whatever order it gave them in: so the type stands at the highest."""
    places: dict = {}
    for index, operation in enumerate(operations):
        if isinstance(operation, edits.Import) and type(operation.artifact.get("version")) is int:
            places.setdefault(operation.artifact_id, []).append(index)
    ordered = list(operations)
    for indices in places.values():
        by_number = sorted((operations[index] for index in indices), key=lambda each: each.artifact["version"])
        for index, operation in zip(indices, by_number):
            ordered[index] = operation
    return ordered


def _read_at(held: port.Port, changes: list[Change]) -> list[int]:
    """The revision each change read its artifact at: the one before the one it leaves; or, for an import, which
    keeps the revision its file gives, the one the set's change before it left that artifact at, and for the first
    the one the store's type stands at when it brings a version above the one that type stands at, else 0, as not
    held. So the versions of one type a set imports land one after another, the type standing at the last."""
    left, read = {}, []
    for change in changes:
        before = left.get(change.artifact_id)
        if change.op != "import":
            read.append(change.revision - 1)
        else:
            read.append(_gained_at(held, change) if before is None else before)
        left[change.artifact_id] = change.revision
    return read


def _gained_at(held: port.Port, change: Change) -> int:
    """The revision a type the store holds stands at, for an import of a version of it above the one it stands at;
    0 for any other import, which lands only where nothing is held."""
    if not (settled.typed(change.left) and held.holds(change.artifact_id)):
        return 0
    stands = held.artifact(change.artifact_id)
    above = settled.typed(stands) and stands["version"] < change.left["version"]
    return stands["revision"] if above else 0


def _drafted(draft: Draft, operations: list) -> list[Change]:
    """Every operation applied in order to a draft, then what the set leaves checked once; refused with every fault,
    in the order of the operations they belong to."""
    outcomes = [_acted(draft, operation) for operation in operations]
    changes = [each for each in outcomes if isinstance(each, Change)]
    last = {change.artifact_id: change for change in changes}
    faults = [fault for outcome in outcomes for fault in _faults(draft, outcome)]
    if faults:
        raise Refused(faults)
    return [handing.versioned(draft, change, last[change.artifact_id] is change) for change in changes]


def _acted(draft: Draft, operation) -> Change | list:
    """What one operation did to the draft, or the faults it was refused with as it acted."""
    if isinstance(operation, requests.Refusal):
        return list(operation.faults)
    try:
        return edits.apply(draft, operation)
    except Refused as refused:
        return list(refused.faults)


def _faults(draft: Draft, outcome: Change | list) -> list:
    """An operation's faults: those it was refused with as it acted; for a removal, every link the set leaves pointing
    at what it removed, then what stands in the way of a type's removal; for a change, those it found as it acted,
    then what it left against its type as the set leaves it, and, for every change the set makes to a type, each
    making a version that is kept, what it left checked as a type."""
    if not isinstance(outcome, Change):
        return outcome
    if outcome.left is None:
        return [
            refusals.still_linked(str(outcome.artifact_id), each.source, each.place)
            for each in draft.links_in(outcome.artifact_id) if each.source != outcome.artifact_id
        ] + standing.in_the_way(draft, outcome)
    faults = [*outcome.faults, *_fits(draft, outcome)]
    typed = composition.artifact_kind(outcome.left) == values.TYPE_KIND
    if not faults and typed:
        faults = definitions.faults(outcome.artifact_id, settled.checked(outcome.left), draft)
    return _in_order(draft, outcome, faults)


def _kept_whole(draft: Draft, changes: list[Change]) -> None:
    """Refused, when the set has no other fault, with every link into a part the store held in an artifact and the
    set leaves it without, from an artifact the set leaves as it is (one the set changes is checked as it leaves it):
    the artifacts in the order the set first changes them, the links into each in the order of the names of the
    artifacts holding them, the part named as a link writes it."""
    dropped = {change.artifact_id: draft.dropped(change.artifact_id) for change in changes}
    linked = [
        refusals.still_linked(names.pointing(artifact_id, each.part), each.source, each.place)
        for artifact_id, gone in dropped.items() if gone
        for each in draft.links_in(artifact_id) if each.part in gone and not draft.changed(each.source)
    ]
    if linked:
        raise Refused(linked)


def _in_order(draft: Draft, change: Change, faults: list) -> list:
    """A change's faults in the order its artifact reads back, read through the type it is checked against."""
    if len(faults) < 2:
        return faults
    try:
        declared = composition.declared(handing.typed(draft, change)["schema"], draft)
    except Refused:
        return faults
    return fault_order.ordered(faults, settled.checked(change.left), declared)


def _fits(draft: Draft, change: Change) -> list:
    """Every fault of what a change left against its type, its links landing, both as the set leaves them, but
    that a link the store already held waiting still waits, and so does each an import brings into a part its held
    target lacks."""
    try:
        schema = handing.typed(draft, change)
    except Refused as refused:
        return list(refused.faults)
    waited = draft.waited(change.artifact_id)
    return validation.validate(
        str(change.artifact_id), settled.checked(change.left), schema["schema"], draft, waited, change.op == "import",
    )
