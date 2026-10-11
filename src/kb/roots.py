"""The values a store's start and the operator's commands take: a root, a directory, a file.

Each is the name as given and the path it makes; what stands there is for the store, the export, the import or the
backup to check.
"""
import os
from dataclasses import dataclass
from pathlib import Path

from kb import rules
from kb.contract import kb_pb2
from kb.values import Refused


@dataclass(frozen=True)
class Root:
    """The directory a store is started in, and the name the request gave it, which a refusal quotes."""
    path: Path
    named: str


def root(named: "str | os.PathLike") -> Root:
    """The directory a store is started in, as it is named, as text or as a path; relative names stay relative.
    What stands there is the store's to check. Anything else, and no name, is refused."""
    text = os.fspath(named) if isinstance(named, os.PathLike) else named
    if not isinstance(text, str):
        raise Refused([kb_pb2.Fault(
            rule=rules.ROOT,
            message=f"a store is started in a directory named as text or as a path; it was named {named!r}",
        )])
    if not text:
        raise Refused([kb_pb2.Fault(
            rule=rules.ROOT,
            message="a store is started in a directory that was named and that exists; no directory was named",
        )])
    return Root(Path(text), text)


@dataclass(frozen=True)
class Named:
    """A directory or a file the operator names for the store's files, and the name given, which a refusal quotes."""
    path: Path
    named: str


def directory(text: str) -> Named:
    """The directory the operator names, as named; relative names stay relative. What stands there is the export's
    to check."""
    return Named(Path(text), text)


def file(text: str) -> Named:
    """The file the operator names for a backup, as named; relative names stay relative. What stands there is the
    backup's to check."""
    return Named(Path(text), text)
