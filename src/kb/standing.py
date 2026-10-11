"""What a type's place is settled by (decision/a-types-place-is-settled-by-what-sits-under-it): an IRI belongs to
the nearest held type it sits under, and what is held or waited on there fixes that. What already sits under an IRI a
type would be defined at, read from the draft as it stands, so a define is judged against the operations before it in
its set, as slice 158's identity check is; and, for a set as the port takes it, the IRIs at which a type defined
before the set lands would stand nearer to what it makes or links to than the type it was drafted under, each handed
as holding nothing, so the port refuses the set once something has landed at one."""
import dataclasses

from kb import composition, names, port, values

TYPE_OF_TYPES = values.type_of(values.TYPE_KIND)


def under(type_id: values.ArtifactId, draft) -> tuple[values.ArtifactId | None, list[values.ArtifactId]]:
    """The nearest held type an IRI a type would be defined at sits under, None for one under no held type, and
    every IRI under the new type's that belongs to that other type: each artifact of its kind the draft holds there,
    but under the type of types, to which no type belongs by where it sits (decision/type-iris-are-free); and each
    IRI not held a link waits on there with no nearer held type above it, and the new type's own IRI when a link
    waits on it, whole or on a part of it, but under the type of types, where the type defined is the artifact of
    that type the link waits on; once each, in the order of their names."""
    other = composition.nearest_type(type_id, draft)
    if other is None:
        return None, []
    kept = [] if other == TYPE_OF_TYPES else draft.ids(values.Kind(str(other)))
    held = [each for each in kept if str(type_id) in names.above(each)]
    own = [] if other == TYPE_OF_TYPES else [type_id]
    waited = [
        each.target for each in draft.waiting()
        if each.target in own or composition.nearest_was(each.target, type_id, draft)
    ]
    return other, sorted({*held, *waited}, key=names.order)


def guarded(handed: list[port.Change], draft) -> tuple[list[port.Change], bool]:
    """A set's changes as the port takes them, each saying, beside the types it was read through, that nothing is
    held, revision 0, at each IRI where a type could be defined nearer (`_open`): the port then refuses the set
    when anything landed at one since. An IRI the set itself changes is left out, its own change being compared
    there. And whether the draft holds something at one of them, which is handed for none: an artifact that is no
    type may be removed and a type defined there at the revision it stood at, so no revision tells them apart."""
    found = [[each for each in _open(change) if not draft.changed(each)] for change in handed]
    held = {each: draft.holds(each) for gap in found for each in gap}
    return [
        dataclasses.replace(change, through=(*change.through, *((each, 0) for each in gap if not held[each])))
        for change, gap in zip(handed, found, strict=True)
    ], any(held.values())


def _open(change: port.Change) -> list[values.ArtifactId]:
    """Each IRI, once, at which a type defined before a change lands would take what the change makes or links to
    from the type it was drafted under: those between a new artifact's IRI and its type's, never a type's, whose
    IRI is free; and those between the target of each link it hands, held or not, since one held may be removed
    before the link lands, and the type that target was found under."""
    if change.content is None:
        return []
    made = change.read == 0 and change.kind != values.TYPE_KIND
    own = _between(change.artifact, values.type_of(change.kind)) if made else []
    linked = [
        each for link in change.links if link.under is not None and not link.implicit
        for each in _between(link.target, link.under)
    ]
    return list(dict.fromkeys([*own, *linked]))


def _between(artifact_id: values.ArtifactId, type_id: values.ArtifactId) -> list[values.ArtifactId]:
    """The IRIs an IRI sits under that sit under a type's; none for an IRI that does not sit under the type's."""
    above = names.above(artifact_id)
    return [values.ArtifactId(each) for each in above[:above.index(str(type_id))]] if str(type_id) in above else []
