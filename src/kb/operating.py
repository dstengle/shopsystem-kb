"""The operator's commands that are not rpcs, export and the import check, over one store, each run inside the
servicer's one boundary: the store opened first, the command's values made, one call into the domain, and any refusal
or escaping exception its faults."""
from kb import export, importing, values
from kb.servicer import boundary


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
