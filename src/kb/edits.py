"""What each operation of a set does to the draft: a new artifact, a whole or placed replacement, an item added to a
collection, an artifact removed. Each acts on the draft as the operations before it left it, on a copy of what it was
asked to put there, so the same set can act again on another draft, and is refused there with every fault it finds in
what it names, the revisions it makes and the names of its items; what its content and links come to is checked once
the whole set has acted (kb.write). An import puts an artifact in the draft whole, as the file it came from gives it."""
import copy
from typing import NamedTuple

from kb import changes, composition, names, places, refusals, settled, values
from kb.draft import Draft
from kb.values import ArtifactId, Refused


class Import(NamedTuple):
    """An artifact brought whole from a file for import: its name, and the artifact, identity and all."""
    artifact_id: ArtifactId
    artifact: dict


class Change(NamedTuple):
    """What one operation did, to which artifact, at which place in it, and, for an item added, the item's name; the
    version its entry records and the IRI of the type version it conforms to; the artifact as this
    operation left it, None for a removal; the type of its kind as it acted, which it is checked against when the set
    leaves none; and the faults of the names it handed back, which refuse the set while it still acts, so what it
    leaves is checked too."""
    op: str
    artifact_id: ArtifactId
    path: str = ""
    item: str = ""
    revision: int = 0
    type: str = ""
    left: dict | None = None
    acted: dict | None = None
    faults: tuple = ()


def apply(draft: Draft, operation) -> Change:
    """One operation applied to the draft. Returns what it did, settled as it did it; raises Refused."""
    if isinstance(operation, changes.Remove):
        return _delete(draft, operation)
    change = _changed(draft, operation)
    left = draft.artifact(change.artifact_id)
    acted = composition.artifact_schema(left, draft) if change.op == "import" else composition.conformed(left, draft)
    return change._replace(revision=left["revision"], type=left["type"], left=left, acted=acted)


def _changed(draft: Draft, operation) -> Change:
    if isinstance(operation, Import):
        draft.put(operation.artifact_id, copy.deepcopy(operation.artifact))
        return Change("import", operation.artifact_id)
    if isinstance(operation, changes.Create):
        return Change("create", _create(draft, operation))
    if isinstance(operation, changes.Add):
        return _append(draft, operation)
    return _replace(draft, operation)


def _create(draft: Draft, creation: changes.Create) -> ArtifactId:
    """A new artifact at the IRI its create gives, conforming to the type version it names, which the draft must
    hold."""
    schema = _named(draft, creation)
    type_id = values.type_of(creation.version.kind)
    faults = [
        *_identity(draft, creation, type_id), *creation.title_faults,
        *creation.content.refusal(str(creation.name)),
    ]
    if faults:
        raise Refused(faults)
    content = copy.deepcopy(creation.content.tree)
    if type_id == values.type_of(values.TYPE_KIND):
        _numbered(draft, creation.name, content)
    declared = composition.declared(schema["schema"], draft)
    names.items(declared["parts"], content, False, _item_parts(draft))
    artifact = settled.given(content, str(creation.name), str(creation.version), 1, creation.title)
    draft.put(creation.name, settled.order(artifact, declared))
    return creation.name


def _named(draft: Draft, creation: changes.Create) -> dict:
    """The type version a create names, whatever version its type stands at; one the draft does not hold refused
    beside the IRI its set carries twice."""
    try:
        return composition.version_schema(creation.version, draft)
    except Refused as refused:
        raise Refused([*creation.carried, *refused.faults])


def _identity(draft: Draft, creation: changes.Create, type_id: ArtifactId) -> list:
    """The faults of the IRI a create gives: an artifact's belongs to the type its create names, the nearest held
    type it sits under, while a type's is any IRI its client chooses; and neither a create before it in its set
    carries it, said once and as the set's, nor does the draft hold anything at it."""
    name, faults = creation.name, []
    if type_id != values.type_of(values.TYPE_KIND) and composition.nearest_type(name, draft) != type_id:
        faults.append(refusals.not_under(name, type_id))
    if creation.carried:
        faults += creation.carried
    elif draft.holds(name):
        faults.append(refusals.already_held(name))
    return faults


def _replace(draft: Draft, replacement: changes.Replace) -> Change:
    locator = replacement.locator
    _as_read(draft, locator.id, replacement.expected)
    if replacement.content.problems:
        raise Refused(replacement.content.refusal(str(locator.id)))
    content, current = copy.deepcopy(replacement.content.tree), draft.artifact(locator.id)
    if locator.place:
        content = _placed(current, locator, content)
    faults = _revise(draft, locator.id, current, content, _ends_at(draft, locator.id, current, replacement.version))
    return Change("write", locator.id, names.placed(locator.place), faults=faults)


def _ends_at(draft: Draft, artifact_id: ArtifactId, current: dict, named: values.Version | None) -> values.Version:
    """The version of its type a replaced artifact ends at: the one it conforms to when its replacement names none,
    else the one named, refused unless the artifact may move to it."""
    if named is None:
        return composition.conforming(current)
    if not composition.moves_to(current, named, draft):
        raise Refused([refusals.not_later(artifact_id, str(named), str(composition.conforming(current)))])
    return named


def _append(draft: Draft, addition: changes.Add) -> Change:
    """One item put at the end of a collection the artifact's type declares, and named there."""
    locator = addition.locator
    _as_read(draft, locator.id, addition.expected)
    if addition.item.problems:
        raise Refused(addition.item.refusal(str(locator.id)))
    if not locator.place:
        raise Refused([refusals.not_a_collection(locator)])
    current = draft.artifact(locator.id)
    content = _content_of(current)
    spot = places.resolve(content, locator)
    if spot.key not in _collections_at(draft, locator):
        raise Refused([refusals.not_a_collection(locator)])
    if not isinstance(spot.holder.get(spot.key, []), list):
        raise Refused([refusals.not_a_collection(locator)])
    item = copy.deepcopy(addition.item.tree)
    spot.holder.setdefault(spot.key, []).append(item)
    faults = _revise(draft, locator.id, current, content, composition.conforming(current))
    return Change("append", locator.id, names.placed((*locator.place, item["id"])), item["id"], faults=faults)


def _collections_at(draft: Draft, locator: values.Locator) -> dict:
    """The collections the version of its type the artifact conforms to declares where the locator's last step stands: the artifact's own, or those of the
    item type of each collection the place passes through on the way."""
    declared = composition.declared(composition.conformed(draft.artifact(locator.id), draft)["schema"], draft)
    for collection in locator.place[:-1:2]:
        part = declared["parts"].get(collection)
        if part is None:
            return {}
        declared = composition.declared(part.get("items", {}), draft)
    return declared["parts"]


def _delete(draft: Draft, removal: changes.Remove) -> Change:
    """A whole artifact taken out of the draft; what still points at it is judged once the whole set has acted."""
    locator = removal.locator
    _as_read(draft, locator.id, removal.expected)
    if locator.place:
        raise Refused([refusals.whole_only(locator)])
    removed = draft.artifact(locator.id)
    draft.remove(locator.id)
    return Change("delete", locator.id, revision=removed["revision"] + 1, type=removed["type"])


def _as_read(draft: Draft, artifact_id: ArtifactId, expected: int | None) -> None:
    """Refuse a change to an artifact the draft does not hold, or to one that stands at another revision than the one
    the change says it was read at, as the changes before it in the set left it."""
    if not draft.holds(artifact_id):
        raise Refused([refusals.not_found(artifact_id)])
    revision = draft.artifact(artifact_id)["revision"]
    if expected is not None and revision != expected:
        raise Refused([refusals.moved(artifact_id, revision)])


def _revise(draft: Draft, artifact_id: ArtifactId, current: dict, content: dict, version: values.Version) -> tuple:
    """The artifact's next revision put in the draft, conforming to the version of its type given: its new items
    named, its revision up by one, its title kept, and a type given the number of the version this change makes.
    Returns the faults of the names its items hand back that the artifact did not hold, with any of which no item is
    named."""
    kind = composition.artifact_kind(current)
    schema = composition.version_schema(version, draft)
    declared = composition.declared(schema["schema"], draft)
    held = names.held(declared["parts"], current)
    misnamed = [refusals.misnamed(artifact_id, found) for found in names.handed_back(declared, content, held)]
    if not misnamed:
        names.items(declared["parts"], content, True, _item_parts(draft))
    if kind == values.TYPE_KIND:
        _numbered(draft, artifact_id, content)
    artifact = settled.given(content, current["id"], str(version), current["revision"] + 1, current["title"])
    draft.put(artifact_id, settled.order(artifact, declared))
    return tuple(misnamed)


def _numbered(draft: Draft, type_id: ArtifactId, content: dict) -> None:
    """A type's content given, as its `version`, the number kb makes this version of it at, over any number its
    client sent or none; what a client sent there that is no number stays, for the type of types to refuse."""
    number, sent = draft.numbered(type_id), content.get("version", 0)
    if isinstance(sent, (int, float)) and not isinstance(sent, bool):
        content["version"] = number


def _item_parts(draft: Draft):
    """What gives the collections an item's type declares, read through its composition, from the declaration of the
    collection the item is in."""
    return lambda part: composition.declared(part.get("items", {}), draft)["parts"]


def _content_of(artifact: dict) -> dict:
    """A copy of what an artifact holds but its identity keys, to be changed without changing it."""
    return copy.deepcopy(settled.content(artifact))


def _placed(artifact: dict, locator: values.Locator, node: dict) -> dict:
    """The artifact's content with the node at the locator's place replaced by the one given; an item keeps its
    name."""
    content = _content_of(artifact)
    spot = places.resolve(content, locator)
    if spot.collection and spot.collection != "sections":
        node = {"id": locator.place[-1], **node}
    spot.holder[spot.key] = node
    return content
