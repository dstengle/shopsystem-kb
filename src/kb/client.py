"""The client: an object with the stub's method names that, on each call, finds what it reaches and chooses the
transport for it, the servicer called directly for a store found, the network (kb.network) for the connection to a
server; and, beside it, the operator's commands that are not rpcs, each a function over the store it finds, never
through a server."""
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

from kb import network, refusals, responses, store
from kb.export import Exported
from kb.importing import Checked
from kb.contract import kb_pb2
from kb.operating import Importing, Operator
from kb.servicer import KbServicer


def _found(root: Path | None) -> tuple[store.Found | None, kb_pb2.Fault | None]:
    """What a call reaches: the store or the connection to a server found the way git finds a repository, upward
    from the root given or, with none, from the working directory; or the fault that says none was found."""
    if root is not None:
        return store.locate_from(root)
    return store.locate(os.environ)


@dataclass(frozen=True)
class Where:
    """Where the client's search stopped, as a call would make it, nothing opened and nothing called: `root`, the
    directory it stopped at; `address`, the server's `host:port` when what it found there is the connection to one,
    and empty otherwise; `faults`, the reasons a call would be refused for finding nothing, never beside a root."""
    root: str = ""
    address: str = ""
    faults: list[kb_pb2.Fault] = field(default_factory=list)


class Client:
    """Same method names, requests and responses as kb_pb2_grpc.KbStub.

    Readied without finding a store. Each call finds what it reaches as it is made, from the root the client was
    given or, with none, the way git finds a repository: a store, called in this process, or the connection to a
    server, called over the network; a call that finds neither answers with that fault and touches nothing. A store
    is started by `kb.init`, never through a client.
    """

    def __init__(self, root: Path | None = None, clock: Callable[[], datetime] | None = None):
        self._root = root
        self._clock = clock

    def where(self) -> Where:
        """Where a call made now would go: the search it would make, given back as a value."""
        found, refusal = _found(self._root)
        if refusal is not None:
            return Where(faults=[refusal])
        return Where(str(found.root), "" if found.address is None else str(found.address))

    def _call(self, rpc: str, request, response):
        """The rpc on what this call finds, or the response carrying the fault that says nothing was found."""
        found, refusal = _found(self._root)
        if refusal is not None:
            return responses.refused(response, [refusal])
        if found.address is not None:
            if self._clock is not None and getattr(KbServicer, rpc).writes:
                return responses.refused(response, [refusals.clock_with_a_server()])
            return network.called(found.address, rpc, request, response)
        return getattr(KbServicer(found.root, self._clock), rpc)(request, None)

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


def connect(root=None, *, clock: Callable[[], datetime] | None = None) -> Client:
    """A client over the store at <root>/kb/, in this process; with no root, over whichever store, or server, each
    call finds.
    Each change it makes is stamped in the history with the moment the clock gives, read at each stamp; with no
    clock, with the machine's. A clock returns a `datetime`, read as UTC when it has no zone; the history gives every
    moment in UTC. `kb.init` takes the same clock."""
    return Client(Path(root) if root is not None else None, clock)


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
    found, or that a server's connection was."""
    found, refusal = _found(None)
    refusal = refusal or store.directly(found)
    if refusal is not None:
        return responses.refused(response, [refusal])
    return getattr(Operator(found.root), command)(request)
