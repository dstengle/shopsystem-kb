"""The journal: one file per entry under <store>/journal/<YYYY>/<MM>/<DD>/, written inside the commit that made the change."""
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, NamedTuple

from kb import canonical, refusals
from kb.signatures import Signed
from kb.store import Damaged


Clock = Callable[[], datetime]


def now() -> datetime:
    """The machine's clock, which stamps an entry when no clock is given. Looked up as each entry is stamped, so a
    replacement made from outside still takes effect, until shop-knowledge's slice 50.23 moves to the given clock."""
    return datetime.now(timezone.utc)


class Stamp(NamedTuple):
    """An entry's moment, the clock's unchanged, and its id, free in the journal and in the set it belongs to."""
    at: datetime
    id: str


def stamps(store_dir: Path, count: int, clock: Clock | None = None) -> list[Stamp]:
    """The stamps of a set's `count` entries, in order, each read from the clock and given the next id free at its
    moment, after every id the journal holds there and every one settled before it in the set. Settled before the
    set's first write, so a clock that raises leaves nothing written."""
    settled: list[Stamp] = []
    for _ in range(count):
        at = _stamp(clock)
        settled.append(Stamp(at, _entry_id(at, _next_seq(store_dir, at, settled))))
    return settled


def _stamp(clock: Clock | None) -> datetime:
    """The moment an entry is stamped with: the clock given, read now, or, with none, this module's `now`."""
    return (clock or now)()


def _moment(at: datetime) -> str:
    """The moment as an id and its file name begin with it."""
    return at.strftime("%Y%m%dT%H%M%S%fZ")


def _entry_id(at: datetime, seq: int) -> str:
    """The one place an entry's id is made: its moment, then its seq among the entries stamped with that moment."""
    return f"{_moment(at)}-{seq}"


def _next_seq(store_dir: Path, at: datetime, settled: list[Stamp]) -> int:
    """One after every seq taken at this moment, by a file in the journal's day or an id settled earlier in the set,
    so an entry stamped later at the same moment is ordered after them. Reads names, never what a file holds."""
    taken = re.compile(re.escape(_moment(at)) + r"-(\d+)")
    names = [path.stem for path in _day(store_dir, at).glob("*.yaml")] + [stamp.id for stamp in settled]
    return 1 + max((int(found[1]) for found in map(taken.fullmatch, names) if found), default=0)


def digest(path: Path) -> str:
    """The fingerprint of a stored file: sha256 of its bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint(text: str) -> str:
    """The fingerprint of text about to be written: sha256 of the bytes it is written as."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write(store_dir: Path, *, signed: Signed, op: str, artifact: str, path: str, revision: int,
          schema_version: int, text: str | None, stamp: Stamp, batch: str = "") -> Path:
    """Write one entry under its settled stamp and return its file; its stem is the entry's id. A change made alone
    names itself as its batch. The fingerprint is of the text the change writes; a removal writes none, so its
    entry's fingerprint is empty."""
    entry = {
        "id": stamp.id,
        "at": stamp.at.isoformat(),
        "actor": {"role": signed.actor.role, "execution": signed.actor.execution},
        "op": op,
        "artifact": artifact,
        "path": path,
        "revision": revision,
        "schema_version": schema_version,
        "digest": fingerprint(text) if text is not None else "",
        "message": signed.message,
        "batch": batch or stamp.id,
    }
    return _save(store_dir, stamp.at, entry)


def snapshot(store_dir: Path, *, signed: Signed, read: list[dict], stamp: Stamp) -> Path:
    """Write the entry recording what a piece of work read, each artifact as { artifact, revision, digest }, under
    its settled stamp, and return its file. It names no artifact of its own and is a set of its own."""
    entry = {
        "id": stamp.id,
        "at": stamp.at.isoformat(),
        "actor": {"role": signed.actor.role, "execution": signed.actor.execution},
        "op": "snapshot",
        "read": read,
        "message": signed.message,
        "batch": stamp.id,
    }
    return _save(store_dir, stamp.at, entry)


def _day(store_dir: Path, at: datetime) -> Path:
    """The directory holding the entries stamped on the day of that moment."""
    return store_dir / "journal" / at.strftime("%Y") / at.strftime("%m") / at.strftime("%d")


def _save(store_dir: Path, at: datetime, entry: dict) -> Path:
    target = _day(store_dir, at) / f"{entry['id']}.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(canonical.dump(entry), encoding="utf-8")
    return target


def entries(store_dir: Path) -> list[dict] | Damaged:
    """Every entry in the journal, oldest first: by the time in its id, then by its seq, the order in which entries
    stamped with that moment were written. When an entry's
    file cannot be read, the fault naming the first such file in place of them all. Never raises for what a file
    holds."""
    found = []
    for path in sorted((store_dir / "journal").rglob("*.yaml")):
        try:
            found.append(canonical.entries(canonical.decoded(path.read_bytes())))
        except canonical.NotCanonical as error:
            return Damaged(refusals.unreadable("", path.relative_to(store_dir), str(error)))
    return sorted(found, key=_order)


def _order(entry: dict) -> tuple[str, int]:
    stamp, _, seq = entry["id"].rpartition("-")
    return stamp, int(seq)
