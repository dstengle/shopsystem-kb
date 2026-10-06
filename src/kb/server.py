"""The store hosted over the network: the servicer an in-process client reaches, for one store, served by
`grpc.server` at the address the operator gives, stamping each change with the server's own clock. A root that
holds nothing this kb can serve is refused before anything listens (`refused`). A server is
started (`started`), says the address it serves at (`Server.address`), the port the system gave when it was asked
for none, and is stopped (`Server.stop`); `kb serve` runs one until it is signalled to stop (`until_signalled`)."""
import signal
import threading
from concurrent import futures
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import grpc

from kb import names, store
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


class Server:
    """A store served at an address, answering until it is stopped."""

    def __init__(self, root: Path, listen: Address, clock=None):
        self._grpc = grpc.server(futures.ThreadPoolExecutor(max_workers=WORKERS))
        kb_pb2_grpc.add_KbServicer_to_server(KbServicer(root, clock), self._grpc)
        self.address = Address(listen.host, self._grpc.add_insecure_port(str(listen)))

    def start(self) -> None:
        """Answers from now on."""
        self._grpc.start()

    def stop(self) -> None:
        """Stops answering, the calls in flight given GRACE seconds to finish."""
        self._grpc.stop(GRACE).wait()


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
