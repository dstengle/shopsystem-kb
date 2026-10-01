"""What each operation of a set does to the draft: a new artifact, a whole or placed replacement, an item added to a
collection, an artifact removed. Each is checked against the draft as the operations before it left it, and refused
with every fault it finds."""
import copy
from typing import NamedTuple

from kb import composition, definitions, names, places, refusals, requests, settled, validation, values
from kb.draft import Draft
from kb.values import ArtifactId, Refused


class Change(NamedTuple):
    """What one operation did, to which artifact, at which place in it, and, for an item added, the item's name; the
    version its entry records and the version of the type it was last checked against; and the artifact as this
    operation left it, None for a removal."""
    op: str
    artifact_id: ArtifactId
    path: str = ""
    item: str = ""
    revision: int = 0
    schema_version: int = 0
    left: dict | None = None


def apply(draft: Draft, operation) -> Change:
    """One operation applied to the draft. Returns what it did, settled as it did it; raises Refused."""
    if isinstance(operation, requests.Remove):
        return _delete(draft, operation)
    change = _changed(draft, operation)
    left = draft.artifact(change.artifact_id)
    return change._replace(revision=left["revision"], schema_version=left["schema_version"], left=left)


def _changed(draft: Draft, operation) -> Change:
    if isinstance(operation, requests.Create):
        return Change("create", _create(draft, operation))
    if isinstance(operation, requests.Add):
        return _append(draft, operation)
    return Change("write", _replace(draft, operation), names.placed(operation.locator.place))


def _create(draft: Draft, creation: requests.Create) -> ArtifactId:
    kind = creation.kind
    type_id = composition.kind_type(kind, draft)
    at, faults = creation.at, list(creation.title_faults)
    if creation.name is not None:
        artifact_id = _unclaimed(draft, creation.name)
        at = str(artifact_id)
    faults += creation.content.refusal(at)
    if faults:
        raise Refused(faults)
    content = creation.content.tree
    schema = draft.artifact(type_id)
    faults = _fits(draft, artifact_id, {"title": creation.title, **content}, schema)
    if faults:
        raise Refused(faults)
    declared = composition.declared(schema["schema"], draft)
    names.items(declared["parts"], content, False, _item_parts(draft))
    artifact = settled.given(content, str(artifact_id), kind.name, schema["version"], 1, creation.title)
    draft.put(artifact_id, settled.order(artifact, declared))
    return artifact_id


def _replace(draft: Draft, replacement: requests.Replace) -> ArtifactId:
    locator = replacement.locator
    if not draft.holds(locator.id):
        raise Refused([refusals.not_found(locator.id)])
    if replacement.content.problems:
        raise Refused(replacement.content.refusal(str(locator.id)))
    content, current = replacement.content.tree, draft.artifact(locator.id)
    if locator.place:
        content = _placed(current, locator, content)
    _revise(draft, locator.id, current, content)
    return locator.id


def _append(draft: Draft, addition: requests.Add) -> Change:
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
    item = addition.item.tree
    spot.holder.setdefault(spot.key, []).append(item)
    _revise(draft, locator.id, current, content)
    return Change("append", locator.id, names.placed((*locator.place, item["id"])), item["id"])


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


def _delete(draft: Draft, removal: requests.Remove) -> Change:
    """A whole artifact taken out of the draft, refused with one fault for each link that still points at it."""
    locator = removal.locator
    if not draft.holds(locator.id):
        raise Refused([refusals.not_found(locator.id)])
    if locator.place:
        raise Refused([refusals.whole_only(locator)])
    blocking = [
        refusals.still_linked(locator.id, each.source, each.place)
        for each in draft.links_in(locator.id) if each.source != locator.id
    ]
    if blocking:
        raise Refused(blocking)
    removed = draft.artifact(locator.id)
    draft.remove(locator.id)
    return Change("delete", locator.id, revision=removed["revision"] + 1, schema_version=removed["schema_version"])


def _revise(draft: Draft, artifact_id: ArtifactId, current: dict, content: dict) -> None:
    """The artifact's next version put in the draft: the names its items hand back checked against those the artifact
    held, the content checked against the current version of its type, its new items named, its version up by one,
    its title kept. Raises Refused with every fault."""
    schema = composition.kind_schema(artifact_id.kind, draft)
    declared = composition.declared(schema["schema"], draft)
    held = names.held(declared["parts"], current)
    faults = [refusals.misnamed(artifact_id, found) for found in names.handed_back(declared, content, held)]
    faults += _fits(draft, artifact_id, {"title": current["title"], **content}, schema)
    if faults:
        raise Refused(faults)
    names.items(declared["parts"], content, True, _item_parts(draft))
    artifact = settled.given(
        content, current["id"], current["type"], schema["version"], current["revision"] + 1, current["title"],
    )
    draft.put(artifact_id, settled.order(artifact, declared))


def _item_parts(draft: Draft):
    """What gives the collections an item's type declares, read through its composition, from the declaration of the
    collection the item is in."""
    return lambda part: composition.declared(part.get("items", {}), draft)["parts"]


def _fits(draft: Draft, artifact_id: ArtifactId, content: dict, schema: dict) -> list:
    """Every fault of the content against its type; a type, once it fits the type of types, checked as a type too."""
    faults = validation.validate(str(artifact_id), content, schema["schema"], draft)
    if not faults and artifact_id.kind == values.TYPE_KIND:
        faults = definitions.faults(artifact_id, content, draft)
    return faults


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
