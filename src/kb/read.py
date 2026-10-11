"""Reads: an artifact whole, with its links followed as far as asked; one of its sections; or its summary, with a stub
of each artifact it links to, each part it holds, and how many artifacts point at it. The stub is every query's too.
A link to an IRI the store does not hold is never followed: its stub is the IRI alone, marked as not held, and read
whole it stays a name. A link into a part of an artifact is read as a link to that artifact, and read whole it stays
the reference written. A whole read gives, beside its content, each link the artifact carries that lands on nothing
held: on an IRI the store does not hold, or on a part the artifact it holds there lacks."""
from dataclasses import replace

from kb import composition, links, names, places, refusals, settled, values
from kb.content import dumps
from kb.contract import kb_pb2
from kb.requests import Reading
from kb.port import Port
from kb.values import ArtifactId, Locator, Refused


def artifact(store: Port, reading: Reading) -> kb_pb2.Artifact:
    """The artifact at the level asked. Raises Refused for a name the store lacks, a place or a section it holds
    nothing at."""
    if reading.version is not None:
        return _version(store, reading)
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


def _version(store: Port, reading: Reading) -> kb_pb2.Artifact:
    """A version of a type, read as the artifact it was made as, under the version's IRI, with the revision and the
    title it was made with. Raises Refused when the store keeps no such version."""
    version = reading.version
    held = composition.kept(values.type_of(version.kind), version.number, store)
    if held is None:
        raise Refused([refusals.not_found(ArtifactId(str(version)))])
    at = ArtifactId(str(version))
    made = {**held.content, "id": str(at), "revision": held.revision, "title": held.title}
    return artifact(_Kept(store, at, made), replace(reading, locator=Locator(at, reading.locator.place), version=None))


class _Kept:
    """The store with one artifact put over it, as a version of a type is read as an artifact; all else is the store's."""

    def __init__(self, store: Port, artifact_id: ArtifactId, made: dict):
        self._store, self._id, self._made = store, artifact_id, made

    def holds(self, artifact_id: ArtifactId) -> bool:
        return artifact_id == self._id or self._store.holds(artifact_id)

    def artifact(self, artifact_id: ArtifactId) -> dict:
        return self._made if artifact_id == self._id else self._store.artifact(artifact_id)

    def __getattr__(self, name):
        return getattr(self._store, name)


def stub(store: Port, field: str, target_id: ArtifactId) -> kb_pb2.Stub:
    """An artifact in brief, under the field that reached it: its identity and the fields its type shows at a glance.
    An IRI the store does not hold, which a link may point at, is given as the IRI alone, marked as not held."""
    if not store.holds(target_id):
        return kb_pb2.Stub(field=field, id=str(target_id), not_held=True)
    target = store.artifact(target_id)
    return _stub(field, target, _shown(store, target))


def stubs(store: Port, artifact_ids: list[ArtifactId]) -> list[kb_pb2.Stub]:
    """Artifacts in brief, as `stub` gives each under no field, each through the version of the type it
    conforms to, a version read once."""
    shown: dict[int, dict] = {}
    stubbed = []
    for artifact_id in artifact_ids:
        found = store.artifact(artifact_id)
        number = settled.version(found)
        if number not in shown:
            shown[number] = _shown(store, found)
        stubbed.append(_stub("", found, shown[number]))
    return stubbed


def _shown(store: Port, artifact: dict) -> dict:
    """What the version of its type an artifact conforms to declares, the fields it shows at a glance among it."""
    return composition.declared(composition.artifact_schema(artifact, store)["schema"], store)


def _stub(field: str, target: dict, shown: dict) -> kb_pb2.Stub:
    return kb_pb2.Stub(
        field=field, id=target["id"], type=target["type"], title=target["title"],
        fields=dumps(_summary_fields(target, shown)),
    )


def _whole(store: Port, locator: Locator, depth: int) -> kb_pb2.Artifact:
    found = _resolved(store, locator.id, depth, {str(locator.id)})
    response = _response(found, dumps(settled.content(found)))
    response.placeholders.extend(_placeholders(store, store.artifact(locator.id)))
    return response


def _placeholders(store: Port, found: dict) -> list[kb_pb2.Placeholder]:
    """Each IRI a link the artifact carries lands on nothing at, in the order of their names, with those links in the
    order the artifact holds them, each saying the part of the IRI it names."""
    waited: dict[str, list] = {}
    for link in links.carried(found, composition.artifact_schema(found, store)["schema"], store):
        target = values.target(link.target)
        if not _lands(store, target):
            waited.setdefault(str(target.id), []).append(kb_pb2.Linking(
                artifact=found["id"], field=link.field, place=link.place, part=names.placed(target.place),
            ))
    return [kb_pb2.Placeholder(id=name, links=waited[name]) for name in sorted(waited, key=names.order)]


def _lands(store: Port, target: Locator) -> bool:
    """Whether a link lands on something held: the artifact it names, and the part of it when it names one."""
    if not store.holds(target.id):
        return False
    return not target.place or places.holds_part(store.artifact(target.id), target.place)


def _section(store: Port, locator: Locator, title: str) -> kb_pb2.Artifact:
    """The first section with that title, at any depth, in the order the artifact holds them, and nothing else."""
    found = store.artifact(locator.id)
    section = _find_section(found.get("sections", []), title)
    if section is None:
        raise Refused([refusals.no_section(locator.id, title)])
    return _response(found, dumps(section))


def _summary(store: Port, locator: Locator) -> kb_pb2.Artifact:
    found = store.artifact(locator.id)
    schema = composition.artifact_schema(found, store)["schema"]
    declared = composition.declared(schema, store)
    response = _response(found, dumps(_summary_fields(found, declared)))
    for link in links.carried(found, schema, store):
        response.references.append(stub(store, link.field, values.target(link.target).id))
    for collection in declared["parts"]:
        for item in found.get(collection, []):
            response.parts.append(kb_pb2.PartStub(collection=collection, id=item["id"], title=item["title"]))
    for (type_name, field), count in _inbound(store, locator.id).items():
        response.inbound.append(kb_pb2.InboundCount(kind=type_name, field=field, count=count))
    return response


def _response(found: dict, content: str) -> kb_pb2.Artifact:
    return kb_pb2.Artifact(
        id=found["id"], type=found["type"], revision=found["revision"],
        title=found["title"], content=content,
    )


def _resolved(store: Port, artifact_id: ArtifactId, depth: int, on_path: set) -> dict:
    """The artifact as stored, each link in its own fields followed depth steps with the target, itself resolved, in
    place of its name; a link inside one of its items stays a name. A target on the path already being filled in
    stays a name, so a loop ends, and so does one the store does not hold; a link into a part of an artifact stays
    the reference written, a part being no artifact."""
    found = store.artifact(artifact_id)
    if depth < 1:
        return found
    def fill(target):
        linked = values.target(target)
        if linked.place or target in on_path or not store.holds(linked.id):
            return target
        return _resolved(store, linked.id, depth - 1, on_path | {target})
    resolved = dict(found)
    carried = links.carried(found, composition.artifact_schema(found, store)["schema"], store)
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
