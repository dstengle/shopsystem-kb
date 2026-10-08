"""A seeded setup stopped partway, as an operator's Ctrl-C, a container's stop or the machine's kill stops one: the
installed `kb init --seed` run as a program, and a signal sent to it the moment the directory it was named holds
anything new while it still holds no store. It watches only the directory the operator named, never kb's own layout
inside it, and nothing in kb is told to wait for it."""
import contextlib
import os
import signal
import subprocess
import time
from types import SimpleNamespace

from serving import KB, PATIENCE

POLL = 0.001  # seconds between two looks at the directory


def begun(root):
    """Whether root holds anything new, which only the run under way puts there."""
    return bool(os.listdir(root))


def stopped(root, seed, role, how=signal.SIGKILL, ready=begun):
    """`kb init <root> --seed <seed>` under the role, sent `how` once `ready(root)` holds (by default, once root holds
    anything) and root still holds no `kb/`; its exit code and what it wrote to each stream. Fails when it finished,
    or made the store, before it could be stopped."""
    env = {key: value for key, value in os.environ.items() if key not in ("KB_ROOT", "KB_ACTOR")}
    with _interruptible():
        process = subprocess.Popen(
            [str(KB), "init", str(root), "--seed", str(seed)], env={**env, "KB_ACTOR": role}, cwd=root,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
    try:
        _readied(root, process, ready)
        process.send_signal(how)
        out, err = process.communicate(timeout=PATIENCE)
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate()
    return SimpleNamespace(returncode=process.returncode, stdout=out, stderr=err)


@contextlib.contextmanager
def _interruptible():
    """A program started in the block hears SIGINT as one started from a terminal does, even when the suite itself
    was started ignoring it (a shell's background job), since a program inherits an ignored signal."""
    ignored = signal.getsignal(signal.SIGINT) == signal.SIG_IGN
    if ignored:
        signal.signal(signal.SIGINT, signal.default_int_handler)
    try:
        yield
    finally:
        if ignored:
            signal.signal(signal.SIGINT, signal.SIG_IGN)


def _readied(root, process, ready):
    """Waits until ready(root) holds; fails if the run ended first or put a store in root before it was seen."""
    deadline = time.monotonic() + PATIENCE
    while not ready(root):
        assert process.poll() is None, f"kb init ended, {process.returncode}, before it could be stopped"
        assert time.monotonic() < deadline, "kb init put nothing in the directory"
        time.sleep(POLL)
    assert "kb" not in os.listdir(root), "kb init had placed the store before it could be stopped"
