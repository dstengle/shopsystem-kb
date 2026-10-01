"""The SQLite adapter's search rows: the rows an artifact is found by, each section at every depth by its title with
its body, then each field holding text by its name with its value, written into the FTS5 table and noted in `searched`
under the artifact, so they can be taken out again, since FTS5 finds rows only by their words."""
import sqlite3

from kb import search


def unsearched(db: sqlite3.Connection, name: str) -> None:
    """An artifact's search rows taken out."""
    db.execute("DELETE FROM search WHERE rowid IN (SELECT row FROM searched WHERE artifact = ?)", (name,))
    db.execute("DELETE FROM searched WHERE artifact = ?", (name,))


def searchable(db: sqlite3.Connection, name: str, kind: str, content: dict) -> None:
    """An artifact's search rows, each noted in `searched` under the artifact."""
    for ordinal, (what, label, words) in enumerate(_searched(content)):
        row = db.execute(
            "INSERT INTO search VALUES (?, ?, ?, ?, ?, ?)",
            (" ".join(search.tokens(words)), name, kind, what, label, ordinal),
        ).lastrowid
        db.execute("INSERT INTO searched VALUES (?, ?)", (row, name))


def _searched(content: dict):
    def sections(held):
        for section in held:
            yield "section", section["title"], section["body"]
            yield from sections(section.get("sections", []))
    yield from sections(content.get("sections", []))
    for key, value in content.items():
        if isinstance(key, str) and isinstance(value, str):
            yield "field", key, value
