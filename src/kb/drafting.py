"""A set drafted against the store as it stands: its operations applied in order to a draft, each acting on it as
the operations before it left it, then every artifact the set touched checked once, its content, its links and a type
as a type, against the store as the whole set leaves it; each change then as the port takes it, with the revisions of
the types it was read through. A fault anywhere refuses the whole set with every fault found."""
from typing import NamedTuple

from kb import (
    canonical, composition, definitions, edits, keys, links, places, port, refusals, requests, search, settled,
    validation, values,
)
from kb.draft import Draft
from kb.edits import Change
from kb.values import Refused


class Drafted(NamedTuple):
    """A set drafted against the store as it stood: the draft, its changes, their texts, the changes as the port takes
    them, the links read again of what the set leaves as it is, and the kinds whose links it reads anew."""
    draft: Draft
    changes: list[Change]
    texts: list[str | None]
    handed: list[port.Change]
    relinks: list[port.Relink]
    kinds: tuple[values.Kind, ...]


def drafted(held: port.Port, operations: list) -> Drafted:
    """The set drafted and serialised against the store as it stands, each change as the port takes it, and the
    links of what it leaves as it is read again."""
    draft = Draft(held)
    changes = _drafted(draft, operations)
    texts = _serialised(changes)
    last = {change.artifact_id: index for index, change in enumerate(changes)}
    handed = [_handed(draft, change, last[change.artifact_id] == index) for index, change in enumerate(changes)]
    relinks = [_relinked(draft, each) for each in draft.stale()]
    return Drafted(draft, changes, texts, handed, relinks, tuple(draft.reread()))


def _relinked(draft: Draft, artifact_id: values.ArtifactId) -> port.Relink:
    """The links of an artifact the set leaves as it is, read again through the types as the set leaves them, with the
    revision it was read at and those of the types it was read through that the set leaves as they are."""
    artifact = draft.artifact(artifact_id)
    return port.Relink(
        artifact_id, tuple(links.handed(artifact_id, artifact, draft)), artifact["revision"],
        draft.as_read(composition.read_through(artifact_id.kind, draft)),
    )


def _drafted(draft: Draft, operations: list) -> list[Change]:
    """Every operation applied in order to a draft, then what the set leaves checked once; refused with every fault,
    in the order of the operations they belong to."""
    outcomes = keys.resolved(draft, operations, [_acted(draft, operation) for operation in operations])
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
    declares; the last the set makes to an artifact put in the draft so. An import keeps the version it was written
    against."""
    if change.left is None or change.op == "import":
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
    """A change as the port takes it, read at the revision before the one it leaves, or, for an import, as not held:
    its content as it left the artifact with the rows it is found by, and, for the last change the set makes to that
    artifact, its links and the places of its parts as the set leaves them, read through the types as the set leaves
    them, with the revisions of those types the set leaves as they are."""
    read = 0 if change.op == "import" else change.revision - 1
    if change.left is None:
        return port.Change(change.artifact_id, None, read=read, revision=change.revision)
    searched = tuple(search.searchable(change.left))
    if not last:
        return port.Change(change.artifact_id, change.left, read=read, revision=change.revision, searched=searched)
    return port.Change(
        change.artifact_id, change.left, tuple(links.handed(change.artifact_id, change.left, draft)),
        tuple(places.parts(change.left)), read, change.revision,
        draft.as_read(composition.read_through(change.artifact_id.kind, draft)), searched,
    )
