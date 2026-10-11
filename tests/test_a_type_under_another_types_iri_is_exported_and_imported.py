"""The export of a valid store checks clean and is imported, also where a type is defined under another type's IRI
and a link waits on an IRI under it: into a fresh store, which then exports the same files byte for byte, and into
the store it came from, which holds it all already. A type file's place is judged against the store and the type
files ahead of it, never against the links the directory's own artifacts bring: a link that waited in the store,
under the other type, before the import still keeps the type out. The commands are the operator's."""
from pathlib import Path

import pytest

from calls import DECISION_TYPE, NOTE_TYPE, TAG_TYPE, create, define, filed, iri, start_a_store, type_iri
from conftest import OPERATOR, _kb, exported
import held
from kb import client as kb_client

DECISIONS = type_iri("decision")
RULINGS = f"{DECISIONS}/ruling"
TO_COME = f"{RULINGS}/to-come"
SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"}, {"title": "Rationale", "body": "Costs move.\n"},
]
RULING_TYPE = {**TAG_TYPE, "title": "Ruling"}
DOCKET_TYPE = {
    "title": "Docket",
    "version": 1,
    "schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "ruling": {
                "type": "string",
                "ref": {"targets": [RULINGS], "cardinality": "one", "parts": False, "on_delete": "refuse"},
            },
        },
        "required": ["title"],
    },
}


def _fill(client):
    """A type for decisions, a type for rulings under its IRI, a decision, a ruling, and two dockets, one whose link
    lands on the ruling and one whose link waits on an IRI under the type for rulings."""
    define(client, DECISION_TYPE)
    define(client, RULING_TYPE, at=RULINGS)
    create(client, "decision", {"title": "Price reviews happen weekly", "sections": SECTIONS})
    create(client, RULINGS, {"title": "Weekly it is"})
    define(client, DOCKET_TYPE)
    create(client, "docket", {"title": "Heard", "ruling": f"{RULINGS}/weekly-it-is"})
    create(client, "docket", {"title": "Pending", "ruling": TO_COME})


def _files(directory):
    """Every file below a directory, by its place, with its bytes."""
    return {
        str(path.relative_to(directory)): path.read_bytes() for path in Path(directory).rglob("*") if path.is_file()
    }


def _clean(ran):
    """Whether a command ended well, its report naming no file with an error and none skipped."""
    report = [line for line in ran.stdout.splitlines() if line.split("\t")[0] in ("error", "skipped")]
    return (ran.returncode, ran.stderr, report) == (0, "", [])


def test_the_store_exported_is_valid_and_holds_a_link_waiting_under_the_nested_type(tmp_path):
    exported(tmp_path, _fill)
    validated = _kb("validate", cwd=tmp_path / "source")
    assert (validated.returncode, validated.stderr) == (0, ""), validated.stdout
    assert [line.split("\t")[:2] for line in validated.stdout.splitlines()] == [["placeholder", TO_COME]]


def test_its_export_checks_clean_and_is_imported_into_a_fresh_store_which_exports_the_same_files(root, tmp_path):
    target = exported(tmp_path, _fill)
    start_a_store(root)

    checked = _kb("import", str(target), "--check", cwd=root)
    assert _clean(checked), (checked.stdout, checked.stderr)
    ran = _kb("import", str(target), cwd=root, env={"KB_ACTOR": OPERATOR})
    assert _clean(ran), (ran.stdout, ran.stderr)

    again = tmp_path / "exported-again"
    assert _kb("export", str(again), cwd=root).returncode == 0
    assert _files(again) == _files(target)
    assert _kb("validate", cwd=root).returncode == 0


def test_its_export_checks_clean_and_is_imported_into_the_store_it_came_from(tmp_path):
    target, source = exported(tmp_path, _fill), tmp_path / "source"
    before = held.holds(source)

    checked = _kb("import", str(target), "--check", cwd=source)
    assert _clean(checked), (checked.stdout, checked.stderr)
    ran = _kb("import", str(target), cwd=source, env={"KB_ACTOR": OPERATOR})
    assert _clean(ran), (ran.stdout, ran.stderr)

    assert held.holds(source) == before
    again = tmp_path / "exported-again"
    assert _kb("export", str(again), cwd=source).returncode == 0
    assert _files(again) == _files(target)


def test_a_type_file_is_kept_out_by_a_link_that_waited_in_the_store_under_another_type(root, tmp_path):
    """The store's note waits on an IRI that belongs to the type for decisions; a type brought at an IRI above it
    would take it, so its file has an error, as its define would be refused."""
    target = exported(tmp_path, lambda client: define(client, RULING_TYPE, at=RULINGS))
    start_a_store(root)
    client = kb_client.connect(root)
    define(client, DECISION_TYPE)
    define(client, NOTE_TYPE)
    create(client, "note", {"title": "On a ruling to come", "about": TO_COME})
    before = held.holds(root)

    checked = _kb("import", str(target), "--check", cwd=root)

    errors = [line.split("\t") for line in checked.stdout.splitlines() if line.startswith("error\t")]
    assert [line[1:3] for line in errors] == [[filed(RULINGS, 1), "identity"]], checked.stdout
    assert f"{TO_COME!r} belongs to {DECISIONS!r}" in errors[0][3]
    assert (checked.returncode, checked.stderr, held.holds(root)) == (1, "", before)
    assert _kb("import", str(target), cwd=root, env={"KB_ACTOR": OPERATOR}).returncode == 2
    assert held.holds(root) == before


def _report(ran):
    """The lines of a report that name a file with an error or one skipped, each as its kind, its file and, for an
    error, the rule broken."""
    lines = [line.split("\t") for line in ran.stdout.splitlines()]
    return sorted(line[:3] for line in lines if line[0] in ("error", "skipped"))


@pytest.mark.parametrize("nested", [("o", "o/i"), ("o", "o/i", "o/i/j")], ids=["two", "three"])
def test_every_type_file_above_a_link_that_waited_in_the_store_is_kept_out_however_they_nest(root, tmp_path, nested):
    """The store's note waits on an IRI under the innermost type brought, which belongs to the type for decisions:
    each type brought would take it, so each file has an error, as each define would be refused, and a type file
    whose place is refused shields none above it. With errors skipped nothing lands and the store stays valid."""
    brought = [f"{DECISIONS}/{each}" for each in nested]
    waited_on = f"{brought[-1]}/to-come"
    target = exported(tmp_path, lambda client: [define(client, RULING_TYPE, at=each) for each in brought])
    start_a_store(root)
    client = kb_client.connect(root)
    define(client, DECISION_TYPE)
    define(client, NOTE_TYPE)
    create(client, "note", {"title": "On a ruling to come", "about": waited_on})
    before = held.names(root)

    checked = _kb("import", str(target), "--check", cwd=root)

    assert _report(checked) == sorted(["error", filed(each, 1), "identity"] for each in brought), checked.stdout
    errors = [line for line in checked.stdout.splitlines() if line.startswith("error\t")]
    assert all(f"{waited_on!r} belongs to {DECISIONS!r}" in line for line in errors), checked.stdout
    assert (checked.returncode, checked.stderr) == (1, "")

    ran = _kb("import", str(target), "--skip-errors", cwd=root, env={"KB_ACTOR": OPERATOR})
    assert (ran.returncode, ran.stderr) == (0, ""), (ran.stdout, ran.stderr)
    assert _report(ran) == _report(checked)
    assert held.names(root) == before
    validated = _kb("validate", cwd=root)
    assert (validated.returncode, validated.stderr) == (0, ""), validated.stdout
    assert [line.split("\t")[:2] for line in validated.stdout.splitlines()] == [["placeholder", waited_on]]
    again = _kb("import", str(target), "--check", cwd=root)
    assert (again.returncode, again.stdout, again.stderr) == (checked.returncode, checked.stdout, checked.stderr)
