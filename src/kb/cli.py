"""kb's own command line, for the operator: set a store up, empty or seeded from a directory of files, check one,
export one, back one up, restore a backup, check a directory for import, import one into a store, and
serve one to callers over the network. Nothing else; every other change to content goes through a client.

Each command is one call on the client, or on one of the operator's commands beside it, or, to set a store up seeded
or to restore one, on kb.staging, or, to serve, on kb.server, a store started first on kb.staging when a start is asked
for and the root holds none, and taken back there should it then not be served.
A refusal is printed to stderr and exits 2, an import's after the check's report; a check that finds a violation
exits 1, and one that finds only placeholders, or artifacts behind their type, exits 0. A store served is served
until the process is told to stop, and then exits 0.
"""
import argparse
import os
import signal
import sys
from pathlib import Path

import kb
from kb import client as kb_client
from kb import addresses, reports, rules, server, staging
from kb.contract import kb_pb2
from kb.values import Refused

REFUSED, VIOLATED = 2, 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="kb", description="Look after a kb store.")
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="set up a store in a directory")
    init.add_argument("root", help="the directory the store is made inside, as its kb/ subdirectory")
    init.add_argument("--seed", metavar="DIR", help="a directory of files, laid out as an export lays them out, for the "
                      "store to hold from the start, as an import into it would land them")
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
    backing_up = commands.add_parser("backup", help="back the store found here, or the one KB_ROOT names, up whole, "
                                     "its history and journal included, as one file")
    backing_up.add_argument("file", help="the file the backup is written as, where nothing is")
    restoring = commands.add_parser("restore", help="restore a backup as a store in a directory that holds none")
    restoring.add_argument("file", help="the backup, as kb backup wrote it")
    restoring.add_argument("root", help="the directory the store is restored inside, as its kb/ subdirectory")
    serving = commands.add_parser("serve", help="serve a store to callers over the network, at the address given")
    serving.add_argument("root", help="the directory the store sits in, as its kb/ subdirectory")
    serving.add_argument("--listen", metavar="HOST:PORT", help="the address to serve at; none is assumed")
    serving.add_argument("--start", action="store_true", help="start a store there first, under the role KB_ACTOR "
                         "names, when it holds none")
    args = parser.parse_args(argv)
    if args.command == "serve":
        return _serve(args.root, args.listen, args.start)
    if args.command == "init":
        return _init(args.root, args.seed)
    if args.command == "export":
        return _export(args.directory)
    if args.command == "import":
        return _import_check(args.directory) if args.check else _import(args.directory, args.skip_errors)
    if args.command == "backup":
        return _backup(args.file)
    if args.command == "restore":
        return _restore(args.file, args.root)
    return _validate()


def _init(root: str, seed: str | None) -> int:
    """Start a store under the role KB_ACTOR names, holding the seed directory's files when one is named, the check's
    report shown first; or none."""
    role = os.environ.get("KB_ACTOR", "")
    if not role:
        return _unnamed("init")
    try:
        if seed is None:
            kb.init(root, role)
            return 0
        imported = staging.seeded(root, role, seed)
    except kb.NotStarted as refused:
        return _refused("init", refused.faults)
    except KeyboardInterrupt:
        return _interrupted()
    reports.imported(imported)
    return _refused("init", imported.faults) if imported.faults else 0


def _unnamed(command: str) -> int:
    """A store's start refused because no role is named to start it under."""
    return _refused(command, [kb_pb2.Fault(
        rule=rules.ACTOR, message="a store can only be started under a role, named through KB_ACTOR",
    )])


def _interrupted() -> int:
    """The process ended by SIGINT, as Python ends one an interrupt reached, once what the run staged is gone, but
    without the traceback: an operator's Ctrl-C is no fault of kb's. Should SIGINT be held back, the code a shell gives
    a process it ended."""
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    os.kill(os.getpid(), signal.SIGINT)
    return 128 + signal.SIGINT


def _serve(root: str, listen: str | None, start: bool) -> int:
    """Serve the store at root at the address given until told to stop, saying on one line where it serves, a store
    started there first when a start is asked for and root holds none; with no address given, or one it cannot be
    served at, nothing is served."""
    if listen is None:
        print("kb serve: refused: no address is assumed; give the one to serve at with --listen HOST:PORT",
              file=sys.stderr)
        return REFUSED
    try:
        address = addresses.address(listen)
    except ValueError as unservable:
        return _unservable(listen, unservable)
    role = None
    if start and staging.wanted(root):
        role = os.environ.get("KB_ACTOR", "")
        if not role:
            return _unnamed("serve")
    try:
        with staging.serving(root, role) as keep:
            faults = server.refused(Path(root))
            if faults:
                return _refused("serve", faults)
            served = server.started(Path(root), address)
            keep()
    except kb.NotStarted as refused:
        return _refused("serve", refused.faults)
    except Refused as owned:
        return _refused("serve", owned.faults)
    except ValueError as unservable:
        return _unservable(listen, unservable)
    server.until_signalled(served, lambda: print(f"serving\t{served.address}", flush=True))
    return 0


def _unservable(listen: str, unservable: ValueError) -> int:
    """Serving refused at the address given, which is named back with why."""
    print(f"kb serve: refused: the store cannot be served at {listen!r}: {unservable}", file=sys.stderr)
    return REFUSED


def _validate() -> int:
    """Check the store this directory finds: every violation, then every artifact behind its type, then every link
    into a placeholder, with the part it names, one to a line. Only a violation makes the check fail."""
    answered = kb_client.connect().Check(kb_pb2.CheckRequest())
    if answered.WhichOneof("outcome") == "refusal":
        return _refused("validate", answered.refusal.faults)
    checked = answered.result
    reports.checked(checked)
    return VIOLATED if checked.violations else 0


def _export(directory: str) -> int:
    """Write the store this directory finds out as files into the directory named."""
    exported = kb_client.export(directory)
    if exported.faults:
        return _refused("export", exported.faults)
    return 0


def _backup(file: str) -> int:
    """Back the store this directory finds up whole, as one file at the place named."""
    backed_up = kb_client.backup(file)
    if backed_up.faults:
        return _refused("backup", backed_up.faults)
    return 0


def _restore(file: str, root: str) -> int:
    """Restore the backup named as a store inside root; no role is read, since nothing is signed."""
    try:
        restored = staging.restored(root, file)
    except kb.NotStarted as refused:
        return _refused("restore", refused.faults)
    except KeyboardInterrupt:
        return _interrupted()
    return _refused("restore", restored.faults) if restored.faults else 0


def _import_check(directory: str) -> int:
    """Check the directory named for import into the store this directory finds: every error, then every file that
    would be skipped with the chain of files leading to a broken one, one to a line; or a line saying it is clean."""
    checked = kb_client.import_check(directory)
    if checked.faults:
        return _refused("import", checked.faults)
    reports.imported(checked)
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
    reports.imported(imported)
    if imported.faults:
        return _refused("import", imported.faults)
    return 0


def _refused(command: str, faults) -> int:
    for fault in faults:
        print(f"kb {command}: refused: {fault.rule}: {fault.message}", file=sys.stderr)
    return REFUSED
