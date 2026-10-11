"""`kb import --check` reports every error of a file: a link that lands on nothing and waits under no type is
reported beside whatever else is wrong with its file, where JSON Schema left the link readable, and such a file is
left out by an import with errors skipped as the check says. Each directory is the export of a store of its own, one
file of it then written wrong by hand."""
import copy
from pathlib import Path

from calls import DECISION_TYPE, NOTE_TYPE, create, define, filed, iri, start_a_store
from conftest import OPERATOR, _kb, exported
import held

SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"}, {"title": "Rationale", "body": "Costs move.\n"},
]
WEEKLY, MONTHLY = iri("decision", "price-reviews-happen-weekly"), iri("decision", "price-reviews-happen-monthly")
MEMO = iri("memo", "on-the-reviews")
UNDER_NO_TYPE = "https://shop.example/kb/nokind/x"

# A type whose artifacts link to decisions from two fields.
MEMO_TYPE = copy.deepcopy(NOTE_TYPE)
MEMO_TYPE["title"] = "Memo"
MEMO_TYPE["schema"]["properties"]["also"] = copy.deepcopy(NOTE_TYPE["schema"]["properties"]["about"])


def _fill(client):
    """Two decisions, the second superseding the first, and a memo about both."""
    define(client, DECISION_TYPE)
    create(client, "decision", {"title": "Price reviews happen weekly", "sections": SECTIONS})
    create(client, "decision", {"title": "Price reviews happen monthly", "sections": SECTIONS, "supersedes": WEEKLY})
    define(client, MEMO_TYPE)
    create(client, "memo", {"title": "On the reviews", "about": WEEKLY, "also": MONTHLY})


def _rewritten(target, name, *replacements):
    """An artifact's file with each text given, found once, replaced by another."""
    file = Path(target) / filed(name)
    text = file.read_text(encoding="utf-8")
    for old, new in replacements:
        assert text.count(old) == 1, (old, text)
        text = text.replace(old, new)
    file.write_text(text, encoding="utf-8")


def _report(ran):
    """The lines of a report that name a file with an error or one skipped, each as its kind, its file and, for an
    error, the rule broken."""
    lines = [line.split("\t") for line in ran.stdout.splitlines()]
    return sorted(line[:3] for line in lines if line[0] in ("error", "skipped"))


def _checked(root, target):
    start_a_store(root)
    before = held.holds(root)
    checked = _kb("import", str(target), "--check", cwd=root)
    assert (checked.returncode, checked.stderr) == (1, "") and held.holds(root) == before, checked.stderr
    return checked


def _imports_all_but(root, target, file, checked):
    """An import with errors skipped reports what the check did and lands every file but the one named."""
    ran = _kb("import", str(target), "--skip-errors", cwd=root, env={"KB_ACTOR": OPERATOR})
    assert (ran.returncode, ran.stderr) == (0, ""), (ran.stdout, ran.stderr)
    assert _report(ran) == _report(checked)
    landed = {filed(name) for name in held.names(root) if name not in held.versions(root)}
    assert landed == {filed(name) for name in (WEEKLY, MONTHLY, MEMO)} - {file}
    assert _kb("validate", cwd=root).returncode == 0


def test_a_file_that_breaks_its_type_and_carries_a_link_that_lands_on_nothing_is_reported_with_both(root, tmp_path):
    target = exported(tmp_path, _fill)
    _rewritten(target, MONTHLY, ("  - title: Rationale\n    body: |\n      Costs move.\n", ""), (WEEKLY, UNDER_NO_TYPE))

    checked = _checked(root, target)

    file = filed(MONTHLY)
    assert _report(checked) == [["error", file, "ref"], ["error", file, "sections"]]
    assert f"{UNDER_NO_TYPE!r} does not" in checked.stdout
    _imports_all_but(root, target, file, checked)


def test_a_link_is_reported_beside_another_link_field_that_json_schema_refuses(root, tmp_path):
    """The field JSON Schema refuses is not read as a link; the other is, and lands on nothing."""
    target = exported(tmp_path, _fill)
    _rewritten(target, MEMO, (f"about: {WEEKLY}\n", "about: 7\n"), (f"also: {MONTHLY}\n", f"also: {UNDER_NO_TYPE}\n"))

    checked = _checked(root, target)

    file = filed(MEMO)
    assert _report(checked) == [["error", file, "ref"], ["error", file, "type"]]
    _imports_all_but(root, target, file, checked)
