"""A store started out of sight beneath the root it is for and put in place inside it whole: started, and seeded, in a
staging place under the root, then moved to where a store goes by one rename, on the one filesystem the root is on, so
the root holds either no store or the whole of one: a store started to be served (`started`), and one seeded from a
directory of files (`seeded`); and a store started for a server to serve (`serving`), taken back out of the root
should the server not then serve it. What an earlier stopped run left in the staging place is removed first, and the
staging place is removed whenever a start ends, placed or refused. The staging place is the store's own layout, not
published."""
import contextlib
import os
import shutil
from pathlib import Path
from typing import Callable, Iterator

from kb import importing, operating, starting, store

_STAGING = ".kb-starting"


def started(root, role: str) -> None:
    """A store started inside root under the role, holding nothing yet, as a server is started on it to serve it.
    Raises NotStarted, leaving root as it found it, when no store can be started there."""
    _vacant(root)
    with staged(root) as place:
        starting.init(place, role)
        placed(place, root)


@contextlib.contextmanager
def serving(root, role: str | None) -> Iterator[Callable[[], None]]:
    """With a role, a store started inside root under it (`started`) for the block to serve; the block is given what it
    calls once the store is served, to keep it. A store this run placed and the block did not keep is taken back out
    of root, whole, however the block ended, leaving root as it found it. With no role, nothing is started, and
    nothing is ever taken back. Raises NotStarted, leaving root as it found it, when no store can be started there."""
    if role is not None:
        started(root, role)
    kept = []
    try:
        yield lambda: kept.append(True)
    finally:
        if role is not None and not kept:
            _taken_back(root)


def seeded(root, role: str, seed: str) -> importing.Checked:
    """A store started inside root under the role, holding the seed directory's files as the operator's import lands
    them into a freshly started store, or none: the import's answer, its report and the faults that refused it. Raises
    NotStarted, leaving root as it found it, when no store can be started there."""
    _vacant(root)
    with staged(root) as place:
        starting.init(place, role)
        imported = operating.Operator(place).import_(operating.Importing(seed, role, False))
        if not imported.faults:
            placed(place, root)
    return imported


@contextlib.contextmanager
def staged(root) -> Iterator[Path]:
    """The staging place beneath root, cleared of whatever an earlier stopped run left there, for the block to start a
    store in; removed whole when the block ends, however it ends. Raises NotStarted, with the fault, when it cannot be
    made."""
    place = Path(root) / _STAGING
    starting.prepared(lambda: _emptied(place))
    try:
        yield place
    finally:
        _cleared(place)


def placed(place: Path, root) -> None:
    """The store started in the staging place put where a store goes inside root, whole, by one rename."""
    os.rename(place / store.MARKER.parent, Path(root) / store.MARKER.parent)


def _taken_back(root) -> None:
    """The store placed inside root moved out to the staging place by one rename, and removed with it."""
    with staged(root) as place:
        os.rename(Path(root) / store.MARKER.parent, place / store.MARKER.parent)


def _vacant(root) -> None:
    """Raises NotStarted with the faults kb.init would refuse root for, before anything is made."""
    faults = starting.refused(root)
    if faults:
        raise starting.NotStarted(faults)


def _emptied(place: Path) -> None:
    _cleared(place)
    place.mkdir()


def _cleared(place: Path) -> None:
    if place.exists():
        shutil.rmtree(place)
