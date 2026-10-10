"""The SQLite adapter's online copy of a store's database: into a new file, a backup, whole and at one moment, and out
of a backup into a new database. A backup carries kb's mark (`MARK`, as its `application_id`) and the form of the store
it holds (as its `user_version`) in its header, and is kept in rollback-journal mode, so it is one file and reading it
makes nothing beside it. A database copied out of one is in WAL mode, as sqlite_store.make leaves a database, and
keeps the header values it was copied with."""
import os
import sqlite3
from pathlib import Path

from kb.port import Unreadable

MARK = int.from_bytes(b"kbst", "big")  # kb's application_id, set in the header of every backup


def copied(db: sqlite3.Connection, path: Path, form: int, store: Path) -> None:
    """The database db is open on, the store's at `store`, copied whole into a new file at path, in one step, so in
    one read transaction and at one moment, which neither takes nor waits for the write lock; the copy checked whole,
    then its header set to the form given and, last, kb's mark, so a copy cut short there is no backup kb made.
    Raises FileExistsError, writing nothing, when anything is at path; a copy that fails removes the file it made, and
    nothing else. A failure writing the copy is an OSError naming what SQLite said; a database found damaged, in the
    copy or while copying, is Unreadable naming the store's database, as reading the store would be."""
    _created(path)
    done = False
    try:
        target = sqlite3.connect(path, isolation_level=None)
        try:
            db.backup(target)
            _whole(target, store)
            target.execute("PRAGMA journal_mode = DELETE")
            target.execute(f"PRAGMA user_version = {int(form)}")
            target.execute(f"PRAGMA application_id = {MARK}")
        finally:
            target.close()
        done = True
    except sqlite3.Error as error:
        if _damaged(error):
            raise Unreadable(f"{store}: {error}") from error
        raise OSError(str(error)) from error
    finally:
        if not done:
            path.unlink(missing_ok=True)


def copied_out(backup: Path, path: Path) -> None:
    """A new database at path, the backup copied into it whole, in WAL mode. Raises FileExistsError when anything is
    at path, and sqlite3.Error when the backup cannot be read; `header` is asked first."""
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
    """The mark and the form a file's header says it holds, read without writing anything. Raises Unreadable, naming
    the file, when it is not a database that can be read whole."""
    try:
        source = sqlite3.connect(f"{backup.resolve().as_uri()}?mode=ro", uri=True)
        try:
            _whole(source, backup)
            return (source.execute("PRAGMA application_id").fetchone()[0],
                    source.execute("PRAGMA user_version").fetchone()[0])
        finally:
            source.close()
    except sqlite3.Error as error:
        raise Unreadable(f"{backup}: {error}") from error


def _whole(db: sqlite3.Connection, named: Path) -> None:
    """Raises Unreadable, naming the database named, when SQLite's check of every page finds db damaged; SQLite may
    say so by raising, as sqlite3.Error, or by the faults it lists."""
    if db.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
        raise Unreadable(f"{named}: database disk image is malformed")


def _damaged(error: sqlite3.Error) -> bool:
    """Whether SQLite found a database damaged, or not a database at all: its primary result code, never its message."""
    return getattr(error, "sqlite_errorcode", 0) & 0xFF in (sqlite3.SQLITE_CORRUPT, sqlite3.SQLITE_NOTADB)


def _created(path: Path) -> None:
    """An empty file made at path, only where nothing is: FileExistsError otherwise."""
    os.close(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644))
