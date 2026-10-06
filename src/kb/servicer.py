"""The contract's servicer: every rpc, over one store. Called in-process by a client, or hosted by grpc.server (kb.server).

Each rpc, each of the operator's commands kb.operating holds, and kb.init (kb.starting), runs inside one boundary:
the store is opened for that call alone and closed when it ends, unless the call starts one, its request becomes
values (kb.requests, kb.values), one call is made into the domain, and its response is made from what comes back
(kb.responses). A refusal anywhere becomes that rpc's refusal, here and only here, and so does any exception that
escapes: the clock's failure, the database's, or anything else, each with nothing written.
"""
import contextlib
import functools
from datetime import datetime

from kb import changes, check, escapes, port, query, read, requests, responses, served, store, values, write
from kb.contract import kb_pb2, kb_pb2_grpc


def guarded(clock):
    """The client's clock, read so that any failure of it surfaces as ClockFailed; None, the machine's, as it is."""
    if clock is None:
        return None

    def read_it() -> datetime:
        try:
            moment = clock()
        except Exception as error:
            raise escapes.ClockFailed(str(error)) from error
        if not isinstance(moment, datetime):
            raise escapes.ClockFailed(f"it gave {moment!r}, which is not a moment")
        return moment
    return read_it


def boundary(response, opens: bool = True, at_one_moment: bool = False, writes: bool = False):
    """The rpc or the operator's command, over the store opened for it unless it starts one, every read it makes
    seeing the store at one moment when it only reads, answered with a response of this type: what it gave, or a
    refusal when anything in it is refused or any exception escapes it. An rpc that writes is refused while a server
    owns the store, unless this servicer is the one that server hosts, and says it writes (`writes`)."""
    def wrap(rpc):
        @functools.wraps(rpc)
        def run(self, request, context=None):
            try:
                if writes and not self._hosted:
                    served.unserved(self._root)
                if not opens:
                    return responses.answered(response, rpc(self, request))
                with store.opened(self._root) as held, _reading(held, at_one_moment):
                    return responses.answered(response, rpc(self, request, held))
            except values.Refused as refused:
                return responses.refused(response, refused.faults)
            except Exception as error:
                return responses.refused(response, [escapes.fault(error)])
        run.writes = writes
        return run
    return wrap


def _reading(held: port.Port, at_one_moment: bool):
    """The block the rpc runs in: one moment of the store for an rpc that only reads, nothing more for one that lands."""
    return held.at_one_moment() if at_one_moment else contextlib.nullcontext()


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

    @changing(kb_pb2.SnapshotResponse)
    def Snapshot(self, request, held):
        return kb_pb2.Recorded(entry=write.record(held, *requests.snapshot(request), self._clock))
