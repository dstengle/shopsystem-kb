"""A file carrying a link to an IRI under a type no version of which lands is skipped with the chain to that type's
version file, also where the type sits under another type's IRI and the link's field allows that outer type too: the
nearest type the directory offers at the IRI decides (decision/an-iri-belongs-to-its-nearest-type), so the link does
not wait under the outer type, where it would keep the mended type out of the store ever after. The directory is the
export of a valid store, one type file of it then broken by hand. The commands are the operator's."""
from pathlib import Path

from calls import DECISION_TYPE, TAG_TYPE, create, define, filed, iri, start_a_store, targets, type_iri
from conftest import OPERATOR, _kb, exported
import held

DECISIONS = type_iri("decision")
RULINGS = f"{DECISIONS}/ruling"
RULING, DECISION = f"{RULINGS}/weekly-it-is", iri("decision", "price-reviews-happen-weekly")
DOCKET, NOTE, MEMO = iri("docket", "heard"), iri("note", "seen-so-far"), iri("memo", "on-the-reviews")
SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"}, {"title": "Rationale", "body": "Costs move.\n"},
]
RULING_TYPE = {**TAG_TYPE, "title": "Ruling"}


def _linking(title, field, allowed):
    """A type whose artifacts carry a list of links to artifacts of the kinds allowed."""
    ref = {"targets": allowed, "cardinality": "many", "parts": False, "on_delete": "refuse"}
    properties = {"title": {"type": "string"}, field: {"type": "array", "items": {"type": "string"}, "ref": ref}}
    return {"title": title, "version": 1, "schema": {"type": "object", "properties": properties, "required": ["title"]}}


DOCKET_TYPE = _linking("Docket", "rulings", [RULINGS])
NOTE_TYPE = _linking("Note", "seen", [*targets("decision"), RULINGS])
MEMO_TYPE = _linking("Memo", "seen", [*targets("decision"), RULINGS])
BROKEN = filed(RULINGS, 1)
LEFT_OUT = {RULINGS, RULING, DOCKET, NOTE}


def _fill(client):
    """A type for decisions and a decision; a type for rulings under its IRI and a ruling; a docket, whose field
    allows rulings only, and a note, whose field allows decisions too, each linking to the ruling; and a memo, of a
    field like the note's, linking to the decision only."""
    define(client, DECISION_TYPE)
    define(client, RULING_TYPE, at=RULINGS)
    create(client, "decision", {"title": "Price reviews happen weekly", "sections": SECTIONS})
    create(client, RULINGS, {"title": "Weekly it is"})
    for content in (DOCKET_TYPE, NOTE_TYPE, MEMO_TYPE):
        define(client, content)
    create(client, "docket", {"title": "Heard", "rulings": [RULING]})
    create(client, "note", {"title": "Seen so far", "seen": [DECISION, RULING]})
    create(client, "memo", {"title": "On the reviews", "seen": [DECISION]})


def _report(ran):
    """The lines of a report that name a file with an error or one skipped: an error with its file and the rule
    broken, a file skipped with the chain of files that leads to the broken one."""
    lines = [line.split("\t") for line in ran.stdout.splitlines()]
    return sorted(line[:3] for line in lines if line[0] in ("error", "skipped"))


def _artifacts(root):
    """The names of what a store holds, but the versions of its types."""
    return set(held.names(root)) - set(held.versions(root))


def test_a_file_linking_under_a_nested_type_that_does_not_land_is_skipped_though_its_field_allows_the_outer_type(
        root, tmp_path):
    target = exported(tmp_path, _fill)
    everything = _artifacts(tmp_path / "source")
    type_file = Path(target) / BROKEN
    sound = type_file.read_text(encoding="utf-8")
    assert sound.count("type: object\n") == 1
    type_file.write_text(sound.replace("type: object\n", "type: objekt\n"), encoding="utf-8")
    start_a_store(root)
    fresh = _artifacts(root)

    checked = _kb("import", str(target), "--check", cwd=root)

    assert (checked.returncode, checked.stderr) == (1, "")
    assert [line[:2] for line in _report(checked) if line[0] == "error"] == [["error", BROKEN]]
    skipped = {line[1]: line[2] for line in _report(checked) if line[0] == "skipped"}
    assert set(skipped) == {filed(name) for name in (RULING, DOCKET, NOTE)}
    assert all(chain.endswith(BROKEN) for chain in skipped.values()), skipped
    assert skipped[filed(NOTE)] == f"{filed(NOTE)} -> {BROKEN}"

    ran = _kb("import", str(target), "--skip-errors", cwd=root, env={"KB_ACTOR": OPERATOR})
    assert (ran.returncode, ran.stderr) == (0, ""), (ran.stdout, ran.stderr)
    assert _report(ran) == _report(checked)
    assert _artifacts(root) - fresh == everything - fresh - LEFT_OUT
    validated = _kb("validate", cwd=root)
    assert (validated.returncode, validated.stdout, validated.stderr) == (0, "", ""), validated.stdout
    again = _kb("import", str(target), "--check", cwd=root)
    assert (again.returncode, again.stderr, _report(again)) == (1, "", _report(checked)), again.stdout

    type_file.write_text(sound, encoding="utf-8")
    mended = _kb("import", str(target), cwd=root, env={"KB_ACTOR": OPERATOR})
    assert (mended.returncode, mended.stderr, _report(mended)) == (0, "", []), (mended.stdout, mended.stderr)
    assert _artifacts(root) == everything
    assert _kb("validate", cwd=root).returncode == 0
