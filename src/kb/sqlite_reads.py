"""The SQLite adapter's reads, over one open connection, and content as the database keeps it.

Every read is one statement whose rows are all fetched, so no read leaves a transaction open behind it. Names come
back in `names.order`, links in the order they were handed in, and fields are compared in Python on the text YAML 1.2
writes a value as, never through SQLite's JSON functions, which turn a large integer into a float.
"""
import json
import sqlite3
from datetime import datetime, timedelta, timezone

from kb import names
from kb.content import text
from kb.port import Candidate, Linking, Reached
from kb.values import ArtifactId, Kind, artifact_id

PAIRS = "~pairs"
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def encoded(content: dict) -> str:
    """Content as JSON text that reads back as every value kb accepts: a mapping with a key that is not text, or
    whose one key is PAIRS, is kept as its pairs under PAIRS."""
    return json.dumps(_encodable(content), ensure_ascii=False)


def decoded(stored: str) -> dict:
    return json.loads(stored, object_hook=_mapping)


def _encodable(value):
    if isinstance(value, dict):
        if all(isinstance(key, str) for key in value) and list(value) != [PAIRS]:
            return {key: _encodable(item) for key, item in value.items()}
        return {PAIRS: [[key, _encodable(item)] for key, item in value.items()]}
    if isinstance(value, list):
        return [_encodable(item) for item in value]
    return value


def _mapping(read: dict) -> dict:
    if list(read) == [PAIRS]:
        return {key: item for key, item in read[PAIRS]}
    return read


def moment(at: datetime) -> int:
    """A moment as the database orders and compares it: microseconds since the epoch."""
    return (at - EPOCH) // timedelta(microseconds=1)


def ordered(written: list[str]) -> list[ArtifactId]:
    return [artifact_id(name) for name in sorted(written, key=names.order)]


class Reads:
    """What the port reads, answered from one connection."""

    def __init__(self, db: sqlite3.Connection):
        self._db = db

    def _rows(self, sql: str, *args) -> list:
        return self._db.execute(sql, args).fetchall()

    def holds(self, artifact_id: ArtifactId) -> bool:
        return bool(self._rows("SELECT 1 FROM artifacts WHERE id = ?", str(artifact_id)))

    def artifact(self, artifact_id: ArtifactId, as_of: str = "") -> dict:
        if as_of:
            rows = self._rows(
                "SELECT content FROM versions WHERE artifact = ? AND landed <= (SELECT seq FROM sets WHERE batch = ?) "
                "ORDER BY landed DESC, step DESC LIMIT 1", str(artifact_id), as_of,
            )
        else:
            rows = self._rows("SELECT content FROM artifacts WHERE id = ?", str(artifact_id))
        if not rows or rows[0][0] is None:
            raise KeyError(str(artifact_id))
        return decoded(rows[0][0])

    def ids(self, kind: Kind | None = None, fields: dict[str, str] | None = None) -> list[ArtifactId]:
        narrowed = "" if kind is None else " WHERE kind = ?"
        rows = self._rows(f"SELECT id, content FROM artifacts{narrowed}", *([] if kind is None else [kind.name]))
        return ordered([name for name, stored in rows if not fields or _holds(decoded(stored), fields)])

    def links_out(self, artifact_id: ArtifactId, place: str = "") -> list[Linking]:
        rows = self._rows(
            "SELECT source, field, place, target, part FROM links WHERE source = ? ORDER BY ordinal", str(artifact_id),
        )
        found = [_linking(*row) for row in rows]
        return [each for each in found if not place or each.place == place or each.place.startswith(f"{place}/")]

    def links_in(self, artifact_id: ArtifactId, field: str = "", kind: Kind | None = None) -> list[Linking]:
        rows = self._rows(
            "SELECT source, field, place, target, part, ordinal FROM links WHERE target = ?", str(artifact_id),
        )
        rows.sort(key=lambda row: (names.order(row[0]), row[5]))
        found = [_linking(*row[:5]) for row in rows]
        return [
            each for each in found
            if (not field or each.field == field) and (kind is None or each.source.kind == kind)
        ]

    def inbound(self, artifact_id: ArtifactId) -> dict[tuple[str, str], int]:
        counts, counted = {}, set()
        for each in self.links_in(artifact_id):
            key = (each.source.kind.name, each.field)
            if (key, each.source) not in counted:
                counted.add((key, each.source))
                counts[key] = counts.get(key, 0) + 1
        return counts

    def traverse(self, artifact_id: ArtifactId, inward: bool, depth: int, field: str = "",
                 kind: Kind | None = None) -> list[Reached]:
        reached, seen, frontier = [], {artifact_id}, [(artifact_id, ())]
        for _ in range(depth):
            following = []
            for at, route in frontier:
                for each in self.links_in(at) if inward else self.links_out(at):
                    other = each.source if inward else each.target
                    if other in seen or (field and each.field != field) or (kind is not None and other.kind != kind):
                        continue
                    seen.add(other)
                    taken = (*route, (each.field, other))
                    reached.append(Reached(other, taken))
                    following.append((other, taken))
            frontier = following
        return reached

    def search(self, words: list[str], kind: Kind | None = None, sections: bool = True,
               fields: bool = True) -> list[Candidate]:
        if not words:
            return []
        query = " OR ".join('"' + word.replace('"', '""') + '"' for word in words)
        rows = self._rows("SELECT artifact, kind, what, name, ordinal FROM search WHERE search MATCH ?", query)
        rows.sort(key=lambda row: (names.order(row[0]), row[4]))
        wanted = {what for what, asked in (("section", sections), ("field", fields)) if asked}
        return [
            Candidate(artifact_id(name), label if what == "section" else "", label if what == "field" else "")
            for name, of_kind, what, label, _ in rows
            if what in wanted and (kind is None or of_kind == kind.name)
        ]

    def history(self, artifact: ArtifactId | None = None, role: str = "", execution: str = "",
                since: datetime | None = None, batch: str = "") -> list[dict]:
        asked = {
            "artifact = ?": None if artifact is None else str(artifact), "role = ?": role or None,
            "execution = ?": execution or None, "moment >= ?": None if since is None else moment(since),
            "batch = ?": batch or None,
        }
        clauses = [clause for clause, value in asked.items() if value is not None]
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self._rows(
            f"SELECT record FROM entries{where} ORDER BY moment, seq", *(value for value in asked.values() if value is not None),
        )
        return [decoded(record) for (record,) in rows]

    def entry_ids(self, at: datetime) -> list[str]:
        return [entry_id for (entry_id,) in self._rows("SELECT id FROM entries WHERE moment = ?", moment(at))]


def _linking(source: str, field: str, place: str, target: str, part: str) -> Linking:
    return Linking(artifact_id(source), field, place, artifact_id(target), part)


def _holds(artifact: dict, fields: dict[str, str]) -> bool:
    """Whether each field named holds the value given, compared as the text the value is written as."""
    return all(field in artifact and text(artifact[field]) == value for field, value in fields.items())
