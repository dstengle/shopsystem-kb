"""The SQLite adapter's search rows: the rows kb gives a change to find its artifact by, each written into `searched`
under the artifact at a row id the adapter gives it, after every one held, and then into the FTS5 table under that
same row id, given outright, so they can be taken out again, since FTS5 finds rows only by their words."""
import sqlite3


def unsearched(db: sqlite3.Connection, name: str) -> None:
    """An artifact's search rows taken out."""
    db.execute("DELETE FROM search WHERE rowid IN (SELECT row FROM searched WHERE artifact = ?)", (name,))
    db.execute("DELETE FROM searched WHERE artifact = ?", (name,))


def searchable(db: sqlite3.Connection, name: str, kind: str, rows: tuple[tuple[str, str, str], ...]) -> None:
    """An artifact's search rows, each noted in `searched` under a row id after every one held, then kept in `search`
    under that row id."""
    [last] = db.execute("SELECT COALESCE(MAX(row), 0) FROM searched").fetchone()
    numbered = [(last + ordinal + 1, ordinal, row) for ordinal, row in enumerate(rows)]
    db.executemany("INSERT INTO searched (row, artifact) VALUES (?, ?)", [(row, name) for row, _, _ in numbered])
    db.executemany(
        "INSERT INTO search (rowid, words, artifact, kind, what, name, ordinal) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(row, words, name, kind, what, label, ordinal) for row, ordinal, (what, label, words) in numbered],
    )
