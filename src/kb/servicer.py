"""The contract's servicer: every rpc, over one store. Hosted in-process today; grpc.server can host it later.

Each rpc first turns what the request carries into checked values (kb.values); nothing past that point sees a
string that came from the request.
"""
from kb import query, read, requests, validation, values, write
from kb.contract import kb_pb2, kb_pb2_grpc
from kb.store import Store


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
        return validation.check(self._store)

    def Journal(self, request, context):
        try:
            return query.entries(self._store, requests.journal(request))
        except values.Refused as refused:
            return kb_pb2.JournalResponse(faults=refused.faults)

    def Search(self, request, context):
        try:
            return query.found(self._store, requests.searching(request))
        except values.Refused as refused:
            return kb_pb2.SearchResponse(faults=refused.faults)

    def Refs(self, request, context):
        try:
            return query.walk(self._store, requests.walk(request))
        except values.Refused as refused:
            return kb_pb2.RefsResponse(faults=refused.faults)

    def List(self, request, context):
        try:
            return query.listing(self._store, requests.listing(request))
        except values.Refused as refused:
            return kb_pb2.ListResponse(faults=refused.faults)

    def Snapshot(self, request, context):
        try:
            snapshotted = query.snapshotted(self._store, requests.snapshotted(request.artifacts))
        except values.Refused as refused:
            return kb_pb2.SnapshotResponse(faults=refused.faults)
        signed = values.signed(request.actor, request.message)
        return kb_pb2.SnapshotResponse(entry=write.record(self._store, snapshotted, signed))
