"""The one test module that knows how a store is kept: a `kb/` directory below the directory it was started in,
holding a marker and one SQLite database beside it. The steps ask for what they mean here and never look at a path.
What the store holds comes back through the port's public reads, or as an opaque value that a step only compares
with another taken at another time."""
import contextlib
import hashlib
import io
import os
import sqlite3
import types
from pathlib import Path

from kb import canonical, sqlite_store, store
from kb.contract import kb_pb2
from kb.sqlite_reads import encoded
from kb.values import artifact_id

_PLACE = "kb"
_MARKER = "store.yaml"
_DATABASE = "store.sqlite3"
WAIT = 0.2  # seconds the store waits for the write lock while a test holds it


def _place(root):
    return Path(root) / _PLACE


def artifact(root, name):
    """The artifact the store holds under a name, as a mapping."""
    with store.opened(root) as opened:
        return opened.artifact(artifact_id(name))


def text(root, name):
    """The canonical text the store holds under a name."""
    return canonical.dump(artifact(root, name))


def fingerprint(root, name):
    """The fingerprint of the canonical text the store holds under a name, its UTF-8 bytes hashed, as the history's
    fingerprints are."""
    return hashlib.sha256(text(root, name).encode("utf-8")).hexdigest()


def holds_artifact(root, name):
    """Whether the store holds anything under a name."""
    with store.opened(root) as opened:
        return opened.holds(artifact_id(name))


def names(root):
    """The name of every artifact the store holds, sorted."""
    with store.opened(root) as opened:
        return sorted(str(each) for each in opened.ids())


def history(client):
    """The store's history, oldest first, as the `History` rpc gives it."""
    return list(client.History(kb_pb2.HistoryRequest()).result.entries)


def holds(root):
    """Everything the store started in `root` holds, as one value to compare with another taken later."""
    return _kept(_place(root))


def holds_a_store(directory):
    """Whether a store has been started in `directory`."""
    return (_place(directory) / _MARKER).is_file()


def holds_anything_in_the_place(directory):
    """Whether `directory` holds anything, a store or not, in the place a store goes."""
    return _place(directory).exists()


def holds_nothing(directory):
    """Whether `directory` holds nothing at all."""
    return not any(Path(directory).iterdir())


def occupy_the_place(directory, how):
    """Put an empty folder, or a file, in the place a store goes in `directory`."""
    place = _place(directory)
    if how == "folder":
        place.mkdir()
    else:
        place.write_bytes(b"notes the store must not write through\n")


def apart_from_the_store(directory):
    """What `directory` holds outside any store inside it: each path relative to it, with the bytes of a file."""
    return _apart(Path(directory), _stores_under(Path(directory)))


def everything_in(directory):
    """What `directory` holds apart from any store inside it, together with what each such store holds."""
    stores = _stores_under(Path(directory))
    return {
        "apart": _apart(Path(directory), stores),
        "stores": {place.relative_to(directory): _kept(place) for place in stores},
    }


def plant(root, name, content):
    """Put content under a name behind the store's back, as a mapping, so it can break what the store allows. The
    store refuses to land such content, so its row is written here; nothing else of the store is touched."""
    with _connected(_place(root)) as db, db:
        changed = db.execute("UPDATE artifacts SET content = ? WHERE id = ?", (encoded(content), name)).rowcount
    assert changed == 1, name


class _connected:
    """The store's database, open read-write for a block, and closed after it."""

    def __init__(self, place):
        self._uri = f"{(place / _DATABASE).resolve().as_uri()}?mode=rw"

    def __enter__(self):
        self._db = sqlite3.connect(self._uri, uri=True)
        return self._db

    def __exit__(self, *raised):
        self._db.close()


def _kept(place):
    """What a store holds: its marker's bytes, the names beside it, and every row of every table of its database,
    compared as rows, never as the database's bytes, which can differ with nothing changed."""
    with _connected(place) as db:
        tables = [name for (name,) in db.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name",
        )]
        rows = {table: sorted(db.execute(f'SELECT * FROM "{table}"').fetchall(), key=repr) for table in tables}
    beside = sorted(path.name for path in place.iterdir() if not path.name.endswith(("-wal", "-shm")))
    return {"marker": (place / _MARKER).read_bytes(), "beside": beside, "rows": rows}


def _stores_under(directory):
    return sorted(marker.parent for marker in directory.rglob(_MARKER))


def _apart(directory, stores):
    return {
        path.relative_to(directory): path.read_bytes() if path.is_file() else None
        for path in sorted(directory.rglob("*"))
        if not any(store == path or store in path.parents for store in stores)
    }


def damage_the_database(root):
    """Overwrite the store's database with other bytes behind its back, the marker beside it left as it was."""
    (_place(root) / _DATABASE).write_bytes(b"notes written over the store's database by hand\n" * 64)


def take_away_the_database(root):
    """Take the store's database away behind its back, the marker beside it left where it is."""
    (_place(root) / _DATABASE).unlink()


def make_read_only(root, what):
    """Make the store's place (`what` is "directory") or its database file (`what` is "file") read-only, and give back
    the call that restores it, so the directory can be cleaned up."""
    target = _place(root) if what == "directory" else _place(root) / _DATABASE
    mode = target.stat().st_mode
    target.chmod(0o555 if what == "directory" else 0o444)
    return lambda: target.chmod(mode)


def made_by_an_earlier_kb(root):
    """Make the store in `root` the way kb 0.3.0 kept one: its marker holding the contract, every artifact a canonical
    file at kb/<kind>/<slug>.yaml, the history in kb/journal/, a git repository in kb/.git/, and no database. A
    store this kb started there is taken apart into it; where none was started, it is a store of nothing."""
    place = _place(root)
    files = {name: text(root, name) for name in names(root)} if (place / _DATABASE).exists() else {}
    place.mkdir(exist_ok=True)
    for leftover in place.glob(f"{_DATABASE}*"):
        leftover.unlink()
    for name, canonical_text in files.items():
        (place / f"{name}.yaml").parent.mkdir(exist_ok=True)
        (place / f"{name}.yaml").write_text(canonical_text, encoding="utf-8")
    for directory, name, data in (("journal", "0001.yaml", "entry: first\n"), (".git", "HEAD", "ref: refs/heads/main\n")):
        (place / directory).mkdir(exist_ok=True)
        (place / directory / name).write_text(data, encoding="utf-8")
    (place / _MARKER).write_text(canonical.dump({"contract": "0.1"}), encoding="utf-8")


def made_by_a_later_kb(root):
    """Make the store in `root` look as a later kb would keep it: its marker naming a form of store this kb does not
    know, the database beside it left as this kb wrote it, so that opening it would succeed."""
    (_place(root) / _MARKER).write_text(canonical.dump({"store": store.STORE_FORM + 1}), encoding="utf-8")


def with_a_marker_that_cannot_be_read(root):
    """Overwrite the store's marker with bytes that are neither UTF-8 nor YAML, the database beside it left as it was."""
    (_place(root) / _MARKER).write_bytes(b"\xff\xfe\x00 not a marker \x9c\n")


def bytes_held(root):
    """Everything in the place of the store started in `root`, each path with its bytes: what a store whose database
    cannot be read holds, compared byte for byte, since no read of it can be made."""
    return _apart(_place(root), [])


class Holding:
    """Another change being written: the store's write lock taken by BEGIN IMMEDIATE on a connection of its own, and
    held until it is let go; what the store held as it was taken, to compare with what it holds later."""

    def __init__(self, root):
        self.held = holds(root)
        self._db = sqlite3.connect(_connected(_place(root))._uri, uri=True, isolation_level=None)
        try:
            self._db.execute("BEGIN IMMEDIATE")
        except sqlite3.Error:
            self._db.close()
            raise

    def let_go(self):
        """The lock let go, the change taken back, nothing of it written; once only, however often asked."""
        if self._db is None:
            return
        db, self._db = self._db, None
        try:
            db.execute("ROLLBACK")
        finally:
            db.close()


def another_change_holds(root, request, monkeypatch):
    """The store's write lock held by another change for the rest of the test, let go at its end whatever happens,
    and the store's wait for the lock, in this process and in the operator's, shortened to WAIT."""
    monkeypatch.setattr(sqlite_store, "BUSY", WAIT)
    holding = Holding(root)
    request.addfinalizer(holding.let_go)
    return holding




def in_process(main, argv, cwd, env):
    """A command line's `main` run in this process as a program would be: in a directory, with exactly the environment
    given, its output captured; what a finished program shows, its exit code and what it wrote to each stream. The
    directory and the environment are put back afterwards, whatever happens."""
    out, err = io.StringIO(), io.StringIO()
    was_in, was_env = os.getcwd(), dict(os.environ)
    try:
        os.chdir(cwd)
        os.environ.clear()
        os.environ.update(env)
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = main(argv)
            except SystemExit as exited:
                code = exited.code if isinstance(exited.code, int) else 2
    finally:
        os.chdir(was_in)
        os.environ.clear()
        os.environ.update(was_env)
    return types.SimpleNamespace(returncode=code or 0, stdout=out.getvalue(), stderr=err.getvalue())
