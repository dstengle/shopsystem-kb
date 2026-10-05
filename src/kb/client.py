"""Transports. In-process: an object with the stub's method names that calls the servicer directly; and, beside it, the
operator's commands that are not rpcs, each a function over the store it finds."""
import os
from datetime import datetime
from pathlib import Path
from typing import Callable

from kb import responses, store
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

    Readied without finding a store. Each call finds its store as it is made, from the root the client was given
    or, with none, the way git finds a repository; a call that finds none answers with that fault and touches
    nothing. A store is started by `kb.init`, never through a client.
    """

    def __init__(self, root: Path | None = None, clock: Callable[[], datetime] | None = None):
        self._root = root
        self._clock = clock

    def _servicer(self) -> tuple[KbServicer | None, kb_pb2.Fault | None]:
        root, refusal = _found(self._root)
        if refusal is not None:
            return None, refusal
        return KbServicer(root, self._clock), None

    def _call(self, rpc: str, request, response):
        """The rpc on the store this call finds, or the response carrying the fault that says none was found."""
        servicer, refusal = self._servicer()
        if refusal is not None:
            return responses.refused(response, [refusal])
        return getattr(servicer, rpc)(request, None)

    def Create(self, request, timeout=None):
        return self._call("Create", request, kb_pb2.CreateResponse)

    def Read(self, request, timeout=None):
        return self._call("Read", request, kb_pb2.ReadResponse)

    def Check(self, request, timeout=None):
        return self._call("Check", request, kb_pb2.CheckResponse)

    def Replace(self, request, timeout=None):
        return self._call("Replace", request, kb_pb2.ReplaceResponse)

    def History(self, request, timeout=None):
        return self._call("History", request, kb_pb2.HistoryResponse)

    def Search(self, request, timeout=None):
        return self._call("Search", request, kb_pb2.SearchResponse)

    def Follow(self, request, timeout=None):
        return self._call("Follow", request, kb_pb2.FollowResponse)

    def List(self, request, timeout=None):
        return self._call("List", request, kb_pb2.ListResponse)

    def Snapshot(self, request, timeout=None):
        return self._call("Snapshot", request, kb_pb2.SnapshotResponse)

    def Add(self, request, timeout=None):
        return self._call("Add", request, kb_pb2.AddResponse)

    def Remove(self, request, timeout=None):
        return self._call("Remove", request, kb_pb2.RemoveResponse)

    def BatchCreate(self, request, timeout=None):
        return self._call("BatchCreate", request, kb_pb2.BatchCreateResponse)

    def BatchReplace(self, request, timeout=None):
        return self._call("BatchReplace", request, kb_pb2.BatchReplaceResponse)

    def BatchAdd(self, request, timeout=None):
        return self._call("BatchAdd", request, kb_pb2.BatchAddResponse)

    def BatchRemove(self, request, timeout=None):
        return self._call("BatchRemove", request, kb_pb2.BatchRemoveResponse)


def connect(root=None, *, clock: Callable[[], datetime] | None = None) -> InProcessClient:
    """A client over the store at <root>/kb/, in this process; with no root, over whichever store each call finds.
    Each change it makes is stamped in the history with the moment the clock gives, read at each stamp; with no
    clock, with the machine's. A clock returns a `datetime`, read as UTC when it has no zone; the history gives every
    moment in UTC. `kb.init` takes the same clock."""
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
        return responses.refused(response, [refusal])
    return getattr(Operator(root), command)(request)
