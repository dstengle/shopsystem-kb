"""Questions asked of the store through the port: the artifacts of a kind, what links reach out of or into an artifact,
where words occur, what the history holds, and what a piece of work read. Nothing here writes."""
from kb import composition, journal, links, names, places, read, refusals, search, values
from kb.contract import kb_pb2
from kb.port import Port
from kb.requests import JournalFilter, Listing, Refusal, Searching, Walk
from kb.values import ArtifactId, Locator, Refused


def listing(store: Port, asked: Listing) -> kb_pb2.ListResponse:
    """Every artifact of a kind whose fields hold the values asked for, in path order, as stubs or names. Raises
    Refused for a kind the store holds no type for."""
    composition.kind_type(asked.kind, store)
    matched = store.ids(asked.kind, asked.fields)
    if asked.ids:
        return kb_pb2.ListResponse(ids=[str(artifact_id) for artifact_id in matched])
    return kb_pb2.ListResponse(stubs=read.stubs(store, asked.kind, matched))


def walk(store: Port, asked: Walk) -> kb_pb2.RefsResponse:
    """What an artifact's links reach, out of it, or out of the place inside it the locator names, or into it, a step at
    a time out to the depth asked: each artifact once, by the shortest route, the one asked about never. A via or a
    type narrows every step. Raises Refused for a kind the store holds no type for, a name the store lacks, or, going
    out, a place it holds nothing at."""
    if asked.kind is not None:
        composition.kind_type(asked.kind, store)
    start = asked.locator.id
    if not store.holds(start):
        raise Refused([refusals.not_found(start)])
    step = _inward if asked.inward else _outward
    reached, seen, frontier = [], {str(start)}, [(asked.locator, [])]
    for _ in range(asked.depth):
        following = []
        for locator, route in frontier:
            for field, other_id in step(store, locator):
                if str(other_id) in seen or (asked.via and field != asked.via):
                    continue
                if asked.kind is not None and other_id.kind != asked.kind:
                    continue
                seen.add(str(other_id))
                taken = [*route, kb_pb2.Hop(field=field, id=str(other_id))]
                reached.append(kb_pb2.Reached(stub=read.stub(store, field, other_id), route=taken))
                following.append((Locator(other_id, ()), taken))
        frontier = following
    return kb_pb2.RefsResponse(reached=reached)


def found(store: Port, asked: Searching) -> kb_pb2.SearchResponse:
    """Every section whose prose, or field whose value, holds a word searched for, as the scope asks, among the
    artifacts of one kind when a type is given, with a stub of its artifact, most often first. Raises Refused for a
    kind the store holds no type for."""
    if asked.kind is not None:
        composition.kind_type(asked.kind, store)
    candidates = store.search(search.terms(asked.text), asked.kind, asked.sections, asked.fields)
    named = sorted({candidate.artifact for candidate in candidates}, key=names.order)
    artifacts = (store.artifact(artifact_id) for artifact_id in named)
    hits = search.rank(artifacts, asked.text, sections=asked.sections, fields=asked.fields)
    return kb_pb2.SearchResponse(matches=[
        kb_pb2.Match(
            stub=read.stub(store, "", values.artifact_id(hit.artifact)), section=hit.section, field=hit.field,
            snippet=hit.snippet,
        )
        for hit in hits
    ])


def entries(store: Port, asked: JournalFilter) -> kb_pb2.JournalResponse:
    """The history's entries, oldest first, narrowed by each of artifact, role, piece of work, time and set given."""
    found = store.history(asked.artifact, asked.role, asked.execution, asked.since, asked.batch)
    return kb_pb2.JournalResponse(entries=[_entry(entry) for entry in found])


def snapshotted(store: Port, named: list) -> list[dict]:
    """Each artifact named with its version now and the fingerprint of its canonical text. Raises Refused with a fault for
    every name that did not convert or that the store lacks, in the order named."""
    faults = []
    for artifact_id in named:
        if isinstance(artifact_id, Refusal):
            faults += artifact_id.faults
        elif not store.holds(artifact_id):
            faults.append(refusals.not_found(artifact_id))
    if faults:
        raise Refused(faults)
    return [
        {
            "artifact": str(artifact_id), "revision": store.artifact(artifact_id)["revision"],
            "digest": journal.digest(store.artifact(artifact_id)),
        }
        for artifact_id in named
    ]


def _outward(store: Port, locator: Locator) -> list[tuple[str, ArtifactId]]:
    """Each link out of an artifact, or out of the place inside it the locator names, as the field and the name it
    points at."""
    artifact = store.artifact(locator.id)
    schema = composition.kind_schema(locator.id.kind, store)["schema"]
    found = links.inside(artifact, schema, store, places.node(artifact, locator))
    return [(link.field, values.artifact_id(link.target)) for link in found]


def _inward(store: Port, locator: Locator) -> list[tuple[str, ArtifactId]]:
    """Each link into an artifact or a part inside it, as the field that points there and the artifact that holds
    that field, in the order of their names. The place the locator names, if any, is not asked."""
    return [(each.field, each.source) for each in store.links_in(locator.id)]


def _entry(entry: dict) -> kb_pb2.Entry:
    """An entry as the contract carries it. A snapshot's entry has no artifact, place, version or fingerprint of its
    own, only what was read."""
    return kb_pb2.Entry(
        id=entry["id"], at=entry["at"], actor=kb_pb2.Actor(**entry["actor"]), op=entry["op"],
        artifact=entry.get("artifact", ""), path=entry.get("path", ""), revision=entry.get("revision", 0),
        schema_version=entry.get("schema_version", 0), digest=entry.get("digest", ""), message=entry["message"],
        batch=entry["batch"], read=[kb_pb2.Snapshotted(**each) for each in entry.get("read", [])],
    )
