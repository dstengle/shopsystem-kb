"""The journal: one file per entry under <store>/journal/<YYYY>/<MM>/<DD>/, written inside the commit that made the change."""
import hashlib
from datetime import datetime, timezone
from pathlib import Path

from kb import canonical
from kb.values import Signed


def now() -> datetime:
    """The clock entries are stamped with. A module function so a later slice can set it from outside."""
    return datetime.now(timezone.utc)


def digest(path: Path) -> str:
    """The fingerprint of what was written: sha256 of the file's bytes after the write."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(store_dir: Path, *, signed: Signed, op: str, artifact: str, path: str, revision: int,
          schema_version: int, written: Path | None, seq: int = 1, batch: str = "") -> Path:
    """Write one entry and return its file; its stem is the entry's id. A change made alone names itself as its batch.
    A removal wrote nothing, so its entry's fingerprint is empty."""
    at = now()
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
        "digest": digest(written) if written is not None else "",
        "message": signed.message,
        "batch": batch or entry_id,
    }
    return _save(store_dir, at, entry)


def snapshot(store_dir: Path, *, signed: Signed, read: list[dict]) -> Path:
    """Write the entry recording what a piece of work read, each artifact as { artifact, revision, digest }, and
    return its file. It names no artifact of its own and is a set of its own."""
    at = now()
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
    target.write_text(canonical.dump(entry))
    return target


def entries(store_dir: Path) -> list[dict]:
    """Every entry in the journal, oldest first: by the time in its id, then by its place in its set."""
    found = [canonical.load(path.read_text()) for path in (store_dir / "journal").rglob("*.yaml")]
    return sorted(found, key=_order)


def _order(entry: dict) -> tuple[str, int]:
    stamp, _, seq = entry["id"].rpartition("-")
    return stamp, int(seq)
