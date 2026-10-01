"""The operator's commands that are not rpcs, export, the import check and the import, over one store, each run inside
the servicer's one boundary: the store opened first, the command's values made, one call into the domain, and any
refusal or escaping exception its faults."""
from typing import NamedTuple

from kb import export, importing, signatures, values
from kb.contract import kb_pb2
from kb.servicer import boundary


class Importing(NamedTuple):
    """An import as the operator asks for it: the directory as named, the role it lands under, and whether the
    files with errors, and those leading to them, are skipped."""
    directory: str
    role: str
    skip_errors: bool


class Operator:
    def __init__(self, root):
        """Over the store at root."""
        self._root = root

    @boundary(export.Exported)
    def export(self, directory: str, held):
        """The store written out as files into the directory named."""
        export.written(held, values.directory(directory))
        return export.Exported()

    @boundary(importing.Checked)
    def import_check(self, directory: str, held):
        """A directory read as a set for import into the store, its errors and what would be skipped; nothing written."""
        return importing.checked(held, values.directory(directory))

    @boundary(importing.Checked)
    def import_(self, request: Importing, held):
        """A directory checked, then landed in the store as one set signed by the role, with a message naming it."""
        signed = signatures.signed(kb_pb2.Actor(role=request.role), f"import {request.directory}")
        return importing.imported(held, values.directory(request.directory), signed, request.skip_errors)
