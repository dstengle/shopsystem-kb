"""Transports. In-process: an object with the stub's method names that calls the servicer directly; and, beside it, the
operator's commands that are not rpcs, each a function over the store it finds."""
import os
from datetime import datetime
from pathlib import Path
from typing import Callable

from kb import store
from kb.export import Exported
from kb.importing import Checked
from kb.contract import kb_pb2
from kb.operating import Importing, Operator
from kb.servicer import KbServicer


def _found(root: Path | None) -> tuple[Path | None, kb_pb2.Fault | None]:
    """The store's root: the one given, when it holds a store, or, with none, the one found the way git finds a
    repository; or the fault that says none was found."""
    if root is not None:
        refusal = store.given(root)
        return (None, refusal) if refusal is not None else (root, None)
    return store.locate(os.environ)


class InProcessClient:
    """Same method names, requests and responses as kb_pb2_grpc.KbStub, with no channel between.

    Readied without finding a store. Each call but Init finds its store as it is made, from the root the client
    was given or, with none, the way git finds a repository; a call that finds none answers with that fault and
    touches nothing. Init takes its root from the request and finds nothing.
    """

    def __init__(self, root: Path | None = None, clock: Callable[[], datetime] | None = None):
        self._root = root
        self._clock = clock

    def _servicer(self) -> tuple[KbServicer | None, kb_pb2.Fault | None]:
        root, refusal = _found(self._root)
        if refusal is not None:
            return None, refusal
        return KbServicer(root, self._clock), None

    def Init(self, request, timeout=None):
        return KbServicer(clock=self._clock).Init(request, None)

    def _call(self, rpc: str, request, response):
        """The rpc on the store this call finds, or the response carrying the fault that says none was found."""
        servicer, refusal = self._servicer()
        if refusal is not None:
            return response(faults=[refusal])
        return getattr(servicer, rpc)(request, None)

    def Create(self, request, timeout=None):
        return self._call("Create", request, kb_pb2.CreateResponse)

    def Read(self, request, timeout=None):
        return self._call("Read", request, kb_pb2.ReadResponse)

    def Validate(self, request, timeout=None):
        return self._call("Validate", request, kb_pb2.ValidateResponse)

    def Write(self, request, timeout=None):
        return self._call("Write", request, kb_pb2.WriteResponse)

    def Apply(self, request, timeout=None):
        return self._call("Apply", request, kb_pb2.ApplyResponse)

    def Journal(self, request, timeout=None):
        return self._call("Journal", request, kb_pb2.JournalResponse)

    def Search(self, request, timeout=None):
        return self._call("Search", request, kb_pb2.SearchResponse)

    def Refs(self, request, timeout=None):
        return self._call("Refs", request, kb_pb2.RefsResponse)

    def List(self, request, timeout=None):
        return self._call("List", request, kb_pb2.ListResponse)

    def Snapshot(self, request, timeout=None):
        return self._call("Snapshot", request, kb_pb2.SnapshotResponse)

    def Append(self, request, timeout=None):
        return self._call("Append", request, kb_pb2.AppendResponse)

    def Delete(self, request, timeout=None):
        return self._call("Delete", request, kb_pb2.DeleteResponse)


def connect(root=None, *, clock: Callable[[], datetime] | None = None) -> InProcessClient:
    """A client over the store at <root>/kb/, in this process; with no root, over whichever store each call finds.
    Each change it makes, Init's included, is stamped in the journal with the moment the clock gives, read at each
    stamp; with no clock, with the machine's. A clock returns a `datetime`, read as UTC when it has no zone; the
    journal gives every moment in UTC."""
    return InProcessClient(Path(root) if root is not None else None, clock)


def export(directory: str) -> Exported:
    """The operator's export of the store this call finds to the directory named; not part of the contract."""
    return _operated("export", directory, Exported)


def import_check(directory: str) -> Checked:
    """The operator's check of the directory named for import into the store this call finds; not part of the
    contract."""
    return _operated("import_check", directory, Checked)


def import_(directory: str, role: str, skip_errors: bool = False) -> Checked:
    """The operator's import of the directory named into the store this call finds, under the role named, the files
    with errors and those leading to them skipped when asked; not part of the contract."""
    return _operated("import_", Importing(directory, role, skip_errors), Checked)


def _operated(command: str, request, response):
    """The operator's command on the store this call finds, or the response carrying the fault that says none was
    found."""
    root, refusal = _found(None)
    if refusal is not None:
        return response(faults=[refusal])
    return getattr(Operator(root), command)(request)
