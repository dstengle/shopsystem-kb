"""What each operation of a set does to the draft: a new artifact, a whole or placed replacement, an item added to a
collection, an artifact removed. Each acts on the draft as the operations before it left it, on a copy of what it was
asked to put there, so the same set can act again on another draft, and is refused there with every fault it finds in
what it names, the revisions it makes and the names of its items; what its content and links come to is checked once
the whole set has acted (kb.write). An import puts an artifact in the draft whole, as the file it came from gives it."""
import copy
from typing import NamedTuple

from kb import changes, composition, definitions, names, places, refusals, settled, values
from kb.draft import Draft
from kb.values import ArtifactId, Refused


class Import(NamedTuple):
    """An artifact brought whole from a file for import: its name, and the artifact, identity and all."""
    artifact_id: ArtifactId
    artifact: dict


class Change(NamedTuple):
    """What one operation did, to which artifact, at which place in it, and, for an item added, the item's name; the
    version its entry records and the version of the type it was last checked against; the artifact as this
    operation left it, None for a removal; the type of its kind as it acted, which it is checked against when the set
    leaves none; and the faults of the names it handed back and of a type's version kept, which refuse the set while
    it still acts, so what it leaves is checked too."""
    op: str
    artifact_id: ArtifactId
    path: str = ""
    item: str = ""
    revision: int = 0
    schema_version: int = 0
    left: dict | None = None
    acted: dict | None = None
    faults: tuple = ()


def apply(draft: Draft, operation) -> Change:
    """One operation applied to the draft. Returns what it did, settled as it did it; raises Refused."""
    if isinstance(operation, changes.Remove):
        return _delete(draft, operation)
    change = _changed(draft, operation)
    left = draft.artifact(change.artifact_id)
    return change._replace(
        revision=left["revision"], schema_version=left["schema_version"], left=left,
        acted=composition.kind_schema(change.artifact_id.kind, draft),
    )


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
    kind = creation.kind
    type_id = composition.kind_type(kind, draft)
    at, faults = creation.at, list(creation.title_faults)
    if creation.name is not None:
        artifact_id = _unclaimed(draft, creation.name)
        at = str(artifact_id)
    faults += creation.content.refusal(at)
    if faults:
        raise Refused(faults)
    content = copy.deepcopy(creation.content.tree)
    schema = draft.artifact(type_id)
    declared = composition.declared(schema["schema"], draft)
    names.items(declared["parts"], content, False, _item_parts(draft))
    artifact = settled.given(content, str(artifact_id), kind.name, schema["version"], 1, creation.title)
    draft.put(artifact_id, settled.order(artifact, declared))
    return artifact_id


def _replace(draft: Draft, replacement: changes.Replace) -> Change:
    locator = replacement.locator
    if not draft.holds(locator.id):
        raise Refused([refusals.not_found(locator.id)])
    if replacement.content.problems:
        raise Refused(replacement.content.refusal(str(locator.id)))
    content, current = copy.deepcopy(replacement.content.tree), draft.artifact(locator.id)
    if locator.place:
        content = _placed(current, locator, content)
    faults = _revise(draft, locator.id, current, content)
    return Change("write", locator.id, names.placed(locator.place), faults=faults)


def _append(draft: Draft, addition: changes.Add) -> Change:
    """One item put at the end of a collection the artifact's type declares, and named there."""
    locator = addition.locator
    if not draft.holds(locator.id):
        raise Refused([refusals.not_found(locator.id)])
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
    faults = _revise(draft, locator.id, current, content)
    return Change("append", locator.id, names.placed((*locator.place, item["id"])), item["id"], faults=faults)


def _collections_at(draft: Draft, locator: values.Locator) -> dict:
    """The collections the type declares where the locator's last step stands: the artifact's own, or those of the
    item type of each collection the place passes through on the way."""
    declared = composition.declared(composition.kind_schema(locator.id.kind, draft)["schema"], draft)
    for collection in locator.place[:-1:2]:
        part = declared["parts"].get(collection)
        if part is None:
            return {}
        declared = composition.declared(part.get("items", {}), draft)
    return declared["parts"]


def _delete(draft: Draft, removal: changes.Remove) -> Change:
    """A whole artifact taken out of the draft; what still points at it is judged once the whole set has acted."""
    locator = removal.locator
    if not draft.holds(locator.id):
        raise Refused([refusals.not_found(locator.id)])
    if locator.place:
        raise Refused([refusals.whole_only(locator)])
    removed = draft.artifact(locator.id)
    draft.remove(locator.id)
    return Change("delete", locator.id, revision=removed["revision"] + 1, schema_version=removed["schema_version"])


def _revise(draft: Draft, artifact_id: ArtifactId, current: dict, content: dict) -> tuple:
    """The artifact's next version put in the draft: its new items named, its version up by one, its title kept.
    Returns the faults of the names its items hand back that the artifact did not hold, with any of which no item is
    named, and, for a type, of a schema changed while its version did not move on from the one it acted on."""
    schema = composition.kind_schema(artifact_id.kind, draft)
    declared = composition.declared(schema["schema"], draft)
    held = names.held(declared["parts"], current)
    misnamed = [refusals.misnamed(artifact_id, found) for found in names.handed_back(declared, content, held)]
    if not misnamed:
        names.items(declared["parts"], content, True, _item_parts(draft))
    kept = definitions.version_kept(artifact_id, content, current) if artifact_id.kind == values.TYPE_KIND else []
    artifact = settled.given(
        content, current["id"], current["type"], schema["version"], current["revision"] + 1, current["title"],
    )
    draft.put(artifact_id, settled.order(artifact, declared))
    return (*misnamed, *kept)


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


def _unclaimed(draft: Draft, named: ArtifactId) -> ArtifactId:
    """The name a title gives, or, when the store or an earlier change in the set already holds it, that name with
    -2, -3 and so on added: the first that nothing holds. What already holds a name keeps it."""
    return ArtifactId(named.kind, names.numbered(named.slug, lambda slug: draft.holds(ArtifactId(named.kind, slug))))
