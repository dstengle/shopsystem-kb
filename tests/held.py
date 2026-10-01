"""The one test module that knows how a store is kept: a `kb/` directory below the directory it was started in,
holding a marker and one SQLite database beside it. The steps ask for what they mean here and never look at a path.
What the store holds comes back through the port's public reads, or as an opaque value that a step only compares
with another taken at another time."""
import hashlib
import sqlite3
from pathlib import Path

from kb import canonical, store
from kb.contract import kb_pb2
from kb.sqlite_reads import encoded
from kb.values import artifact_id

_PLACE = "kb"
_MARKER = "store.yaml"
_DATABASE = "store.sqlite3"


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
    """The store's history, oldest first, as the `Journal` rpc gives it."""
    return list(client.Journal(kb_pb2.JournalRequest()).entries)


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
