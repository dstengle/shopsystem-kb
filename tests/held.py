"""The one test module that knows how a store is kept. Today it is kept as files under a `kb/` directory below the
directory it was started in; the steps ask for what they mean here and never look at a path. What the store holds
comes back as an opaque value that a step only compares with another taken at another time."""
import hashlib
from pathlib import Path

from kb import canonical
from kb.contract import kb_pb2

_PLACE = "kb"
_MARKER = "store.yaml"


def _store(root):
    return Path(root) / _PLACE


def _file(root, name):
    return _store(root) / f"{name}.yaml"


def artifact(root, name):
    """The artifact the store holds under a name, as a mapping."""
    return canonical.load(text(root, name))


def text(root, name):
    """The canonical text the store holds under a name."""
    return _file(root, name).read_text()


def fingerprint(root, name):
    """The fingerprint of the text the store holds under a name."""
    return hashlib.sha256(text(root, name).encode()).hexdigest()


def holds_artifact(root, name):
    """Whether the store holds anything under a name."""
    return _file(root, name).exists()


def names(root):
    """The name of every artifact the store holds, sorted."""
    store = _store(root)
    found = [path.relative_to(store).with_suffix("").as_posix() for path in store.rglob("*.yaml")]
    return sorted(name for name in found if name != "store" and not name.startswith("journal/"))


def history(client):
    """The store's history, oldest first, as the `Journal` rpc gives it."""
    return list(client.Journal(kb_pb2.JournalRequest()).entries)


def holds(root):
    """Everything the store started in `root` holds, as one value to compare with another taken later."""
    return _everything_under(_store(root))


def holds_a_store(directory):
    """Whether a store has been started in `directory`."""
    return (_store(directory) / _MARKER).is_file()


def holds_anything_in_the_place(directory):
    """Whether `directory` holds anything, a store or not, in the place a store goes."""
    return _store(directory).exists()


def occupy_the_place(directory, how):
    """Put an empty folder, or a file, in the place a store goes in `directory`."""
    place = _store(directory)
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
        "stores": {store.relative_to(directory): _everything_under(store) for store in stores},
    }


def plant(root, name, content):
    """Write an artifact under a name behind the store's back, as a mapping, so it can break what the store allows."""
    _file(root, name).write_text(canonical.dump(content))


def _everything_under(directory):
    return {path: path.read_bytes() if path.is_file() else None for path in sorted(directory.rglob("*"))}


def _stores_under(directory):
    return sorted(marker.parent for marker in directory.rglob(_MARKER))


def _apart(directory, stores):
    return {
        path.relative_to(directory): path.read_bytes() if path.is_file() else None
        for path in sorted(directory.rglob("*"))
        if not any(store == path or store in path.parents for store in stores)
    }
