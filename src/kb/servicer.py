"""The contract's servicer: every rpc, over one store. Hosted in-process today; grpc.server can host it later.

Each rpc first turns what the request carries into checked values (kb.values); nothing past that point sees a
string that came from the request.
"""
from datetime import datetime

from kb import canonical, journal, read, requests, search, validation, values, write
from kb.content import text
from kb.contract import kb_pb2, kb_pb2_grpc
from kb.store import Store, Unreadable
from kb.values import ArtifactId
from kb.refusals import not_found as _not_found


class KbServicer(kb_pb2_grpc.KbServicer):
    def __init__(self, root=None):
        """Over the store at root; with none, a servicer that can only start a store, taking its root from the request."""
        self._store = Store(root) if root is not None else None

    def Init(self, request, context):
        try:
            actor, root = requests.starting(request)
            write.start(root, actor)
        except values.Refused as refused:
            return kb_pb2.InitResponse(faults=refused.faults)
        return kb_pb2.InitResponse()

    def Create(self, request, context):
        creation = kb_pb2.Creation(type=request.type, title=request.title, content=request.content)
        try:
            landed = self._land([kb_pb2.Operation(create=creation)], request)
        except values.Refused as refused:
            return kb_pb2.CreateResponse(faults=refused.faults)
        return kb_pb2.CreateResponse(id=str(landed.results[0].artifact_id), revision=landed.results[0].revision)

    def Write(self, request, context):
        replacement = kb_pb2.Replacement(locator=request.locator, content=request.content)
        try:
            landed = self._land([kb_pb2.Operation(write=replacement)], request)
        except values.Refused as refused:
            return kb_pb2.WriteResponse(faults=refused.faults)
        return kb_pb2.WriteResponse(revision=landed.results[0].revision)

    def Append(self, request, context):
        addition = kb_pb2.Addition(locator=request.locator, content=request.content)
        try:
            landed = self._land([kb_pb2.Operation(append=addition)], request)
        except values.Refused as refused:
            return kb_pb2.AppendResponse(faults=refused.faults)
        return kb_pb2.AppendResponse(id=landed.results[0].item, revision=landed.results[0].revision)

    def Delete(self, request, context):
        removal = kb_pb2.Removal(locator=request.locator)
        try:
            landed = self._land([kb_pb2.Operation(delete=removal)], request)
        except values.Refused as refused:
            return kb_pb2.DeleteResponse(faults=refused.faults)
        return kb_pb2.DeleteResponse(revision=landed.results[0].revision)

    def Apply(self, request, context):
        try:
            landed = self._land(request.operations, request)
        except values.Refused as refused:
            return kb_pb2.ApplyResponse(faults=refused.faults)
        return kb_pb2.ApplyResponse(batch=landed.batch, results=[
            kb_pb2.Result(id=str(result.artifact_id), revision=result.revision, item=result.item)
            for result in landed.results
        ])

    def _land(self, operations, request) -> write.Landed:
        """A set of operations landed under the request's actor and message."""
        return write.land(self._store, requests.operations(operations), values.signed(request.actor, request.message))

    def Read(self, request, context):
        try:
            return read.artifact(self._store, requests.reading(request))
        except values.Refused as refused:
            return kb_pb2.ReadResponse(faults=refused.faults)

    def Validate(self, request, context):
        """Every artifact checked against the current version of its type, and listed as stale when it was last
        checked against an older one; a file that cannot be read is reported and the check goes on."""
        violations, stale = [], []
        for artifact_id in self._store.ids():
            try:
                artifact = self._store.load(artifact_id)
                schema = self._store.schema(artifact_id.kind)
            except Unreadable as unreadable:
                violations.append(unreadable.fault)
                continue
            if artifact["schema_version"] < schema["version"]:
                stale.append(kb_pb2.Stale(
                    artifact=str(artifact_id), schema_version=artifact["schema_version"], current=schema["version"],
                ))
            content = {key: value for key, value in artifact.items() if key not in canonical.IDENTITY[:4]}
            violations += validation.validate(str(artifact_id), content, schema["schema"], self._store)
        return kb_pb2.ValidateResponse(violations=violations, stale=stale)

    def Journal(self, request, context):
        """The journal's entries, oldest first, narrowed by each of artifact, role, piece of work, time and set given."""
        try:
            wanted = requests.journal(request)
        except values.Refused as refused:
            return kb_pb2.JournalResponse(faults=refused.faults)
        return kb_pb2.JournalResponse(entries=[
            _entry(entry) for entry in journal.entries(self._store.dir)
            if (wanted.artifact is None or entry.get("artifact") == str(wanted.artifact))
            and (not wanted.role or entry["actor"]["role"] == wanted.role)
            and (not wanted.execution or entry["actor"]["execution"] == wanted.execution)
            and (wanted.since is None or datetime.fromisoformat(entry["at"]) >= wanted.since)
            and (not wanted.batch or entry["batch"] == wanted.batch)
        ])

    def Search(self, request, context):
        """Every section whose prose, or field whose value, holds a word searched for, as the scope asks, among the
        artifacts of one kind when a type is given, with a stub of its artifact, most often first."""
        try:
            searching = requests.searching(request)
        except values.Refused as refused:
            return kb_pb2.SearchResponse(faults=refused.faults)
        kind = searching.kind
        artifacts = (artifact for artifact in self._store.artifacts() if kind is None or artifact["type"] == kind.name)
        hits = search.rank(artifacts, searching.text, sections=searching.sections, fields=searching.fields)
        return kb_pb2.SearchResponse(matches=[
            kb_pb2.Match(
                stub=read.stub(self._store, "", values.artifact_id(hit.artifact)), section=hit.section, field=hit.field,
                snippet=hit.snippet,
            )
            for hit in hits
        ])

    def Refs(self, request, context):
        """What an artifact's links reach, out of it or into it, a step at a time out to the depth asked: each artifact
        once, by the shortest route, the one asked about never. A via or a type narrows every step."""
        try:
            walk = requests.walk(request)
        except values.Refused as refused:
            return kb_pb2.RefsResponse(faults=refused.faults)
        locator, kind = walk.locator, walk.kind
        if not self._store.holds(locator.id):
            return kb_pb2.RefsResponse(faults=[_not_found(locator.id)])
        step = self._inward if walk.inward else self._outward
        reached, seen, frontier = [], {str(locator.id)}, [(locator.id, [])]
        for _ in range(walk.depth):
            following = []
            for artifact_id, route in frontier:
                for field, other_id in step(artifact_id):
                    if str(other_id) in seen or (walk.via and field != walk.via):
                        continue
                    if kind is not None and other_id.kind != kind:
                        continue
                    seen.add(str(other_id))
                    taken = [*route, kb_pb2.Hop(field=field, id=str(other_id))]
                    reached.append(kb_pb2.Reached(stub=read.stub(self._store, field, other_id), route=taken))
                    following.append((other_id, taken))
            frontier = following
        return kb_pb2.RefsResponse(reached=reached)

    def _outward(self, artifact_id: ArtifactId) -> list[tuple[str, ArtifactId]]:
        """Each link out of an artifact, as the field and the name it points at."""
        artifact = self._store.load(artifact_id)
        schema = self._store.schema(artifact_id.kind)["schema"]
        return [(field, values.artifact_id(target)) for field, _, target in validation.links(artifact, schema, self._store)]

    def _inward(self, artifact_id: ArtifactId) -> list[tuple[str, ArtifactId]]:
        """Each link into an artifact or a part inside it, as the field that points there and the artifact that holds
        that field, in path order."""
        found = []
        for other_id in self._store.ids():
            other = self._store.load(other_id)
            schema = self._store.schema(other_id.kind)["schema"]
            for field, _, target in validation.links(other, schema, self._store):
                if validation.points_at(target, artifact_id):
                    found.append((field, other_id))
        return found

    def List(self, request, context):
        """Every artifact of a kind whose fields hold the values asked for, in path order, as stubs or names."""
        try:
            listing = requests.listing(request)
        except values.Refused as refused:
            return kb_pb2.ListResponse(faults=refused.faults)
        matched = [
            artifact_id for artifact_id in self._store.ids()
            if artifact_id.kind == listing.kind and _holds(self._store.load(artifact_id), listing.fields)
        ]
        if listing.ids:
            return kb_pb2.ListResponse(ids=[str(artifact_id) for artifact_id in matched])
        return kb_pb2.ListResponse(stubs=[read.stub(self._store, "", artifact_id) for artifact_id in matched])

    def Snapshot(self, request, context):
        """One journal entry listing each artifact named with its version now and the fingerprint of its file, under
        the actor and the message given, in a commit of its own."""
        named, faults = [], []
        for artifact_id in requests.snapshotted(request.artifacts):
            if isinstance(artifact_id, requests.Refusal):
                faults += artifact_id.faults
                continue
            if not self._store.holds(artifact_id):
                faults.append(_not_found(artifact_id))
                continue
            named.append(artifact_id)
        if faults:
            return kb_pb2.SnapshotResponse(faults=faults)
        read = [
            {
                "artifact": str(artifact_id), "revision": self._store.load(artifact_id)["revision"],
                "digest": journal.digest(self._store.path(artifact_id)),
            }
            for artifact_id in named
        ]
        signed = values.signed(request.actor, request.message)
        return kb_pb2.SnapshotResponse(entry=write.record(self._store, read, signed))

def _holds(artifact: dict, fields) -> bool:
    """Whether each field named holds the value given, compared as the text the value is written as."""
    return all(field in artifact and text(artifact[field]) == value for field, value in fields.items())


def _entry(entry: dict) -> kb_pb2.Entry:
    """An entry as the contract carries it. A snapshot's entry has no artifact, place, version or fingerprint of its
    own, only what was read."""
    return kb_pb2.Entry(
        id=entry["id"], at=entry["at"], actor=kb_pb2.Actor(**entry["actor"]), op=entry["op"],
        artifact=entry.get("artifact", ""), path=entry.get("path", ""), revision=entry.get("revision", 0),
        schema_version=entry.get("schema_version", 0), digest=entry.get("digest", ""), message=entry["message"],
        batch=entry["batch"], read=[kb_pb2.Snapshotted(**read) for read in entry.get("read", [])],
    )
