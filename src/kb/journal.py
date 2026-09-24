"""The journal: one file per entry under <store>/journal/<YYYY>/<MM>/<DD>/, written inside the commit that made the change."""
import hashlib
from datetime import datetime, timezone
from pathlib import Path

from kb import canonical


def now() -> datetime:
    """The clock entries are stamped with. A module function so a later slice can set it from outside."""
    return datetime.now(timezone.utc)


def digest(path: Path) -> str:
    """The fingerprint of what was written: sha256 of the file's bytes after the write."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(store_dir: Path, *, actor, op: str, artifact: str, path: str, revision: int,
          schema_version: int, written: Path, message: str, seq: int = 1, batch: str = "") -> Path:
    """Write one entry and return its file; its stem is the entry's id. A change made alone names itself as its batch."""
    at = now()
    entry_id = f"{at.strftime('%Y%m%dT%H%M%S%fZ')}-{seq}"
    entry = {
        "id": entry_id,
        "at": at.isoformat(),
        "actor": {"role": actor.role, "execution": actor.execution},
        "op": op,
        "artifact": artifact,
        "path": path,
        "revision": revision,
        "schema_version": schema_version,
        "digest": digest(written),
        "message": message,
        "batch": batch or entry_id,
    }
    target = store_dir / "journal" / at.strftime("%Y") / at.strftime("%m") / at.strftime("%d") / f"{entry_id}.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(canonical.dump(entry))
    return target
