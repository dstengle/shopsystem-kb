"""The SQLite adapter: one database, made once in WAL mode and opened read-write, never created, for each call; and
the landing of a set in one BEGIN IMMEDIATE transaction, which takes the write lock before reading anything, so a
second writer waits, then finds the first's result.

Inside the transaction each change's revision, and that of every type it was read through, is compared with the
one it was read at, every link the set hands must land, and nothing outside the set may link into what the set
removes or drops. Any refusal rolls the whole set back. Opening checks the SQLite this process runs has FTS5 and is at least FLOOR.
"""
import contextlib
import functools
import sqlite3
from pathlib import Path
from typing import Iterator

from kb import search
from kb.port import Change, Conflict, Entry, Linked, Linking, Relink, Unlanded, Unreadable
from kb.sqlite_reads import Reads, encoded, moment

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
CREATE INDEX entries_in_order ON entries (moment, seq);
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
    opened, which creates nothing, or when any statement finds it damaged, which shows only once one is made."""
    supported()
    try:
        db = sqlite3.connect(_uri(path, "rw"), uri=True, timeout=BUSY, isolation_level=None)
    except sqlite3.OperationalError as error:
        raise Unreadable(f"{path}: {error}") from None
    try:
        yield SqliteStore(db)
    except sqlite3.DatabaseError as error:
        raise Unreadable(f"{path}: {error}") from error
    finally:
        db.close()


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


class SqliteStore(Reads):
    """The port over one open connection."""

    def land(self, changes: list[Change], entries: list[Entry], relinks: list[Relink] = ()) -> None:
        with self._db:
            self._db.execute("BEGIN IMMEDIATE")
            self._unheld(entries)
            landed = self._db.execute(
                "INSERT INTO sets (batch) VALUES (?)", (entries[0].batch if entries else None,),
            ).lastrowid
            self._unmoved(changes)
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

    def _compared(self, artifact, read: int) -> int:
        """The revision the artifact stands at; Conflict when it was read at another."""
        rows = self._rows("SELECT revision FROM artifacts WHERE id = ?", str(artifact))
        held = rows[0][0] if rows else 0
        if held != read:
            raise Conflict(f"{artifact} was read at revision {read} and stands at revision {held}")
        return held

    def _unmoved(self, changes: list[Change]) -> None:
        """Conflict when a type a change was read through stands at another revision than the one it was read at."""
        for type_id, read in {each for change in changes for each in change.through}:
            self._compared(type_id, read)

    def _parts(self, artifact) -> list[str]:
        return [place for (place,) in self._rows("SELECT place FROM parts WHERE artifact = ?", str(artifact))]

    def _written(self, change: Change, landed: int, step: int) -> None:
        name = str(change.artifact)
        self._unsearched(name)
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
        self._searchable(name, kind, change.content)

    def _unsearched(self, name: str) -> None:
        """An artifact's search rows taken out, found through `searched`, since search finds rows only by words."""
        self._db.execute("DELETE FROM search WHERE rowid IN (SELECT row FROM searched WHERE artifact = ?)", (name,))
        self._db.execute("DELETE FROM searched WHERE artifact = ?", (name,))

    def _searchable(self, name: str, kind: str, content: dict) -> None:
        """An artifact's search rows, each noted in `searched` under the artifact."""
        for ordinal, (what, label, words) in enumerate(_searched(content)):
            row = self._db.execute(
                "INSERT INTO search VALUES (?, ?, ?, ?, ?, ?)",
                (" ".join(search.tokens(words)), name, kind, what, label, ordinal),
            ).lastrowid
            self._db.execute("INSERT INTO searched VALUES (?, ?)", (row, name))

    def _linked(self, artifact, links) -> None:
        """The links an artifact holds, in place of those it held."""
        self._db.execute("DELETE FROM links WHERE source = ?", (str(artifact),))
        self._db.executemany("INSERT INTO links VALUES (?, ?, ?, ?, ?, ?, ?)", [
            (str(artifact), ordinal, link.field, link.place, str(link.target), link.part, int(link.implicit))
            for ordinal, link in enumerate(links)
        ])

    def _integral(self, changes: list[Change], before: dict) -> None:
        """Unlanded for every link the set hands that lands on nothing held or on a kind it may not land on; then
        Linked for every link from outside the set into an artifact the set removes or a part it drops."""
        last = {change.artifact: change for change in changes}
        unlanded = [
            Linking(artifact, link.field, link.place, link.target, link.part)
            for artifact, change in last.items() if change.content is not None
            for link in change.links if not self._lands(link)
        ]
        if unlanded:
            raise Unlanded(unlanded)
        linked = []
        for artifact, (held, parts) in before.items():
            gone = parts - set(self._parts(artifact)) if self.holds(artifact) else None
            if held:
                linked += [
                    each for each in self._links_into(artifact)
                    if each.source not in last and (gone is None or each.part in gone)
                ]
        if linked:
            raise Linked(linked)

    def _lands(self, link) -> bool:
        if link.target.kind.name not in link.kinds or not self.holds(link.target):
            return False
        return not link.part or link.part in self._parts(link.target)

    def _unheld(self, entries: list[Entry]) -> None:
        """Conflict when an entry's id is already held, or given twice."""
        ids = [entry.id for entry in entries]
        held = self._rows(f"SELECT id FROM entries WHERE id IN ({', '.join('?' * len(ids))})", *ids)
        if held or len(set(ids)) != len(ids):
            raise Conflict(f"an entry's id is held once; {[each for (each,) in held] or ids} already is")

    def _recorded(self, entries: list[Entry]) -> None:
        self._db.executemany("INSERT INTO entries VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [
            (entry.id, moment(entry.at), entry.seq, entry.artifact, entry.role, entry.execution, entry.batch,
             encoded(entry.record))
            for entry in entries
        ])


def _searched(content: dict):
    """The rows search keeps of an artifact: each section at every depth by its title, with its body; then each
    field holding text by its name, with its value."""
    def sections(held):
        for section in held:
            yield "section", section["title"], section["body"]
            yield from sections(section.get("sections", []))
    yield from sections(content.get("sections", []))
    for key, value in content.items():
        if isinstance(key, str) and isinstance(value, str):
            yield "field", key, value
