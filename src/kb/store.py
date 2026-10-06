"""Where a store is and what marks it: <root>/kb/, holding the marker store.yaml and beside it the database the
adapter keeps the store in; or the connection to a server serving one, kb/server.yaml, written by whoever arranges
the callers and naming the server's `address`. Finding either, the way git finds a repository: upward from the
working directory, or named by KB_ROOT. STORE_FORM is the store marker's value alone, written to store.yaml when the
store is started; the store's own, not part of the published contract (adrs/0018). An earlier kb's marker held
`contract`, and a store it made is told apart by that."""
import contextlib
import shutil
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping

from kb import canonical, rules, sqlite_store
from kb.addresses import Address, address
from kb.contract import kb_pb2
from kb.port import Port, Unreadable
from kb.values import Refused, Root

MARKER = Path("kb") / "store.yaml"
DATABASE = MARKER.parent / "store.sqlite3"
CONNECTION = MARKER.parent / "server.yaml"
STORE_FORM = 1


@dataclass(frozen=True)
class Found:
    """Where a search stopped: the directory, and, when what it found there is the connection to a server rather
    than a store, the address that connection names."""
    root: Path
    address: Address | None = None


def _found_at(directory: Path) -> Found:
    """What the directory holds: its store, or, with none, the connection to a server."""
    if (directory / MARKER).is_file():
        return Found(directory)
    return Found(directory, _connection(directory / CONNECTION))


def _connection(path: Path) -> Address:
    """The address the connection at path names, its `address` read from it as YAML 1.2."""
    return address(canonical.load(path.read_text(encoding="utf-8"))["address"])


def _marks(directory: Path) -> bool:
    """Whether the directory holds a store or the connection to a server."""
    return (directory / MARKER).is_file() or (directory / CONNECTION).is_file()


class EarlierKb(Exception):
    """The store was made by an earlier version of kb, in a form this kb cannot read: where it is, and the directory
    holding its files, which are imported into a new store to move it."""

    def __init__(self, root: Path):
        super().__init__(str(root))
        self.root = root
        self.files = root / MARKER.parent


class LaterKb(Exception):
    """The store's marker names a form of store this kb does not know, or cannot be read at all: a later version of kb
    is needed to read it. It carries where the store is."""

    def __init__(self, root: Path):
        super().__init__(str(root))
        self.root = root


def opened(root) -> contextlib.AbstractContextManager[Port]:
    """The store at root, open until the block ends: the database beside its marker, handed to the adapter. Raises,
    opening nothing, EarlierKb when the marker is the one an earlier kb wrote, and LaterKb when it is any other but
    this kb's own or cannot be read at all."""
    _told_apart(Path(root))
    return sqlite_store.opened(Path(root) / DATABASE)


def _told_apart(root: Path) -> None:
    """Refuse a store whose marker is not exactly this kb's: one holding `contract`, which an earlier kb wrote, as an
    earlier kb's; any other, and one that cannot be read at all, whatever its bytes, as a later kb's."""
    try:
        marker = canonical.load((root / MARKER).read_text(encoding="utf-8"))
    except (canonical.NotCanonical, UnicodeDecodeError, OSError):
        raise LaterKb(root) from None
    if isinstance(marker, dict) and canonical.dump(marker) == canonical.dump({"store": STORE_FORM}):
        return
    if isinstance(marker, dict) and "contract" in marker:
        raise EarlierKb(root)
    raise LaterKb(root)


def start(root: Root, fill: Callable[[Port], None]) -> None:
    """The store's place made, then its database, filled by `fill`, then its marker, last, so a store is marked only
    once it is whole. A SQLite that cannot keep a store is refused before anything is made; when making the
    database or the marker raises, the place is removed and the error raised: a failed start leaves nothing."""
    sqlite_store.supported()
    place = root.path / MARKER.parent
    place.mkdir()
    try:
        sqlite_store.make(root.path / DATABASE)
        with sqlite_store.opened(root.path / DATABASE) as made:
            fill(made)
        (root.path / MARKER).write_text(canonical.dump({"store": STORE_FORM}), encoding="utf-8")
    except (sqlite3.Error, OSError, Unreadable):
        shutil.rmtree(place)
        raise


def vacant(root: Root) -> None:
    """Refuse a root a store cannot be started in: one that is not there, is not a directory, has a store inside it or
    anything else in the place a store goes, or is inside a store. A relative root cannot be resolved once the
    working directory it is read against is itself gone; that is refused too, never raised."""
    def refuse(message: str):
        raise Refused([kb_pb2.Fault(rule=rules.ROOT, message=message)])

    named = repr(root.named)
    if not root.path.is_absolute() and working_directory() is None:
        refuse(f"a store is started in a directory that exists; whether {named} does depends on the working "
               f"directory, and it is gone")
    if not root.path.exists():
        refuse(f"a store is started in a directory that exists; {named} does not")
    if not root.path.is_dir():
        refuse(f"a store is started in a directory, and {named} is not one")
    if (root.path / MARKER).is_file():
        refuse(f"a store is never started over another; {named} already has a store inside it")
    if (root.path / MARKER.parent).exists() or (root.path / MARKER.parent).is_symlink():
        refuse(f"a store goes in a place of its own, and {named} already holds something in that place")
    above = find_above(root.path.resolve().parent)
    if above is not None:
        refuse(f"stores do not nest; {named} is inside the store at {str(above)!r}")


def find_above(start: Path) -> Path | None:
    """The nearest directory at or above `start` with a store inside it, or None."""
    for directory in (start, *start.parents):
        if (directory / MARKER).is_file():
            return directory
    return None


def working_directory() -> Path | None:
    """The directory this process is working in, or None when it has since been removed."""
    try:
        return Path.cwd()
    except FileNotFoundError:
        return None


def _search_above(start: Path) -> Path | None:
    """The nearest directory at or above `start` holding a store or the connection to a server, or None."""
    for directory in (start, *start.parents):
        if _marks(directory):
            return directory
    return None


def directly(found: Found) -> kb_pb2.Fault | None:
    """The fault for an operator's command over the store's own files that found the connection to a server; None
    when it found the store."""
    if found.address is None:
        return None
    return kb_pb2.Fault(rule=rules.STORE, message=(
        f"these commands run where the store is, not through a server: {found.root} holds the connection to the "
        f"server at {found.address}"
    ))


def given(root: Path) -> kb_pb2.Fault | None:
    """The fault for a root given outright that holds no store, its marker not inside it; None when it holds one."""
    if (root / MARKER).is_file():
        return None
    return kb_pb2.Fault(rule=rules.STORE, message=f"the root given holds no store: {root}")


def locate(env: Mapping[str, str]) -> tuple[Found | None, kb_pb2.Fault | None]:
    """The store, or the connection to the server serving one, a call goes to from the working directory, or the
    fault that refuses it. Nothing is guessed at. A working directory that is gone is inside no store."""
    cwd = working_directory()
    above = None if cwd is None else _search_above(cwd)
    if "KB_ROOT" not in env:
        if above is None:
            return None, _nothing_found(cwd)
        return _found_at(above), None
    value = env["KB_ROOT"]
    named = Path(value)
    if not value or not _marks(named):
        return None, kb_pb2.Fault(
            rule=rules.STORE, message=f"KB_ROOT names a directory that holds no store: {value}",
        )
    if above is not None and above.resolve() != named.resolve():
        return None, kb_pb2.Fault(
            rule=rules.STORE,
            message=f"KB_ROOT names a store other than the one {cwd} is working in: KB_ROOT is {named}, "
                    f"the working directory is inside {above}; neither is guessed at",
        )
    return _found_at(named), None


def _nothing_found(cwd: Path | None) -> kb_pb2.Fault:
    """The fault for a call that finds no store above where it works and none named: where it works is named, or,
    when that is gone, said to be gone."""
    if cwd is None:
        return kb_pb2.Fault(
            rule=rules.STORE, message="no store was found: the working directory is gone, and nothing named one outright",
        )
    return kb_pb2.Fault(rule=rules.STORE, message=f"no store was found, neither above {cwd} nor named outright")
