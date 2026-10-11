"""Making a store's database commits its whole schema once: every table, index, virtual table and trigger of it is
created in one transaction, so a start pays for one commit and not for one a statement. Seen through SQLite's own
trace of the statements the making runs, never through a clock; the database is one on disk, as a store's is."""
import sqlite3

from kb import sqlite_store


def traced(monkeypatch):
    """The statements every connection made from here on runs, in order, as SQLite traces them."""
    statements = []
    connect = sqlite3.connect

    def connecting(*args, **kwargs):
        db = connect(*args, **kwargs)
        db.set_trace_callback(statements.append)
        return db

    monkeypatch.setattr(sqlite3, "connect", connecting)
    return statements


def transactions(statements):
    """The statements grouped by the transaction each ran in: those from a BEGIN to its COMMIT in one, and any
    statement outside such a pair in one of its own, as SQLite commits it. A statement SQLite runs for another, which
    it traces as a comment, is that other's."""
    groups, held = [], None
    for statement in (text.strip() for text in statements if not text.lstrip().startswith("--")):
        word = statement.rstrip(";").split()[0].upper()
        if word == "BEGIN":
            held = []
        elif word == "COMMIT":
            groups.append(held)
            held = None
        elif held is None:
            groups.append([statement])
        else:
            held.append(statement)
    assert held is None, "a transaction was left open"
    return groups


def creating(group):
    return [statement for statement in group if statement.upper().startswith("CREATE")]


def test_making_a_database_creates_its_whole_schema_in_one_transaction(tmp_path, monkeypatch):
    sqlite_store.supported()  # asked once a process, of a database of its own that is none of the store's
    statements = traced(monkeypatch)
    path = tmp_path / "store.sqlite3"

    sqlite_store.make(path)

    schema = [group for group in transactions(statements) if creating(group)]
    assert len(schema) == 1, f"the schema was created in {len(schema)} transactions"
    monkeypatch.undo()
    db = sqlite3.connect(path)
    try:
        held = db.execute("SELECT count(*) FROM sqlite_master WHERE sql LIKE 'CREATE%'").fetchone()[0]
        # every statement of the schema made what it names; a virtual table makes tables of its own besides
        assert held >= len(creating(schema[0])) > 1
        assert db.execute("PRAGMA journal_mode").fetchone() == ("wal",)
    finally:
        db.close()
