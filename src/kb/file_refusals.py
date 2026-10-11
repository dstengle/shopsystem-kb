"""The faults of the operator's directories and files, each with its rule and its message, from plain values: a
directory an export or an import is refused for, a place a backup cannot be written at, a file offered for restore
that is not a backup this kb can read, a file offered for import that cannot be read, is not in canonical form or is
of a kind nothing offers a type for, and an import refused whole."""
from kb import rules
from kb.contract import kb_pb2


def not_an_import_directory(named: str) -> kb_pb2.Fault:
    """A name offered for import that is not a directory."""
    return kb_pb2.Fault(rule=rules.ROOT, message=f"an import is read from a directory; {named!r} is not one")


def not_an_export_directory(named: str) -> kb_pb2.Fault:
    """A name an export is to be written into that is not a directory."""
    return kb_pb2.Fault(
        rule=rules.ROOT, message=f"an export is written into a directory; {named!r} is not a directory",
    )


def export_would_overwrite(named: str) -> kb_pb2.Fault:
    """A directory an export is to be written into that already holds something."""
    return kb_pb2.Fault(rule=rules.ROOT, message=f"an export never overwrites; {named!r} already holds something")


def backup_would_overwrite(named: str) -> kb_pb2.Fault:
    """A place a backup is to be written at where anything already is."""
    return kb_pb2.Fault(rule=rules.ROOT, message=f"a backup never overwrites; {named!r} already holds something")


def backup_cannot_be_written(named: str, problem: str) -> kb_pb2.Fault:
    """A place a backup cannot be written at: nothing there is the store's own."""
    return kb_pb2.Fault(rule=rules.ROOT, message=f"a backup cannot be written at {named!r}: {problem}")


def unreadable_file(file: str, problem: str) -> kb_pb2.Fault:
    """A file offered for import that cannot be read as YAML 1.2."""
    return kb_pb2.Fault(artifact=file, rule=rules.UNREADABLE, message=f"it cannot be read as YAML 1.2: {problem}")


def not_canonical(file: str, problem: str) -> kb_pb2.Fault:
    """A file offered for import that is not in canonical form, its place in the directory included."""
    return kb_pb2.Fault(artifact=file, rule=rules.CONTENT, message=f"it is not in canonical form: {problem}")


def no_type_offered(file: str, kind_name: str) -> kb_pb2.Fault:
    """A file offered for import of a kind neither the directory nor the store holds a type for."""
    return kb_pb2.Fault(
        artifact=file, rule=rules.KIND,
        message=f"a kind must name a type the directory or the store holds; neither holds a type called {kind_name!r}",
    )


def no_version_offered(file: str, version: str) -> kb_pb2.Fault:
    """A file offered for import conforming to a version of its type neither the directory nor the store holds."""
    return kb_pb2.Fault(
        artifact=file, rule=rules.VERSION,
        message=f"an artifact conforms to a version of its type the directory or the store holds; neither holds "
                f"{version!r}",
    )


def not_fresh(held: int) -> kb_pb2.Fault:
    """An import into a store that holds artifacts besides the type that describes types."""
    return kb_pb2.Fault(
        rule=rules.STORE,
        message=f"import goes only into a freshly started store; this one holds {held} artifact(s) besides the type "
                f"that describes types",
    )


def check_failed(errors: int) -> kb_pb2.Fault:
    """An import of a directory whose check found errors, with none skipped."""
    return kb_pb2.Fault(
        rule=rules.CONTENT, message=f"the check found {errors} error(s) in the directory, and nothing was written",
    )


def nothing_lands() -> kb_pb2.Fault:
    """An import that would land nothing."""
    return kb_pb2.Fault(rule=rules.OPERATIONS, message="nothing in the directory would land, and nothing was written")


def not_a_backup(file: str) -> kb_pb2.Fault:
    """A file offered for restore that is not a backup kb made."""
    return kb_pb2.Fault(rule=rules.UNREADABLE, message=f"{file!r} is not a backup kb made")


def backup_by_earlier_kb(file: str) -> kb_pb2.Fault:
    """A backup an earlier kb made, which this kb cannot read as a store."""
    return kb_pb2.Fault(rule=rules.UNREADABLE, message=f"{file!r} was made by an earlier kb, which this kb cannot read")


def backup_by_later_kb(file: str) -> kb_pb2.Fault:
    """A backup a later kb made, which that kb is needed to read."""
    return kb_pb2.Fault(
        rule=rules.UNREADABLE, message=f"{file!r} was made by a later version of kb, which is needed to read it")
