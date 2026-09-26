"""What each operation of a set does to the draft: a new artifact, a whole or placed replacement, an item added to a
collection, an artifact removed. Each is checked against the draft as the operations before it left it, and refused
with every fault it finds."""
import copy
from typing import NamedTuple

from kb import canonical, names, requests, validation, values
from kb.contract import kb_pb2
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
        raise Refused([kb_pb2.Fault(
            rule="kind", message=f"a kind must name a type the store holds; the store holds no type called {kind.name!r}",
        )])
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
        raise Refused([not_found(locator.id)])
    if replacement.content.problems:
        raise Refused(replacement.content.refusal(str(locator.id)))
    content, current = replacement.content.tree, draft.load(locator.id)
    if locator.place:
        content = _placed(current, locator, content)
    _revise(draft, locator.id, current, content)
    return locator.id


def _append(draft: Draft, addition: requests.Add) -> Change:
    """One item put at the end of a collection the artifact's type declares, and named there."""
    locator = addition.locator
    if not draft.holds(locator.id):
        raise Refused([not_found(locator.id)])
    if addition.item.problems:
        raise Refused(addition.item.refusal(str(locator.id)))
    item, collection = addition.item.tree, "/".join(locator.place)
    if collection not in draft.schema(locator.id.kind)["schema"].get("parts", {}):
        raise Refused([kb_pb2.Fault(
            artifact=str(locator.id), path=collection, rule="not-found",
            message=f"{str(locator.id)!r} holds no collection called {collection!r}",
        )])
    current = draft.load(locator.id)
    content = _content_of(current)
    content.setdefault(collection, []).append(item)
    _revise(draft, locator.id, current, content)
    return Change("append", locator.id, f"{collection}/{item['id']}", item["id"])


def _delete(draft: Draft, removal: requests.Remove) -> Change:
    """A whole artifact taken out of the draft, refused with one fault for each link that still points at it."""
    locator = removal.locator
    if not draft.holds(locator.id):
        raise Refused([not_found(locator.id)])
    if locator.place:
        raise Refused([kb_pb2.Fault(
            artifact=str(locator.id), path="/".join(locator.place), rule="locator",
            message=f"a removal takes out a whole artifact; {'/'.join(locator.place)!r} is a place inside {str(locator.id)!r}",
        )])
    blocking = []
    for other_id in draft.ids():
        if other_id == locator.id:
            continue
        schema = draft.schema(other_id.kind)["schema"]
        for field, place, target in validation.links(draft.load(other_id), schema, draft):
            if validation.points_at(target, locator.id):
                blocking.append(kb_pb2.Fault(
                    artifact=str(other_id), path=place, rule="on_delete",
                    message=f"{str(locator.id)!r} cannot be removed while {str(other_id)!r} points at it at {place!r}",
                ))
    if blocking:
        raise Refused(blocking)
    removed = draft.load(locator.id)
    draft.remove(locator.id)
    return Change("delete", locator.id, revision=removed["revision"] + 1, schema_version=removed["schema_version"])


def _revise(draft: Draft, artifact_id: ArtifactId, current: dict, content: dict) -> None:
    """The artifact's next version put in the draft: the content checked against the current version of its type,
    its items named, its version up by one, its title kept. Raises Refused with every fault."""
    schema = draft.schema(artifact_id.kind)
    faults = validation.validate(str(artifact_id), {"title": current["title"], **content}, schema["schema"], draft)
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
    """The artifact's content with the node at the locator's place replaced by the one given. A place is pairs of a
    list and an item in it, a section named by its title's name and a part by its id, and may end in a field."""
    content = _content_of(artifact)
    holder, steps = content, list(locator.place)
    while len(steps) > 1:
        collection, name = steps.pop(0), steps.pop(0)
        found = holder.get(collection, [])
        index = next((index for index, item in enumerate(found) if _node_name(collection, item) == name), None)
        if index is None:
            raise Refused([kb_pb2.Fault(
                artifact=str(locator.id), path="/".join(locator.place), rule="not-found",
                message=f"{str(locator.id)!r} holds nothing at {'/'.join(locator.place)!r}",
            )])
        if not steps:
            found[index] = node if collection == "sections" else {"id": name, **node}
            return content
        holder = found[index]
    holder[steps[0]] = node
    return content


def _node_name(collection: str, item: dict) -> str:
    """How a place names an item: a section by its title's name, a part by its id."""
    return names.slug(item["title"]) if collection == "sections" else item.get("id")


def _unclaimed(draft: Draft, named: ArtifactId) -> ArtifactId:
    """The name a title gives, or, when the store or an earlier change in the set already holds it, that name with
    -2, -3 and so on added: the first that nothing holds. What already holds a name keeps it."""
    return ArtifactId(named.kind, names.numbered(named.slug, lambda slug: draft.holds(ArtifactId(named.kind, slug))))


def not_found(artifact_id: ArtifactId) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(artifact_id), rule="not-found", message=f"the store holds nothing by the name {str(artifact_id)!r}",
    )
