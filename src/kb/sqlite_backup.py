"""The SQLite adapter's online copy of a store's database: into a new file, a backup, whole and at one moment, and out
of a backup into a new database. A backup carries kb's mark (`MARK`, as its `application_id`) and the form of the store
it holds (as its `user_version`) in its header, and is kept in rollback-journal mode, so it is one file and reading it
makes nothing beside it. A database copied out of one is in WAL mode, as sqlite_store.make leaves a database, and
keeps the header values it was copied with."""
import os
import sqlite3
from pathlib import Path

MARK = int.from_bytes(b"kbst", "big")  # kb's application_id, set in the header of every backup


def copied(db: sqlite3.Connection, path: Path, form: int) -> None:
    """The database db is open on copied whole into a new file at path, in one step, so in one read transaction and
    at one moment, which neither takes nor waits for the write lock; its header set to kb's mark and the form given.
    Raises FileExistsError, writing nothing, when anything is at path; a copy that fails removes the file it made, and
    nothing else."""
    _created(path)
    done = False
    try:
        target = sqlite3.connect(path, isolation_level=None)
        try:
            db.backup(target)
            target.execute("PRAGMA journal_mode = DELETE")
            target.execute(f"PRAGMA application_id = {MARK}")
            target.execute(f"PRAGMA user_version = {int(form)}")
        finally:
            target.close()
        done = True
    finally:
        if not done:
            path.unlink(missing_ok=True)


def copied_out(backup: Path, path: Path) -> None:
    """A new database at path, the backup copied into it whole, in WAL mode. Raises FileExistsError when anything is
    at path, and sqlite3.Error when the backup cannot be read."""
    _created(path)
    source = sqlite3.connect(f"{backup.resolve().as_uri()}?mode=ro", uri=True)
    try:
        target = sqlite3.connect(path, isolation_level=None)
        try:
            source.backup(target)
            target.execute("PRAGMA journal_mode = WAL")
        finally:
            target.close()
    finally:
        source.close()


def header(backup: Path) -> tuple[int, int]:
    """The mark and the form a file's header says it holds, read without writing anything. Raises sqlite3.Error when
    the file is not a database that can be read."""
    source = sqlite3.connect(f"{backup.resolve().as_uri()}?mode=ro", uri=True)
    try:
        return (source.execute("PRAGMA application_id").fetchone()[0],
                source.execute("PRAGMA user_version").fetchone()[0])
    finally:
        source.close()


def _created(path: Path) -> None:
    """An empty file made at path, only where nothing is: FileExistsError otherwise."""
    os.close(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644))
