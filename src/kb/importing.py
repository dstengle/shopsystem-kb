"""A directory imported into a store, fresh or already holding artifacts: the directory examined (kb.examining), then
every artifact that checks clean, or with errors skipped everything that leads to none, landed as one set through the
write pipeline (kb.write), but what the store already holds identically (kb.comparing), which is passed over. A
directory that differs from what the store holds at any IRI is refused whole, naming each, with errors skipped or
not: a difference is never skipped. The type that describes types is the store's own and is never landed."""
from pathlib import Path

from kb import comparing, examining, file_refusals, names, offers, rules, write
from kb.edits import Import
from kb.examining import METASCHEMA_ID, Checked
from kb.offers import Offered
from kb.port import Port
from kb.signatures import Signed
from kb.roots import Named
from kb.values import ArtifactId


def imported(store: Port, directory: Named, signed: Signed, skip_errors: bool,
             passed_over: Path | None = None) -> Checked:
    """The directory checked, then every artifact in it landed as one set under the signature, each type ahead of the
    artifacts of its kind; the store's own type that describes types is kept, and so is every artifact, and every
    version of a type, the store already holds as its file gives it, which has no entry in the history. A directory
    holding a file that differs from what the store holds at its IRI is refused with one fault for each such IRI,
    whether or not errors are skipped, and nothing is written. A directory with errors and no difference is refused
    with the check's report, and nothing is written; or, with errors skipped, every artifact lands but the broken
    files and the files that would be skipped, and the report says which they are and why. Files under the place
    passed over, when one is given, are not offered. The store's write lock is held from before the directory is read
    to the landing, so what is identical is judged against the store as it stands when the set lands, and nothing
    lands between them."""
    with store.exclusive():
        return _imported(store, directory, signed, skip_errors, passed_over)


def _imported(store: Port, directory: Named, signed: Signed, skip_errors: bool, passed_over: Path | None) -> Checked:
    """The import, made while the store's write lock is held."""
    offered = offers.offered(directory, passed_over)
    report = examining.examined(store, offered)
    differing = _differing(offered)
    if differing:
        return Checked([file_refusals.differing(str(name)) for name in differing], report.errors, report.skipped)
    if report.errors and not skip_errors:
        return Checked([file_refusals.check_failed(len(report.errors))], report.errors, report.skipped)
    taken = _taken(offered, report)
    if not taken and not _sound(offered, report):
        return Checked([file_refusals.nothing_lands()], report.errors, report.skipped)
    held = comparing.compared(store, list(taken.values())).identical
    landing = {name: each for name, each in taken.items() if name not in held}
    if landing:
        write.land(store, [Import(landing[name].id, landing[name].artifact) for name in examining.in_order(landing)],
                   signed)
    return report


def _differing(offered: list[Offered]) -> list[ArtifactId]:
    """The IRIs at which the files examined differ from what the store holds, each once, in the order of names."""
    found = {each.id for each in offered if any(fault.rule == rules.DIFFERS for fault in each.errors)}
    return sorted(found, key=names.order)


def _sound(offered: list[Offered], report: Checked) -> bool:
    """Whether any file is sound: no error, not to be skipped, the type that describes types included, which is passed
    over."""
    left_out = {skipped.file for skipped in report.skipped}
    return any(each.name is not None and not each.errors and each.file not in left_out for each in offered)


def _taken(offered: list[Offered], report: Checked) -> dict[ArtifactId, Offered]:
    """The files an import takes, by name: every artifact but the type that describes types, a file with an error and
    a file that would be skipped."""
    left_out = {skipped.file for skipped in report.skipped}
    return {
        each.name: each for each in offered
        if each.name is not None and each.id != METASCHEMA_ID and not each.errors and each.file not in left_out
    }
