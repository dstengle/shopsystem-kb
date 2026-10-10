"""A backup: the one file a store is copied to whole, its history and its journal included, as it stood at one moment,
never over anything; made from the store held, through the port, and restored as a store, its database the backup's
copy and its marker written last, with nothing signed and nothing landed (operate-a-store)."""
from dataclasses import dataclass, field

from kb import refusals, sqlite_backup, store
from kb.port import Port, Unreadable
from kb.roots import Named, Root
from kb.values import Refused


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
    this kb's form. Raises Refused, writing nothing, when anything is at the place, even a dangling link, or the file
    cannot be made there; a copy that fails there leaves nothing."""
    if into.path.is_symlink() or into.path.exists():
        raise Refused([refusals.backup_would_overwrite(into.named)])
    try:
        held.copied(into.path, store.STORE_FORM)
    except FileExistsError:
        raise Refused([refusals.backup_would_overwrite(into.named)]) from None
    except OSError as error:
        raise Refused([refusals.backup_cannot_be_written(into.named, error.strerror or str(error))]) from None


def read(backup: Named) -> None:
    """Raises Refused, with the fault, when the file is not a backup this kb made: not one kb made, damaged, or one an
    earlier or a later kb made. Nothing is written."""
    try:
        mark, form = sqlite_backup.header(backup.path)
    except Unreadable:
        raise Refused([refusals.not_a_backup(backup.named)]) from None
    if mark != sqlite_backup.MARK:
        raise Refused([refusals.not_a_backup(backup.named)])
    if form < store.STORE_FORM:
        raise Refused([refusals.backup_by_earlier_kb(backup.named)])
    if form > store.STORE_FORM:
        raise Refused([refusals.backup_by_later_kb(backup.named)])


def restored(root: Root, backup: Named) -> None:
    """A store at root whose database is the backup's copy, marked last, as a store is started."""
    store.start(root, lambda opened: None, lambda database: sqlite_backup.copied_out(backup.path, database))
