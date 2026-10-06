"""The store hosted over the network: the servicer an in-process client reaches, for one store, served by
`grpc.server` at the address the operator gives, stamping each change with the server's own clock. A root that
holds nothing this kb can serve is refused before anything listens (`refused`), and so is a store another server
owns: a server owns the store it serves, its lock (kb.served) taken before anything is bound and held until it stops,
so a change asked of the store directly is refused meanwhile. It takes changes one at a time, in the order they arrive
at it, each checked against the store as every earlier change left it; reads are answered as they come. A server is
started (`started`), says the address it serves at (`Server.address`), the port the system gave when it was asked
for none, and is stopped (`Server.stop`); `kb serve` runs one until it is signalled to stop (`until_signalled`)."""
import functools
import signal
import threading
from concurrent import futures
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import grpc

from kb import names, served, store
from kb.addresses import Address
from kb.contract import kb_pb2, kb_pb2_grpc
from kb.servicer import KbServicer, boundary
from kb.values import artifact_id

WORKERS = 8  # calls answered at once
GRACE = 3  # seconds the calls in flight are given to finish when the server stops


@dataclass
class Opened:
    """What opening the store to serve it answers: the faults that refused it, none when it can be served."""
    faults: list = field(default_factory=list)


class _Opening:
    def __init__(self, root: Path):
        self._root = root

    @boundary(Opened)
    def opened(self, request, held):
        """The store opened and read, which a damaged database is found by only once it is."""
        held.holds(artifact_id(names.written(names.TYPES, names.TYPES)))
        return Opened()


def refused(root: Path) -> list[kb_pb2.Fault]:
    """Why the store at root, given outright, cannot be served: none is there, or it cannot be opened and read;
    nothing when it can."""
    missing = store.given(root)
    if missing is not None:
        return [missing]
    return _Opening(root).opened(None).faults


class _OneAtATime:
    """The servicer a server hosts, each rpc that writes taken under the server's lock (`Server.taking`), so changes
    are taken one at a time in the order they come to it; every other rpc as the servicer answers it."""

    def __init__(self, servicer: KbServicer, server: "Server"):
        self._servicer, self._server = servicer, server

    def __getattr__(self, name):
        rpc = getattr(self._servicer, name)
        if not getattr(rpc, "writes", False):
            return rpc

        @functools.wraps(rpc)
        def taken(request, context=None):
            with self._server.taking:
                return rpc(request, context)
        return taken


class Server:
    """A store served at an address, answering until it is stopped; `taking` is the lock its changes are taken
    under, one at a time."""

    def __init__(self, root: Path, listen: Address, clock=None):
        """The store owned, its lock taken before anything listens, then bound at the address, which the lock names.
        Refused with `served` when another server owns the store."""
        self._owned = served.owned(root)
        self.taking = threading.Lock()
        self._grpc = grpc.server(futures.ThreadPoolExecutor(max_workers=WORKERS))
        kb_pb2_grpc.add_KbServicer_to_server(_OneAtATime(KbServicer(root, clock, hosted=True), self), self._grpc)
        self.address = Address(listen.host, self._grpc.add_insecure_port(str(listen)))
        served.mark(self._owned, self.address)

    def start(self) -> None:
        """Answers from now on."""
        self._grpc.start()

    def stop(self) -> None:
        """Stops answering, the calls in flight given GRACE seconds to finish, then lets the store go."""
        self._grpc.stop(GRACE).wait()
        self._owned.close()


def started(root: Path, listen: Address, clock=None) -> Server:
    """The store at root served at the address, the port the system's when it is 0, answering from now on."""
    server = Server(root, listen, clock)
    server.start()
    return server


def until_signalled(server: Server, ready: Callable[[], None]) -> None:
    """Once ready has been told, waits until the process is told to stop, by SIGINT or SIGTERM, then stops the
    server; a signal that comes as soon as ready is told is already heard."""
    stopping = threading.Event()
    previous = {each: signal.signal(each, lambda *_: stopping.set()) for each in (signal.SIGINT, signal.SIGTERM)}
    try:
        ready()
        stopping.wait()
    finally:
        for each, handler in previous.items():
            signal.signal(each, handler)
        server.stop()
