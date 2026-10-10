"""The operator's commands that are not rpcs, export, the import check, the import, the backup and the restore, over
one store, each run inside the servicer's one boundary: the store opened first (but for a restore, which makes it),
the command's values made, one call into the domain, and any refusal or escaping exception its faults."""
from pathlib import Path
from typing import NamedTuple

from kb import backups, export, importing, signatures, values
from kb.contract import kb_pb2
from kb.servicer import boundary


class Importing(NamedTuple):
    """An import as the operator asks for it: the directory as named, the role it lands under, and whether the
    files with errors, and those leading to them, are skipped; and, when a start gives one, the place it made inside
    the directory, which is not offered."""
    directory: str
    role: str
    skip_errors: bool
    passed_over: Path | None = None


class Operator:
    def __init__(self, root):
        """Over the store at root."""
        self._root = root

    @boundary(export.Exported)
    def export(self, directory: str, held):
        """The store written out as files into the directory named."""
        export.written(held, values.directory(directory))
        return export.Exported()

    @boundary(importing.Checked, at_one_moment=True)
    def import_check(self, directory: str, held):
        """A directory read as a set for import into the store, its errors and what would be skipped; nothing written."""
        return importing.checked(held, values.directory(directory))

    @boundary(importing.Checked)
    def import_(self, request: Importing, held):
        """A directory checked, then landed in the store as one set signed by the role, with a message naming it."""
        signed = signatures.signed(kb_pb2.Signature(role=request.role, message=f"import {request.directory}"))
        return importing.imported(held, values.directory(request.directory), signed, request.skip_errors,
                                request.passed_over)

    @boundary(backups.BackedUp)
    def backup(self, file: str, held):
        """The store copied whole, as it stood at one moment, into a new file at the place named."""
        backups.made(held, values.file(file))
        return backups.BackedUp()

    @boundary(backups.Restored, opens=False)
    def restore(self, file: str):
        """The store restored from the backup named, where no store is; nothing signed and nothing landed."""
        backups.restored(values.root(self._root), values.file(file))
        return backups.Restored()
