"""Whether a store is served, and at what address: while it serves, a server holds an exclusive lock of the operating
system (`flock`) on kb/served.yaml, the store's own file naming the address it serves at, and the lock goes when the
server's process does, however it ends. The file left there with nobody holding its lock, or no file at all, is a
store nobody serves. A lock of this kind conflicts between files opened apart, in one process as across processes."""
import fcntl
from pathlib import Path
from typing import IO

from kb import canonical, refusals, store
from kb.addresses import Address, address
from kb.values import Refused

LOCK = store.MARKER.parent / "served.yaml"


def owned(root: Path) -> IO:
    """The lock on the store at root, held until the file it gives is closed; refused with `served`, naming the
    address the store is served at, when another server holds it."""
    held = open(root / LOCK, "a+", encoding="utf-8")
    try:
        fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        held.close()
        raise Refused([refusals.served(str(_named(root)))]) from None
    return held


def mark(held: IO, at: Address) -> None:
    """The lock's file made to name the address its server serves at."""
    held.seek(0)
    held.truncate()
    held.write(canonical.dump({"address": str(at)}))
    held.flush()


def unserved(root: Path) -> None:
    """Refuse, with `served` naming the server's address, a change asked of the store at root directly while a server
    holds its lock."""
    at = _serving(root)
    if at is not None:
        raise Refused([refusals.served(str(at))])


def _serving(root: Path) -> Address | None:
    """The address the store at root is served at, or None when no server holds its lock."""
    try:
        file = open(root / LOCK, encoding="utf-8")
    except FileNotFoundError:
        return None
    with file:
        try:
            fcntl.flock(file, fcntl.LOCK_SH | fcntl.LOCK_NB)
        except BlockingIOError:
            return _named(root)
        return None


def _named(root: Path) -> Address:
    """The address the lock's file names."""
    return address(canonical.load((root / LOCK).read_text(encoding="utf-8"))["address"])
