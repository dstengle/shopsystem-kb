"""What each operation of a set does to the draft: a new artifact, a whole or placed replacement, an item added to a
collection, an artifact removed. Each is checked against the draft as the operations before it left it, and refused
with every fault it finds."""
import copy
from typing import NamedTuple

from kb import canonical, names, places, refusals, requests, validation, values
from kb.store import Draft
from kb.values import ArtifactId, Kind, Refused


class Change(NamedTuple):
    """What one operation did, to which artifact, at which place in it, and, for an item added, the item's name. A
    removal carries the version its entry records and the version of the type it was last checked against."""
    op: str
    artifact_id: ArtifactId
    path: str = ""
    item: str = ""
    revision: int = 0
    schema_version: int = 0


def apply(draft: Draft, operation) -> Change:
    """One operation applied to the draft. Returns what it did; raises Refused."""
    if isinstance(operation, requests.Create):
        return Change("create", _create(draft, operation))
    if isinstance(operation, requests.Add):
        return _append(draft, operation)
    if isinstance(operation, requests.Remove):
        return _delete(draft, operation)
    return Change("write", _replace(draft, operation))


def _create(draft: Draft, creation: requests.Create) -> ArtifactId:
    kind = creation.kind
    if not draft.holds(ArtifactId(Kind("schema"), kind.name)):
        raise Refused([refusals.no_type(kind.name)])
    at, faults = creation.at, list(creation.title_faults)
    if creation.name is not None:
        artifact_id = _unclaimed(draft, creation.name)
        at = str(artifact_id)
    faults += creation.content.refusal(at)
    if faults:
        raise Refused(faults)
    content = creation.content.tree
    schema = draft.schema(kind)
    faults = validation.validate(at, {"title": creation.title, **content}, schema["schema"], draft)
    if faults:
        raise Refused(faults)
    names.items(schema["schema"], content, keep_named=False)
    artifact = {
        **content,
        "id": str(artifact_id), "type": kind.name,
        "schema_version": schema["version"], "revision": 1, "title": creation.title,
    }
    draft.put(artifact_id, canonical.order(artifact, schema["schema"]))
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
    if spot.holder is not content or spot.key not in draft.schema(locator.id.kind)["schema"].get("parts", {}):
        raise Refused([refusals.not_a_collection(locator)])
    item = addition.item.tree
    content.setdefault(spot.key, []).append(item)
    _revise(draft, locator.id, current, content)
    return Change("append", locator.id, f"{spot.key}/{item['id']}", item["id"])


def _delete(draft: Draft, removal: requests.Remove) -> Change:
    """A whole artifact taken out of the draft, refused with one fault for each link that still points at it."""
    locator = removal.locator
    if not draft.holds(locator.id):
        raise Refused([refusals.not_found(locator.id)])
    if locator.place:
        raise Refused([refusals.whole_only(locator)])
    blocking = []
    for other_id in draft.ids():
        if other_id == locator.id:
            continue
        schema = draft.schema(other_id.kind)["schema"]
        for link in validation.links(draft.artifact(other_id), schema, draft):
            if validation.points_at(link.target, locator.id):
                blocking.append(refusals.still_linked(locator.id, other_id, link.place))
    if blocking:
        raise Refused(blocking)
    removed = draft.artifact(locator.id)
    draft.remove(locator.id)
    return Change("delete", locator.id, revision=removed["revision"] + 1, schema_version=removed["schema_version"])


def _revise(draft: Draft, artifact_id: ArtifactId, current: dict, content: dict) -> None:
    """The artifact's next version put in the draft: the names its items hand back checked against those the artifact
    held, the content checked against the current version of its type, its new items named, its version up by one,
    its title kept. Raises Refused with every fault."""
    schema = draft.schema(artifact_id.kind)
    held = {collection: {item.get("id") for item in current.get(collection, [])}
            for collection in schema["schema"].get("parts", {})}
    faults = [refusals.misnamed(artifact_id, found) for found in names.handed_back(schema["schema"], content, held)]
    faults += validation.validate(str(artifact_id), {"title": current["title"], **content}, schema["schema"], draft)
    if faults:
        raise Refused(faults)
    names.items(schema["schema"], content, keep_named=True)
    artifact = {
        **content,
        "id": current["id"], "type": current["type"],
        "schema_version": schema["version"], "revision": current["revision"] + 1, "title": current["title"],
    }
    draft.put(artifact_id, canonical.order(artifact, schema["schema"]))


def _content_of(artifact: dict) -> dict:
    """A copy of what an artifact holds but its identity keys, to be changed without changing it."""
    return copy.deepcopy({key: value for key, value in artifact.items() if key not in canonical.IDENTITY})


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
