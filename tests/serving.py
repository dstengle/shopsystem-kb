"""A store served as the operator serves one: the installed `kb serve` run as a program on a port the system picks,
the address it says it serves at read from the one line it prints, and the server stopped when the test ends, passed
or failed; a server hosted in the test's own process, its clock a gate a step can shut and its changes' lock watched;
and the connection to a server, written where a step says, as whoever arranges the callers writes it."""
import os
import socket
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

from kb import canonical, server
from kb.addresses import Address

KB = Path(sys.executable).with_name("kb")
STOPPING = 10  # seconds a server is given to stop at the end of a test before it is killed


class Serving:
    """`kb serve` started on a root, listening where it was asked; `address` once it has said where it serves."""

    def __init__(self, root, listen):
        env = {key: value for key, value in os.environ.items() if key not in ("KB_ROOT", "KB_ACTOR")}
        self.process = subprocess.Popen(
            [str(KB), "serve", str(root), "--listen", listen], env=env, cwd=root,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )

    def said(self):
        """The line the server printed once it was serving, or what it said on stderr when it ended without one."""
        line = self.process.stdout.readline()
        if line:
            return line.rstrip("\n")
        return self.process.stderr.read()

    def kill(self):
        """The server's process killed without warning, as SIGKILL kills it, giving it no chance to let anything go."""
        self.process.kill()
        self.process.wait()

    def stop(self):
        """The server stopped, as the operator stops one, and killed if it does not stop in time."""
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=STOPPING)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        self.process.stdout.close()
        self.process.stderr.close()


def started(root, request, listen="127.0.0.1:0"):
    """`kb serve` on root, listening where asked, stopped when the test ends."""
    serving = Serving(root, listen)
    request.addfinalizer(serving.stop)
    return serving


def serving(root, request):
    """`kb serve` on root on 127.0.0.1 at a port the system picks, stopped when the test ends; the address it serves
    at, as `host:port`."""
    said = started(root, request).said()
    host_and_port = said.split("\t")[-1]
    assert said.startswith("serving\t") and host_and_port.startswith("127.0.0.1:"), said
    return host_and_port


def connection(directory, address):
    """The connection to the server at `address`, written in `directory` as whoever arranges the callers writes it."""
    place = Path(directory) / "kb"
    place.mkdir(parents=True, exist_ok=True)
    (place / "server.yaml").write_text(canonical.dump({"address": address}), encoding="utf-8")
    return place / "server.yaml"


def closed_port():
    """An address on 127.0.0.1 at a port the system gave this test, bound and closed again, so no server was ever
    there."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as bound:
        bound.bind(("127.0.0.1", 0))
        return f"127.0.0.1:{bound.getsockname()[1]}"


class Silent:
    """A plain TCP listener on 127.0.0.1 at a port the system gave this test, that accepts every connection and never
    says anything on it: something at the address that is not a kb server."""

    def __init__(self):
        self._listener = socket.create_server(("127.0.0.1", 0))
        self._accepted = []
        self.address = f"127.0.0.1:{self._listener.getsockname()[1]}"
        threading.Thread(target=self._accept, daemon=True).start()

    def _accept(self):
        while True:
            try:
                self._accepted.append(self._listener.accept()[0])
            except OSError:
                return

    def close(self):
        self._listener.close()
        for accepted in self._accepted:
            accepted.close()


def silent(request):
    """A listener that accepts and never answers, closed when the test ends; its address, as `host:port`."""
    listening = Silent()
    request.addfinalizer(listening.close)
    return listening.address


PATIENCE = 30.0  # seconds a step waits for the server's signal before the test fails


class Gate:
    """A server's clock that, once shut, holds the next change that asks it the time, saying it is waiting, until it
    is opened; open, it reads the machine's. kb reads the clock after a change's draft and before its landing."""

    def __init__(self):
        self._shut, self._waiting, self._go = False, threading.Event(), threading.Event()

    def __call__(self):
        if self._shut:
            self._shut = False
            self._waiting.set()
            if not self._go.wait(PATIENCE):
                raise TimeoutError("the held change was never let go")
        return datetime.now(timezone.utc)

    def shut(self):
        self._shut = True

    def holding(self):
        """Waits until a change is held at the gate."""
        assert self._waiting.wait(PATIENCE), "no change asked the time"

    def open(self):
        self._go.set()


class Arrivals:
    """The lock a server takes its changes under, watched: `second` is set once a second change has come to it."""

    def __init__(self, taking):
        self._taking, self._count, self._counting = taking, 0, threading.Lock()
        self.second = threading.Event()

    def __enter__(self):
        with self._counting:
            self._count += 1
            if self._count == 2:
                self.second.set()
        return self._taking.__enter__()

    def __exit__(self, *raised):
        return self._taking.__exit__(*raised)


def hosted(root, request, clock):
    """A server for the store at root in this process, on 127.0.0.1 at a port the system picks, stamping with the
    clock and stopped when the test ends."""
    hosting = server.started(root, Address("127.0.0.1", 0), clock=clock)
    request.addfinalizer(hosting.stop)
    return hosting
