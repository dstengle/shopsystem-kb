"""A directory imported into a freshly started store: the directory examined (kb.examining), then every artifact that
checks clean, or with errors skipped everything that leads to none, landed as one set through the write pipeline
(kb.write). The type that describes types is the store's own and is never landed."""
from pathlib import Path

from kb import examining, file_refusals, offers, write
from kb.edits import Import
from kb.examining import METASCHEMA_ID, Checked
from kb.offers import Offered
from kb.port import Port
from kb.signatures import Signed
from kb.roots import Named
from kb.values import ArtifactId, Refused


def imported(store: Port, directory: Named, signed: Signed, skip_errors: bool,
             passed_over: Path | None = None) -> Checked:
    """The directory checked, then every artifact in it landed as one set under the signature, each type ahead of the
    artifacts of its kind; the store's own type that describes types is kept. A directory with errors is refused with
    the check's report, and nothing is written; or, with errors skipped, every artifact lands but the broken files
    and the files that would be skipped, and the report says which they are and why. Files under the place passed
    over, when one is given, are not offered. The store's write lock is held from finding the store fresh to the
    landing, so nothing lands between them."""
    with store.exclusive():
        return _imported(store, directory, signed, skip_errors, passed_over)


def _imported(store: Port, directory: Named, signed: Signed, skip_errors: bool, passed_over: Path | None) -> Checked:
    """The import, made while the store's write lock is held."""
    _fresh(store)
    offered = offers.offered(directory, passed_over)
    report = examining.examined(store, offered)
    if report.errors and not skip_errors:
        return Checked([file_refusals.check_failed(len(report.errors))], report.errors, report.skipped)
    landing = _landing(offered, report)
    if not landing:
        return Checked([file_refusals.nothing_lands()], report.errors, report.skipped)
    write.land(store, [Import(landing[name].id, landing[name].artifact) for name in examining.in_order(landing)], signed)
    return report


def _fresh(store: Port) -> None:
    """Refuse a store that holds any artifact besides the type that describes types: import never merges."""
    held = [name for name in store.ids() if name != METASCHEMA_ID]
    if held:
        raise Refused([file_refusals.not_fresh(len(held))])


def _landing(offered: list[Offered], report: Checked) -> dict[ArtifactId, Offered]:
    """The files that land, by name: every artifact but the type that describes types, a file with an error and a
    file that would be skipped."""
    left_out = {skipped.file for skipped in report.skipped}
    return {
        each.name: each for each in offered
        if each.name is not None and each.id != METASCHEMA_ID and not each.errors and each.file not in left_out
    }
