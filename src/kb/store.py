"""Where a store is and what marks it: <root>/kb/, holding the marker store.yaml and beside it the database the
adapter keeps the store in; and finding it, the way git finds a repository: upward from the working directory, or
named by KB_ROOT. CONTRACT_VERSION is the store marker's value alone, written to store.yaml when the store is
started; the store's own, not part of the published contract (adrs/0018)."""
import contextlib
import shutil
import sqlite3
from pathlib import Path
from typing import Callable, Mapping

from kb import canonical, rules, sqlite_store
from kb.contract import kb_pb2
from kb.port import Port, Unreadable
from kb.values import Refused, Root

MARKER = Path("kb") / "store.yaml"
DATABASE = MARKER.parent / "store.sqlite3"
CONTRACT_VERSION = "0.1"


def opened(root) -> contextlib.AbstractContextManager[Port]:
    """The store at root, open until the block ends: the database beside its marker, handed to the adapter."""
    return sqlite_store.opened(Path(root) / DATABASE)


def start(root: Root, fill: Callable[[Port], None]) -> None:
    """The store's place made, then its database, filled by `fill`, then its marker, last, so a store is marked only
    once it is whole. A SQLite that cannot keep a store is refused before anything is made; when making the
    database or the marker raises, the place is removed and the error raised: a failed start leaves nothing."""
    sqlite_store.supported()
    place = root.path / MARKER.parent
    place.mkdir()
    try:
        sqlite_store.make(root.path / DATABASE)
        with opened(root.path) as made:
            fill(made)
        (root.path / MARKER).write_text(canonical.dump({"contract": CONTRACT_VERSION}), encoding="utf-8")
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


def given(root: Path) -> kb_pb2.Fault | None:
    """The fault for a root given outright that holds no store, its marker not inside it; None when it holds one."""
    if (root / MARKER).is_file():
        return None
    return kb_pb2.Fault(rule=rules.STORE, message=f"the root given holds no store: {root}")


def locate(env: Mapping[str, str]) -> tuple[Path | None, kb_pb2.Fault | None]:
    """The store a call goes to from the working directory, or the fault that refuses it. Nothing is guessed at. A
    working directory that is gone is inside no store."""
    cwd = working_directory()
    above = None if cwd is None else find_above(cwd)
    if "KB_ROOT" not in env:
        if above is None:
            return None, _nothing_found(cwd)
        return above, None
    value = env["KB_ROOT"]
    named = Path(value)
    if not value or not (named / MARKER).is_file():
        return None, kb_pb2.Fault(
            rule=rules.STORE, message=f"KB_ROOT names a directory that holds no store: {value}",
        )
    if above is not None and above.resolve() != named.resolve():
        return None, kb_pb2.Fault(
            rule=rules.STORE,
            message=f"KB_ROOT names a store other than the one {cwd} is working in: KB_ROOT is {named}, "
                    f"the working directory is inside {above}; neither is guessed at",
        )
    return named, None


def _nothing_found(cwd: Path | None) -> kb_pb2.Fault:
    """The fault for a call that finds no store above where it works and none named: where it works is named, or,
    when that is gone, said to be gone."""
    if cwd is None:
        return kb_pb2.Fault(
            rule=rules.STORE, message="no store was found: the working directory is gone, and nothing named one outright",
        )
    return kb_pb2.Fault(rule=rules.STORE, message=f"no store was found, neither above {cwd} nor named outright")
