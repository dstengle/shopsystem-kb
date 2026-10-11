"""The SQLite adapter's type versions: a table of their own beside `artifacts`, each row a version of a type under the
version's IRI, as a change hands it, with the type's IRI, the number, and the revision, the title and the content the
version was made with. A version lands beside the earlier ones of its type, which stay as they were made; which of
them the type stands at is the type's own row's to say, in `artifacts`. The versions kept under an IRI go when what
is held at that IRI is removed, so a type held there again starts with none."""
import sqlite3

SCHEMA = """
CREATE TABLE type_versions (
    id TEXT PRIMARY KEY, type TEXT NOT NULL, number INTEGER NOT NULL, revision INTEGER NOT NULL, title TEXT NOT NULL,
    content TEXT NOT NULL
);
CREATE INDEX type_versions_by_type ON type_versions (type);
"""


def made(db: sqlite3.Connection, type_id: str, version: str, number: int, revision: int, title: str,
          stored: str) -> None:
    """A version of a type, beside every version of it already held, at an IRI no version is held at: kb gives each
    version of a type a number of its own. The number is handed as its digits, which SQLite keeps as an integer when
    it can hold it."""
    db.execute(
        "INSERT INTO type_versions (id, type, number, revision, title, content) VALUES (?, ?, ?, ?, ?, ?)",
        (version, type_id, str(number), revision, title, stored),
    )


def removed(db: sqlite3.Connection, type_id: str) -> None:
    """Every version kept under the IRI of what a change removes: all of a type's, and nothing for anything else,
    which has none. The adapter is not told the removed artifact was a type, and need not be."""
    db.execute("DELETE FROM type_versions WHERE type = ?", (type_id,))


def numbers(db: sqlite3.Connection, type_id: str) -> list[int]:
    """The number of every version kept under a type's IRI, lowest first."""
    rows = db.execute("SELECT number FROM type_versions WHERE type = ? ORDER BY number", (type_id,)).fetchall()
    return [number for (number,) in rows]


def read(db: sqlite3.Connection, version: str) -> tuple[str, int, str] | None:
    """The content as the database keeps it, the revision and the title of the version at an IRI; None when no
    version is held there."""
    return db.execute("SELECT content, revision, title FROM type_versions WHERE id = ?", (version,)).fetchone()
