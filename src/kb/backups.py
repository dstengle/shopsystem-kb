"""A backup: the one file a store is copied to whole, its history and its journal included, as it stood at one moment,
never over anything; made from the store held, through the port, and restored as a store, its database the backup's
copy and its marker written last, with nothing signed and nothing landed (operate-a-store)."""
from dataclasses import dataclass, field

from kb import sqlite_backup, store
from kb.port import Port
from kb.values import Named, Root


@dataclass(frozen=True)
class BackedUp:
    """What a backup answers: the faults that refused it, none when it was made."""
    faults: list = field(default_factory=list)


@dataclass(frozen=True)
class Restored:
    """What a restore answers: the faults that refused it, none when the store was restored."""
    faults: list = field(default_factory=list)


def made(held: Port, into: Named) -> None:
    """The store held copied whole, at one moment, into a new file at the place named, which says it holds a store of
    this kb's form."""
    held.copied(into.path, store.STORE_FORM)


def restored(root: Root, backup: Named) -> None:
    """A store at root whose database is the backup's copy, marked last, as a store is started."""
    store.start(root, lambda opened: None, lambda database: sqlite_backup.copied_out(backup.path, database))
