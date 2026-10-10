"""A set drafted against the store as it stands: its operations applied in order to a draft, each acting on it as
the operations before it left it, then every artifact the set touched checked once, its content, its links and a type
as a type, against the store as the whole set leaves it; each change then as the port takes it, with the revisions of
the types it was read through. Only what the set changes is handed: a type's change restates the links of no
artifact, which stay as the version it conforms to declares them. A fault anywhere refuses the whole set with every
fault found."""
from typing import NamedTuple

from kb import (
    canonical, composition, definitions, edits, fault_order, links, names, places, port, refusals, requests,
    search, settled, validation, values,
)
from kb.draft import Draft
from kb.edits import Change
from kb.values import Refused


class Drafted(NamedTuple):
    """A set drafted against the store as it stood: the draft, its changes, their texts, and the changes as the port
    takes them."""
    draft: Draft
    changes: list[Change]
    texts: list[str | None]
    handed: list[port.Change]


def drafted(held: port.Port, operations: list) -> Drafted:
    """The set drafted and serialised against the store as it stands, each change as the port takes it."""
    draft = Draft(held)
    changes = _drafted(draft, operations)
    texts = _serialised(changes)
    last = {change.artifact_id: index for index, change in enumerate(changes)}
    handed = [_handed(draft, change, last[change.artifact_id] == index) for index, change in enumerate(changes)]
    return Drafted(draft, changes, texts, handed)


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
    typed = composition.artifact_kind(outcome.left) == values.TYPE_KIND
    if not faults and last[outcome.artifact_id] is outcome and typed:
        faults = definitions.faults(outcome.artifact_id, settled.checked(outcome.left), draft)
    return _in_order(draft, outcome, faults)


def _in_order(draft: Draft, change: Change, faults: list) -> list:
    """A change's faults in the order its artifact reads back, read through the type it is checked against."""
    if len(faults) < 2:
        return faults
    try:
        declared = composition.declared(_typed(draft, change)["schema"], draft)
    except Refused:
        return faults
    return fault_order.ordered(faults, settled.checked(change.left), declared)


def _fits(draft: Draft, change: Change) -> list:
    """Every fault of what a change left against its type, its links landing, both as the set leaves them."""
    try:
        schema = _typed(draft, change)
    except Refused as refused:
        return list(refused.faults)
    return validation.validate(str(change.artifact_id), settled.checked(change.left), schema["schema"], draft)


def _typed(draft: Draft, change: Change) -> dict:
    """The type a change is checked against: the version of its type its artifact conforms to as the change left it
    (the one a create or a replacement names, else the one it conformed to), whatever its type stands at; for an
    import, its kind's as the set leaves it; or, for an artifact the set later removes when it leaves no such type,
    as the change acted on it. Raises Refused when an artifact the set leaves has no type."""
    kind = composition.artifact_kind(change.left)
    if not draft.holds(change.artifact_id) and not draft.holds(values.type_of(kind)):
        return change.acted
    if change.op == "import":
        return composition.kind_schema(kind, draft)
    return composition.conformed(change.left, draft)


def _versioned(draft: Draft, change: Change, last: bool) -> Change:
    """A change recording the version of the type it was checked against, its entries in the order that type
    declares; the last the set makes to an artifact put in the draft so. An import keeps the version it was written
    against."""
    if change.left is None or change.op == "import":
        return change
    schema = _typed(draft, change)
    version = names.versioned(settled.kind(change.left), schema["version"])
    left = settled.order({**change.left, "type": version}, composition.declared(schema["schema"], draft))
    if last:
        draft.put(change.artifact_id, left)
    return change._replace(type=version, left=left)


def _serialised(changes: list[Change]) -> list[str | None]:
    """Each change's canonical text as the change left its artifact, None for a removal; refused if any cannot be
    written."""
    texts, found = [], []
    for change in changes:
        try:
            texts.append(None if change.left is None else canonical.dump(change.left))
        except canonical.NotCanonical as fault:
            found.append(refusals.unwritable(change.artifact_id, str(fault), fault.path))
    if found:
        raise Refused(found)
    return texts


def _handed(draft: Draft, change: Change, last: bool) -> port.Change:
    """A change as the port takes it, read at the revision before the one it leaves, or, for an import, as not held:
    its content as it left the artifact with the rows it is found by, and, for the last change the set makes to that
    artifact, its links and the places of its parts as the set leaves them, read through the type it was checked
    against, with the revisions of the types it is read through that the set leaves as they are."""
    read = 0 if change.op == "import" else change.revision - 1
    if change.left is None:
        return port.Change(change.artifact_id, None, read=read, revision=change.revision)
    searched, kind = tuple(search.searchable(change.left)), composition.artifact_kind(change.left)
    version = _stands_at(change.left) if kind == values.TYPE_KIND else None
    if not last:
        return port.Change(
            change.artifact_id, change.left, read=read, revision=change.revision, searched=searched, kind=kind,
            version=version,
        )
    return port.Change(
        change.artifact_id, change.left,
        tuple(links.handed(change.artifact_id, change.left, draft, _typed(draft, change))),
        tuple(places.parts(change.left)), read, change.revision,
        draft.as_read(composition.read_through(kind, draft)), searched, kind, version,
    )


def _stands_at(held: dict) -> port.Versioned:
    """The version a type stands at as the port takes it: of the kind its IRI names, the number and the title it
    holds."""
    return port.Versioned(values.Version(values.Kind(held["id"]), held["version"]), held["title"])
