"""The SQLite adapter's type versions: a table of their own beside `artifacts`, each row a version of a type under the
version's IRI, as a change hands it, with the type's IRI, the number, and the revision, the title and the content the
version was made with. Until the store numbers a type's versions a type has the one row, the version it stands at,
written in place of the row it had."""
import sqlite3

SCHEMA = """
CREATE TABLE type_versions (
    id TEXT PRIMARY KEY, type TEXT NOT NULL, number INTEGER NOT NULL, revision INTEGER NOT NULL, title TEXT NOT NULL,
    content TEXT NOT NULL
);
CREATE INDEX type_versions_by_type ON type_versions (type);
"""


def stood(db: sqlite3.Connection, type_id: str, version: str, number: int, revision: int, title: str,
          stored: str) -> None:
    """The version a type stands at, in place of the one it stood at. The number is handed as its digits, which
    SQLite keeps as an integer when it can hold it: one of any size is still a client's to give."""
    db.execute("DELETE FROM type_versions WHERE type = ?", (type_id,))
    db.execute(
        "INSERT INTO type_versions (id, type, number, revision, title, content) VALUES (?, ?, ?, ?, ?, ?)",
        (version, type_id, str(number), revision, title, stored),
    )


def read(db: sqlite3.Connection, version: str) -> tuple[str, int, str] | None:
    """The content as the database keeps it, the revision and the title of the version at an IRI; None when no
    version is held there."""
    return db.execute("SELECT content, revision, title FROM type_versions WHERE id = ?", (version,)).fetchone()
