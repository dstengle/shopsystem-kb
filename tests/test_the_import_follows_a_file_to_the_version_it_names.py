"""The import's check follows each file to the version of its type that file names, and a type to each version it
refers to by a `kb:` reference, and to no other version of those types: what leads to a broken version's file is
skipped with its chain, what is read through another version of that type is checked and lands. Each directory is the
export of a store of its own, one version's file then broken; the check and the import are the operator's commands."""
from pathlib import Path

from calls import (
    TYPE_OF_TYPES, a_decision_type_and_a_decision, change_type, create, define, filed, iri, kb_ref, start_a_store,
    type_iri,
)
from conftest import OPERATOR, _kb, exported
import held

NOTE, DECISION = type_iri("note"), type_iri("decision")
WEEKLY = iri("decision", "price-reviews-happen-weekly")


def _note_schema(*fields):
    """A note type's schema: a title, the fields named, and a label other types may refer to."""
    properties = {name: {"type": "string"} for name in ("title", *fields)}
    return {"type": "object", "$defs": {"label": {"type": "string"}}, "properties": properties, "required": ["title"]}


def _referring_to_note(title, number):
    """A type whose label is the one a version of the note type declares, named by a `kb:` reference."""
    properties = {"title": {"type": "string"}, "label": {"$ref": kb_ref("note", number, "#/$defs/label")}}
    return {"title": title, "version": 1, "schema": {"type": "object", "properties": properties, "required": ["title"]}}


def _note_type_at(client, versions):
    """The note type defined and changed until it stands at the version given, a note made at each version named."""
    for number in range(1, max(versions) + 1):
        if number == 1:
            define(client, {"title": "Note", "version": 1, "schema": _note_schema("body")})
        else:
            changed = change_type(client, "note", _note_schema("body", *(f"field-{n}" for n in range(2, number + 1))))
            assert not changed.faults, changed.faults
        if number in versions:
            create(client, "note", {"title": f"At {number}", "body": "Count on Fridays."})


def _at(number):
    return iri("note", f"at-{number}")


def _broken(target, number):
    """The note type's file for a version given a schema of a type JSON Schema does not know."""
    file = Path(target) / filed(NOTE, number)
    text = file.read_text(encoding="utf-8")
    assert text.count("type: object") == 1, text
    file.write_text(text.replace("type: object", "type: objekt"), encoding="utf-8")
    return filed(NOTE, number)


def _commented(target, name):
    """An artifact's file with a comment written above it, so it is no longer the text kb writes. Returns the text it
    held."""
    file = Path(target) / filed(name)
    text = file.read_text(encoding="utf-8")
    file.write_text("# reviewed by hand\n" + text, encoding="utf-8")
    return text


def _checked(root, target):
    """The check's report of a directory: the files with an error, and each file skipped with its chain."""
    ran = _kb("import", str(target), "--check", cwd=root)
    assert (ran.returncode, ran.stderr) == (1, ""), (ran.stdout, ran.stderr)
    lines = [line.split("\t") for line in ran.stdout.splitlines()]
    assert {line[0] for line in lines} <= {"error", "skipped"}, ran.stdout
    errors = sorted({line[1] for line in lines if line[0] == "error"})
    return errors, {line[1]: line[2] for line in lines if line[0] == "skipped"}


def _chain(*files):
    return " -> ".join(files)


def _imported_with_errors_skipped(root, target):
    ran = _kb("import", str(target), "--skip-errors", cwd=root, env={"KB_ACTOR": OPERATOR})
    assert (ran.returncode, ran.stderr) == (0, ""), (ran.stdout, ran.stderr)


def test_a_note_at_a_broken_version_of_its_type_is_skipped_with_its_chain_and_the_rest_lands(root, tmp_path):
    def fill(client):
        _note_type_at(client, [1])
        a_decision_type_and_a_decision(client)

    target = exported(tmp_path, fill)
    broken = _broken(target, 1)
    start_a_store(root)

    assert _checked(root, target) == ([broken], {filed(_at(1)): _chain(filed(_at(1)), broken)})
    _imported_with_errors_skipped(root, target)

    assert held.names(root) == sorted([TYPE_OF_TYPES, DECISION, WEEKLY])
    for name, number in ((DECISION, 1), (WEEKLY, None)):
        assert held.text(root, name) == (target / filed(name, number)).read_text(encoding="utf-8")


def test_a_type_referring_by_a_kb_reference_to_a_broken_version_is_skipped_with_its_chain(root, tmp_path):
    def fill(client):
        _note_type_at(client, [2])
        define(client, _referring_to_note("Memo", 1))
        define(client, _referring_to_note("Letter", 2))
        create(client, "memo", {"title": "Stock is low", "label": "stock"})
        create(client, "letter", {"title": "To the supplier", "label": "orders"})

    target = exported(tmp_path, fill)
    broken = _broken(target, 1)
    memo_type, memo = filed(type_iri("memo"), 1), filed(iri("memo", "stock-is-low"))
    start_a_store(root)

    assert _checked(root, target) == ([broken], {
        memo_type: _chain(memo_type, broken), memo: _chain(memo, memo_type, broken),
    })
    _imported_with_errors_skipped(root, target)

    assert held.names(root) == sorted([
        TYPE_OF_TYPES, NOTE, _at(2), type_iri("letter"), iri("letter", "to-the-supplier"),
    ])
    assert held.versions(root)[NOTE] == [2]


def test_a_note_at_the_first_version_of_a_type_whose_second_is_broken_is_checked_and_lands(root, tmp_path):
    target = exported(tmp_path, lambda client: _note_type_at(client, [1, 2]))
    (target / filed(_at(2))).unlink()
    broken = _broken(target, 2)
    start_a_store(root)

    written = _commented(target, _at(1))
    assert _checked(root, target) == ([filed(_at(1)), broken], {})

    (target / filed(_at(1))).write_text(written, encoding="utf-8")
    assert _checked(root, target) == ([broken], {})
    _imported_with_errors_skipped(root, target)

    assert held.names(root) == sorted([TYPE_OF_TYPES, NOTE, _at(1)])
    assert held.versions(root)[NOTE] == [1]
    assert held.text(root, _at(1)) == written


def test_notes_at_the_other_versions_of_a_type_one_of_whose_ten_is_broken_are_checked_and_land(root, tmp_path):
    target = exported(tmp_path, lambda client: _note_type_at(client, [1, 2, 5, 10]))
    broken = _broken(target, 5)
    skipped = {filed(_at(5)): _chain(filed(_at(5)), broken)}
    start_a_store(root)

    for number in (1, 2, 10):
        written = _commented(target, _at(number))
        assert _checked(root, target) == (sorted([filed(_at(number)), broken]), skipped), number
        (target / filed(_at(number))).write_text(written, encoding="utf-8")

    assert _checked(root, target) == ([broken], skipped)
    _imported_with_errors_skipped(root, target)

    assert held.names(root) == sorted([TYPE_OF_TYPES, NOTE, _at(1), _at(2), _at(10)])
    assert held.versions(root)[NOTE] == [1, 2, 3, 4, 6, 7, 8, 9, 10]
    for number in (1, 2, 10):
        assert held.text(root, _at(number)) == (target / filed(_at(number))).read_text(encoding="utf-8")
