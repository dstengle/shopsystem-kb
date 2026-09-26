"""The contract's servicer: every rpc, over one store. Hosted in-process today; grpc.server can host it later.

Each rpc runs inside one boundary: its request becomes values (kb.requests, kb.values), one call is made into the
domain, and its response is made from what comes back. A refusal anywhere becomes that rpc's faults, here and only
here.
"""
import functools

from kb import query, read, requests, validation, values, write
from kb.contract import kb_pb2, kb_pb2_grpc
from kb.store import Store


def _boundary(response):
    """The rpc, answered with a response of this type carrying the faults when anything in it is refused."""
    def wrap(rpc):
        @functools.wraps(rpc)
        def run(self, request, context=None):
            try:
                return rpc(self, request)
            except values.Refused as refused:
                return response(faults=refused.faults)
        return run
    return wrap


class KbServicer(kb_pb2_grpc.KbServicer):
    def __init__(self, root=None):
        """Over the store at root; with none, a servicer that can only start a store, taking its root from the request."""
        self._store = Store(root) if root is not None else None

    @_boundary(kb_pb2.InitResponse)
    def Init(self, request):
        actor, root = requests.starting(request)
        write.start(root, actor)
        return kb_pb2.InitResponse()

    @_boundary(kb_pb2.CreateResponse)
    def Create(self, request):
        creation = kb_pb2.Creation(type=request.type, title=request.title, content=request.content)
        result = self._land([kb_pb2.Operation(create=creation)], request).results[0]
        return kb_pb2.CreateResponse(id=str(result.artifact_id), revision=result.revision)

    @_boundary(kb_pb2.WriteResponse)
    def Write(self, request):
        replacement = kb_pb2.Replacement(locator=request.locator, content=request.content)
        result = self._land([kb_pb2.Operation(write=replacement)], request).results[0]
        return kb_pb2.WriteResponse(revision=result.revision)

    @_boundary(kb_pb2.AppendResponse)
    def Append(self, request):
        addition = kb_pb2.Addition(locator=request.locator, content=request.content)
        result = self._land([kb_pb2.Operation(append=addition)], request).results[0]
        return kb_pb2.AppendResponse(id=result.item, revision=result.revision)

    @_boundary(kb_pb2.DeleteResponse)
    def Delete(self, request):
        removal = kb_pb2.Removal(locator=request.locator)
        result = self._land([kb_pb2.Operation(delete=removal)], request).results[0]
        return kb_pb2.DeleteResponse(revision=result.revision)

    @_boundary(kb_pb2.ApplyResponse)
    def Apply(self, request):
        landed = self._land(request.operations, request)
        return kb_pb2.ApplyResponse(batch=landed.batch, results=[
            kb_pb2.Result(id=str(result.artifact_id), revision=result.revision, item=result.item)
            for result in landed.results
        ])

    def _land(self, operations, request) -> write.Landed:
        """A set of operations landed under the request's actor and message."""
        return write.land(self._store, requests.operations(operations), values.signed(request.actor, request.message))

    @_boundary(kb_pb2.ReadResponse)
    def Read(self, request):
        return read.artifact(self._store, requests.reading(request))

    @_boundary(kb_pb2.ValidateResponse)
    def Validate(self, request):
        return validation.check(self._store)

    @_boundary(kb_pb2.JournalResponse)
    def Journal(self, request):
        return query.entries(self._store, requests.journal(request))

    @_boundary(kb_pb2.SearchResponse)
    def Search(self, request):
        return query.found(self._store, requests.searching(request))

    @_boundary(kb_pb2.RefsResponse)
    def Refs(self, request):
        return query.walk(self._store, requests.walk(request))

    @_boundary(kb_pb2.ListResponse)
    def List(self, request):
        return query.listing(self._store, requests.listing(request))

    @_boundary(kb_pb2.SnapshotResponse)
    def Snapshot(self, request):
        named, signed = requests.snapshotted(request.artifacts), values.signed(request.actor, request.message)
        return kb_pb2.SnapshotResponse(entry=write.record(self._store, named, signed))
