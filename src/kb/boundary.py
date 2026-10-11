"""The one fail-closed boundary: every rpc, every operator's command kb.operating holds, and kb.init (kb.starting) runs in it.

The store is opened for that call alone and closed when it ends, unless the call starts one, its request becomes
values (kb.requests, kb.values), one call is made into the domain, and its response is made from what comes back
(kb.responses). A refusal anywhere becomes that call's refusal, here and only here, and so does any exception that
escapes: the clock's failure, the database's, or anything else, each with nothing written.
"""
import contextlib
import functools
from datetime import datetime

from kb import escapes, port, responses, served, store, values


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
