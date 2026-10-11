"""The contract's servicer: every rpc, over one store. Called in-process by a client, or hosted by grpc.server (kb.server).

Each rpc is a request in, one call into the domain, a response out, or, for `Export`, a stream of them, inside
kb.boundary's one boundary; which rpcs write is marked here (`changing`).
"""
from kb import changes, check, export, query, read, requests, responses, write
from kb.boundary import boundary, guarded, streamed
from kb.contract import kb_pb2, kb_pb2_grpc


def changing(response):
    """The boundary of an rpc that writes."""
    return boundary(response, writes=True)


class KbServicer(kb_pb2_grpc.KbServicer):
    def __init__(self, root, clock=None, hosted: bool = False):
        """Over the store at root, hosted by the server that owns it or not. Each change it makes is stamped by the
        clock, or the machine's with none."""
        self._root = root
        self._clock = guarded(clock)
        self._hosted = hosted

    @changing(kb_pb2.CreateResponse)
    def Create(self, request, held):
        return responses.created(self._land(held, changes.creating(request)).results[0])

    @changing(kb_pb2.ReplaceResponse)
    def Replace(self, request, held):
        return responses.replaced(self._land(held, changes.replacing(request)).results[0])

    @changing(kb_pb2.AddResponse)
    def Add(self, request, held):
        return responses.added(self._land(held, changes.adding(request)).results[0])

    @changing(kb_pb2.RemoveResponse)
    def Remove(self, request, held):
        return responses.removed(self._land(held, changes.removing(request)).results[0])

    @changing(kb_pb2.BatchCreateResponse)
    def BatchCreate(self, request, held):
        return responses.landed(kb_pb2.BatchCreated, self._land(held, changes.creating_many(request)), responses.created)

    @changing(kb_pb2.BatchReplaceResponse)
    def BatchReplace(self, request, held):
        return responses.landed(kb_pb2.BatchReplaced, self._land(held, changes.replacing_many(request)), responses.replaced)

    @changing(kb_pb2.BatchAddResponse)
    def BatchAdd(self, request, held):
        return responses.landed(kb_pb2.BatchAdded, self._land(held, changes.adding_many(request)), responses.added)

    @changing(kb_pb2.BatchRemoveResponse)
    def BatchRemove(self, request, held):
        return responses.landed(kb_pb2.BatchRemoved, self._land(held, changes.removing_many(request)), responses.removed)

    def _land(self, held, change) -> write.Landed:
        """A set of changes landed under its signature."""
        return write.land(held, *change, self._clock)

    @boundary(kb_pb2.ReadResponse, at_one_moment=True)
    def Read(self, request, held):
        return read.artifact(held, requests.reading(request))

    @boundary(kb_pb2.CheckResponse, at_one_moment=True)
    def Check(self, request, held):
        return check.everything(held)

    @boundary(kb_pb2.HistoryResponse, at_one_moment=True)
    def History(self, request, held):
        return query.entries(held, requests.history(request))

    @boundary(kb_pb2.SearchResponse, at_one_moment=True)
    def Search(self, request, held):
        return query.found(held, requests.searching(request))

    @boundary(kb_pb2.FollowResponse, at_one_moment=True)
    def Follow(self, request, held):
        return query.walk(held, requests.following(request))

    @boundary(kb_pb2.ListResponse, at_one_moment=True)
    def List(self, request, held):
        return query.listing(held, requests.listing(request))

    @boundary(kb_pb2.PlaceholdersResponse, at_one_moment=True)
    def Placeholders(self, request, held):
        return query.placeholders(held)

    @streamed(kb_pb2.ExportResponse)
    def Export(self, request, held):
        return map(responses.exported, export.taken(held, requests.exporting(request)))

    @changing(kb_pb2.SnapshotResponse)
    def Snapshot(self, request, held):
        return kb_pb2.Recorded(entry=write.record(held, *requests.snapshot(request), self._clock))
