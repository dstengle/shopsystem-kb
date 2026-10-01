"""kb's own command line, for the operator: set a store up, check one, export one, and check a directory for import.
Nothing else; every change to content goes through a client.

Each command is one call on the in-process client, or on one of the operator's commands beside it. A refusal is
printed to stderr and exits 2; a check that finds a violation exits 1.
"""
import argparse
import os
import sys

from kb import client as kb_client
from kb import rules
from kb.contract import kb_pb2

REFUSED, VIOLATED = 2, 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="kb", description="Look after a kb store.")
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="set up a store in a directory")
    init.add_argument("root", help="the directory the store is made inside, as its kb/ subdirectory")
    commands.add_parser("validate", help="check the store found here, or the one KB_ROOT names")
    exporting = commands.add_parser("export", help="write the store found here, or the one KB_ROOT names, out as files")
    exporting.add_argument("directory", help="an empty directory, or one that does not exist, for the files")
    importing = commands.add_parser("import", help="bring a directory of files into the store found here")
    importing.add_argument("directory", help="the directory of files, laid out as an export lays them out")
    how = importing.add_mutually_exclusive_group(required=True)
    how.add_argument("--check", action="store_true", help="only check the directory, writing nothing")
    args = parser.parse_args(argv)
    if args.command == "init":
        return _init(args.root)
    if args.command == "export":
        return _export(args.directory)
    if args.command == "import":
        return _import_check(args.directory)
    return _validate()


def _init(root: str) -> int:
    """Start a store under the role KB_ACTOR names."""
    role = os.environ.get("KB_ACTOR", "")
    if not role:
        return _refused("init", [kb_pb2.Fault(
            rule=rules.ACTOR, message="a store can only be started under a role, named through KB_ACTOR",
        )])
    started = kb_client.connect().Init(kb_pb2.InitRequest(root=root, actor=kb_pb2.Actor(role=role)))
    if started.faults:
        return _refused("init", started.faults)
    return 0


def _validate() -> int:
    """Check the store this directory finds: every violation, then every artifact behind its type, one to a line."""
    checked = kb_client.connect().Validate(kb_pb2.ValidateRequest())
    if checked.faults:
        return _refused("validate", checked.faults)
    for fault in checked.violations:
        print("\t".join(("violation", fault.artifact, fault.path, fault.rule, fault.message)))
    for stale in checked.stale:
        print(f"stale\t{stale.artifact}\tchecked against version {stale.schema_version} of its type, "
              f"which is at {stale.current}")
    return VIOLATED if checked.violations else 0


def _export(directory: str) -> int:
    """Write the store this directory finds out as files into the directory named."""
    exported = kb_client.export(directory)
    if exported.faults:
        return _refused("export", exported.faults)
    return 0


def _import_check(directory: str) -> int:
    """Check the directory named for import into the store this directory finds: every error, then every file that
    would be skipped with the chain of files leading to a broken one, one to a line; or a line saying it is clean."""
    checked = kb_client.import_check(directory)
    if checked.faults:
        return _refused("import", checked.faults)
    for fault in checked.errors:
        print("\t".join(("error", fault.artifact, fault.rule, fault.message)))
    for skipped in checked.skipped:
        print("\t".join(("skipped", skipped.file, " -> ".join(skipped.chain))))
    if checked.errors:
        return VIOLATED
    print(f"clean\t{directory} checks clean for import")
    return 0


def _refused(command: str, faults) -> int:
    for fault in faults:
        print(f"kb {command}: refused: {fault.rule}: {fault.message}", file=sys.stderr)
    return REFUSED
