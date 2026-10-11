"""Reads: an artifact whole, with its links followed as far as asked; one of its sections; or its summary, with a stub
of each artifact it links to, each part it holds, and how many artifacts point at it. The stub is every query's too.
A link to an IRI the store does not hold is never followed: its stub is the IRI alone, marked as not held, and read
whole it stays a name. A link into a part of an artifact is read as a link to that artifact, and read whole it stays
the reference written. A read at a glance or whole gives, beside its content, each link it shows that lands on nothing
held, on an IRI the store does not hold or on a part the artifact it holds there lacks: the links of the artifact
read and, read whole following links, of each artifact filled in. A section shows no link and gives none. A read that
names a part gives that part and nothing else of its artifact, at the level asked, beside its artifact's identity."""
from dataclasses import replace
from typing import NamedTuple

from kb import composition, links, names, places, refusals, settled, values
from kb.content import dumps
from kb.contract import kb_pb2
from kb.requests import Reading
from kb.port import Port
from kb.values import ArtifactId, Locator, Refused


def artifact(store: Port, reading: Reading) -> kb_pb2.Artifact:
    """The artifact at the level asked, or, when the locator's place names a part of it, that part. Raises Refused
    for a name the store lacks, a place or a section it holds nothing at."""
    if reading.version is not None:
        return _version(store, reading)
    locator = reading.locator
    if not store.holds(locator.id):
        raise Refused([refusals.not_found(locator.id)])
    found = store.artifact(locator.id)
    if locator.place:
        places.resolve(found, locator)
    if reading.level == "section":
        return _section(found, "" if _node(found, locator) is found else names.placed(locator.place), reading.section)
    if reading.level == "whole":
        return _whole(store, _read(store, found, locator), reading.depth)
    return _summary(store, _read(store, found, locator))


class _Read(NamedTuple):
    """What a read gives: the artifact, the node of it read (the artifact itself, or the part its place names), what
    that node's type declares, the links the node carries, in its own fields and in its items at every depth, and
    how a link says that node holds it (`links.Link.holder`)."""
    found: dict
    node: dict
    declared: dict
    links: list
    holder: str


def _node(found: dict, locator: Locator) -> dict:
    """What of an artifact a read gives: the part its place names, when it names one, otherwise the artifact."""
    names_part = locator.place and places.holds_part(found, locator.place)
    return places.node(found, locator) if names_part else found


def _read(store: Port, found: dict, locator: Locator) -> _Read:
    schema = composition.artifact_schema(found, store)["schema"]
    declared, node = composition.declared(schema, store), _node(found, locator)
    if node is found:
        return _Read(found, found, declared, links.carried(found, schema, store), "")
    for collection in locator.place[::2]:
        declared = composition.declared(declared["parts"].get(collection, {}).get("items", {}), store)
    inside = links.inside(found, schema, store, node)
    return _Read(found, node, declared, inside, names.placed(locator.place))


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
    conforms to, whatever its type, a version read once."""
    shown: dict[str, dict] = {}
    stubbed = []
    for artifact_id in artifact_ids:
        found = store.artifact(artifact_id)
        version = found["type"]
        if version not in shown:
            shown[version] = _shown(store, found)
        stubbed.append(_stub("", found, shown[version]))
    return stubbed


def _shown(store: Port, artifact: dict) -> dict:
    """What the version of its type an artifact conforms to declares, the fields it shows at a glance among it."""
    return composition.declared(composition.artifact_schema(artifact, store)["schema"], store)


def _stub(field: str, target: dict, shown: dict) -> kb_pb2.Stub:
    return kb_pb2.Stub(
        field=field, id=target["id"], type=target["type"], title=target["title"],
        fields=dumps(_summary_fields(target, shown)),
    )


def _whole(store: Port, read: _Read, depth: int) -> kb_pb2.Artifact:
    """The node whole: an artifact's content, or a part as its artifact holds it, its name with it; the links in the
    node's own fields followed as far as asked."""
    filled_in: dict[str, dict] = {}
    own = {link.field for link in read.links if link.holder == read.holder}
    filled = _filled(store, read.node, own, depth, {read.found["id"]}, filled_in)
    response = _response(read.found, dumps(settled.content(filled) if read.node is read.found else filled))
    shown = {read.found["id"]: read.links, **{name: _carried(store, each) for name, each in filled_in.items()}}
    response.placeholders.extend(_placeholders(store, shown))
    return response


def _carried(store: Port, found: dict) -> list:
    return links.carried(found, composition.artifact_schema(found, store)["schema"], store)


def _placeholders(store: Port, shown: dict[str, list]) -> list[kb_pb2.Placeholder]:
    """Each IRI a link shown lands on nothing at, in the order of their names, with those links, the artifacts
    holding them in the order of their names and each one's links in the order it holds them, each saying whose it
    is and the part of the IRI it names. shown is the links shown of each artifact, by its name."""
    waited: dict[str, list] = {}
    for holding in sorted(shown, key=names.order):
        for link in shown[holding]:
            target = values.target(link.target)
            if not _lands(store, target):
                waited.setdefault(str(target.id), []).append(kb_pb2.Linking(
                    artifact=holding, field=link.field, place=link.place, part=names.placed(target.place),
                ))
    return [kb_pb2.Placeholder(id=name, links=waited[name]) for name in sorted(waited, key=names.order)]


def _lands(store: Port, target: Locator) -> bool:
    """Whether a link lands on something held: the artifact it names, and the part of it when it names one."""
    if not store.holds(target.id):
        return False
    return not target.place or places.holds_part(store.artifact(target.id), target.place)


def _section(found: dict, part: str, title: str) -> kb_pb2.Artifact:
    """The first section with that title, at any depth, in the order the artifact holds them, and nothing else. A
    part, given by its place, holds no section: one asked of it is refused as lacking, of the part, not its artifact."""
    section = None if part else _find_section(found.get("sections", []), title)
    if section is None:
        raise Refused([refusals.no_section(ArtifactId(found["id"]), title, part)])
    return _response(found, dumps(section))


def _summary(store: Port, read: _Read) -> kb_pb2.Artifact:
    """The node at a glance: for an artifact the fields its type shows at a glance, for a part, whose type shows
    none, its name and its title; a stub of each thing a link in it points at and of each of its parts; and, for an
    artifact, how many point at it or at a part inside it, by their type and the field they use."""
    response = _response(read.found, dumps(_glance(read)))
    for link in read.links:
        response.references.append(stub(store, link.field, values.target(link.target).id))
    response.placeholders.extend(_placeholders(store, {read.found["id"]: read.links}))
    for collection in read.declared["parts"]:
        for item in read.node.get(collection, []):
            response.parts.append(kb_pb2.PartStub(collection=collection, id=item["id"], title=item["title"]))
    if read.node is read.found:
        for (type_name, field), count in store.inbound(ArtifactId(read.found["id"])).items():
            response.inbound.append(kb_pb2.InboundCount(kind=type_name, field=field, count=count))
    return response


def _glance(read: _Read) -> dict:
    if read.node is read.found:
        return _summary_fields(read.found, read.declared)
    return {key: read.node[key] for key in ("id", "title") if key in read.node}


def _response(found: dict, content: str) -> kb_pb2.Artifact:
    return kb_pb2.Artifact(
        id=found["id"], type=found["type"], revision=found["revision"],
        title=found["title"], content=content,
    )


def _resolved(store: Port, artifact_id: ArtifactId, depth: int, on_path: set, shown: dict[str, dict]) -> dict:
    """The artifact as stored, each link in its own fields followed depth steps with the target, itself resolved, in
    place of its name; a link inside one of its items stays a name. A target on the path already being filled in
    stays a name, so a loop ends, and so does one the store does not hold; a link into a part of an artifact stays
    the reference written, a part being no artifact. Each artifact given, this one and those filled in, is put in
    `shown` as stored, once."""
    found = store.artifact(artifact_id)
    shown.setdefault(str(artifact_id), found)
    if depth < 1:
        return found
    return _filled(store, found, {link.field for link in _carried(store, found) if link.own}, depth, on_path, shown)


def _filled(store: Port, node: dict, fields: set, depth: int, on_path: set, shown: dict[str, dict]) -> dict:
    """A node with each link in those fields of it followed depth steps, as `_resolved` says."""
    if depth < 1:
        return node
    def fill(target):
        linked = values.target(target)
        if linked.place or target in on_path or not store.holds(linked.id):
            return target
        return _resolved(store, linked.id, depth - 1, on_path | {target}, shown)
    filled = dict(node)
    for field in fields:
        value = node[field]
        filled[field] = [fill(target) for target in value] if isinstance(value, list) else fill(value)
    return filled


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
