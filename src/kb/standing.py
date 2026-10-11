"""What already sits under an IRI a type would be defined at, and which changes a type defined before they land
could move to a type they were not drafted against (decision/a-types-place-is-settled-by-what-sits-under-it): an IRI
belongs to the nearest held type it sits under, and what is held or waited on there fixes that. Read from the draft
as it stands, so a define is judged against the operations before it in its set, as slice 158's identity check is."""
from kb import composition, names, port, values


def under(type_id: values.ArtifactId, draft) -> tuple[values.ArtifactId | None, list[values.ArtifactId]]:
    """The nearest held type an IRI a type would be defined at sits under, None for one under no held type, and
    every IRI under the new type's that belongs to that other type: each artifact of its kind the draft holds there,
    and each IRI not held a link waits on there with no nearer held type above it; once each, in the order of their
    names."""
    other = composition.nearest_type(type_id, draft)
    if other is None:
        return None, []
    held = [each for each in draft.ids(values.Kind(str(other))) if str(type_id) in names.above(each)]
    waited = [each.target for each in draft.waiting() if composition.nearest_was(each.target, type_id, draft)]
    return other, sorted({*held, *waited}, key=names.order)


def movable(change: port.Change, draft) -> bool:
    """Whether a type landing between a change's draft and its landing could leave the change against what
    stands, with nothing the port compares showing it: a define of a type, under whose IRI an artifact or a link
    may land meanwhile; a create at an IRI that does not sit directly under its type's, or a link to an IRI not
    held that does not sit directly under the type it was found under, between which a type may be defined."""
    if change.content is None:
        return False
    if change.read == 0 and (change.kind == values.TYPE_KIND or _apart(change.artifact, values.type_of(change.kind))):
        return True
    return any(
        _apart(link.target, link.under) for link in change.links
        if link.under is not None and not link.implicit and not draft.holds(link.target)
    )


def _apart(artifact_id: values.ArtifactId, type_id: values.ArtifactId) -> bool:
    """Whether an IRI lies between an IRI and the type's it sits under."""
    return names.above(artifact_id)[:1] != (str(type_id),)
