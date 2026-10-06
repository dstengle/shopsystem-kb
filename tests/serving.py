"""A store served as the operator serves one: the installed `kb serve` run as a program on a port the system picks,
the address it says it serves at read from the one line it prints, and the server stopped when the test ends, passed
or failed; and the connection to a server, written where a step says, as whoever arranges the callers writes it."""
import os
import subprocess
import sys
from pathlib import Path

from kb import canonical

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
