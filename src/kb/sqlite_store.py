"""The SQLite adapter: one database, made once in WAL mode and opened read-write, never created, for each call; and
the landing of a set in one BEGIN IMMEDIATE transaction, which takes the write lock before reading anything, so a
second writer waits, then finds the first's result. A block may hold that lock across reads and landings
(`exclusive`), each set landed in it under a savepoint of its own.

Inside the transaction the set is checked (kb.sqlite_checks); any refusal rolls the whole set back. Opening checks the SQLite this process runs has FTS5 and is at least FLOOR.
"""
import contextlib
import functools
import sqlite3
from pathlib import Path
from typing import Iterator

from kb import sqlite_search
from kb.port import Busy, Change, Entry, Relink, Unreadable
from kb.sqlite_checks import Checks
from kb.values import Kind
from kb.sqlite_reads import encoded, moment

FLOOR = (3, 9, 0)  # FTS5 and its ascii tokenizer; the suite has run on the SQLite Python 3.11 ships
BUSY = 30.0  # seconds a writer waits for the write lock

SCHEMA = """
CREATE TABLE artifacts (id TEXT PRIMARY KEY, kind TEXT NOT NULL, revision INTEGER NOT NULL, content TEXT NOT NULL);
CREATE INDEX artifacts_by_kind ON artifacts (kind);
CREATE TABLE parts (artifact TEXT NOT NULL, place TEXT NOT NULL, PRIMARY KEY (artifact, place));
CREATE TABLE links (
    source TEXT NOT NULL, ordinal INTEGER NOT NULL, field TEXT NOT NULL, place TEXT NOT NULL, target TEXT NOT NULL,
    part TEXT NOT NULL, implicit INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (source, ordinal)
);
CREATE INDEX links_in ON links (target, part);
CREATE TABLE sets (seq INTEGER PRIMARY KEY AUTOINCREMENT, batch TEXT UNIQUE);
CREATE TABLE versions (
    artifact TEXT NOT NULL, landed INTEGER NOT NULL, step INTEGER NOT NULL, revision INTEGER NOT NULL, content TEXT,
    PRIMARY KEY (artifact, landed, step)
);
CREATE TABLE entries (
    id TEXT PRIMARY KEY, moment INTEGER NOT NULL, seq INTEGER NOT NULL, artifact TEXT NOT NULL, role TEXT NOT NULL,
    execution TEXT NOT NULL, batch TEXT NOT NULL, record TEXT NOT NULL
);
CREATE INDEX entries_in_order ON entries (moment);
CREATE VIRTUAL TABLE search USING fts5 (
    words, artifact UNINDEXED, kind UNINDEXED, what UNINDEXED, name UNINDEXED, ordinal UNINDEXED,
    tokenize = "ascii tokenchars '_'"
);
CREATE TABLE searched (row INTEGER PRIMARY KEY, artifact TEXT NOT NULL);
CREATE INDEX searched_by_artifact ON searched (artifact);
"""


def make(path: Path) -> None:
    """A new database at path, its tables made and WAL mode set, once. Raises FileExistsError when anything is
    there, sqlite3.Error when it cannot be made, and Unreadable as `supported` does."""
    supported()
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"a database is made only where nothing is: {path}")
    db = sqlite3.connect(_uri(path, "rwc"), uri=True)
    try:
        db.executescript(SCHEMA)
        db.execute("PRAGMA journal_mode = WAL")
    finally:
        db.close()


@contextlib.contextmanager
def opened(path: Path) -> Iterator["SqliteStore"]:
    """The database at path, open read-write until the block ends. Raises Unreadable, naming it, when it cannot be
    opened, which creates nothing, or when any statement finds it damaged, which shows only once one is made; Busy
    when a writer waited BUSY seconds for the write lock and another connection still held it."""
    supported()
    try:
        db = sqlite3.connect(_uri(path, "rw"), uri=True, timeout=BUSY, isolation_level=None)
    except sqlite3.OperationalError as error:
        raise Unreadable(f"{path}: {error}") from None
    try:
        yield SqliteStore(db)
    except sqlite3.DatabaseError as error:
        raise (Busy if _busy(error) else Unreadable)(f"{path}: {error}") from error
    finally:
        db.close()


def _busy(error: sqlite3.DatabaseError) -> bool:
    """Whether SQLite gave up waiting for a lock another connection held: its primary result code, never its message."""
    return getattr(error, "sqlite_errorcode", 0) & 0xFF == sqlite3.SQLITE_BUSY


def _uri(path: Path, mode: str) -> str:
    return f"{Path(path).resolve().as_uri()}?mode={mode}"


def supported() -> None:
    """Raises Unreadable when the SQLite this process runs is older than FLOOR or has no FTS5."""
    lacking = _lacking()
    if lacking:
        raise Unreadable(lacking)


@functools.cache
def _lacking() -> str:
    """What the SQLite this process runs lacks for a store, empty when nothing; found once a process."""
    if sqlite3.sqlite_version_info < FLOOR:
        return f"a store needs SQLite {'.'.join(map(str, FLOOR))} or later; this is {sqlite3.sqlite_version}"
    probe = sqlite3.connect(":memory:")
    try:
        probe.execute("CREATE VIRTUAL TABLE probe USING fts5 (words)")
    except sqlite3.OperationalError:
        return f"a store needs SQLite with full-text search (FTS5); {sqlite3.sqlite_version} has none"
    finally:
        probe.close()
    return ""


class SqliteStore(Checks):
    """The port over one open connection."""

    def __init__(self, db: sqlite3.Connection):
        super().__init__(db)
        self._locked = False

    @contextlib.contextmanager
    def exclusive(self):
        """The write lock taken by BEGIN IMMEDIATE for the block, committed when it ends, rolled back when it raises; a
        block inside one that already holds it runs within the outer block."""
        if self._locked:
            yield
            return
        self._db.execute("BEGIN IMMEDIATE")
        self._locked = True
        committed = False
        try:
            yield
            self._db.execute("COMMIT")
            committed = True
        finally:
            if not committed and self._db.in_transaction:
                self._db.execute("ROLLBACK")
            self._locked = False

    def land(self, changes: list[Change], entries: list[Entry], relinks: list[Relink] = (),
             kinds: tuple[Kind, ...] = ()) -> None:
        with contextlib.nullcontext() if self._locked else self.exclusive(), self._saved():
            self._unheld(entries)
            landed = self._db.execute(
                "INSERT INTO sets (batch) VALUES (?)", (entries[0].batch if entries else None,),
            ).lastrowid
            self._unmoved(changes, relinks)
            self._restated(kinds, changes, relinks)
            before = {}
            for step, change in enumerate(changes):
                held = self._compared(change.artifact, change.read)
                before.setdefault(change.artifact, (held, set(self._parts(change.artifact))))
                self._written(change, landed, step)
            for relink in relinks:
                self._compared(relink.artifact, relink.read)
                self._linked(relink.artifact, relink.links)
            self._integral(changes, before)
            self._recorded(entries)

    @contextlib.contextmanager
    def _saved(self):
        """A savepoint around one set: a refusal takes back the set alone, and a lock held for a block stays held."""
        self._db.execute("SAVEPOINT landing")
        released = False
        try:
            yield
            self._db.execute("RELEASE landing")
            released = True
        finally:
            if not released:
                self._db.execute("ROLLBACK TO landing")
                self._db.execute("RELEASE landing")

    def _written(self, change: Change, landed: int, step: int) -> None:
        name = str(change.artifact)
        sqlite_search.unsearched(self._db, name)
        for table, column in (("parts", "artifact"), ("artifacts", "id")):
            self._db.execute(f"DELETE FROM {table} WHERE {column} = ?", (name,))
        self._linked(change.artifact, () if change.content is None else change.links)
        stored = None if change.content is None else encoded(change.content)
        self._db.execute(
            "INSERT INTO versions (artifact, landed, step, revision, content) VALUES (?, ?, ?, ?, ?)",
            (name, landed, step, change.revision, stored),
        )
        if stored is None:
            return
        kind = change.artifact.kind.name
        self._db.execute(
            "INSERT INTO artifacts (id, kind, revision, content) VALUES (?, ?, ?, ?)", (name, kind, change.revision, stored),
        )
        self._db.executemany("INSERT INTO parts VALUES (?, ?)", [(name, place) for place in set(change.parts)])
        sqlite_search.searchable(self._db, name, kind, change.searched)

    def _linked(self, artifact, links) -> None:
        """The links an artifact holds, in place of those it held."""
        self._db.execute("DELETE FROM links WHERE source = ?", (str(artifact),))
        self._db.executemany("INSERT INTO links VALUES (?, ?, ?, ?, ?, ?, ?)", [
            (str(artifact), ordinal, link.field, link.place, str(link.target), link.part, int(link.implicit))
            for ordinal, link in enumerate(links)
        ])

    def _recorded(self, entries: list[Entry]) -> None:
        self._db.executemany("INSERT INTO entries VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [
            (entry.id, moment(entry.at), entry.seq, entry.artifact, entry.role, entry.execution, entry.batch,
             encoded(entry.record))
            for entry in entries
        ])

