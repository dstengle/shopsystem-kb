"""The one fail-closed boundary: every rpc, every operator's command kb.operating holds, and kb.init (kb.starting) runs in it.

The store is opened for that call alone and closed when it ends, unless the call starts one, its request becomes
values (kb.requests, kb.values), one call is made into the domain, and its response is made from what comes back
(kb.responses). A refusal anywhere becomes that call's refusal, here and only here, and so does any exception that
escapes: the clock's failure, the database's, or anything else, each with nothing written. An rpc that answers with a
stream runs in the same boundary held open for the stream's length (`streamed`).
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


def never(request) -> bool:
    """What a call that never writes, whatever its request, says of each: that it does not."""
    return False


def boundary(response, opens: bool = True, at_one_moment: bool = False, writes=never):
    """The rpc or the operator's command, over the store opened for it unless it starts one, every read it makes
    seeing the store at one moment when it only reads, answered with a response of this type: what it gave, or a
    refusal when anything in it is refused or any exception escapes it. A call that writes is refused while a server
    owns the store, unless this servicer is the one that server hosts; whether a call writes is asked of its request
    (`writes`), which the rpc carries for whoever else must know."""
    def wrap(rpc):
        @functools.wraps(rpc)
        def run(self, request, context=None):
            try:
                if writes(request) and not self._hosted:
                    served.unserved(self._root)
                if not opens:
                    return responses.answered(response, rpc(self, request))
                with store.opened(self._root) as held, _reading(held, at_one_moment):
                    return responses.answered(response, rpc(self, request, held))
            except Exception as error:
                return _refusal(response, error)
        run.writes = writes
        return run
    return wrap


def streamed(response):
    """The rpc that answers with a stream and only reads, over the store opened for it, every read it makes seeing
    the store at one moment: the store and that moment are kept until the stream ends, its caller closes it or lets
    it go, or it fails, and no longer. Each thing the rpc gives becomes a message of this type as it is asked for.
    A refusal anywhere, or any exception that escapes, becomes one more message, the refusal: the stream's only
    message when nothing had been given, and its last otherwise, in place of whatever was still to come. Only what is
    raised while the store is read is refused so: no message is given from inside the guarded block, so what the
    caller does to the stream is the caller's. An exception it throws in is raised to it as itself, and a stream it
    closes or lets go ends without another message, the store let go first in both; and on whatever thread it reads,
    closes or lets go, the store's connection being held to none."""
    def wrap(rpc):
        @functools.wraps(rpc)
        def run(self, request, context=None):
            with contextlib.closing(_given(rpc, self, request)) as given:
                more = True
                while more:
                    message, more = _next(response, given)
                    if message is not None:
                        yield message
        run.writes = never
        return run
    return wrap


def _given(rpc, servicer, request):
    """What the rpc gives, each as it is asked for, the store open and at one moment until it is closed."""
    with store.opened(servicer._root, any_thread=True) as held, held.at_one_moment():
        yield from rpc(servicer, request, held)


def _next(response, given):
    """The stream's next message and whether another may follow it: what the rpc gives next; or the refusal, the
    last, when reading it was refused or raised; or no message when the rpc has given everything."""
    try:
        return responses.answered(response, next(given)), True
    except StopIteration:
        return None, False
    except Exception as error:
        return _refusal(response, error), False


def _refusal(response, error: Exception):
    """The response of this type refused for what was raised: a refusal's own faults, or the fault of anything else."""
    faults = error.faults if isinstance(error, values.Refused) else [escapes.fault(error)]
    return responses.refused(response, faults)


def _reading(held: port.Port, at_one_moment: bool):
    """The block the rpc runs in: one moment of the store for an rpc that only reads, nothing more for one that lands."""
    return held.at_one_moment() if at_one_moment else contextlib.nullcontext()
