"""Two changes made at once, landed in an order a step chooses.

The client that must land second is readied with a clock that blocks: the first time it is asked the time, it says it
is waiting and waits for a go. kb reads the clock after drafting a change and before landing it, so that client is
held with a draft of the store as it stood. The other change then runs to its end, the go is given, and the held
client lands second. In one program the held client runs on a thread; in two, it is `client_program.py`, run with the
suite's interpreter, whose clock waits on files in a directory of the test's own.

A change that must land between another's stamping and its landing, which no clock can hold, is run as that other is
handed to the store (`handed_after`): the port the set is landed through runs it first, the once.

Nothing here sleeps in the hope that the other side has moved on: each side waits for the other's signal.
"""
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from calls import answer
from kb import client as kb_client
from kb import store, values, write
from kb.contract import kb_pb2

PROGRAM = Path(__file__).with_name("client_program.py")
PATIENCE = 30.0  # seconds either side waits for the other's signal before the test fails


class OnAThread:
    """A client in this program, its change made on a thread of its own, held at its clock until let go."""

    def __init__(self, root, rpc: str, request):
        self._waiting, self._go = threading.Event(), threading.Event()
        self._client = kb_client.connect(root, clock=self._clock)
        self._rpc, self._request = rpc, request
        self._response = None
        self.drafts = 0
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _clock(self) -> datetime:
        """kb reads the clock once after each draft of a change, so its readings count the drafts."""
        self.drafts += 1
        self._waiting.set()
        if not self._go.wait(PATIENCE):
            raise TimeoutError("the held change was never let go")
        return datetime.now(timezone.utc)

    def _run(self):
        self._response = getattr(self._client, self._rpc)(self._request)

    def hold(self) -> None:
        self._thread.start()
        if not self._waiting.wait(PATIENCE):
            raise TimeoutError("the held change never asked the time")

    def release(self):
        self._go.set()
        self._thread.join(PATIENCE)
        assert not self._thread.is_alive(), "the held change never finished"
        return self._response


class InAnotherProgram:
    """A client in a program of its own on the same machine, its clock waiting on files in `gate`."""

    def __init__(self, root, rpc: str, request, gate: Path):
        self._root, self._rpc, self._request, self._gate = root, rpc, request, Path(gate)
        self._gate.mkdir()
        self._process = None

    def hold(self) -> None:
        env = {key: value for key, value in os.environ.items() if key != "KB_ROOT"}
        (self._gate / "request").write_bytes(self._request.SerializeToString())
        self._process = subprocess.Popen(
            [sys.executable, str(PROGRAM), str(self._root), str(self._gate), self._rpc],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self._gate, env=env,
        )
        deadline = time.monotonic() + PATIENCE
        while not (self._gate / "waiting").exists():
            if self._process.poll() is not None:
                raise AssertionError(f"the other program ended before asking the time: {self._process.communicate()}")
            if time.monotonic() > deadline:
                raise TimeoutError("the other program never asked the time")
            time.sleep(0.005)

    def release(self):
        (self._gate / "go").touch()
        out, err = self._process.communicate(timeout=PATIENCE)
        assert self._process.returncode == 0, err.decode()
        return getattr(kb_pb2, f"{self._rpc}Response").FromString(out)


def landed_second(held, first):
    """`held`'s change drafted and held at its clock, `first` run to its end, then `held` let go to land second.
    Returns what `held`'s change was answered with, as a step reads it."""
    held.hold()
    first()
    return answer(held.release())


class _RunsFirst:
    """The store's port, but that the first set handed to it lands only after `first` has run to its end."""

    def __init__(self, held, first):
        self._held, self._first = held, first

    def __getattr__(self, name):
        return getattr(self._held, name)

    def land(self, changes, entries):
        first, self._first = self._first, None
        if first is not None:
            first()
        self._held.land(changes, entries)


def handed_after(root, change, first) -> list:
    """A change (kb.changes' reading of its request) drafted and stamped, `first` run to its end just as the set is
    handed to the store, then the set landed. Returns the faults it was refused with, each `(artifact, place,
    rule)`; none when it landed."""
    with store.opened(root) as held:
        try:
            write.land(_RunsFirst(held, first), *change)
        except values.Refused as refused:
            return [(fault.artifact, fault.place, fault.rule) for fault in refused.faults]
    return []
