"""kb's own command line, for the operator: set a store up, check one, export one, check a directory for import,
import one into a freshly started store, and serve one to callers over the network. Nothing else; every other change
to content goes through a client.

Each command is one call on the client, or on one of the operator's commands beside it, or, to serve, on kb.server.
A refusal is printed to stderr and exits 2, an import's after the check's report; a check that finds a violation
exits 1. A store served is served until the process is told to stop, and then exits 0.
"""
import argparse
import os
import sys
from pathlib import Path

import kb
from kb import client as kb_client
from kb import addresses, rules, server
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
    importing = commands.add_parser("import", help="bring a directory of files into a freshly started store")
    importing.add_argument("directory", help="the directory of files, laid out as an export lays them out")
    how = importing.add_mutually_exclusive_group()
    how.add_argument("--check", action="store_true", help="only check the directory, writing nothing")
    how.add_argument(
        "--skip-errors", action="store_true", help="land all but the files with errors and the files leading to them",
    )
    serving = commands.add_parser("serve", help="serve a store to callers over the network, at the address given")
    serving.add_argument("root", help="the directory the store sits in, as its kb/ subdirectory")
    serving.add_argument("--listen", metavar="HOST:PORT", help="the address to serve at; none is assumed")
    args = parser.parse_args(argv)
    if args.command == "serve":
        return _serve(args.root, args.listen)
    if args.command == "init":
        return _init(args.root)
    if args.command == "export":
        return _export(args.directory)
    if args.command == "import":
        return _import_check(args.directory) if args.check else _import(args.directory, args.skip_errors)
    return _validate()


def _init(root: str) -> int:
    """Start a store under the role KB_ACTOR names."""
    role = os.environ.get("KB_ACTOR", "")
    if not role:
        return _refused("init", [kb_pb2.Fault(
            rule=rules.ACTOR, message="a store can only be started under a role, named through KB_ACTOR",
        )])
    try:
        kb.init(root, role)
    except kb.NotStarted as refused:
        return _refused("init", refused.faults)
    return 0


def _serve(root: str, listen: str | None) -> int:
    """Serve the store at root at the address given until told to stop, saying on one line where it serves; with no
    address given, nothing is served."""
    if listen is None:
        print("kb serve: refused: no address is assumed; give the one to serve at with --listen HOST:PORT",
              file=sys.stderr)
        return REFUSED
    faults = server.refused(Path(root))
    if faults:
        return _refused("serve", faults)
    served = server.started(Path(root), addresses.address(listen))
    server.until_signalled(served, lambda: print(f"serving\t{served.address}", flush=True))
    return 0


def _validate() -> int:
    """Check the store this directory finds: every violation, then every artifact behind its type, one to a line."""
    answered = kb_client.connect().Check(kb_pb2.CheckRequest())
    if answered.WhichOneof("outcome") == "refusal":
        return _refused("validate", answered.refusal.faults)
    checked = answered.result
    for fault in checked.violations:
        print("\t".join(("violation", fault.artifact, fault.place, fault.rule, fault.message)))
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
    _reported(checked)
    if checked.errors:
        return VIOLATED
    print(f"clean\t{directory} checks clean for import")
    return 0


def _import(directory: str, skip_errors: bool) -> int:
    """Bring the directory named into the store this directory finds, under the role KB_ACTOR names, the check's
    report shown first; with errors skipped, the files with errors and those leading to them left out."""
    role = os.environ.get("KB_ACTOR", "")
    if not role:
        return _refused("import", [kb_pb2.Fault(
            rule=rules.ACTOR, message="an import lands only under a role, named through KB_ACTOR",
        )])
    imported = kb_client.import_(directory, role, skip_errors)
    _reported(imported)
    if imported.faults:
        return _refused("import", imported.faults)
    return 0


def _reported(checked) -> None:
    """The check's report: every error, then every file that would be skipped with the chain of files leading to a
    broken one, one to a line."""
    for fault in checked.errors:
        print("\t".join(("error", fault.artifact, fault.rule, fault.message)))
    for skipped in checked.skipped:
        print("\t".join(("skipped", skipped.file, " -> ".join(skipped.chain))))


def _refused(command: str, faults) -> int:
    for fault in faults:
        print(f"kb {command}: refused: {fault.rule}: {fault.message}", file=sys.stderr)
    return REFUSED
