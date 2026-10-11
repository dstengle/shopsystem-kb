"""What `kb import --check` calls an error or a skip is exactly what `kb import --skip-errors` leaves out, and that
import never fails with a fault the check did not report: held here for directories in which the files of a type's
version do not land (deleted, unreadable, broken, skipped by a `kb:` reference), with links to its artifacts' files,
to IRIs under it nobody holds and into parts of its artifacts, against a fresh store and against stores that hold
the type. A file that differs from what the store holds refuses the whole import, which is the one exception. Each
directory is the export of a store of its own; the check, the import and `kb validate` are the operator's commands."""
import copy
import itertools
from pathlib import Path

import pytest

from calls import (
    DECISION_TYPE, NOTE_TYPE, TAG_TYPE, TYPE_OF_TYPES, WORK_ITEM_TYPE, create, define, filed, iri, kb_ref,
    next_version, start_a_store, type_iri,
)
from conftest import OPERATOR, _kb, exported
import held
from kb import client as kb_client

DECISIONS, TAGS = type_iri("decision"), type_iri("tag")
WEEKLY, MONTHLY = iri("decision", "price-reviews-happen-weekly"), iri("decision", "price-reviews-happen-monthly")
NOT_ANYWHERE = iri("decision", "not-anywhere")
SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"}, {"title": "Rationale", "body": "Costs move.\n"},
]

HOW = ("deleted", "unreadable", "broken", "skipped by a kb: reference")
LINKS = {
    "to its artifacts' files": ("files",),
    "to IRIs under it nobody holds": ("unheld",),
    "into parts of its artifacts": ("parts",),
    "of every sort": ("files", "unheld", "parts"),
}
# Where the version that does not land stands: the number the directory's type reaches, and what the store that is
# imported into holds of the type beforehand.
SETTINGS = {
    "a fresh store, the type's only version": (1, None),
    "a fresh store, another version of the type landing": (2, None),
    "a store holding another version of the type": (2, "the first"),
    "a store holding the type as the directory gives it": (1, "the same"),
}


def _decision_type(number, referring):
    """The type for decisions as a version of it is written: the first as every test's, or revised with one more
    field; referring to the type for tags by a `kb:` reference when it is to be skipped by one."""
    content = copy.deepcopy(DECISION_TYPE)
    properties = content["schema"]["properties"]
    if number == 2:
        properties["status"] = {"type": "string"}
    if referring:
        properties["label"] = {"$ref": kb_ref("tag", 1, "#/properties/title")}
    return content


def _the_type_for_decisions(client, reaches, referring):
    """The type for decisions standing at the version given, that version the one written as `referring` says; the
    first version, when it is not the one, the plain type."""
    if referring:
        define(client, TAG_TYPE)
    define(client, _decision_type(1, referring and reaches == 1))
    if reaches == 2:
        revised = next_version(client, "decision", _decision_type(2, referring))
        assert not revised.faults, revised.faults


def _filled(reaches, referring, links):
    """What gives a store the type for decisions, two decisions of the version it stands at, and the artifacts of
    other types that carry the links asked for."""
    def fill(client):
        _the_type_for_decisions(client, reaches, referring)
        for title in ("Price reviews happen weekly", "Price reviews happen monthly"):
            create(client, "decision", {"title": title, "sections": SECTIONS, "options": [{"title": "Go monthly"}]})
        define(client, WORK_ITEM_TYPE)
        define(client, NOTE_TYPE)
        if "files" in links:
            create(client, "work-item", {"title": "Tune the prices", "decisions": [WEEKLY, MONTHLY]})
            create(client, "note", {"title": "On the weekly review", "about": WEEKLY})
        if "unheld" in links:
            create(client, "work-item", {"title": "Find the decision", "decisions": [NOT_ANYWHERE]})
            create(client, "note", {"title": "On a decision to come", "about": NOT_ANYWHERE})
        if "parts" in links:
            create(client, "note", {"title": "On going monthly", "about": f"{MONTHLY}#options/go-monthly"})
    return fill


def _a_note_into_a_part_its_decision_lacks(target):
    """A note's file written beside the one linking into an option a decision has, as an export would write it, its
    link into an option the other decision lacks: a link no create may make, which only a file can bring."""
    text = (Path(target) / filed(iri("note", "on-going-monthly"))).read_text(encoding="utf-8")
    for held_part, lacked in ((f"{MONTHLY}#options/go-monthly", f"{WEEKLY}#options/go-yearly"),
                              ("on-going-monthly", "on-going-yearly"), ("On going monthly", "On going yearly")):
        assert text.count(held_part) == 1, text
        text = text.replace(held_part, lacked)
    (Path(target) / filed(iri("note", "on-going-yearly"))).write_text(text, encoding="utf-8")


def _broken(target, name, number):
    """A type version's file given a schema of a type JSON Schema does not know."""
    file = Path(target) / filed(name, number)
    text = file.read_text(encoding="utf-8")
    assert text.count("\n  type: object\n") == 1, text
    file.write_text(text.replace("\n  type: object\n", "\n  type: objekt\n"), encoding="utf-8")


def _not_landing(target, how, reaches):
    """The version of the type for decisions that the decisions conform to kept from landing, in the way named."""
    file = Path(target) / filed(DECISIONS, reaches)
    if how == "deleted":
        file.unlink()
    elif how == "unreadable":
        file.write_text(f"id: {DECISIONS}\ntitle: [never closed\n", encoding="utf-8")
    elif how == "broken":
        _broken(target, DECISIONS, reaches)
    else:
        _broken(target, TAGS, 1)


def _store(root, held_before, how):
    """The store imported into: fresh, or holding the type for decisions, its first version or all the directory's
    source held of it."""
    start_a_store(root)
    client = kb_client.connect(root)
    referring = how == HOW[3]
    if held_before == "the first":
        define(client, DECISION_TYPE)
    elif held_before == "the same":
        _the_type_for_decisions(client, 1, referring)


def _files(target):
    """Every file a directory for import holds but its copy of the type that describes types, sorted."""
    found = sorted(str(path.relative_to(target)) for path in Path(target).rglob("*.yaml"))
    return [file for file in found if file != filed(TYPE_OF_TYPES, 1)]


def _held_files(root):
    """The files an export of the store at root would hold, sorted: one for every held version of every type and one
    for every other artifact."""
    versions = held.versions(root)
    return sorted(
        file for name in held.names(root)
        for file in ([filed(name, number) for number in versions[name]] if name in versions else [filed(name)])
    )


def _report(ran):
    """The lines of a report that name a file with an error or one skipped, each split into its fields."""
    lines = [line.split("\t") for line in ran.stdout.splitlines()]
    return sorted(line for line in lines if line[0] in ("error", "skipped"))


def _rows():
    for setting, how, links in itertools.product(SETTINGS, HOW, LINKS):
        yield pytest.param(setting, how, links, id=f"{setting}; {how}; links {links}")


@pytest.mark.parametrize("setting, how, links", _rows())
def test_what_the_check_reports_is_what_the_import_with_errors_skipped_leaves_out(root, tmp_path, setting, how, links):
    reaches, held_before = SETTINGS[setting]
    target = exported(tmp_path, _filled(reaches, how == HOW[3], LINKS[links]))
    if "parts" in LINKS[links]:
        _a_note_into_a_part_its_decision_lacks(target)
    _not_landing(target, how, reaches)
    _store(root, held_before, how)
    before, files_before = held.holds(root), _held_files(root)

    checked = _kb("import", str(target), "--check", cwd=root)
    assert checked.stderr == "" and held.holds(root) == before, checked.stderr
    report = _report(checked)
    left_out = {line[1] for line in report}
    landing = [file for file in _files(target) if file not in left_out]
    assert landing, checked.stdout

    ran = _kb("import", str(target), "--skip-errors", cwd=root, env={"KB_ACTOR": OPERATOR})

    if any(line[:3:2] == ["error", "differs"] for line in report):
        assert ran.returncode == 2 and "differs" in ran.stderr, (ran.stdout, ran.stderr)
        assert held.holds(root) == before
        return
    assert (ran.returncode, ran.stderr) == (0, ""), (checked.stdout, ran.stdout, ran.stderr)
    assert _report(ran) == report
    assert _held_files(root) == sorted({*files_before, *landing})
    validated = _kb("validate", cwd=root)
    assert (validated.returncode, validated.stderr) == (0, ""), (validated.stdout, validated.stderr)
    assert all(line.startswith("placeholder\t") for line in validated.stdout.splitlines()), validated.stdout
