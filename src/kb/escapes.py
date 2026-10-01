"""The fault an exception that escapes the domain becomes, at the servicer's one boundary: the client's clock failing,
the store busy, a store made by an earlier or a later kb, a database that cannot be read, and anything else."""
import sqlite3

from kb import port, refusals, store
from kb.contract import kb_pb2


class ClockFailed(Exception):
    """The client's clock raised, or gave something other than a moment, when it was asked the time."""


def fault(error: Exception) -> kb_pb2.Fault:
    """The fault an exception that escaped the domain becomes."""
    if isinstance(error, ClockFailed):
        return refusals.clock_failed(str(error))
    if isinstance(error, port.Busy):
        return refusals.busy()
    if isinstance(error, store.EarlierKb):
        return refusals.earlier_kb(str(error.root), str(error.files))
    if isinstance(error, store.LaterKb):
        return refusals.later_kb(str(error.root))
    if isinstance(error, (port.Unreadable, sqlite3.Error)):
        return refusals.unreadable(str(error))
    return refusals.escaped(f"{type(error).__name__}: {error}")
