"""Reads: an artifact whole, with its links followed as far as asked; one of its sections; or its summary, with a stub
of each artifact it links to, each part it holds, and how many artifacts point at it. The stub is every query's too."""
from kb import composition, links, places, refusals, settled, values
from kb.content import dumps
from kb.contract import kb_pb2
from kb.requests import Reading
from kb.port import Port
from kb.values import ArtifactId, Locator, Refused


def artifact(store: Port, reading: Reading) -> kb_pb2.ReadResponse:
    """The artifact at the level asked. Raises Refused for a name the store lacks, a place or a section it holds
    nothing at, or a stored file that cannot be read."""
    locator = reading.locator
    if not store.holds(locator.id):
        raise Refused([refusals.not_found(locator.id)])
    if locator.place:
        places.resolve(store.artifact(locator.id), locator)
    if reading.level == "whole":
        return _whole(store, locator, reading.depth)
    if reading.level == "section":
        return _section(store, locator, reading.section)
    return _summary(store, locator)


def stub(store: Port, field: str, target_id: ArtifactId) -> kb_pb2.Stub:
    """An artifact in brief, under the field that reached it: its identity and the fields its type shows at a glance."""
    target = store.artifact(target_id)
    schema = composition.kind_schema(target_id.kind, store)["schema"]
    return kb_pb2.Stub(
        field=field, id=target["id"], type=target["type"], title=target["title"],
        fields=dumps(_summary_fields(target, composition.declared(schema, store))),
    )


def _whole(store: Port, locator: Locator, depth: int) -> kb_pb2.ReadResponse:
    found = _resolved(store, locator.id, depth, {str(locator.id)})
    return _response(found, dumps(settled.content(found)))


def _section(store: Port, locator: Locator, title: str) -> kb_pb2.ReadResponse:
    """The first section with that title, at any depth, in the order the artifact holds them, and nothing else."""
    found = store.artifact(locator.id)
    section = _find_section(found.get("sections", []), title)
    if section is None:
        raise Refused([refusals.no_section(locator.id, title)])
    return _response(found, dumps(section))


def _summary(store: Port, locator: Locator) -> kb_pb2.ReadResponse:
    found = store.artifact(locator.id)
    schema = composition.kind_schema(locator.id.kind, store)["schema"]
    declared = composition.declared(schema, store)
    response = _response(found, dumps(_summary_fields(found, declared)))
    for link in links.carried(found, schema, store):
        response.references.append(stub(store, link.field, values.artifact_id(link.target)))
    for collection in declared["parts"]:
        for item in found.get(collection, []):
            response.parts.append(kb_pb2.PartStub(collection=collection, id=item["id"], title=item["title"]))
    for (type_name, field), count in _inbound(store, locator.id).items():
        response.inbound.append(kb_pb2.InboundCount(type=type_name, field=field, count=count))
    return response


def _response(found: dict, content: str) -> kb_pb2.ReadResponse:
    return kb_pb2.ReadResponse(
        id=found["id"], type=found["type"], schema_version=found["schema_version"], revision=found["revision"],
        title=found["title"], content=content,
    )


def _resolved(store: Port, artifact_id: ArtifactId, depth: int, on_path: set) -> dict:
    """The artifact as stored, each link in its own fields followed depth steps with the target, itself resolved, in
    place of its name; a link inside one of its items stays a name. A target on the path already being filled in
    stays a name, so a loop ends."""
    found = store.artifact(artifact_id)
    if depth < 1:
        return found
    def fill(target):
        if target in on_path:
            return target
        return _resolved(store, values.artifact_id(target), depth - 1, on_path | {target})
    resolved = dict(found)
    carried = links.carried(found, composition.kind_schema(artifact_id.kind, store)["schema"], store)
    for field in {link.field for link in carried if link.own}:
        value = found[field]
        resolved[field] = [fill(target) for target in value] if isinstance(value, list) else fill(value)
    return resolved


def _inbound(store: Port, artifact_id: ArtifactId) -> dict:
    """How many artifacts point at this one or at a part inside it, by their type and the field they use."""
    return store.inbound(artifact_id)


def _find_section(sections: list, title: str) -> dict | None:
    """The first section titled so, looking at each section before the sections inside it."""
    for section in sections:
        if section["title"] == title:
            return section
        found = _find_section(section.get("sections", []), title)
        if found is not None:
            return found
    return None


def _summary_fields(found: dict, declared: dict) -> dict:
    return {name: found[name] for name in declared["summary"] if name in found}
