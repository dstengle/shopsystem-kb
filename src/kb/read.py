"""Reads: an artifact whole, with its links followed as far as asked; one of its sections; or its summary, with a stub
of each artifact it links to, each part it holds, and how many artifacts point at it. The stub is every query's too."""
from kb import canonical, composition, links, refusals, values
from kb.content import dumps
from kb.contract import kb_pb2
from kb.requests import Reading
from kb.store import Store
from kb.values import ArtifactId, Locator, Refused


def artifact(store: Store, reading: Reading) -> kb_pb2.ReadResponse:
    """The artifact at the level asked. Raises Refused for a name the store lacks, a section it lacks, or a stored
    file that cannot be read."""
    locator = reading.locator
    if not store.holds(locator.id):
        raise Refused([refusals.not_found(locator.id)])
    if reading.level == "whole":
        return _whole(store, locator, reading.depth)
    if reading.level == "section":
        return _section(store, locator, reading.section)
    return _summary(store, locator)


def stub(store: Store, field: str, target_id: ArtifactId) -> kb_pb2.Stub:
    """An artifact in brief, under the field that reached it: its identity and the fields its type shows at a glance."""
    target = store.artifact(target_id)
    schema = store.schema(target_id.kind)["schema"]
    return kb_pb2.Stub(
        field=field, id=target["id"], type=target["type"], title=target["title"],
        fields=dumps(_summary_fields(target, composition.declared(schema, store))),
    )


def _whole(store: Store, locator: Locator, depth: int) -> kb_pb2.ReadResponse:
    found = _resolved(store, locator.id, depth, {str(locator.id)})
    content = {key: value for key, value in found.items() if key not in canonical.IDENTITY}
    return _response(found, dumps(content))


def _section(store: Store, locator: Locator, title: str) -> kb_pb2.ReadResponse:
    """The first section with that title, at any depth, in the order the artifact holds them, and nothing else."""
    found = store.artifact(locator.id)
    section = _find_section(found.get("sections", []), title)
    if section is None:
        raise Refused([refusals.no_section(locator.id, title)])
    return _response(found, dumps(section))


def _summary(store: Store, locator: Locator) -> kb_pb2.ReadResponse:
    found = store.artifact(locator.id)
    schema = store.schema(locator.id.kind)["schema"]
    declared = composition.declared(schema, store)
    response = _response(found, dumps(_summary_fields(found, declared)))
    for link in links.carried(found, schema, store):
        response.references.append(stub(store, link.field, values.artifact_id(link.target)))
    for collection in declared["parts"]:
        for item in found.get(collection, []):
            response.parts.append(kb_pb2.PartStub(collection=collection, id=item["id"], title=item["title"]))
    for (type_name, field), count in _inbound(store, str(locator.id)).items():
        response.inbound.append(kb_pb2.InboundCount(type=type_name, field=field, count=count))
    return response


def _response(found: dict, content: str) -> kb_pb2.ReadResponse:
    return kb_pb2.ReadResponse(
        id=found["id"], type=found["type"], schema_version=found["schema_version"], revision=found["revision"],
        title=found["title"], content=content,
    )


def _resolved(store: Store, artifact_id: ArtifactId, depth: int, on_path: set) -> dict:
    """The artifact as stored, each link followed depth steps with the target, itself resolved, in place of its
    name. A target on the path already being filled in stays a name, so a loop ends."""
    found = store.artifact(artifact_id)
    if depth < 1:
        return found
    def fill(target):
        if target in on_path:
            return target
        return _resolved(store, values.artifact_id(target), depth - 1, on_path | {target})
    resolved = dict(found)
    for field in links.references(store.schema(artifact_id.kind)["schema"], store):
        value = found.get(field)
        if isinstance(value, list):
            resolved[field] = [fill(target) for target in value]
        elif value is not None:
            resolved[field] = fill(value)
    return resolved


def _inbound(store: Store, artifact_id: str) -> dict:
    """How many artifacts point at this one, by their type and the field they use."""
    counts = {}
    for other in store.artifacts():
        schema = store.schema(values.kind(other["type"]))["schema"]
        pointing = {link.field for link in links.carried(other, schema, store) if link.target == artifact_id}
        for field in pointing:
            counts[(other["type"], field)] = counts.get((other["type"], field), 0) + 1
    return counts


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
