"""The contract's servicer: every rpc, over one store. Hosted in-process today; grpc.server can host it later.

Each rpc runs inside one boundary: the store is opened for that call alone and closed when it ends, its request
becomes values (kb.requests, kb.values), one call is made into the domain, and its response is made from what comes
back. A refusal anywhere becomes that rpc's faults, here and only here.
"""
import functools

from kb import check, query, read, requests, store, values, write
from kb.contract import kb_pb2, kb_pb2_grpc


def _boundary(response, opens: bool = True):
    """The rpc, over the store opened for it unless it starts one, answered with a response of this type carrying
    the faults when anything in it is refused."""
    def wrap(rpc):
        @functools.wraps(rpc)
        def run(self, request, context=None):
            try:
                if not opens:
                    return rpc(self, request)
                with store.opened(self._root) as held:
                    return rpc(self, request, held)
            except values.Refused as refused:
                return response(faults=refused.faults)
        return run
    return wrap


class KbServicer(kb_pb2_grpc.KbServicer):
    def __init__(self, root=None, clock=None):
        """Over the store at root; with none, a servicer that can only start a store, taking its root from the request.
        Each change it makes is stamped by the clock, or the machine's with none."""
        self._root = root
        self._clock = clock

    @_boundary(kb_pb2.InitResponse, opens=False)
    def Init(self, request):
        actor, root = requests.starting(request)
        write.start(root, actor, self._clock)
        return kb_pb2.InitResponse()

    @_boundary(kb_pb2.CreateResponse)
    def Create(self, request, held):
        creation = kb_pb2.Creation(type=request.type, title=request.title, content=request.content)
        result = self._land(held, [kb_pb2.Operation(create=creation)], request).results[0]
        return kb_pb2.CreateResponse(id=str(result.artifact_id), revision=result.revision)

    @_boundary(kb_pb2.WriteResponse)
    def Write(self, request, held):
        replacement = kb_pb2.Replacement(locator=request.locator, content=request.content)
        result = self._land(held, [kb_pb2.Operation(write=replacement)], request).results[0]
        return kb_pb2.WriteResponse(revision=result.revision)

    @_boundary(kb_pb2.AppendResponse)
    def Append(self, request, held):
        addition = kb_pb2.Addition(locator=request.locator, content=request.content)
        result = self._land(held, [kb_pb2.Operation(append=addition)], request).results[0]
        return kb_pb2.AppendResponse(id=result.item, revision=result.revision)

    @_boundary(kb_pb2.DeleteResponse)
    def Delete(self, request, held):
        removal = kb_pb2.Removal(locator=request.locator)
        result = self._land(held, [kb_pb2.Operation(delete=removal)], request).results[0]
        return kb_pb2.DeleteResponse(revision=result.revision)

    @_boundary(kb_pb2.ApplyResponse)
    def Apply(self, request, held):
        landed = self._land(held, request.operations, request)
        return kb_pb2.ApplyResponse(batch=landed.batch, results=[
            kb_pb2.Result(id=str(result.artifact_id), revision=result.revision, item=result.item)
            for result in landed.results
        ])

    def _land(self, held, operations, request) -> write.Landed:
        """A set of operations landed under the request's actor and message."""
        return write.land(held, *requests.change(operations, request.actor, request.message), self._clock)

    @_boundary(kb_pb2.ReadResponse)
    def Read(self, request, held):
        return read.artifact(held, requests.reading(request))

    @_boundary(kb_pb2.ValidateResponse)
    def Validate(self, request, held):
        return check.everything(held)

    @_boundary(kb_pb2.JournalResponse)
    def Journal(self, request, held):
        return query.entries(held, requests.journal(request))

    @_boundary(kb_pb2.SearchResponse)
    def Search(self, request, held):
        return query.found(held, requests.searching(request))

    @_boundary(kb_pb2.RefsResponse)
    def Refs(self, request, held):
        return query.walk(held, requests.walk(request))

    @_boundary(kb_pb2.ListResponse)
    def List(self, request, held):
        return query.listing(held, requests.listing(request))

    @_boundary(kb_pb2.SnapshotResponse)
    def Snapshot(self, request, held):
        return kb_pb2.SnapshotResponse(entry=write.record(held, *requests.snapshot(request), self._clock))
