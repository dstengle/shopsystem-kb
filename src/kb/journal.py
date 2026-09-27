"""The journal: one file per entry under <store>/journal/<YYYY>/<MM>/<DD>/, written inside the commit that made the change."""
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from kb import canonical, refusals
from kb.signatures import Signed
from kb.store import Damaged


Clock = Callable[[], datetime]


def now() -> datetime:
    """The machine's clock, which stamps an entry when no clock is given. Looked up as each entry is stamped, so a
    replacement made from outside still takes effect, until shop-knowledge's slice 50.23 moves to the given clock."""
    return datetime.now(timezone.utc)


def _stamp(clock: Clock | None) -> datetime:
    """The moment an entry is stamped with: the clock given, read now, or, with none, this module's `now`."""
    return (clock or now)()


def digest(path: Path) -> str:
    """The fingerprint of a stored file: sha256 of its bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint(text: str) -> str:
    """The fingerprint of text about to be written: sha256 of the bytes it is written as."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write(store_dir: Path, *, signed: Signed, op: str, artifact: str, path: str, revision: int,
          schema_version: int, text: str | None, seq: int = 1, batch: str = "", clock: Clock | None = None) -> Path:
    """Write one entry and return its file; its stem is the entry's id. A change made alone names itself as its batch.
    The fingerprint is of the text the change writes; a removal writes none, so its entry's fingerprint is empty.
    Stamped with the moment the clock gives, or the machine's with none."""
    at = _stamp(clock)
    entry_id = f"{at.strftime('%Y%m%dT%H%M%S%fZ')}-{seq}"
    entry = {
        "id": entry_id,
        "at": at.isoformat(),
        "actor": {"role": signed.actor.role, "execution": signed.actor.execution},
        "op": op,
        "artifact": artifact,
        "path": path,
        "revision": revision,
        "schema_version": schema_version,
        "digest": fingerprint(text) if text is not None else "",
        "message": signed.message,
        "batch": batch or entry_id,
    }
    return _save(store_dir, at, entry)


def snapshot(store_dir: Path, *, signed: Signed, read: list[dict], clock: Clock | None = None) -> Path:
    """Write the entry recording what a piece of work read, each artifact as { artifact, revision, digest }, and
    return its file. It names no artifact of its own and is a set of its own. Stamped as `write` stamps."""
    at = _stamp(clock)
    entry_id = f"{at.strftime('%Y%m%dT%H%M%S%fZ')}-1"
    entry = {
        "id": entry_id,
        "at": at.isoformat(),
        "actor": {"role": signed.actor.role, "execution": signed.actor.execution},
        "op": "snapshot",
        "read": read,
        "message": signed.message,
        "batch": entry_id,
    }
    return _save(store_dir, at, entry)


def _save(store_dir: Path, at: datetime, entry: dict) -> Path:
    target = store_dir / "journal" / at.strftime("%Y") / at.strftime("%m") / at.strftime("%d") / f"{entry['id']}.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(canonical.dump(entry), encoding="utf-8")
    return target


def entries(store_dir: Path) -> list[dict] | Damaged:
    """Every entry in the journal, oldest first: by the time in its id, then by its place in its set. When an entry's
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
