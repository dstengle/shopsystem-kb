"""Questions asked of the loaded corpus: the artifacts of a kind, what links reach out of or into an artifact, where
words occur, what the journal holds, and what a piece of work read. Nothing here writes."""
from datetime import datetime

from kb import journal, read, refusals, search, validation, values
from kb.content import text
from kb.contract import kb_pb2
from kb.requests import JournalFilter, Listing, Refusal, Searching, Walk
from kb.store import Store
from kb.values import ArtifactId, Refused


def listing(store: Store, asked: Listing) -> kb_pb2.ListResponse:
    """Every artifact of a kind whose fields hold the values asked for, in path order, as stubs or names."""
    matched = [
        artifact_id for artifact_id in store.ids()
        if artifact_id.kind == asked.kind and _holds(store.artifact(artifact_id), asked.fields)
    ]
    if asked.ids:
        return kb_pb2.ListResponse(ids=[str(artifact_id) for artifact_id in matched])
    return kb_pb2.ListResponse(stubs=[read.stub(store, "", artifact_id) for artifact_id in matched])


def walk(store: Store, asked: Walk) -> kb_pb2.RefsResponse:
    """What an artifact's links reach, out of it or into it, a step at a time out to the depth asked: each artifact
    once, by the shortest route, the one asked about never. A via or a type narrows every step. Raises Refused for
    a name the store lacks."""
    start = asked.locator.id
    if not store.holds(start):
        raise Refused([refusals.not_found(start)])
    step = _inward if asked.inward else _outward
    reached, seen, frontier = [], {str(start)}, [(start, [])]
    for _ in range(asked.depth):
        following = []
        for artifact_id, route in frontier:
            for field, other_id in step(store, artifact_id):
                if str(other_id) in seen or (asked.via and field != asked.via):
                    continue
                if asked.kind is not None and other_id.kind != asked.kind:
                    continue
                seen.add(str(other_id))
                taken = [*route, kb_pb2.Hop(field=field, id=str(other_id))]
                reached.append(kb_pb2.Reached(stub=read.stub(store, field, other_id), route=taken))
                following.append((other_id, taken))
        frontier = following
    return kb_pb2.RefsResponse(reached=reached)


def found(store: Store, asked: Searching) -> kb_pb2.SearchResponse:
    """Every section whose prose, or field whose value, holds a word searched for, as the scope asks, among the
    artifacts of one kind when a type is given, with a stub of its artifact, most often first."""
    artifacts = (
        artifact for artifact in store.artifacts() if asked.kind is None or artifact["type"] == asked.kind.name
    )
    hits = search.rank(artifacts, asked.text, sections=asked.sections, fields=asked.fields)
    return kb_pb2.SearchResponse(matches=[
        kb_pb2.Match(
            stub=read.stub(store, "", values.artifact_id(hit.artifact)), section=hit.section, field=hit.field,
            snippet=hit.snippet,
        )
        for hit in hits
    ])


def entries(store: Store, asked: JournalFilter) -> kb_pb2.JournalResponse:
    """The journal's entries, oldest first, narrowed by each of artifact, role, piece of work, time and set given."""
    return kb_pb2.JournalResponse(entries=[
        _entry(entry) for entry in journal.entries(store.dir)
        if (asked.artifact is None or entry.get("artifact") == str(asked.artifact))
        and (not asked.role or entry["actor"]["role"] == asked.role)
        and (not asked.execution or entry["actor"]["execution"] == asked.execution)
        and (asked.since is None or datetime.fromisoformat(entry["at"]) >= asked.since)
        and (not asked.batch or entry["batch"] == asked.batch)
    ])


def snapshotted(store: Store, named: list) -> list[dict]:
    """Each artifact named with its version now and the fingerprint of its file. Raises Refused with a fault for
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
            "digest": journal.digest(store.path(artifact_id)),
        }
        for artifact_id in named
    ]


def _outward(store: Store, artifact_id: ArtifactId) -> list[tuple[str, ArtifactId]]:
    """Each link out of an artifact, as the field and the name it points at."""
    artifact = store.artifact(artifact_id)
    schema = store.schema(artifact_id.kind)["schema"]
    return [(field, values.artifact_id(target)) for field, _, target in validation.links(artifact, schema, store)]


def _inward(store: Store, artifact_id: ArtifactId) -> list[tuple[str, ArtifactId]]:
    """Each link into an artifact or a part inside it, as the field that points there and the artifact that holds
    that field, in path order."""
    pointing = []
    for other_id in store.ids():
        other = store.artifact(other_id)
        schema = store.schema(other_id.kind)["schema"]
        for field, _, target in validation.links(other, schema, store):
            if validation.points_at(target, artifact_id):
                pointing.append((field, other_id))
    return pointing


def _holds(artifact: dict, fields: dict) -> bool:
    """Whether each field named holds the value given, compared as the text the value is written as."""
    return all(field in artifact and text(artifact[field]) == value for field, value in fields.items())


def _entry(entry: dict) -> kb_pb2.Entry:
    """An entry as the contract carries it. A snapshot's entry has no artifact, place, version or fingerprint of its
    own, only what was read."""
    return kb_pb2.Entry(
        id=entry["id"], at=entry["at"], actor=kb_pb2.Actor(**entry["actor"]), op=entry["op"],
        artifact=entry.get("artifact", ""), path=entry.get("path", ""), revision=entry.get("revision", 0),
        schema_version=entry.get("schema_version", 0), digest=entry.get("digest", ""), message=entry["message"],
        batch=entry["batch"], read=[kb_pb2.Snapshotted(**each) for each in entry.get("read", [])],
    )
