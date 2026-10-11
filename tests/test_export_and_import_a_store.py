"""Export and import a store, bound scenario by scenario as each slice comes in. The exported files are the operator's
output, read here as files; the store behind them is read through `held`."""
import copy
import re
from pathlib import Path

import pytest

from pytest_bdd import given, parsers, scenario, then, when
from ruamel.yaml import YAML

from calls import (
    DECISION_TYPE, NOTE_TYPE, TAG_TYPE, TYPE_OF_TYPES, TYPES, WORK_ITEM_TYPE, a_decision_type_and_a_decision, add, change_type, check,
    create, create_many, created, define, filed, iri, journal, kb_ref, listing, next_version, placeholders, read, refs, remove,
    replace, replace_many, replaced, request, start_a_store, targets, type_iri, version_iri,
)
from conftest import OPERATOR, _kb, exported
import held
import serving
from kb import canonical, client as kb_client, signatures, sqlite_store, store, values, write
from kb.content import dumps, loads
from kb.edits import Import
from kb.signatures import Signed

FEATURE = "export-and-import-a-store.feature"
IDENTITY = ["id", "type", "revision", "title"]


@scenario("export-and-import-a-store.feature", "Importing a directory holding an artifact the store already holds at the same IRI with other content or another type version is refused")
def test_importing_a_directory_holding_an_artifact_the_store_already_holds_at_the_same_ir():
    pass


@scenario("export-and-import-a-store.feature", "The operator checks a directory for import holding an artifact the store holds at the same IRI with other content or another type version")
def test_the_operator_checks_a_directory_for_import_holding_an_artifact_the_store_holds_a():
    pass


@scenario('export-and-import-a-store.feature', "The operator checks a directory for import that holds a type version's file with an error")
def test_the_operator_checks_a_directory_for_import_that_holds_a_type_version_s_file_with():
    pass


@scenario("export-and-import-a-store.feature", "The operator imports a directory holding a link to an IRI neither the directory nor the store holds, under a type one of them holds that the link field allows")
def test_the_operator_imports_a_directory_holding_a_link_to_an_iri_neither_the_directory():
    pass


@scenario("export-and-import-a-store.feature", "The operator imports a directory holding a link into a part that the artifact at its IRI lacks")
def test_the_operator_imports_a_directory_holding_a_link_into_a_part_that_the_artifact_lacks():
    pass


@scenario("export-and-import-a-store.feature", "The operator checks a directory for import holding a file whose IRI does not sit under its type")
def test_the_operator_checks_a_directory_for_import_holding_a_file_whose_iri_does_not_sit_under_its_type():
    pass


@scenario("export-and-import-a-store.feature", "Importing into a store a server serves is refused")
def test_importing_into_a_store_a_server_serves_is_refused():
    pass


@scenario("export-and-import-a-store.feature", "The operator imports a file holding an item that carries no name")
def test_the_operator_imports_a_file_holding_an_item_that_carries_no_name():
    pass


KEPT, NAMELESS = "kept-name", "Roll back"


@given("a store holding a type for decisions whose decisions carry options")
def _a_store_with_decisions_that_carry_options(root):
    """The store imported into holds the type; the directory, the export of a store holding it, brings the same
    version of it, which is passed over."""
    define(_started(root), DECISION_TYPE)


@given(
    "a directory for import that checks clean, holding a decision with one option that carries a name and one that "
    "carries none",
    target_fixture="target",
)
def _for_import_with_one_option_unnamed(tmp_path):
    def fill(client):
        define(client, DECISION_TYPE)
        create(client, "decision", {"title": "Price reviews", "sections": [
            {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
            {"title": "Rationale", "body": "Costs move weekly.\n"},
        ], "options": [{"id": KEPT, "title": "Keep"}, {"title": NAMELESS}]})

    target = _for_import(tmp_path, fill)
    file = Path(target) / _file(iri("decision", "price-reviews"))
    file.write_text(file.read_text(encoding="utf-8").replace("  - id: roll-back\n    title: Roll back", "  - title: Roll back"))
    assert "roll-back" not in file.read_text(encoding="utf-8")
    return target


@then("the option that carried a name lands with that name")
def _the_named_option_keeps_its_name(ran, root):
    assert (ran.returncode, ran.stderr) == (0, "")
    assert held.artifact(root, iri("decision", "price-reviews"))["options"][0]["id"] == KEPT


@then("the option that carried none lands with a name the store gives it")
def _the_unnamed_option_is_named(ran, root):
    options = held.artifact(root, iri("decision", "price-reviews"))["options"]
    assert list(options[1]) == ["id", "title"] and options[1]["id"] == "roll-back", options[1]


def _the_decision_file(tmp_path, options):
    """The export of a store holding the type for decisions and a decision, its file's options then written as given."""
    def fill(client):
        define(client, DECISION_TYPE)
        create(client, "decision", {"title": "Price reviews", "sections": [
            {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
            {"title": "Rationale", "body": "Costs move weekly.\n"},
        ]})

    target = _for_import(tmp_path, fill)
    file = Path(target) / _file(iri("decision", "price-reviews"))
    written = file.read_text(encoding="utf-8")
    file.write_text(written + "options:\n" + "".join(options), encoding="utf-8")
    return target


def test_an_item_an_import_names_is_named_where_a_create_names_it_and_written_where_a_create_writes_the_name(
    root, tmp_path,
):
    _started(root)
    target = _the_decision_file(tmp_path, ["  - title: Roll back\n", "  - title: Roll back\n"])
    checked = _kb("import", "--check", str(target), cwd=root, env={"KB_ACTOR": OPERATOR})
    assert (checked.returncode, _report(checked)[-1][0]) == (0, "clean"), checked.stdout
    assert _kb("import", str(target), cwd=root, env={"KB_ACTOR": OPERATOR}).returncode == 0
    options = held.artifact(root, iri("decision", "price-reviews"))["options"]
    assert [list(option) for option in options] == [["id", "title"], ["id", "title"]]
    assert [option["id"] for option in options] == ["roll-back", "roll-back-2"]


@pytest.mark.parametrize("options", [
    ["  - id: Not Plain\n    title: Keep\n"],
    ["  - id: kept\n    title: Keep\n", "  - id: kept\n    title: Again\n"],
], ids=["a name that is not plain", "a name carried twice"])
def test_a_name_a_file_gives_an_item_that_it_may_not_carry_is_an_error_of_the_check_and_nothing_lands(
    root, tmp_path, options,
):
    _started(root)
    target = _the_decision_file(tmp_path, options)
    checked = _kb("import", "--check", str(target), cwd=root, env={"KB_ACTOR": OPERATOR})
    errors = [line for line in _report(checked) if line[0] == "error"]
    assert (checked.returncode, [(line[1], line[2]) for line in errors]) == (
        1, [(_file(iri("decision", "price-reviews")), "item-name")],
    ), checked.stdout
    assert _kb("import", str(target), cwd=root, env={"KB_ACTOR": OPERATOR}).returncode != 0
    assert not held.holds_artifact(root, iri("decision", "price-reviews"))


@scenario("export-and-import-a-store.feature", "The operator imports a directory holding an artifact the store already holds at the same IRI, with the same content and the same type version")
def test_the_operator_imports_a_directory_holding_an_artifact_the_store_already_holds_at():
    pass


@scenario("export-and-import-a-store.feature", "The operator imports a directory that checks clean into a store, saying which role they are")
def test_the_operator_imports_a_directory_that_checks_clean_into_a_store_saying_which_rol():
    pass


# An import into a store that already holds artifacts (slice 181): what the store holds identically is passed over,
# with no import entry, and the rest lands.

def _import_into(root, target):
    """A directory checked for import into the store at root, found clean, then imported there."""
    checked = _kb("import", "--check", str(target), cwd=root, env={"KB_ACTOR": OPERATOR})
    assert (checked.returncode, _report(checked)[-1][0]) == (0, "clean"), checked.stdout
    ran = _kb("import", str(target), cwd=root, env={"KB_ACTOR": OPERATOR})
    assert (ran.returncode, ran.stderr, ran.stdout) == (0, "", ""), ran.stderr
    return ran


def _export_of(root, to):
    ran = _kb("export", str(to), cwd=root)
    assert (ran.returncode, ran.stderr) == (0, ""), ran.stderr
    return {file: (to / file).read_bytes() for file in _files(to)}


def test_a_stores_own_export_imported_into_it_lands_nothing_adds_no_history_entry_and_exports_the_same_bytes(
    root, tmp_path,
):
    client = _started(root)
    _decisions_and_a_work_item(client)
    _a_note_type_at_two_versions(client)
    files = _export_of(root, tmp_path / "exported")
    history = held.history(client)

    _import_into(root, tmp_path / "exported")

    assert held.history(client) == history
    assert _export_of(root, tmp_path / "exported-again") == files


def test_a_type_the_store_holds_gains_a_version_by_import_and_the_versions_it_keeps_are_passed_over(root, tmp_path):
    client = _started(root)
    define(client, {"title": "Note", "version": 1, "schema": _note_type("summary", "body")})
    create(client, "note", {"title": "Held", "summary": "It is held.", "body": "Before the import.\n"})
    note, target = type_iri("note"), _for_import(tmp_path, _a_note_type_at_two_versions)
    _put(target, {**_read(target, note, 2), "revision": 7, "title": "Memo"}, 2)

    _import_into(root, target)

    assert held.versions(root)[note] == [1, 2]
    standing = held.artifact(root, note)
    assert (standing["version"], standing["revision"], standing["title"]) == (2, 7, "Memo")
    assert canonical.dump(held.version(root, note, 1)) == (target / _file(note, 1)).read_text("utf-8")
    assert [(entry.artifact, entry.revision) for entry in _imported(root)] == [(note, 7)]
    assert held.artifact(root, iri("note", "held"))["type"] == version_iri("note", 1)


def test_an_import_lands_in_a_store_holding_other_artifacts_which_are_left_as_they_were(root, tmp_path):
    client = _started(root)
    define(client, {"title": "Note", "version": 1, "schema": _note_type("summary", "body")})
    create(client, "note", {"title": "Held", "summary": "It is held.", "body": "Before the import.\n"})
    before, history = held.names(root), held.history(client)
    target = _for_import(tmp_path)

    _import_into(root, target)

    assert held.names(root) == sorted([*before, *_exported_names(target)])
    assert held.history(client)[:len(history)] == history
    assert sorted(entry.artifact for entry in _imported(root)) == _exported_names(target)


DECIDED = iri("decision", "prices-follow-costs")


@given("a store holding a type for work items and a work item")
def _a_store_with_a_work_item(root):
    client = _started(root)
    define(client, WORK_ITEM_TYPE)
    create(client, "work-item", {"title": "Stands alone"})


@given(
    "a directory for import that checks clean, holding both versions of a type for decisions and a decision at "
    "revision 3 written against version 2 of the type for decisions",
    target_fixture="target",
)
def _for_import_with_a_decision_at_revision_3(tmp_path):
    def fill(client):
        define(client, DECISION_TYPE)
        assert not next_version(client, "decision", DECISION_TYPE).faults
        content = _decision(DECIDED)
        create(client, "decision", {"title": content["title"], "sections": content["sections"]})
        for body in ("Costs move monthly.\n", "Costs move daily.\n"):
            sections = [content["sections"][0], {"title": "Rationale", "body": body}]
            assert not replace(client, DECIDED, {"sections": sections}).faults

    target = _for_import(tmp_path, fill)
    assert _version_files(target, type_iri("decision")) == [_file(type_iri("decision"), number) for number in (1, 2)]
    decision = _read(target, DECIDED)
    assert (decision["revision"], decision["type"]) == (3, version_iri("decision", 2))
    return target


@then("the decision lands at the same IRI and with the same title, at revision 3, written against version 2 of the type for decisions")
def _the_decision_lands_as_it_was(root, target):
    landed, given = held.artifact(root, DECIDED), _read(target, DECIDED)
    assert (landed["id"], landed["title"]) == (DECIDED, given["title"])
    assert (landed["revision"], landed["type"]) == (3, version_iri("decision", 2))
    assert held.text(root, DECIDED) == (target / _file(DECIDED)).read_text(encoding="utf-8")


@then("the type for decisions lands at the same IRI and with the same title, at the revision and type version the directory gives it")
def _the_decision_type_lands_as_it_was(root, target):
    decision = type_iri("decision")
    landed, given = held.artifact(root, decision), _read(target, decision, 2)
    assert (landed["id"], landed["title"]) == (decision, given["title"])
    assert (landed["revision"], landed["type"], landed["version"]) == (given["revision"], given["type"], 2)
    for number in (1, 2):
        assert canonical.dump(held.version(root, decision, number)) == (target / _file(decision, number)).read_text("utf-8")


@given("a store holding a type for decisions and a decision")
def _a_store_with_a_decision(root, before):
    client = _started(root)
    a_decision_type_and_a_decision(client)
    before.update(decision=held.text(root, WEEKLY), history=held.history(client))


@given(
    "a directory for import that checks clean, holding that decision at the same IRI with the same content and the "
    "same type version, and a second decision",
    target_fixture="target",
)
def _for_import_with_the_held_decision_and_a_second(tmp_path):
    """The export of a store holding the two decisions, the held one's file given another revision, which is not
    compared; the type for decisions is the store's, and its file is taken out."""
    def fill(client):
        a_decision_type_and_a_decision(client)
        create(client, "decision", {"title": _titled(MONTHLY), "sections": _decision(MONTHLY)["sections"]})

    target = _for_import(tmp_path, fill)
    (target / _file(type_iri("decision"), 1)).unlink()
    _put(target, {**_read(target, WEEKLY), "revision": 5})
    return target


@then("the decision the store held is passed over, left as the store held it")
def _the_held_decision_is_passed_over(ran, root, before):
    assert (ran.returncode, ran.stderr) == (0, "")
    assert held.text(root, WEEKLY) == before["decision"]
    assert WEEKLY not in [entry.artifact for entry in held.history(kb_client.connect(root))[len(before["history"]):]]


@then("the second decision lands")
def _the_second_decision_lands(root, target, before):
    assert held.text(root, MONTHLY) == (target / _file(MONTHLY)).read_text(encoding="utf-8")
    gained = held.history(kb_client.connect(root))[len(before["history"]):]
    assert [(entry.op, entry.artifact) for entry in gained] == [("import", MONTHLY)]


def test_a_file_whose_item_carries_no_name_is_passed_over_when_it_is_imported_a_second_time(root, tmp_path):
    client = _started(root)
    target = _the_decision_file(tmp_path, ["  - title: Roll back\n"])
    _import_into(root, target)
    held_before, history = held.holds(root), held.history(client)

    _import_into(root, target)

    assert (held.holds(root), held.history(client)) == (held_before, history)


def test_a_file_that_differs_from_what_the_store_holds_at_its_iri_lands_nothing(root, tmp_path):
    client = _started(root)
    _decisions_and_a_work_item(client)
    target = tmp_path / "exported"
    _export_of(root, target)
    _put(target, {**_read(target, WEEKLY), "title": "Price reviews happen daily"})
    _put(target, _decision(iri("decision", "a-third")))
    before, history = held.holds(root), held.history(client)

    ran = _kb("import", str(target), cwd=root, env={"KB_ACTOR": OPERATOR})

    assert ran.returncode != 0
    assert (held.holds(root), held.history(client)) == (before, history)


LOOSE_NOTE = {"type": "object", "required": ["title"], "properties": {
    "title": {"type": "string"}, "summary": {"type": "string"}, "body": {"type": "string"},
    "flag": {}, "count": {}, "meta": {},
}}
HELD_NOTE = iri("note", "held")


def _properties_in_another_order(target):
    """The note type's version declaring its body before its summary: another order to write a note's entries in."""
    version = _read(target, type_iri("note"), 1)
    declared = version["schema"]["properties"]
    version["schema"]["properties"] = {name: declared[name] for name in ("title", "body", "summary", "flag", "count", "meta")}
    _put(target, version, 1)
    return {_file(type_iri("note"), 1): type_iri("note")}


def _a_number_where_the_store_holds_a_truth(target):
    _put(target, {**_read(target, HELD_NOTE), "flag": 1})
    return {_file(HELD_NOTE): HELD_NOTE}


def _a_fraction_where_the_store_holds_a_whole_number(target):
    _put(target, {**_read(target, HELD_NOTE), "count": 1.0})
    return {_file(HELD_NOTE): HELD_NOTE}


def _a_mapping_in_another_order(target):
    _put(target, {**_read(target, HELD_NOTE), "meta": {"a": 2, "b": 1}})
    return {_file(HELD_NOTE): HELD_NOTE}


def _differs_at(root, target, differing, others=()):
    """A directory checked for import into the store at root and then imported, with errors skipped and not: the
    check reports each file given as differing, naming its IRI, and the other errors given and no more; each import
    is refused naming each IRI once, in the order of names, shows the check's report, and lands nothing."""
    client = kb_client.connect(root)
    before, history = held.holds(root), held.history(client)
    checked = _kb("import", "--check", str(target), cwd=root)
    errors = [line for line in _report(checked) if line[0] == "error"]
    assert (checked.returncode, checked.stderr) == (1, ""), checked.stdout
    assert sorted((line[1], line[2]) for line in errors) == sorted(
        [*((file, "differs") for file in differing), *others],
    ), checked.stdout
    assert all(repr(differing[line[1]]) in line[3] for line in errors if line[2] == "differs"), checked.stdout
    for how in ((), ("--skip-errors",)):
        ran = _kb("import", *how, str(target), cwd=root, env={"KB_ACTOR": OPERATOR})
        refused = ran.stderr.splitlines()
        assert (ran.returncode, ran.stdout, len(refused)) == (2, checked.stdout, len(set(differing.values()))), ran.stderr
        for line, name in zip(refused, sorted(set(differing.values()))):
            assert line.startswith("kb import: refused: differs: ") and repr(name) in line, ran.stderr
        assert (held.holds(root), held.history(client)) == (before, history)


@pytest.mark.parametrize("differently", [
    _properties_in_another_order, _a_number_where_the_store_holds_a_truth,
    _a_fraction_where_the_store_holds_a_whole_number, _a_mapping_in_another_order,
], ids=lambda differently: differently.__name__.strip("_").replace("_", " "))
def test_a_file_written_other_than_the_store_would_write_what_it_holds_is_a_difference_and_nothing_lands(
    root, tmp_path, differently,
):
    client = _started(root)
    define(client, {"title": "Note", "version": 1, "schema": LOOSE_NOTE})
    create(client, "note", {"title": "Held", "flag": True, "count": 1, "meta": {"b": 1, "a": 2}})
    target = tmp_path / "exported"
    files = _export_of(root, target)
    differing = differently(target)
    assert {file: (target / file).read_bytes() for file in files} != files

    _differs_at(root, target, differing)


def test_a_file_with_only_its_revision_changed_is_not_a_difference(root, tmp_path):
    client = _started(root)
    _decisions_and_a_work_item(client)
    _a_note_type_at_two_versions(client)
    target = tmp_path / "exported"
    _export_of(root, target)
    _put(target, {**_read(target, WEEKLY), "revision": 7})
    _put(target, {**_read(target, type_iri("note"), 1), "revision": 9}, 1)
    before, history = held.holds(root), held.history(client)

    _import_into(root, target)

    assert (held.holds(root), held.history(client)) == (before, history)


def test_a_type_versions_file_that_differs_from_the_version_the_store_keeps_at_its_number_is_a_difference(
    root, tmp_path,
):
    client = _started(root)
    _a_note_type_at_two_versions(client)
    note, target = type_iri("note"), tmp_path / "exported"
    _export_of(root, target)
    _put(target, {**_read(target, note, 1), "title": "Memo"}, 1)
    _put(target, {**_artifact(iri("note", "new"), "New"), "type": version_iri("note", 2)})

    _differs_at(root, target, {_file(note, 1): note})
    assert not held.holds_artifact(root, iri("note", "new"))


def _a_note_type_at_three_versions(client):
    _a_note_type_at_two_versions(client)
    assert not change_type(client, "note", _note_type("body", "summary", "owner")).faults


def test_a_type_versions_file_numbered_below_the_version_the_stores_type_stands_at_that_it_does_not_keep_is_a_difference(
    root, tmp_path,
):
    """The store's type for notes keeps versions 1 and 3 (a directory brought it so); a directory then brings its
    version 2: the directory and the store disagree about that type's versions."""
    _started(root)
    note, target = type_iri("note"), _for_import(tmp_path, _a_note_type_at_three_versions)
    second = (target / _file(note, 2)).read_bytes()
    (target / _file(note, 2)).unlink()
    _import_into(root, target)
    assert held.versions(root)[note] == [1, 3]
    (target / _file(note, 2)).write_bytes(second)

    _differs_at(root, target, {_file(note, 2): note})
    assert held.versions(root)[note] == [1, 3]


def test_a_type_versions_file_above_the_stores_whose_revision_is_not_above_the_one_its_type_stands_at_is_a_difference(
    root, tmp_path,
):
    client = _started(root)
    define(client, {"title": "Note", "version": 1, "schema": _note_type("summary", "body")})
    note, target = type_iri("note"), _for_import(tmp_path, _a_note_type_at_two_versions)
    _put(target, {**_read(target, note, 2), "revision": held.artifact(root, note)["revision"]}, 2)

    _differs_at(root, target, {_file(note, 2): note})
    assert held.versions(root)[note] == [1]


def test_a_file_written_against_a_version_only_the_directory_brings_of_an_artifact_the_store_holds_is_a_difference(
    root, tmp_path,
):
    client = _started(root)
    define(client, {"title": "Note", "version": 1, "schema": _note_type("summary", "body")})
    create(client, "note", {"title": "Held", "summary": "It is held.", "body": "Before the import.\n"})
    note, target = type_iri("note"), tmp_path / "exported"
    _export_of(root, target)
    first = _read(target, note, 1)
    _put(target, {**first, "revision": 2, "version": 2, "schema": _note_type("summary", "body", "owner")}, 2)
    _put(target, {**_read(target, HELD_NOTE), "type": version_iri("note", 2)})

    _differs_at(root, target, {_file(HELD_NOTE): HELD_NOTE})
    assert held.versions(root)[note] == [1]


def test_a_difference_refuses_an_import_whatever_other_errors_the_directory_holds_which_stay_in_the_report(
    root, tmp_path,
):
    client = _started(root)
    _decisions_and_a_work_item(client)
    target = tmp_path / "exported"
    _export_of(root, target)
    _put(target, {**_read(target, WEEKLY), "title": "Price reviews happen daily"})
    unfit = _decision(THIRD)
    _put(target, {**unfit, "sections": unfit["sections"][:1]})

    _differs_at(root, target, {_file(WEEKLY): WEEKLY}, others=[(_file(THIRD), "sections")])


def test_with_errors_skipped_a_directory_whose_sound_files_the_store_all_holds_lands_nothing_and_is_not_refused(
    root, tmp_path,
):
    client = _started(root)
    _decisions_and_a_work_item(client)
    target = tmp_path / "exported"
    _export_of(root, target)
    unfit = _decision(THIRD)
    _put(target, {**unfit, "sections": unfit["sections"][:1]})
    before, history = held.holds(root), held.history(client)

    ran = _kb("import", "--skip-errors", str(target), cwd=root, env={"KB_ACTOR": OPERATOR})

    assert (ran.returncode, ran.stderr) == (0, ""), ran.stderr
    assert [line[:3] for line in _report(ran)] == [["error", _file(THIRD), "sections"]]
    assert (held.holds(root), held.history(client)) == (before, history)


@scenario(FEATURE, "The operator exports the store to a directory that is empty or does not exist")
def test_the_operator_exports_the_store():
    pass


@scenario(
    FEATURE, "An artifact that conforms to an earlier version of its type is exported in the order that version declares",
)
def test_an_artifact_conforming_to_an_earlier_version_is_exported_in_that_version_s_order():
    pass


@scenario(FEATURE, "A store holding an artifact behind its type comes back from its export as it was")
def test_a_store_holding_an_artifact_behind_its_type_comes_back_from_its_export_as_it_was():
    pass


@scenario(FEATURE, "The operator opens an exported artifact's file")
def test_the_operator_opens_an_exported_file():
    pass


@scenario(FEATURE, "Two stores given the same content by the same client are exported")
def test_two_stores_given_the_same_content_are_exported():
    pass


@scenario(FEATURE, "Exporting to a directory that holds anything is refused")
def test_exporting_to_a_directory_that_holds_anything_is_refused():
    pass


@scenario(FEATURE, "The operator checks a directory for import and each error is reported by file and reason")
def test_each_error_is_reported_by_file_and_reason():
    pass


@scenario(FEATURE, "The operator checks a directory for import that holds no error")
def test_a_clean_directory_is_said_to_be_clean():
    pass


@scenario(FEATURE, "A directory checked for import holds an error")
def test_a_directory_holding_an_error_fails_the_check():
    pass


@scenario(FEATURE, "The operator checks a directory for import and the store is left as it was")
def test_checking_leaves_the_store_as_it_was():
    pass


@scenario(FEATURE, "The operator checks a directory for import whose type that describes types differs from the store's")
def test_a_differing_type_of_types_is_an_error():
    pass


def _started(root):
    client = kb_client.connect(root)
    start_a_store(root)
    return client


def _loaded(text):
    """A file as a YAML 1.2 reader other than kb's reads it, its entries in the order written."""
    return YAML(typ="safe", pure=True).load(text)


@given("a store holding a type for decisions, a type for work items, two decisions and a work item")
def _store_with_decisions_and_a_work_item(root):
    _decisions_and_a_work_item(_started(root))


def _decisions_and_a_work_item(client):
    define(client, DECISION_TYPE)
    define(client, WORK_ITEM_TYPE)
    for title in ("Price reviews happen weekly", "Prices are reviewed monthly"):
        create(client, "decision", {"title": title, "sections": [
            {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
            {"title": "Rationale", "body": "Costs move weekly.\n"},
        ]})
    create(client, "work-item", {"title": "Move the review to Mondays", "decisions": [iri("decision", "price-reviews-happen-weekly")]})


@given(parsers.parse("a directory for the export that {state}"), target_fixture="target")
def _directory_for_the_export(tmp_path, state):
    target = tmp_path / "exported"
    if state == "is empty":
        target.mkdir()
    return target


@when("the operator exports the store to that directory", target_fixture="ran")
def _kb_export(root, target):
    return _kb("export", str(target), cwd=root)


def _files(target):
    return sorted(str(path.relative_to(target)) for path in Path(target).rglob("*") if path.is_file())


REVISED_DECISION_TYPE = {**DECISION_TYPE, "version": 2, "schema": {**DECISION_TYPE["schema"], "sections": [
    {"title": "Purpose"}, {"title": "Rationale"}, {"title": "Consequences"},
]}}
VERSIONS = {  # every version the outline's store holds of each type, with the revision and title it was made with
    TYPE_OF_TYPES: {1: (1, "Schema")},
    type_iri("decision"): {1: (1, "Decision"), 2: (2, "Decision")},
    type_iri("work-item"): {1: (1, "Work item")},
}


@given(
    "a store holding a type for decisions at two versions, a type for work items at one version, two decisions and "
    "a work item",
)
def _store_with_a_type_at_two_versions(root):
    client = _started(root)
    _decisions_and_a_work_item(client)
    revised = replace(client, type_iri("decision"), {key: REVISED_DECISION_TYPE[key] for key in ("version", "schema")})
    assert not revised.faults, revised.faults
    assert held.versions(root) == {name: list(numbers) for name, numbers in VERSIONS.items()}


def _version_files(target, name):
    """The files a directory holds at a type's place followed by `@`, sorted."""
    return [file for file in _files(target) if file.startswith(f"{_file(name)[:-len('.yaml')]}@")]


@then("the directory holds one file for each decision and for the work item, at a place that follows the path of its IRI")
def _one_file_for_each_artifact(ran, root, target):
    assert (ran.returncode, ran.stdout, ran.stderr) == (0, "", "")
    assert [file for file in _files(target) if "@" not in file] == sorted(_file(name) for name in (WEEKLY, MONTHLY, MONDAYS))


@then(
    "for each type the directory holds one file for each version the store holds and no other, at the type's place "
    "followed by @ and the version's number",
)
def _one_file_for_each_version(root, target):
    for name, numbers in VERSIONS.items():
        assert _version_files(target, name) == [_file(name, number) for number in numbers], name
    assert _files(target) == _held_files(root)


@then("each version's file gives that version's own revision and title")
def _each_version_its_own_revision_and_title(target):
    for name, numbers in VERSIONS.items():
        for number, made_with in numbers.items():
            written = _read(target, name, number)
            assert (written["version"], (written["revision"], written["title"])) == (number, made_with), (name, number)
    schemas = [_read(target, type_iri("decision"), number)["schema"] for number in (1, 2)]
    assert schemas == [DECISION_TYPE["schema"], REVISED_DECISION_TYPE["schema"]]


def _held_at(root, file):
    """What the store at root holds of the artifact, or the type's version, an export puts at a file's place."""
    name, _, number = ("https://" + file.removesuffix(".yaml")).partition("@")
    return held.version(root, name, int(number)) if number else held.artifact(root, name)


@then(
    "each file gives the artifact's identity first, its IRI, the IRI of the version of its type it conforms to, its "
    "revision and its title, and then its content",
)
def _identity_first(root, target):
    for file in _files(target):
        written, kept = _loaded((Path(target) / file).read_text(encoding="utf-8")), _held_at(root, file)
        assert list(written)[:len(IDENTITY)] == IDENTITY, file
        assert _file(written["id"]).removesuffix(".yaml") == file.removesuffix(".yaml").partition("@")[0], file
        assert written == kept and list(written)[len(IDENTITY):] == [key for key in kept if key not in IDENTITY], file
    assert _read(target, WEEKLY)["type"] == version_iri("decision", 1)
    assert {_read(target, name, number)["type"] for name, numbers in VERSIONS.items() for number in numbers} == {
        version_iri(TYPE_OF_TYPES, 1),
    }


@then("every file shows the store as it stood at one moment")
def _as_the_store_stood(root, target):
    for name in held.names(root):
        assert (Path(target) / _held_file(root, name)).read_text(encoding="utf-8") == held.text(root, name), name
    for file in _files(target):
        assert (Path(target) / file).read_text(encoding="utf-8") == canonical.dump(_held_at(root, file)), file


def _note_type(*fields):
    """The schema of a note type declaring the fields named, in that order, after its title."""
    properties = {name: {"type": "string"} for name in ("title", *fields)}
    return {"type": "object", "properties": properties, "required": ["title"]}


@given(
    "a store holding a note type whose first version declares a summary then a body and whose second declares the "
    "body then the summary",
)
def _store_with_a_note_type_at_two_versions(root):
    client = _started(root)
    define(client, {"title": "Note", "version": 1, "schema": _note_type("summary", "body")})
    changed = change_type(client, "note", _note_type("body", "summary"))
    assert not changed.faults, changed.faults
    assert held.versions(root)[type_iri("note")] == [1, 2]


@given("a note that conforms to the first version, with a summary and a body")
def _a_note_of_the_first_version(root):
    made = request(
        kb_client.connect(root), "note", "Stock count", {"body": "Count on Fridays.", "summary": "Weekly"}, version=1,
    )
    assert not made.faults, made.faults
    assert held.artifact(root, iri("note", "stock-count"))["type"] == version_iri("note", 1)


@then("the note's file gives its summary before its body")
def _summary_before_body(ran):
    assert (ran["ran"].returncode, ran["ran"].stderr) == (0, "")
    written = _loaded((ran["target"] / _file(iri("note", "stock-count"))).read_text(encoding="utf-8"))
    assert list(written) == [*IDENTITY, "summary", "body"]


LONG = (
    "Costs move weekly, so a monthly review leaves prices behind them for up to three weeks at a time, and every "
    "supplier we buy from changes its list on a Monday.\n"
)
LONG_TITLE = "Review on the first working day of each month, after the suppliers have sent their new price lists"


@given(
    "a store holding a decision whose purpose is one short line and which carries a list of options, exported to a "
    "directory",
    target_fixture="target",
)
def _decision_with_options_exported(root, tmp_path):
    client = _started(root)
    define(client, DECISION_TYPE)
    create(client, "decision", {
        "title": "Price reviews happen weekly",
        "sections": [{"title": "Purpose", "body": "Keep prices.\n"}, {"title": "Rationale", "body": LONG}],
        "options": [
            {"title": "Weekly", "body": "Review every Monday.\n"},
            {"title": LONG_TITLE, "body": "Review on the first.\n"},
        ],
    })
    target = tmp_path / "exported"
    ran = _kb("export", str(target), cwd=root)
    assert (ran.returncode, ran.stderr) == (0, ""), ran.stderr
    return target


@when("the operator opens the decision's exported file", target_fixture="opened")
def _open_the_decision(target):
    return (Path(target) / _file(iri("decision", "price-reviews-happen-weekly"))).read_text(encoding="utf-8")


def _bodies(value):
    """Every piece of prose in a file as read: each value under a `body` key, at any depth."""
    if isinstance(value, dict):
        return [found for key, item in value.items()
                for found in ([item] if key == "body" else _bodies(item))]
    if isinstance(value, list):
        return [found for item in value for found in _bodies(item)]
    return []


@then("every piece of prose stands as a block of its own, however short it is")
def _prose_as_blocks(opened):
    bodies = _bodies(_loaded(opened))
    assert "Keep prices.\n" in bodies and len(bodies) == 4
    assert len(re.findall(r"^ *(?:- )?body: \|\n", opened, re.MULTILINE)) == len(bodies)


@then("each list is written beneath the name it belongs to, indented under it")
def _lists_under_their_names(opened):
    lines = opened.splitlines()
    for key in ("sections", "options"):
        below = lines[lines.index(f"{key}:") + 1]
        assert below.startswith("  - "), (key, below)


@then("no line of prose has been broken to fit a width")
def _no_line_broken(opened):
    assert f"    {LONG.rstrip()}\n" in opened
    assert f"    title: {LONG_TITLE}\n" in opened


@then("nothing in the file tells a reader how to build a value")
def _no_tags(opened):
    assert not re.search(r"(^|[\s\[{,])!", opened)


@given(
    "two stores each given the same decision by the same client, and each exported to a directory of its own",
    target_fixture="targets",
)
def _two_stores_exported(tmp_path):
    targets = []
    for each in ("first", "second"):
        root = tmp_path / each
        root.mkdir()
        client = _started(root)
        define(client, DECISION_TYPE)
        create(client, "decision", {
            "title": "Price reviews happen weekly",
            "sections": [
                {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
                {"title": "Rationale", "body": "Costs move weekly.\n"},
            ],
            "options": [{"title": "Weekly", "body": "Review every Monday.\n"}],
        })
        target = tmp_path / f"{each}-exported"
        ran = _kb("export", str(target), cwd=root)
        assert (ran.returncode, ran.stderr) == (0, ""), ran.stderr
        targets.append(target)
    return targets


@when("the operator compares the two exported decision files", target_fixture="compared")
def _compare_the_decision_files(targets):
    return [(target / _file(iri("decision", "price-reviews-happen-weekly"))).read_bytes() for target in targets]


@then("the two files are the same, byte for byte")
def _same_bytes(compared):
    first, second = compared
    assert first.startswith(f"id: {iri('decision', 'price-reviews-happen-weekly')}\n".encode())
    assert first == second


@given("a directory that already holds a file", target_fixture="target")
def _directory_holding_a_file(tmp_path, before):
    target = tmp_path / "exported"
    written = target / _file(iri("decision", "price-reviews-happen-weekly"))
    written.parent.mkdir(parents=True)
    written.write_text("notes the export must not write over\n")
    before.update(target=held.everything_in(target))
    return target


@then("the export is rejected because export never overwrites")
def _rejected_as_never_overwriting(ran, target):
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr == f"kb export: refused: root: an export never overwrites; {str(target)!r} already holds something\n"


@then("what the directory holds is left as it was")
def _directory_as_it_was(target, before):
    assert held.everything_in(target) == before["target"]


# The operator's check of a directory for import. Each directory is a real export of a store of its own, then broken
# in the one way a step names; the files are the operator's input, written and read here as files.

WEEKLY = iri("decision", "price-reviews-happen-weekly")
MONTHLY = iri("decision", "prices-are-reviewed-monthly")
MONDAYS = iri("work-item", "move-the-review-to-mondays")


def _for_import(tmp_path, fill=None):
    """A directory for import: the export of a store holding the types for decisions and work items, two decisions and
    a work item linking to the first; or holding what `fill` gives a started store."""
    return exported(tmp_path, fill or _decisions_and_a_work_item)


def _file(name, version=None):
    """The file the export layout gives an artifact's IRI, or a type's version."""
    return filed(name, version)


def _read(target, name, version=None):
    return canonical.entries((Path(target) / _file(name, version)).read_text(encoding="utf-8"))


def _put(target, artifact, version=None):
    """An artifact written as an export writes it, in canonical form, at its place in the layout: a type at the place
    of the version given."""
    path = Path(target) / _file(artifact["id"], version)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical.dump(artifact), encoding="utf-8")


def _artifact(name, title, **content):
    """An artifact at its first revision, of the first version of the type whose IRI it sits under."""
    return {"id": name, "type": f"{name.rsplit('/', 1)[0]}@1", "revision": 1, "title": title, **content}


def _titled(name):
    """The title an artifact's name was made from."""
    return name.rsplit("/", 1)[1].replace("-", " ").capitalize()


def _decision(name, **fields):
    """A decision that fits its type, carrying the fields given."""
    return _artifact(name, _titled(name), **fields, sections=[
        {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
        {"title": "Rationale", "body": "Costs move weekly.\n"},
    ])


def _unreadable(target):
    for name in (WEEKLY, MONTHLY):
        (Path(target) / _file(name)).write_text(f"id: {name}\ntitle: [never closed\n", encoding="utf-8")
    return {_file(WEEKLY): "unreadable", _file(MONTHLY): "unreadable"}


def _not_canonical(target):
    """One file with a comment in it; the other with its title ahead of its name."""
    weekly = Path(target) / _file(WEEKLY)
    weekly.write_text("# reviewed by hand\n" + weekly.read_text(encoding="utf-8"), encoding="utf-8")
    monthly = Path(target) / _file(MONTHLY)
    lines = monthly.read_text(encoding="utf-8").splitlines(keepends=True)
    titled = [line for line in lines if line.startswith("title: ")]
    monthly.write_text("".join(titled + [line for line in lines if line not in titled]), encoding="utf-8")
    return {_file(WEEKLY): "content", _file(MONTHLY): "content"}


def _no_type_for_the_kind(target):
    for name in (iri("memo", "first-memo"), iri("memo", "second-memo")):
        _put(target, _artifact(name, _titled(name)))
    return {_file(iri("memo", "first-memo")): "kind", _file(iri("memo", "second-memo")): "kind"}


def _not_fitting(target):
    """One decision without the section its type requires second; the other pointing at a number."""
    weekly = _read(target, WEEKLY)
    weekly["sections"] = weekly["sections"][:1]
    _put(target, weekly)
    monthly = _read(target, MONTHLY)
    _put(target, {**{key: monthly[key] for key in IDENTITY}, "supersedes": 5, "sections": monthly["sections"]})
    return {_file(WEEKLY): "sections", _file(MONTHLY): "type"}


def _a_version_nobody_holds(target):
    """Both decisions said to conform to a third version of their type, which nobody holds."""
    for name in (WEEKLY, MONTHLY):
        _put(target, {**_read(target, name), "type": version_iri("decision", 3)})
    return {_file(WEEKLY): "version", _file(MONTHLY): "version"}


def _linking_under_a_type_nobody_holds(target):
    """Two work items whose links name IRIs under a type for memos, which nobody holds."""
    mondays = _read(target, MONDAYS)
    _put(target, {**mondays, "decisions": [WEEKLY, iri("memo", "first-memo")]})
    _put(target, _artifact(iri("work-item", "review-on-fridays"), "Review on Fridays", decisions=[iri("memo", "second-memo")]))
    return {_file(MONDAYS): "ref", _file(iri("work-item", "review-on-fridays")): "ref"}


FAULTS = {
    "cannot be read as YAML 1.2": _unreadable,
    "is not in canonical form": _not_canonical,
    "claims a type neither the directory nor the store holds": _no_type_for_the_kind,
    "conforms to a version of its type neither the directory nor the store holds": _a_version_nobody_holds,
    "has content that does not fit its type": _not_fitting,
    "carries a link to an IRI under a type neither the directory nor the store holds": _linking_under_a_type_nobody_holds,
}


@given(
    parsers.parse("a directory for import holding well-formed files and two files that each {fault}"),
    target_fixture="target",
)
def _for_import_with_two_faults(tmp_path, fault, broken):
    target = _for_import(tmp_path)
    broken.update(FAULTS[fault](target))
    return target


@pytest.fixture
def broken():
    """The files a Given broke, each with the rule it breaks."""
    return {}


@when("the operator checks the directory for import", target_fixture="ran")
def _kb_import_check(root, target):
    return _kb("import", str(target), "--check", cwd=root)


@given("a store holding a type for decisions and a type for work items")
def _a_store_with_the_two_types(root):
    client = _started(root)
    define(client, DECISION_TYPE)
    define(client, WORK_ITEM_TYPE)


@given(
    parsers.parse("a directory for import holding a work item whose IRI {sits}"),
    target_fixture="target",
)
def _for_import_with_a_misplaced_work_item(tmp_path, sits):
    """A directory holding a work item of the type for work items at an IRI that is not under that type's."""
    name = {
        "sits under the type for decisions": iri("decision", "move-the-review-to-mondays"),
        "sits under no type the directory or the store holds": iri("memo", "move-the-review-to-mondays"),
    }[sits]
    target = tmp_path / "import"
    target.mkdir()
    _put(target, {**_artifact(name, _titled(name)), "type": version_iri("work-item", 1)})
    return target


@then("that file is reported as an error, naming the file")
def _that_file_is_an_error(ran, target):
    (file,) = [path.relative_to(target).as_posix() for path in Path(target).rglob("*.yaml")]
    assert ran.stderr == ""
    assert ("error", file, "identity") in {tuple(line[:3]) for line in _report(ran)}, ran.stdout


THIRD = iri("decision", "prices-are-set-by-the-buyer")


def _two_decisions(client, rationale="Costs move weekly.\n"):
    """The two decisions, written against the version the type for decisions stands at."""
    for name in (WEEKLY, MONTHLY):
        create(client, "decision", {"title": _titled(name), "sections": [
            {"title": "Purpose", "body": "Keep prices in step with costs.\n"}, {"title": "Rationale", "body": rationale},
        ]})


def _decisions_at_two_versions(client):
    """The type for decisions defined and written back as its second version, which every decision of the first fits."""
    define(client, DECISION_TYPE)
    assert not next_version(client, "decision", DECISION_TYPE).faults


@given("a store holding a type for decisions at version 2 and two decisions written against version 2")
def _a_store_with_two_decisions_at_version_2(root, before):
    client = _started(root)
    _decisions_at_two_versions(client)
    _two_decisions(client)
    assert {held.artifact(root, name)["type"] for name in (WEEKLY, MONTHLY)} == {version_iri("decision", 2)}
    before.update(held=held.holds(root), history=held.history(client))


def _with_other_content_against_version_2(client):
    _decisions_at_two_versions(client)
    _two_decisions(client, rationale="Costs move daily.\n")


def _with_the_same_content_against_version_1(client):
    define(client, DECISION_TYPE)
    _two_decisions(client)


DIFFERENCES = {
    "with other content, written against version 2 of the type for decisions": (
        _with_other_content_against_version_2, version_iri("decision", 2),
    ),
    "with the same content, written against version 1 of the type for decisions": (
        _with_the_same_content_against_version_1, version_iri("decision", 1),
    ),
}


@given(
    parsers.re(
        r"a directory for import holding both decisions at the same IRIs, each (?P<difference>with .+? of the type for "
        r"decisions)(?P<third>, and a third decision the store does not hold)?"
    ),
    target_fixture="target",
)
def _for_import_with_two_differing_decisions(tmp_path, difference, third):
    """The export of a store of its own holding the two decisions as the row says, and the third when one is named."""
    differing, version = DIFFERENCES[difference]

    def fill(client):
        differing(client)
        if third:
            create(client, "decision", {"title": _titled(THIRD), "sections": _decision(THIRD)["sections"]})

    target = _for_import(tmp_path, fill)
    assert {_read(target, name)["type"] for name in (WEEKLY, MONTHLY)} == {version}
    assert (target / _file(THIRD)).exists() == bool(third)
    return target


@then("each of the two decisions is reported as an error, naming its IRI")
def _each_decision_differs(ran):
    assert ran.stderr == ""
    errors = {(line[1], line[2]): line[3] for line in _report(ran) if line[0] == "error"}
    for name in (WEEKLY, MONTHLY):
        assert name in errors.get((_file(name), "differs"), ""), ran.stdout


@then("the import is rejected, naming the IRI of each of the two decisions")
def _rejected_naming_each_decision(ran):
    refused = ran.stderr.splitlines()
    assert ran.returncode == 2 and len(refused) == 2, ran.stderr
    for line, name in zip(refused, (WEEKLY, MONTHLY)):
        assert line.startswith("kb import: refused: differs: ") and repr(name) in line, ran.stderr


@then("nothing lands, the third decision included")
def _nothing_lands_the_third_included(root, before):
    assert not held.holds_artifact(root, THIRD)
    assert (held.holds(root), held.history(kb_client.connect(root))) == (before["held"], before["history"])


MINOR, SITTING = iri("decision", "minor"), iri("decision", "minor/ship-weekly")


def _decision_content(title):
    """A decision as a user writes it: its title inside, the sections its type requires."""
    return {"title": title, "sections": _decision(WEEKLY)["sections"]}


def _a_type_file_over_a_held_decision(root, tmp_path):
    """A store holding the type for decisions and a decision under `minor`, and a directory for import holding a
    type for tags at `minor` and a decision at a place of its own."""
    client = _started(root)
    define(client, DECISION_TYPE)
    create(client, "decision", _decision_content("Ship weekly"), at=SITTING)

    def fill(source):
        define(source, DECISION_TYPE)
        assert not request(source, TYPES, "Minor", {"schema": TAG_TYPE["schema"]}, "Define Minor", at=MINOR).faults
        create(source, "decision", _decision_content("Price reviews happen weekly"))
    return exported(tmp_path, fill)


def test_a_types_file_standing_where_a_define_would_be_refused_is_an_error_of_the_check(root, tmp_path):
    target = _a_type_file_over_a_held_decision(root, tmp_path)

    ran = _kb("import", str(target), "--check", cwd=root)

    errors = {tuple(line[1:3]) for line in _report(ran) if line[0] == "error"}
    assert (_file(MINOR, 1), "identity") in errors, ran.stdout


def test_with_errors_skipped_a_types_file_standing_where_a_define_would_be_refused_is_left_out_and_the_rest_lands(
    root, tmp_path,
):
    target = _a_type_file_over_a_held_decision(root, tmp_path)

    ran = _kb("import", str(target), "--skip-errors", cwd=root, env={"KB_ACTOR": OPERATOR})

    assert (ran.returncode, ran.stderr) == (0, "")
    assert MINOR not in held.names(root) and WEEKLY in held.names(root), held.names(root)


def _report(ran):
    """The check's report, one line at a time, each split into its fields."""
    return [line.split("\t") for line in ran.stdout.splitlines()]


@then(parsers.parse("each of the two files is reported as an error, naming the file, with the reason that {reason}"))
def _each_reported_with_its_reason(ran, broken):
    errors = {(line[1], line[2]) for line in _report(ran) if line[0] == "error"}
    assert ran.stderr == ""
    for file, rule in broken.items():
        assert (file, rule) in errors, (file, rule, ran.stdout)


def _a_broken_decision_type(target):
    """The type for decisions with a version that is not a number, which the type that describes types refuses."""
    _put(target, {**_read(target, type_iri("decision"), 1), "version": "one"}, 1)
    return type_iri("decision")


@pytest.fixture
def files():
    """The files a Given put in a directory that an import leaves out, each with why: `error`, or the chain that leads
    from it to a broken file as the report writes it."""
    return {}


@given(
    "a directory for import in which every file is well formed, fits its type and links only to what is there",
    target_fixture="target",
)
def _for_import_clean(tmp_path):
    return _for_import(tmp_path)


@given("a directory for import holding one file whose content does not fit its type", target_fixture="target")
def _for_import_with_one_unfit_file(tmp_path):
    target = _for_import(tmp_path)
    weekly = _read(target, WEEKLY)
    weekly["sections"] = weekly["sections"][:1]
    _put(target, weekly)
    return target


@then("the check reports success")
def _check_reports_success(ran, target):
    assert (ran.returncode, ran.stderr) == (0, "")
    assert _report(ran) == [["clean", f"{target} checks clean for import"]]


@then("the check reports failure")
def _check_reports_failure(ran):
    assert (ran.returncode, ran.stderr) == (1, "")
    assert "clean" not in [line[0] for line in _report(ran)], ran.stdout


@given("a directory for import", target_fixture="target")
def _a_directory_for_import(tmp_path, root, before):
    target = _for_import(tmp_path)
    before.update(held=held.holds(root))
    return target


@then("the store holds what it held before")
def _store_as_before(ran, root, before):
    assert ran.returncode in (0, 1), ran.stderr
    assert held.holds(root) == before["held"]


@given("a freshly started store")
def _a_freshly_started_store(root, before):
    _started(root)
    before.update({"started": held.holds(root), "type of types": held.text(root, TYPE_OF_TYPES)})


@given(
    "a directory for import holding a copy of the type that describes types that differs from the store's",
    target_fixture="target",
)
def _for_import_with_a_differing_type_of_types(tmp_path):
    """A clean export whose copy of the type that describes types has a field of its own added."""
    target = _for_import(tmp_path)
    copy = _read(target, TYPE_OF_TYPES, 1)
    copy["schema"]["properties"]["owner"] = {"type": "string"}
    _put(target, copy, 1)
    return target


@then("the file holding that copy is reported as an error, naming the file")
def _the_copy_is_an_error(ran):
    assert ran.returncode == 1, ran.stderr
    assert [line[1] for line in _report(ran) if line[0] == "error"] == [_file(TYPE_OF_TYPES, 1)], ran.stdout


# The operator's import of a directory into a freshly started store. Each directory is, as for the check, a real
# export of a store of its own, broken where a step says; the store imported into is read through `held` and its
# history through the contract.

def _exported_names(target):
    """The IRI of every artifact a directory for import holds but the type that describes types, sorted: the host and
    path its file's place gives, a type's without its version."""
    files = [str(path.relative_to(target)) for path in Path(target).rglob("*.yaml")]
    return sorted(
        "https://" + file.removesuffix(".yaml").partition("@")[0] for file in files
        if file != _file(TYPE_OF_TYPES, 1) and "/" in file and file.split("/")[0] not in ("journal", ".git")
    )


def _held_file(root, name):
    """The file an export of the store at root gives an artifact it holds: a type's at the version it stands at."""
    artifact = held.artifact(root, name)
    return _file(name, artifact["version"] if artifact["type"].startswith(f"{TYPE_OF_TYPES}@") else None)


def _held_files(root):
    """The files an export of the store at root holds, sorted: one for every held version of every type, at the
    type's place with the version's number, and one for every other artifact."""
    versions = held.versions(root)
    return sorted(
        file for name in held.names(root)
        for file in ([_file(name, number) for number in versions[name]] if name in versions else [_file(name)])
    )


@when("the operator imports the directory, saying which role they are", target_fixture="ran")
def _kb_import(root, target):
    return _kb("import", str(target), cwd=root, env={"KB_ACTOR": OPERATOR})


def _imported(root):
    """The entries an import left in the store's history: the import's own, whatever the store held before it."""
    return [entry for entry in held.history(kb_client.connect(root)) if entry.op == "import"]


@then("everything in the directory lands as one set, signed by that role, with a message naming the directory")
def _lands_as_one_signed_set(ran, root, target):
    assert (ran.returncode, ran.stderr) == (0, "")
    assert set(_exported_names(target)) <= set(held.names(root))
    entries = _imported(root)
    assert sorted(entry.artifact for entry in entries) == _exported_names(target)
    assert {(entry.batch, entry.actor.role, entry.message) for entry in entries} == {
        (entries[0].batch, OPERATOR, f"import {target}"),
    }


def _a_note_type_at_two_versions(client):
    """A note type made and then changed, so the store holds two versions of it, and no note."""
    define(client, {"title": "Note", "version": 1, "schema": _note_type("summary", "body")})
    changed = change_type(client, "note", _note_type("body", "summary"))
    assert not changed.faults, changed.faults


def _import_into_a_fresh_store(root, target):
    start_a_store(root)
    ran = _kb("import", str(target), cwd=root, env={"KB_ACTOR": OPERATOR})
    assert (ran.returncode, ran.stderr) == (0, ""), ran.stderr


def test_a_directory_holding_two_versions_of_a_type_and_no_artifact_of_it_lands_each_as_its_file_gives_it(
    root, tmp_path,
):
    note, target = type_iri("note"), _for_import(tmp_path, _a_note_type_at_two_versions)
    assert _version_files(target, note) == [_file(note, 1), _file(note, 2)]

    _import_into_a_fresh_store(root, target)

    assert held.versions(root) == {TYPE_OF_TYPES: [1], note: [1, 2]}
    for number in (1, 2):
        assert canonical.dump(held.version(root, note, number)) == (target / _file(note, number)).read_text("utf-8")
    assert held.text(root, note) == (target / _file(note, 2)).read_text("utf-8")
    assert held.names(root) == sorted([TYPE_OF_TYPES, note])


def test_the_history_of_an_import_holds_one_entry_for_each_version_file_of_a_type_in_the_order_of_their_numbers(
    root, tmp_path,
):
    note, target = type_iri("note"), _for_import(tmp_path, _a_note_type_at_two_versions)

    _import_into_a_fresh_store(root, target)

    entries = _imported(root)
    assert [(entry.op, entry.artifact, entry.revision, entry.type) for entry in entries] == [
        ("import", note, 1, version_iri(TYPE_OF_TYPES, 1)), ("import", note, 2, version_iri(TYPE_OF_TYPES, 1)),
    ]
    assert len({entry.batch for entry in entries}) == 1 and len({entry.digest for entry in entries}) == 2


def test_version_files_of_a_type_land_with_the_revision_and_title_each_gives_the_type_standing_at_the_highest(
    root, tmp_path,
):
    note, target = type_iri("note"), _for_import(tmp_path, _a_note_type_at_two_versions)
    given = {1: (3, "Note"), 2: (7, "Memo")}
    for number, (revision, title) in given.items():
        _put(target, {**_read(target, note, number), "revision": revision, "title": title}, number)

    _import_into_a_fresh_store(root, target)

    assert held.versions(root)[note] == [1, 2]
    for number, (revision, title) in given.items():
        kept = held.version(root, note, number)
        assert (kept["version"], kept["revision"], kept["title"]) == (number, revision, title)
    standing = held.artifact(root, note)
    assert (standing["version"], standing["revision"], standing["title"]) == (2, 7, "Memo")
    assert [(entry.artifact, entry.revision) for entry in _imported(root)] == [(note, 3), (note, 7)]


def test_version_files_of_a_type_land_in_the_order_of_their_numbers_not_of_their_files_names(root, tmp_path):
    note, target = type_iri("note"), _for_import(tmp_path, _a_note_type_at_two_versions)
    for was, number in ((2, 10), (1, 2)):
        _put(target, {**_read(target, note, was), "version": number, "revision": number}, number)
    (target / _file(note, 1)).unlink()
    assert _version_files(target, note) == [_file(note, 10), _file(note, 2)]

    _import_into_a_fresh_store(root, target)

    assert held.versions(root)[note] == [2, 10]
    assert held.text(root, note) == (target / _file(note, 10)).read_text("utf-8")
    assert [(entry.artifact, entry.revision) for entry in _imported(root)] == [(note, 2), (note, 10)]


def test_a_type_at_two_versions_lands_beside_a_type_at_one_and_its_artifact(root, tmp_path):
    def fill(client):
        _a_note_type_at_two_versions(client)
        define(client, WORK_ITEM_TYPE)
        create(client, "work-item", {"title": "Stands alone"})

    note, target = type_iri("note"), _for_import(tmp_path, fill)

    _import_into_a_fresh_store(root, target)

    assert held.versions(root) == {TYPE_OF_TYPES: [1], note: [1, 2], type_iri("work-item"): [1]}
    assert [entry.artifact for entry in _imported(root)] == [
        note, note, type_iri("work-item"), iri("work-item", "stands-alone"),
    ]
    for file in _files(target):
        assert (target / file).read_text(encoding="utf-8") == canonical.dump(_held_at(root, file)), file


# The import reads each artifact through the version its file names (slice 165.6, decision 5). The note type here
# requires a summary at its first version and an owner, in the summary's place, at its second; its first version
# alone links a note to a decision.

def _a_note_schema(required, linking):
    about = {"type": "string"}
    if linking:
        about["ref"] = {"targets": targets("decision"), "cardinality": "one", "parts": False, "on_delete": "refuse"}
    properties = {"title": {"type": "string"}, "summary": {"type": "string"}, "owner": {"type": "string"}, "about": about}
    return {"type": "object", "properties": properties, "required": ["title", required]}


SUMMARISED = iri("note", "stock-count")


def _a_note_behind_its_type(client):
    """The type for decisions and a decision; a note type, a note of its first version, with a summary and no owner,
    about that decision, and then the note type's second version, which the note is left behind."""
    a_decision_type_and_a_decision(client)
    define(client, {"title": "Note", "version": 1, "schema": _a_note_schema("summary", linking=True)})
    create(client, "note", {"title": "Stock count", "summary": "Weekly", "about": WEEKLY})
    changed = change_type(client, "note", _a_note_schema("owner", linking=False))
    assert not changed.faults, changed.faults


def _check_for_import(root, target):
    start_a_store(root)
    return _kb("import", str(target), "--check", cwd=root)


def _errors(ran):
    return [(line[1], line[2]) for line in _report(ran) if line[0] == "error"]


def test_a_note_that_fits_the_version_its_file_names_and_not_the_latest_checks_clean_and_lands(root, tmp_path):
    target = _for_import(tmp_path, _a_note_behind_its_type)
    assert _read(target, SUMMARISED)["type"] == version_iri("note", 1)

    ran = _check_for_import(root, target)
    assert (ran.returncode, ran.stdout, ran.stderr) == (0, f"clean\t{target} checks clean for import\n", "")
    landed = _kb("import", str(target), cwd=root, env={"KB_ACTOR": OPERATOR})
    assert (landed.returncode, landed.stdout, landed.stderr) == (0, "", "")

    assert held.versions(root)[type_iri("note")] == [1, 2]
    assert held.text(root, SUMMARISED) == (target / _file(SUMMARISED)).read_text(encoding="utf-8")
    assert held.artifact(root, SUMMARISED)["type"] == version_iri("note", 1)


def test_a_note_that_fits_the_latest_version_and_not_the_one_its_file_names_is_reported_and_does_not_land(
    root, tmp_path,
):
    target = _for_import(tmp_path, _a_note_behind_its_type)
    note = _read(target, SUMMARISED)
    _put(target, {**{key: note[key] for key in IDENTITY}, "owner": "the shopkeeper", "about": WEEKLY})

    ran = _check_for_import(root, target)
    assert (ran.returncode, ran.stderr) == (1, "")
    assert _errors(ran) == [(_file(SUMMARISED), "required")], ran.stdout
    refused = _kb("import", str(target), cwd=root, env={"KB_ACTOR": OPERATOR})
    assert refused.returncode == 2 and held.names(root) == [TYPE_OF_TYPES]


def test_a_file_naming_a_version_of_its_type_neither_the_directory_nor_the_store_holds_is_an_error_of_the_check(
    root, tmp_path,
):
    target = _for_import(tmp_path, _a_note_behind_its_type)
    _put(target, {**_read(target, SUMMARISED), "type": version_iri("note", 3)})

    ran = _check_for_import(root, target)
    assert (ran.returncode, ran.stderr) == (1, "")
    assert [line for line in _report(ran) if line[0] == "error"] == [[
        "error", _file(SUMMARISED), "version",
        "an artifact conforms to a version of its type the directory or the store holds; neither holds "
        f"{version_iri('note', 3)!r}",
    ]], ran.stdout
    refused = _kb("import", str(target), cwd=root, env={"KB_ACTOR": OPERATOR})
    assert refused.returncode == 2 and held.names(root) == [TYPE_OF_TYPES]


def test_a_link_in_a_field_only_the_version_a_file_names_reads_as_a_link_lands_as_one(root, tmp_path):
    target = _for_import(tmp_path, _a_note_behind_its_type)

    _import_into_a_fresh_store(root, target)

    client = kb_client.connect(root)
    assert [each.stub.id for each in refs(client, WEEKLY, 1, inward=True).reached] == [SUMMARISED]
    refused = remove(client, WEEKLY)
    assert [(fault.rule, fault.artifact) for fault in refused.faults] == [("on_delete", SUMMARISED)], refused.faults


def test_a_link_to_nothing_in_a_field_only_the_version_a_file_names_reads_as_a_link_is_reported(root, tmp_path):
    target = _for_import(tmp_path, _a_note_behind_its_type)
    _put(target, {**_read(target, SUMMARISED), "about": iri("tag", "nothing-by-this-name")})

    ran = _check_for_import(root, target)
    assert (ran.returncode, _errors(ran)) == (1, [(_file(SUMMARISED), "ref")]), ran.stdout


def _versions_2_and_10(target):
    """The note type's two version files renumbered, the first to 2 and the second to 10, so the file of the higher
    version comes first by name, and the note left at what is now version 2."""
    note = type_iri("note")
    for was, number in ((2, 10), (1, 2)):
        _put(target, {**_read(target, note, was), "version": number, "revision": number}, number)
    (target / _file(note, 1)).unlink()
    assert _version_files(target, note) == [_file(note, 10), _file(note, 2)]
    _put(target, {**_read(target, SUMMARISED), "type": version_iri("note", 2)})


def test_each_note_is_checked_through_the_version_its_file_names_whatever_order_the_versions_files_come_in(
    root, tmp_path,
):
    target = _for_import(tmp_path, _a_note_behind_its_type)
    _versions_2_and_10(target)
    owned = iri("note", "till-float")
    _put(target, {"id": owned, "type": version_iri("note", 10), "revision": 1, "title": "Till float", "owner": "Ada"})

    ran = _check_for_import(root, target)
    assert (ran.returncode, ran.stdout, ran.stderr) == (0, f"clean\t{target} checks clean for import\n", "")
    landed = _kb("import", str(target), cwd=root, env={"KB_ACTOR": OPERATOR})
    assert (landed.returncode, landed.stderr) == (0, "")

    assert held.versions(root)[type_iri("note")] == [2, 10]
    assert held.artifact(root, type_iri("note"))["version"] == 10
    assert [held.artifact(root, name)["type"] for name in (SUMMARISED, owned)] == [
        version_iri("note", 2), version_iri("note", 10),
    ]
    assert list(check(kb_client.connect(root)).violations) == []


def test_versions_of_a_type_a_set_imports_out_of_the_order_of_their_numbers_leave_it_standing_at_the_highest(
    root, tmp_path,
):
    target = _for_import(tmp_path, _a_note_behind_its_type)
    _versions_2_and_10(target)
    note = type_iri("note")
    start_a_store(root)
    files = [(note, 10), (type_iri("decision"), 1), (note, 2), (WEEKLY, None), (SUMMARISED, None)]
    operations = [Import(values.artifact_id(name), _read(target, name, number)) for name, number in files]

    with store.opened(root) as opened:
        write.land(opened, operations, Signed(signatures.Actor(OPERATOR, ""), "import out of order"))

    assert held.versions(root)[note] == [2, 10]
    assert held.text(root, note) == (target / _file(note, 10)).read_text("utf-8")
    assert [(entry.artifact, entry.revision) for entry in _imported(root)][:3] == [
        (note, 2), (type_iri("decision"), 1), (note, 10),
    ]
    assert [each.stub.id for each in refs(kb_client.connect(root), WEEKLY, 1, inward=True).reached] == [SUMMARISED]


@scenario(
    FEATURE,
    "The operator imports a directory that checks clean, and the history shows each type landing before its artifacts",
)
def test_each_type_lands_before_its_artifacts():
    pass


@given("a store holding a type for notes and a note")
def _a_store_with_a_note(root, before):
    client = _started(root)
    define(client, {"title": "Note", "version": 1, "schema": _note_type("summary", "body")})
    create(client, "note", {"title": "Held", "summary": "It is held.", "body": "Before the import.\n"})
    before.update(history=held.history(client))


@given(
    "a directory for import that checks clean, holding a type for decisions at two versions, a type for work items at "
    "one version, two decisions and a work item",
    target_fixture="target",
)
def _for_import_with_six_files(tmp_path):
    def fill(client):
        _decisions_and_a_work_item(client)
        assert not next_version(client, "decision", DECISION_TYPE).faults

    target = _for_import(tmp_path, fill)
    assert [file for file in _files(target) if file != _file(TYPE_OF_TYPES, 1)] == sorted([
        _file(type_iri("decision"), 1), _file(type_iri("decision"), 2), _file(type_iri("work-item"), 1),
        _file(WEEKLY), _file(MONTHLY), _file(MONDAYS),
    ])
    return target


@then("the store's history gains one import entry for each of the six files")
def _one_import_entry_for_each_file(ran, root, target, before):
    assert (ran.returncode, ran.stderr) == (0, "")
    history = held.history(kb_client.connect(root))
    assert history[:len(before["history"])] == before["history"]
    gained = history[len(before["history"]):]
    assert {entry.op for entry in gained} == {"import"}
    assert sorted(entry.artifact for entry in gained) == sorted([
        type_iri("decision"), type_iri("decision"), type_iri("work-item"), WEEKLY, MONTHLY, MONDAYS,
    ])


@then("in the history every import entry of a type comes before the import entries of the artifacts of its kind")
def _types_first(root):
    landed = [entry.artifact for entry in _imported(root)]
    for kind in ("decision", "work-item"):
        of_type = [index for index, name in enumerate(landed) if name == type_iri(kind)]
        of_kind = [index for index, name in enumerate(landed) if name.startswith(f"{type_iri(kind)}/")]
        assert of_type and of_kind and max(of_type) < min(of_kind), landed


@scenario(FEATURE, "Importing a directory that holds an error is refused")
def test_importing_a_directory_holding_an_error_is_refused():
    pass


@then("the import is rejected because the check found errors")
def _rejected_as_the_check_found_errors(ran):
    assert ran.returncode == 2
    assert ran.stderr == (
        "kb import: refused: content: the check found 1 error(s) in the directory, and nothing was written\n"
    )


@then("the operator is shown the check's report")
def _shown_the_report(ran, root, target):
    assert ["error", _file(WEEKLY), "sections"] in [line[:3] for line in _report(ran)], ran.stdout
    assert ran.stdout == _kb("import", str(target), "--check", cwd=root).stdout


@then("nothing is written")
def _nothing_written(root, before):
    assert held.holds(root) == before["started"]


@scenario(FEATURE, "The operator imports with errors skipped")
def test_importing_with_errors_skipped():
    pass


STANDALONE = iri("work-item", "stands-alone")
DECISIONS = type_iri("decision")
AT_TWO = iri("decision", "review-prices-on-fridays")
LINKING_UNDER = iri("work-item", "find-the-decision")
NOTES, NOTE = _file(type_iri("note"), 1), _file(iri("note", "stock-is-low"))  # files, as the report names them
TASKS, TASK = _file(type_iri("task"), 1), _file(iri("task", "count-the-stock"))


def _sections(*titles):
    return [{"title": title, "body": "Costs move weekly.\n"} for title in titles]


def _decisions_at(client, number):
    """The type for decisions defined, and revised when it is to stand at version 2."""
    define(client, DECISION_TYPE)
    if number == 2:
        revised = replace(client, DECISIONS, {key: REVISED_DECISION_TYPE[key] for key in ("version", "schema")})
        assert not revised.faults, revised.faults


def _a_decision_of_the_type(client):
    """A decision conforming to the version the type for decisions stands at."""
    create(client, "decision", {
        "title": "Review prices on Fridays", "sections": _sections("Purpose", "Rationale", "Consequences"),
    })


def _breaks(target, name, number):
    """A type version's file given a schema of a type JSON Schema does not know, so its content does not fit the type
    that describes types. Returns the file."""
    version = _read(target, name, number)
    version["schema"]["type"] = "objekt"
    _put(target, version, number)
    return _file(name, number)


def _a_work_item_linking_under_the_type(client):
    """The type for work items, and a work item whose link names an IRI under the type for decisions that nothing
    holds."""
    define(client, WORK_ITEM_TYPE)
    create(client, "work-item", {"title": "Find the decision", "decisions": [iri("decision", "not-anywhere")]})


def _referring_to(title, kind, number):
    """A type whose label is the title a version of another kind's type declares, named by a `kb:` reference."""
    properties = {"title": {"type": "string"}, "label": {"$ref": kb_ref(kind, number, "#/properties/title")}}
    return {"title": title, "version": 1, "schema": {"type": "object", "properties": properties, "required": ["title"]}}


def _notes_of(number):
    """What gives a store version 1 of a type for notes, which refers to that version of the type for decisions, and
    a note conforming to it."""
    def fill(client):
        define(client, _referring_to("Note", "decision", number))
        create(client, "note", {"title": "Stock is low", "label": "stock"})
    return fill


def _tasks_of(number):
    """What gives a store version 1 of a type for notes, which refers to that version of the type for decisions,
    version 1 of a type for tasks, which refers to it, and a task conforming to that."""
    def fill(client):
        define(client, _referring_to("Note", "decision", number))
        define(client, _referring_to("Task", "note", 1))
        create(client, "task", {"title": "Count the stock", "label": "count"})
    return fill


LEADING = {  # what each row's source store is given beside the type for decisions, standing at version 2
    "a decision conforming to version 2 of the type for decisions": _a_decision_of_the_type,
    "a type for work items whose link field allows decisions, and a work item whose link names an IRI under the type "
    "for decisions": _a_work_item_linking_under_the_type,
    "version 1 of a type for notes, which refers to version 2 of the type for decisions by a kb: reference, and a "
    "note conforming to version 1 of the type for notes": _notes_of(2),
    "version 1 of a type for notes, which refers to version 2 of the type for decisions by a kb: reference, version "
    "1 of a type for tasks, which refers to version 1 of the type for notes by a kb: reference, and a task "
    "conforming to version 1 of the type for tasks": _tasks_of(2),
}


@given(
    parsers.parse(
        "a directory for import holding version 2 of a type for decisions, whose content does not fit the type that "
        "describes types, and {leading}"
    ),
    target_fixture="target",
)
def _for_import_with_a_broken_version_and_what_leads_to_it(tmp_path, leading, files):
    def fill(client):
        _decisions_at(client, 2)
        LEADING[leading](client)

    target = _for_import(tmp_path, fill)
    (Path(target) / _file(DECISIONS, 1)).unlink()
    files[_breaks(target, DECISIONS, 2)] = "error"
    return target


SKIPPED = {  # each file a row says would be skipped, with the files its chain passes before the broken one
    "the decision is": [(_file(AT_TWO),)],
    "the work item is": [(_file(LINKING_UNDER),)],
    "version 1 of the type for notes and the note are": [(NOTES,), (NOTE, NOTES)],
    "version 1 of the type for notes, version 1 of the type for tasks and the task are": [
        (NOTES,), (TASKS, NOTES), (TASK, TASKS, NOTES),
    ],
}


@then(parsers.parse(
    "{skipped} reported as a file that would be skipped, each with the chain that leads from it to the broken file"
))
def _reported_as_skipped_with_its_chain(ran, files, skipped):
    (broken,) = files
    assert (ran.returncode, ran.stderr) == (1, ""), ran.stderr
    assert {line[1] for line in _report(ran) if line[0] == "error"} == {broken}, ran.stdout
    assert {line[1]: line[2] for line in _report(ran) if line[0] == "skipped"} == {
        chain[0]: " -> ".join((*chain, broken)) for chain in SKIPPED[skipped]
    }, ran.stdout


BROKEN, SECOND = iri("decision", "broken"), iri("decision", "second")


def _a_decision_with_an_error_and_one_linking(tmp_path):
    """A decision missing the section its type requires second, and a second decision that supersedes it."""
    def fill(client):
        _decisions_at(client, 1)
        define(client, WORK_ITEM_TYPE)
        create(client, "work-item", {"title": "Stands alone"})
        create(client, "decision", {"title": "Broken", "sections": _sections("Purpose", "Rationale")})
        create(client, "decision", {"title": "Second", "supersedes": BROKEN, "sections": _sections("Purpose", "Rationale")})

    target = _for_import(tmp_path, fill)
    broken = _read(target, BROKEN)
    _put(target, {**broken, "sections": broken["sections"][:1]})
    return target, {_file(BROKEN): "error"}


def _a_broken_second_version_and_a_decision_linked_to(tmp_path):
    """The type for decisions at two versions, the second broken, a decision conforming to the second, and the work
    item linking to that decision."""
    def fill(client):
        _decisions_at(client, 2)
        _a_decision_of_the_type(client)
        define(client, WORK_ITEM_TYPE)
        create(client, "work-item", {"title": "Stands alone", "decisions": [AT_TWO]})

    target = _for_import(tmp_path, fill)
    broken = _breaks(target, DECISIONS, 2)
    return target, {broken: "error", _file(AT_TWO): f"{_file(AT_TWO)} -> {broken}"}


def _a_broken_only_version_and(leading, *chains):
    """What makes a directory holding the type for decisions at its one version, broken, the type for work items, the
    work item, and what a row says leads to the broken version: the files left out, each chain given without the
    broken file it ends at."""
    def made(tmp_path):
        def fill(client):
            _decisions_at(client, 1)
            define(client, WORK_ITEM_TYPE)
            create(client, "work-item", {"title": "Stands alone"})
            leading(client)

        target = _for_import(tmp_path, fill)
        broken = _breaks(target, DECISIONS, 1)
        return target, {broken: "error", **{chain[0]: " -> ".join((*chain, broken)) for chain in chains}}
    return made


def _a_second_work_item_linking_under_the_type(client):
    create(client, "work-item", {"title": "Find the decision", "decisions": [iri("decision", "not-anywhere")]})


TOGETHER_WITH = {
    "version 1 of a type for decisions whose content does not fit the type that describes types, and a second work "
    "item whose link names an IRI under the type for decisions":
        _a_broken_only_version_and(_a_second_work_item_linking_under_the_type, (_file(LINKING_UNDER),)),
    "version 1 of a type for decisions whose content does not fit the type that describes types, version 1 of a type "
    "for notes, which refers to it by a kb: reference, and a note conforming to version 1 of the type for notes":
        _a_broken_only_version_and(_notes_of(1), (NOTES,), (NOTE, NOTES)),
    "version 1 of a type for decisions whose content does not fit the type that describes types, version 1 of a type "
    "for notes, which refers to it by a kb: reference, version 1 of a type for tasks, which refers to that one by a "
    "kb: reference, and a task conforming to version 1 of the type for tasks":
        _a_broken_only_version_and(_tasks_of(1), (NOTES,), (TASKS, NOTES), (TASK, TASKS, NOTES)),
    "version 1 of a type for decisions, version 2 of it whose content does not fit the type that describes types, "
    "and a decision conforming to version 2 that the work item links to":
        _a_broken_second_version_and_a_decision_linked_to,
    "a type for decisions, a decision with an error, and a second decision that links to it":
        _a_decision_with_an_error_and_one_linking,
}


@given(
    parsers.parse(
        "a directory for import holding a type for work items whose link field allows decisions, and a work item, "
        "together with {broken}"
    ),
    target_fixture="target",
)
def _for_import_with_errors_to_skip(tmp_path, broken, files):
    target, left_out = TOGETHER_WITH[broken](tmp_path)
    files.update(left_out)
    return target


@when("the operator imports the directory with errors skipped, saying which role they are", target_fixture="ran")
def _kb_import_skipping_errors(root, target):
    return _kb("import", str(target), "--skip-errors", cwd=root, env={"KB_ACTOR": OPERATOR})


@then("the type for work items and the work item land")
def _the_work_item_lands(ran, root, target):
    assert (ran.returncode, ran.stderr) == (0, "")
    for name in (type_iri("work-item"), STANDALONE):
        assert held.text(root, name) == (Path(target) / _held_file(root, name)).read_text(encoding="utf-8")


LEFT_OUT = {
    "the decision with an error": [_file(BROKEN)],
    "the type version and the second work item": [_file(DECISIONS, 1), _file(LINKING_UNDER)],
    "the two type versions and the note": [_file(DECISIONS, 1), NOTES, NOTE],
    "the three type versions and the task": [_file(DECISIONS, 1), NOTES, TASKS, TASK],
    "version 2 of the type for decisions and the decision": [_file(DECISIONS, 2), _file(AT_TWO)],
}


def _directory_files(target):
    """Every file a directory for import holds but its copy of the type that describes types, sorted."""
    found = sorted(str(path.relative_to(target)) for path in Path(target).rglob("*.yaml"))
    return [file for file in found if file != _file(TYPE_OF_TYPES, 1)]


def _iri_of(file):
    """The IRI of the artifact a file's place gives: a type's, without its version."""
    return "https://" + file.removesuffix(".yaml").partition("@")[0]


@then(parsers.parse("{left_out} do not land"))
def _left_out(root, target, files, left_out):
    assert sorted(LEFT_OUT[left_out]) == sorted(files)
    landing = [file for file in _directory_files(target) if file not in files]
    assert _held_files(root) == sorted([*landing, _file(TYPE_OF_TYPES, 1)])
    assert sorted(entry.artifact for entry in _imported(root)) == sorted(_iri_of(file) for file in landing)


def _waiting(root):
    """Each IRI a link in the store waits on, with the artifacts whose links wait there."""
    asked = placeholders(kb_client.connect(root))
    assert not asked.faults, asked.faults
    return {each.id: [link.artifact for link in each.links] for each in asked.placeholders}


@then("the second decision lands, its link landing on a placeholder at the IRI of the decision with an error")
def _the_second_decision_waits_on_the_broken_one(root, target):
    assert held.text(root, SECOND) == (Path(target) / _file(SECOND)).read_text(encoding="utf-8")
    assert _waiting(root) == {BROKEN: [SECOND]}


@then("the work item's link to the decision lands on a placeholder at the decision's IRI")
def _the_work_item_waits_on_the_decision(root):
    assert _waiting(root) == {AT_TWO: [STANDALONE]}


@then("every other file in the directory lands")
def _every_other_file_lands(root, target, files):
    landed = [file for file in _directory_files(target) if file not in files]
    assert landed and _waiting(root) == {}
    for file in landed:
        name = _iri_of(file)
        assert file == _held_file(root, name)
        assert held.text(root, name) == (Path(target) / file).read_text(encoding="utf-8")


@then("the operator is told what was skipped and why")
def _told_what_was_skipped(ran, files):
    told = {
        line[1]: "error" if line[0] == "error" else line[2] for line in _report(ran) if line[0] in ("error", "skipped")
    }
    assert told == files, ran.stdout


def _checked_row(leading):
    return lambda tmp_path: (_for_import_with_a_broken_version_and_what_leads_to_it(tmp_path, leading, {}), None)


@pytest.mark.parametrize("made", [*map(_checked_row, LEADING), *TOGETHER_WITH.values()], ids=[
    *(f"check row {number}" for number in range(1, len(LEADING) + 1)),
    *(f"import row {number}" for number in range(1, len(TOGETHER_WITH) + 1)),
])
def test_what_the_check_calls_an_error_or_a_skip_is_what_an_import_with_errors_skipped_leaves_out(root, tmp_path, made):
    target, _ = made(tmp_path)
    _started(root)
    report = _report(_kb("import", str(target), "--check", cwd=root))
    left_out = {line[1] for line in report if line[0] in ("error", "skipped")}
    landing = [file for file in _directory_files(target) if file not in left_out]

    ran = _kb_import_skipping_errors(root, target)

    assert (ran.returncode, ran.stderr) == (0, "") if landing else (
        2, "kb import: refused: operations: nothing in the directory would land, and nothing was written\n",
    )
    assert _held_files(root) == sorted([*landing, _file(TYPE_OF_TYPES, 1)])


def _skips(root, target):
    """The files the check says would be skipped, each with its chain."""
    return {line[1]: line[2] for line in _report(_kb("import", str(target), "--check", cwd=root)) if line[0] == "skipped"}


def test_a_file_skipped_for_its_link_names_the_broken_version_of_that_type_with_the_lowest_number(root, tmp_path):
    def fill(client):
        _decisions_at(client, 2)
        _a_work_item_linking_under_the_type(client)

    target = _for_import(tmp_path, fill)
    first, _ = (_breaks(target, DECISIONS, number) for number in (1, 2))
    _started(root)

    assert _skips(root, target) == {_file(LINKING_UNDER): f"{_file(LINKING_UNDER)} -> {first}"}


def test_a_link_under_a_type_the_store_holds_is_not_skipped_though_no_version_of_it_would_land(root, tmp_path):
    def fill(client):
        _decisions_at(client, 2)
        _a_work_item_linking_under_the_type(client)

    target = _for_import(tmp_path, fill)
    (Path(target) / _file(DECISIONS, 1)).unlink()
    _breaks(target, DECISIONS, 2)
    define(_started(root), DECISION_TYPE)

    assert _skips(root, target) == {}


def test_a_link_under_a_type_only_the_store_holds_lands_on_a_placeholder_with_errors_skipped_as_the_check_says(
    root, tmp_path,
):
    def fill(client):
        _decisions_at(client, 2)
        _a_work_item_linking_under_the_type(client)

    target = _for_import(tmp_path, fill)
    (Path(target) / _file(DECISIONS, 1)).unlink()
    broken = _breaks(target, DECISIONS, 2)
    define(_started(root), DECISION_TYPE)
    report = _report(_kb("import", str(target), "--check", cwd=root))

    ran = _kb_import_skipping_errors(root, target)

    assert {line[1] for line in report if line[0] in ("error", "skipped")} == {broken}, report
    assert (ran.returncode, ran.stderr) == (0, ""), ran.stderr
    assert held.text(root, LINKING_UNDER) == (Path(target) / _file(LINKING_UNDER)).read_text(encoding="utf-8")
    assert _waiting(root) == {iri("decision", "not-anywhere"): [LINKING_UNDER]}
    assert held.versions(root)[DECISIONS] == [1]
    assert sorted(entry.artifact for entry in _imported(root)) == sorted([type_iri("work-item"), LINKING_UNDER])


NOT_ANYWHERE = iri("decision", "not-anywhere")


@given("a store holding a type for work items whose link field allows decisions")
def _a_store_with_the_type_for_work_items(root):
    define(_started(root), WORK_ITEM_TYPE)


@given(parsers.parse("a type for decisions held by {holder}"), target_fixture="holder")
def _a_type_for_decisions_held_by(root, holder):
    """The store is given the type here; the directory is given it as it is made."""
    if holder == "the store":
        define(kb_client.connect(root), DECISION_TYPE)
    return holder


@given(
    "a directory for import that checks clean, holding a work item whose link names an IRI under the type for "
    "decisions that neither the directory nor the store holds",
    target_fixture="target",
)
def _for_import_with_a_work_item_linking_to_nothing_held(root, tmp_path, holder):
    """The export of a store holding both types and the work item, without the type for decisions when the store
    imported into is the one that holds it."""
    def fill(client):
        define(client, DECISION_TYPE)
        _a_work_item_linking_under_the_type(client)

    target = _for_import(tmp_path, fill)
    if holder == "the store":
        (Path(target) / _file(DECISIONS, 1)).unlink()
    assert not (Path(target) / _file(NOT_ANYWHERE)).exists() and not held.holds_artifact(root, NOT_ANYWHERE)
    assert _report(_kb("import", str(target), "--check", cwd=root)) == [["clean", f"{target} checks clean for import"]]
    return target


@then("the import lands")
def _the_import_lands(ran, root, target):
    assert (ran.returncode, ran.stderr) == (0, "")
    assert set(_exported_names(target)) <= set(held.names(root))


@then("the work item's link lands on a placeholder at that IRI")
def _the_work_item_waits_at_that_iri(root):
    assert held.text(root, LINKING_UNDER)
    assert _waiting(root) == {NOT_ANYWHERE: [LINKING_UNDER]}


EARLY, LATER = iri("note", "early"), iri("decision", "later")
KEEP = "options/keep"
ANSWERING_TYPE = copy.deepcopy(DECISION_TYPE)  # decisions carry options, and may link to an option of another
ANSWERING_TYPE["schema"]["properties"]["answers"] = {
    "type": "string", "ref": {"targets": targets("decision"), "cardinality": "one", "parts": True, "on_delete": "refuse"},
}
FIRST_DECISION, ANSWERING = iri("decision", "first-decision"), iri("decision", "second-decision")


def _the_first_decision_with_no_option(client):
    create(client, "decision", {"title": "First decision", "sections": _sections("Purpose", "Rationale")})


@given("a store holding a type for decisions whose decisions carry options and may link to an option of another")
def _a_store_with_decisions_that_may_link_to_an_option(root):
    define(_started(root), ANSWERING_TYPE)


@given(parsers.parse("a decision with no option held by {holder}"), target_fixture="holder")
def _a_decision_with_no_option_held_by(root, holder):
    """The store is given the decision here; the directory is given it as it is made."""
    if holder == "the store":
        _the_first_decision_with_no_option(kb_client.connect(root))
    return holder


@given(
    "a directory for import that checks clean, holding a second decision whose link names an option of the first",
    target_fixture="target",
)
def _for_import_with_a_decision_linking_to_an_option_the_first_lacks(root, tmp_path, holder):
    """The export of a store whose second decision was written before the first, which was then created with no
    option; without the first decision's file when the store imported into is the one that holds it."""
    def fill(client):
        define(client, ANSWERING_TYPE)
        create(client, "decision", {
            "title": "Second decision", "sections": _sections("Purpose", "Rationale"), "answers": f"{FIRST_DECISION}#{KEEP}",
        })
        _the_first_decision_with_no_option(client)

    target = _for_import(tmp_path, fill)
    if holder == "the store":
        (Path(target) / _file(FIRST_DECISION)).unlink()
    assert (Path(target) / _file(FIRST_DECISION)).exists() != held.holds_artifact(root, FIRST_DECISION)
    assert _report(_kb("import", str(target), "--check", cwd=root)) == [["clean", f"{target} checks clean for import"]]
    return target


@then("the second decision's link waits on a placeholder for that option of the first decision")
def _the_second_decision_waits_for_the_option(root):
    assert "options" not in held.artifact(root, FIRST_DECISION)
    assert _waiting_for(root) == [(FIRST_DECISION, ANSWERING, "answers", KEEP)]


def _a_note_waiting_on_an_option_its_decision_was_created_without(client):
    """The release gate's store: a note about an option of a decision, written while the decision was not held, and
    that decision, created since with no option."""
    define(client, DECISION_TYPE)
    define(client, NOTE_TYPE)
    create(client, "note", {"title": "Early", "about": f"{LATER}#{KEEP}"})
    create(client, "decision", {"title": "Later", "sections": _sections("Purpose", "Rationale")})


def _waiting_for(root):
    """Each link in the store that waits, as the store's check lists it: the IRI, the artifact, its field and the
    part it waits for; the check finding no violation."""
    checked = check(kb_client.connect(root))
    assert not checked.faults and list(checked.violations) == [], checked
    assert list(checked.placeholders) == list(placeholders(kb_client.connect(root)).placeholders)
    return [(each.id, link.artifact, link.field, link.part) for each in checked.placeholders for link in each.links]


def test_the_export_of_a_store_holding_a_link_into_a_part_its_target_lacks_checks_clean_lands_and_waits_as_it_did(
    root, tmp_path,
):
    target = _for_import(tmp_path, _a_note_waiting_on_an_option_its_decision_was_created_without)
    waited = _waiting_for(tmp_path / "source")

    checked = _check_for_import(root, target)
    ran = _kb_import(root, target)

    assert (checked.returncode, _report(checked)) == (0, [["clean", f"{target} checks clean for import"]])
    assert (ran.returncode, ran.stderr) == (0, "")
    assert waited == _waiting_for(root) == [(LATER, EARLY, "about", KEEP)]
    assert _export_of(root, tmp_path / "again") == {file: (target / file).read_bytes() for file in _files(target)}
    validated = _kb("validate", cwd=root)
    assert validated.returncode == 0 and f"{LATER}#{KEEP}" in validated.stdout, validated.stdout


def test_the_export_of_a_store_holding_a_link_into_a_part_its_target_lacks_is_passed_over_by_the_store_it_came_from(
    tmp_path,
):
    target = _for_import(tmp_path, _a_note_waiting_on_an_option_its_decision_was_created_without)
    source = tmp_path / "source"

    checked = _kb("import", str(target), "--check", cwd=source)
    ran = _kb_import(source, target)

    assert (checked.returncode, _report(checked)) == (0, [["clean", f"{target} checks clean for import"]])
    assert (ran.returncode, ran.stderr) == (0, "") and _imported(source) == []
    assert _waiting_for(source) == [(LATER, EARLY, "about", KEEP)]


def test_a_link_an_import_left_waiting_on_a_part_is_kept_by_a_later_change_and_refused_when_a_client_writes_one(root, tmp_path):
    """Only the import lets such a link wait: once landed it is the store's own, kept by a change that leaves it, while
    a create, and a replacement that adds one, are refused as they always were."""
    _import_into_a_fresh_store(root, _for_import(tmp_path, _a_note_waiting_on_an_option_its_decision_was_created_without))
    client = kb_client.connect(root)

    kept = replace(client, EARLY, {"about": f"{LATER}#{KEEP}", "status": "said again"})
    created = request(client, "note", "Late", {"about": f"{LATER}#{KEEP}"}, "Create an artifact")
    altered = replace(client, EARLY, {"about": f"{LATER}#options/drop"})

    assert not kept.faults, kept.faults
    assert [(fault.rule, fault.place) for fault in created.faults] == [("ref", "about")]
    assert [(fault.rule, fault.place) for fault in altered.faults] == [("ref", "about")]
    assert _waiting_for(root) == [(LATER, EARLY, "about", KEEP)]


def _handed_to_the_port(monkeypatch):
    """Every link handed to the port from here on, but kb's own implicit ones, each with the mark it carries."""
    handed = []
    land = sqlite_store.SqliteStore.land

    def spied(self, changes, entries):
        handed.extend((str(change.artifact), link.imported) for change in changes for link in change.links if not link.implicit)
        return land(self, changes, entries)

    monkeypatch.setattr(sqlite_store.SqliteStore, "land", spied)
    return handed


def test_only_an_import_marks_the_links_it_hands_the_port_and_no_change_a_client_asks_for_does(root, tmp_path, monkeypatch):
    """Review Focus 4: a create, a replacement, an addition and their sets hand every link unmarked, whatever they
    send; an import hands each of its links marked."""
    target = _for_import(tmp_path, _a_note_waiting_on_an_option_its_decision_was_created_without)
    client = _started(root)
    define(client, DECISION_TYPE)
    define(client, NOTE_TYPE)
    linking = copy.deepcopy(DECISION_TYPE)
    linking["schema"]["parts"]["options"]["items"]["properties"]["about"] = NOTE_TYPE["schema"]["properties"]["about"]
    define(client, {**linking, "title": "Ruling"})
    create(client, "decision", {"title": "Held", "sections": _sections("Purpose", "Rationale"), "options": [{"title": "Keep"}]})
    into, ruling = f"{iri('decision', 'held')}#{KEEP}", {"title": "First", "sections": _sections("Purpose", "Rationale")}
    handed = _handed_to_the_port(monkeypatch)

    create(client, "note", {"title": "One", "about": into, "imported": True})
    assert not create_many(client, [created("note", "Two", {"about": into})]).faults
    assert not replace(client, iri("note", "one"), {"about": iri("decision", "held")}).faults
    assert not replace_many(client, [replaced(iri("note", "two"), {"about": iri("decision", "held")})]).faults
    create(client, "ruling", ruling)
    assert not add(client, iri("ruling", "first"), "options", {"title": "Keep", "about": into}).faults
    assert len(handed) == 5 and {mark for _, mark in handed} == {False}, handed

    del handed[:]
    ran = _kb_import(root, target)
    assert (ran.returncode, ran.stderr) == (0, "")
    assert handed == [(EARLY, True)]


SECOND_DECISION, SECOND_NOTE = iri("decision", "second"), iri("note", "second")
LACKING = {  # a file carrying a link into a part its target lacks that no import lets wait
    "in a field that allows no part": lambda: {
        **{key: _decision(SECOND_DECISION)[key] for key in IDENTITY}, "supersedes": f"{LATER}#{KEEP}",
        "sections": _decision(SECOND_DECISION)["sections"],
    },
    "into an artifact of a kind the field does not allow": lambda: _artifact(SECOND_NOTE, "Second", about=f"{EARLY}#{KEEP}"),
}


@pytest.mark.parametrize("carrying", LACKING.values(), ids=list(LACKING))
def test_a_link_into_a_part_is_still_an_error_of_the_check_where_no_link_could_wait_and_the_import_is_refused(
    root, tmp_path, carrying,
):
    target = _for_import(tmp_path, _a_note_waiting_on_an_option_its_decision_was_created_without)
    _put(target, carrying())

    checked = _check_for_import(root, target)
    ran = _kb_import(root, target)

    assert (checked.returncode, _errors(checked)) == (1, [(_file(carrying()["id"]), "ref")]), checked.stdout
    assert ran.returncode == 2 and held.names(root) == [TYPE_OF_TYPES]


@given("a directory for import that checks clean", target_fixture="target")
def _for_import_that_checks_clean(tmp_path):
    return _for_import(tmp_path, lambda client: define(client, WORK_ITEM_TYPE))


@given("a server serves that store", target_fixture="address")
def _a_server_serves_that_store(root, request, before):
    address = serving.serving(root, request)
    before["started"] = held.holds(root)
    return address


@given("a directory for import that checks clean, holding a second decision", target_fixture="target")
def _for_import_holding_a_second_decision(tmp_path):
    """The export of a store holding the second decision, the type for decisions the store's own and its file taken out."""
    def fill(client):
        define(client, DECISION_TYPE)
        create(client, "decision", {"title": _titled(MONTHLY), "sections": _decision(MONTHLY)["sections"]})

    target = _for_import(tmp_path, fill)
    (target / _file(type_iri("decision"), 1)).unlink()
    return target


@then("the import is rejected because the store is served, naming the server's address")
def _import_rejected_as_served(ran, address):
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr.startswith("kb import: refused: served: ") and address in ran.stderr, ran.stderr


@scenario(FEATURE, "Importing into a store a server serves is refused")
def test_importing_into_a_store_a_server_serves_is_refused():
    pass


def _served_with_a_decision(root, request):
    """A store holding the type for decisions and a decision, a server serving it; the server's process."""
    a_decision_type_and_a_decision(_started(root))
    server = serving.started(root, request)
    assert server.said().startswith("serving\t")
    return server


def test_the_check_an_export_and_a_backup_are_answered_beside_the_server_that_serves_the_store(root, tmp_path, request):
    _served_with_a_decision(root, request)
    target = _for_import(tmp_path, lambda client: define(client, WORK_ITEM_TYPE))
    exported_to, backup = tmp_path / "exported", tmp_path / "backup.sqlite3"
    exported_to.mkdir()
    for ran in (
        _kb("import", str(target), "--check", cwd=root),
        _kb("export", str(exported_to), cwd=root),
        _kb("backup", str(backup), cwd=root),
    ):
        assert (ran.returncode, ran.stderr) == (0, ""), ran.stderr


def test_an_import_lands_once_the_server_has_stopped(root, tmp_path, request):
    server = _served_with_a_decision(root, request)
    target = _for_import(tmp_path, lambda client: define(client, WORK_ITEM_TYPE))
    assert _kb("import", str(target), cwd=root, env={"KB_ACTOR": OPERATOR}).returncode == 2
    server.stop()
    ran = _kb("import", str(target), cwd=root, env={"KB_ACTOR": OPERATOR})
    assert (ran.returncode, ran.stderr) == (0, "")
    assert held.holds_artifact(root, type_iri("work-item"))


@scenario(FEATURE, "The operator imports the kb directory of an existing store")
def test_importing_the_kb_directory_of_an_existing_store():
    pass


PASSED_OVER = {
    ".git/HEAD": b"ref: refs/heads/main\n",
    ".git/objects/ab/cdef": b"\x78\x9c\x00\x01",
    "journal/20260924T120000000000Z-1.yaml": b"id: 20260924T120000000000Z-1\nop: create\n",
    "store.yaml": b"contract: '0.1'\n",
    "store.sqlite3": b"SQLite format 3\x00\x10\x00",
    "store.sqlite3-wal": b"\x37\x7f\x06\x82",
    "store.sqlite3-shm": b"\x00\x00",
}


@given(
    "the kb directory of an existing store, holding its types and artifacts, which check clean, together with its "
    "history and its store marker",
    target_fixture="target",
)
def _the_kb_directory_of_a_store(tmp_path):
    """An export laid out as a store's kb directory is: the files of its types and artifacts, beside them the history
    an old store kept in git and in `journal/`, and the marker and database files a store keeps."""
    target = _for_import(tmp_path)
    for file, data in PASSED_OVER.items():
        (target / file).parent.mkdir(parents=True, exist_ok=True)
        (target / file).write_bytes(data)
    return target


def test_the_lock_file_a_server_leaves_in_a_kb_directory_is_passed_over_by_the_import_check(tmp_path, root):
    """A store once served keeps `served.yaml` beside its marker and database (kb.served): the kb directory of such
    a store, checked for import, is clean, the lock file passed over as the files that mark and keep a store are."""
    target = _the_kb_directory_of_a_store(tmp_path)
    (target / "served.yaml").write_text("address: 127.0.0.1:50051\n", encoding="utf-8")
    _started(root)
    ran = _kb("import", str(target), "--check", cwd=root)
    assert (ran.returncode, ran.stdout, ran.stderr) == (0, f"clean\t{target} checks clean for import\n", ""), ran.stdout


@when("the operator imports that kb directory, saying which role they are", target_fixture="ran")
def _kb_import_the_kb_directory(root, target):
    return _kb_import(root, target)


@then("its types and artifacts land as they would from an export")
def _land_as_from_an_export(ran, root, target):
    assert (ran.returncode, ran.stdout, ran.stderr) == (0, "", "")
    names = _exported_names(target)
    assert held.names(root) == sorted([*names, TYPE_OF_TYPES])
    for name in names:
        assert held.text(root, name) == (Path(target) / _held_file(root, name)).read_text(encoding="utf-8"), name


@then("its history and its store marker are passed over, neither landing in the store")
def _history_and_marker_passed_over(root, target, before):
    assert sorted(entry.artifact for entry in _imported(root)) == _exported_names(target)
    assert not any(name.startswith(("journal/", ".git/", "store")) for name in held.names(root))
    assert held.holds(root)["marker"] == before["started"]["marker"]


@scenario(FEATURE, "Importing when nothing names the operator's role is refused")
def test_importing_without_a_role_is_refused():
    pass


@given("a freshly started store, and nothing names which role the operator is")
def _a_freshly_started_store_and_no_role(root, before):
    _a_freshly_started_store(root, before)


@when("the operator imports the directory", target_fixture="ran")
def _kb_import_without_a_role(root, target):
    return _kb("import", str(target), cwd=root)


@then("the import is rejected because the role must be named through KB_ACTOR")
def _rejected_without_kb_actor(ran):
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr == "kb import: refused: actor: an import lands only under a role, named through KB_ACTOR\n"


@scenario(FEATURE, "kb export and kb import find the store as kb validate does, with the same refusals")
def test_export_and_import_find_the_store_as_validate_does():
    pass


@given(
    "a freshly started store, with the operator working in a folder deep inside the directory it sits in",
    target_fixture="where",
)
def _fresh_and_working_deep_inside(root):
    _started(root)
    deep = root / "notes" / "2026" / "september"
    deep.mkdir(parents=True)
    return {"cwd": deep, "env": {}}


@given(
    "a freshly started store, with the operator working outside any store and KB_ROOT naming that one",
    target_fixture="where",
)
def _fresh_and_named_from_outside(root, tmp_path):
    _started(root)
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    return {"cwd": outside, "env": {"KB_ROOT": str(root)}}


@when("the operator runs kb export to an empty directory there", target_fixture="ran")
def _kb_export_there(where, tmp_path):
    target = tmp_path / "exported"
    target.mkdir()
    where["target"] = target
    return _kb("export", str(target), cwd=where["cwd"], env=where["env"])


@when(
    "the operator runs kb import of a directory that checks clean, saying which role they are there",
    target_fixture="ran",
)
def _kb_import_there(where, tmp_path):
    where["target"] = _for_import(tmp_path)
    return _kb("import", str(where["target"]), cwd=where["cwd"], env={**where["env"], "KB_ACTOR": OPERATOR})


@then("the store found above where they are working is the one exported")
@then("the store KB_ROOT names is the one exported")
def _that_store_exported(ran, root, where):
    assert (ran.returncode, ran.stdout, ran.stderr) == (0, "", "")
    assert _files(where["target"]) == _held_files(root)


@then("the store found above where they are working is the one imported into")
@then("the store KB_ROOT names is the one imported into")
def _that_store_imported_into(ran, root, where):
    assert (ran.returncode, ran.stdout, ran.stderr) == (0, "", "")
    assert held.names(root) == sorted([*_exported_names(where["target"]), TYPE_OF_TYPES])


@then(parsers.parse(
    "the {command} is rejected because no store was found, neither above where they are working nor named outright"
))
def _rejected_as_no_store(ran, where, command):
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr == (
        f"kb {command}: refused: store: no store was found, neither above {where['cwd']} nor named outright\n"
    )


@then(parsers.parse("the {command} is rejected because KB_ROOT names a directory that holds no store"))
def _rejected_as_kb_root_names_no_store(ran, where, command):
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr == (
        f"kb {command}: refused: store: KB_ROOT names a directory that holds no store: {where['env']['KB_ROOT']}\n"
    )


@then(parsers.parse(
    "the {command} is rejected because KB_ROOT names a store other than the one they are standing in, and neither of "
    "the two is guessed at"
))
def _rejected_as_two_stores(ran, where, command):
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr == (
        f"kb {command}: refused: store: KB_ROOT names a store other than the one {where['cwd']} is working in: "
        f"KB_ROOT is {where['env']['KB_ROOT']}, the working directory is inside {where['cwd']}; neither is guessed at\n"
    )


@scenario(FEATURE, "Importing with errors skipped when nothing would land is refused")
def test_importing_with_errors_skipped_when_nothing_would_land_is_refused():
    pass


@given("a directory for import in which every file has an error", target_fixture="target")
def _for_import_all_broken(tmp_path):
    """The export of a store holding the types for decisions and work items, the decisions and the work item, each
    file then broken: the type for decisions given a version that is not a number, the type for work items, the
    decisions and the work item made unreadable, and the copy of the type that describes types given a field of its
    own."""
    target = _for_import(tmp_path)
    _a_broken_decision_type(target)
    for name, version in ((type_iri("work-item"), 1), (WEEKLY, None), (MONTHLY, None), (MONDAYS, None)):
        (Path(target) / _file(name, version)).write_text(f"id: {name}\ntitle: [never closed\n", encoding="utf-8")
    copy = _read(target, TYPE_OF_TYPES, 1)
    copy["schema"]["properties"]["owner"] = {"type": "string"}
    _put(target, copy, 1)
    return target


@then("the import is rejected because nothing would land")
def _rejected_as_nothing_would_land(ran):
    assert ran.returncode == 2
    assert {line[1] for line in _report(ran) if line[0] == "error"} == {
        *(_file(name, 1) for name in (TYPE_OF_TYPES, type_iri("decision"), type_iri("work-item"))),
        *(_file(name) for name in (WEEKLY, MONTHLY, MONDAYS)),
    }, ran.stdout
    assert ran.stderr == (
        "kb import: refused: operations: nothing in the directory would land, and nothing was written\n"
    )


@scenario(FEATURE, "The operator imports a directory whose type that describes types matches the store's")
def test_a_matching_type_of_types_is_passed_over():
    pass


@given(
    "a directory for import that checks clean, holding a copy of the type that describes types that matches the "
    "store's",
    target_fixture="target",
)
def _for_import_with_a_matching_type_of_types(tmp_path, root):
    target = _for_import(tmp_path, lambda client: define(client, DECISION_TYPE))
    assert (Path(target) / _file(TYPE_OF_TYPES, 1)).read_text(encoding="utf-8") == held.text(root, TYPE_OF_TYPES)
    return target


@then("the directory's copy of the type that describes types is passed over")
def _the_copy_is_passed_over(ran, root):
    assert (ran.returncode, ran.stdout, ran.stderr) == (0, "", "")
    assert [entry.artifact for entry in _imported(root)] == [type_iri("decision")]


@then("the store's type that describes types is kept as it was")
def _the_type_of_types_kept(root, before):
    assert held.text(root, TYPE_OF_TYPES) == before["type of types"]
    entries = journal(kb_client.connect(root), artifact=TYPE_OF_TYPES).entries
    assert [(entry.op, entry.message) for entry in entries] == [("create", "initialise store")]


def test_a_store_holding_a_type_at_two_versions_exports_the_same_files_twice(root, tmp_path):
    _store_with_a_type_at_two_versions(root)
    first, second = (tmp_path / each for each in ("first", "second"))
    for target in (first, second):
        ran = _kb("export", str(target), cwd=root)
        assert (ran.returncode, ran.stdout, ran.stderr) == (0, "", "")
    assert _files(first) == _files(second) == _held_files(root)
    for file in _files(first):
        assert (first / file).read_bytes() == (second / file).read_bytes(), file


def _a_note_left_at_version_1_by_a_type_reordered_at_2(tmp_path, monkeypatch):
    def typed(order, version):
        fields = {name: {"type": "string"} for name in ["title", *order]}
        return {"version": version, "schema": {"type": "object", "properties": fields, "required": ["title"]}}

    source, target, exported = (tmp_path / each for each in ("source", "target", "exported"))
    for root in (source, target):
        root.mkdir()
        start_a_store(root)
    client = kb_client.connect(source)
    define(client, {"title": "Note", **typed(["a", "b"], 1)})
    create(client, "note", {"title": "X", "b": "second", "a": "first"})
    replace(client, type_iri("note"), typed(["b", "a"], 2))
    assert list(check(client).violations) == []
    monkeypatch.setenv("KB_ROOT", str(source))
    assert kb_client.export(str(exported)).faults == []
    text = (exported / _file(iri("note", "x"))).read_text(encoding="utf-8")
    assert list(_loaded(text)) == [*IDENTITY, "a", "b"]
    assert (_loaded(text)["type"], _loaded(text)["revision"]) == (version_iri("note", 1), 1)
    return target, exported


def test_an_artifact_left_at_its_version_when_its_type_reordered_its_fields_exports_in_the_order_that_version_declares(
    tmp_path, monkeypatch,
):
    _a_note_left_at_version_1_by_a_type_reordered_at_2(tmp_path, monkeypatch)


def test_the_export_of_an_artifact_left_at_its_version_imports_into_a_fresh_store(tmp_path, monkeypatch):
    target, exported = _a_note_left_at_version_1_by_a_type_reordered_at_2(tmp_path, monkeypatch)
    monkeypatch.setenv("KB_ROOT", str(target))
    checked = kb_client.import_check(str(exported))
    assert (checked.faults, list(checked.errors), list(checked.skipped)) == ([], [], [])
    assert kb_client.import_(str(exported), OPERATOR).faults == []
    assert held.artifact(target, iri("note", "x"))["b"] == "second"


# A store holding an artifact behind its type, exported and imported into a fresh store (slice 165.6): the review's
# reproduction of batch 33's RELEASE GATE, the scenario first, then each call on the imported store held separately,
# each compared with the same call on the store exported.

BEHIND = iri("note", "stock-count")


def _owned_note_type(*required):
    """The schema of a note type declaring a body and an owner, requiring its title and the fields named."""
    properties = {name: {"type": "string"} for name in ("title", "body", "owner")}
    return {"type": "object", "properties": properties, "required": ["title", *required]}


def _a_note_left_without_the_owner_its_type_now_requires(client):
    define(client, {"title": "Note", "version": 1, "schema": _owned_note_type()})
    create(client, "note", {"title": "Stock count", "body": "Count on Fridays."})
    changed = change_type(client, "note", _owned_note_type("owner"))
    assert not changed.faults, changed.faults


@given(
    "a store holding a note type at two versions, the second requiring an owner the first does not, and a note that "
    "conforms to the first version, with no owner",
    target_fixture="source",
)
def _store_with_a_note_behind_its_type(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    start_a_store(source)
    _a_note_left_without_the_owner_its_type_now_requires(kb_client.connect(source))
    assert held.versions(source)[type_iri("note")] == [1, 2]
    assert held.artifact(source, BEHIND)["type"] == version_iri("note", 1) and "owner" not in held.artifact(source, BEHIND)
    return source


@given("that store exported to a directory", target_fixture="target")
def _exported_to_a_directory(source, tmp_path):
    target = tmp_path / "exported"
    ran = _kb("export", str(target), cwd=source)
    assert (ran.returncode, ran.stdout, ran.stderr) == (0, "", "")
    return target


@when("the operator imports that directory into a freshly started store, saying which role they are", target_fixture="ran")
def _kb_import_into_a_fresh_store(root, target):
    start_a_store(root)
    return _kb("import", str(target), cwd=root, env={"KB_ACTOR": OPERATOR})


@then("the new store holds both versions of the note type as their files give them")
def _both_versions_as_their_files_give_them(ran, root, target):
    assert (ran.returncode, ran.stdout, ran.stderr) == (0, "", "")
    note = type_iri("note")
    assert held.versions(root)[note] == [1, 2]
    for number in (1, 2):
        assert canonical.dump(held.version(root, note, number)) == (target / _file(note, number)).read_text("utf-8")


@then("the note still conforms to the first version of the note type")
def _the_note_at_the_first_version(root, target):
    assert held.artifact(root, BEHIND)["type"] == version_iri("note", 1)
    assert held.text(root, BEHIND) == (target / _file(BEHIND)).read_text(encoding="utf-8")


def _behind(client):
    """What a check of the store lists: its violations, and the stale as the artifact, its version and its type's."""
    checked = check(client)
    assert not checked.refused, checked.faults
    return list(checked.violations), [(each.artifact, each.schema_version, each.current) for each in checked.stale]


@then(
    "the note can be read, listed and replaced there, and checking that store lists it as behind its type, not as a "
    "violation",
)
def _read_listed_checked_and_replaced(root):
    client = kb_client.connect(root)
    for whole in (False, True):
        assert not read(client, BEHIND, whole=whole).refused
    assert [stub.id for stub in listing(client, "note").stubs] == [BEHIND]
    assert _behind(client) == ([], [(BEHIND, 1, 2)])
    replaced = replace(client, BEHIND, {"body": "Count on Mondays."})
    assert not replaced.refused, replaced.faults
    assert held.artifact(root, BEHIND)["body"] == "Count on Mondays."


@pytest.fixture
def came_back(tmp_path, root):
    """A client on the store exported, holding a note behind its type, and one on the fresh store its export was
    imported into; the check of that directory for import found it clean."""
    source = _store_with_a_note_behind_its_type(tmp_path)
    target = _exported_to_a_directory(source, tmp_path)
    ran = _check_for_import(root, target)
    assert (ran.returncode, ran.stdout, ran.stderr) == (0, f"clean\t{target} checks clean for import\n", "")
    landed = _kb("import", str(target), cwd=root, env={"KB_ACTOR": OPERATOR})
    assert (landed.returncode, landed.stdout, landed.stderr) == (0, "", "")
    return kb_client.connect(source), kb_client.connect(root)


def test_a_note_behind_its_type_reads_at_a_glance_in_the_store_its_export_was_imported_into_as_it_did(came_back):
    exported_from, imported_into = (read(client, BEHIND) for client in came_back)
    assert not imported_into.refused, imported_into.faults
    assert imported_into == exported_from
    assert (imported_into.revision, imported_into.type) == (1, version_iri("note", 1))


def test_a_note_behind_its_type_reads_whole_in_the_store_its_export_was_imported_into_as_it_did(came_back):
    exported_from, imported_into = (read(client, BEHIND, whole=True) for client in came_back)
    assert not imported_into.refused, imported_into.faults
    assert imported_into == exported_from
    assert loads(imported_into.content) == {"body": "Count on Fridays."}


def test_a_note_behind_its_type_is_listed_in_the_store_its_export_was_imported_into_as_it_was(came_back):
    exported_from, imported_into = (listing(client, "note") for client in came_back)
    assert not imported_into.refused, imported_into.faults
    assert imported_into == exported_from
    assert [(stub.id, stub.type) for stub in imported_into.stubs] == [(BEHIND, version_iri("note", 1))]


def test_checking_the_store_an_export_was_imported_into_lists_a_note_behind_its_type_as_behind_and_no_violation(
    came_back,
):
    exported_from, imported_into = (_behind(client) for client in came_back)
    assert imported_into == exported_from == ([], [(BEHIND, 1, 2)])


def test_a_note_behind_its_type_is_replaced_in_the_store_its_export_was_imported_into_as_it_would_have_been(
    came_back, root,
):
    exported_from, imported_into = (replace(client, BEHIND, {"body": "Count on Mondays."}) for client in came_back)
    assert not imported_into.refused, imported_into.faults
    assert imported_into.revision == exported_from.revision == 2
    kept = held.artifact(root, BEHIND)
    assert (kept["type"], kept["body"]) == (version_iri("note", 1), "Count on Mondays.") and "owner" not in kept
    assert [read(client, BEHIND, whole=True).content for client in came_back] == [dumps({"body": "Count on Mondays."})] * 2


def test_a_note_behind_its_type_moves_to_the_latest_version_in_the_store_its_export_was_imported_into(came_back, root):
    _, imported_into = came_back
    moved = replace(
        imported_into, BEHIND, {"body": "Count on Fridays.", "owner": "Ada"}, version=version_iri("note", 2),
    )
    assert not moved.refused, moved.faults
    assert held.artifact(root, BEHIND)["type"] == version_iri("note", 2)
    assert _behind(imported_into) == ([], [])


def test_the_export_of_a_store_imported_into_a_fresh_store_exports_the_same_files_byte_for_byte(root, tmp_path):
    source = tmp_path / "held"
    source.mkdir()
    _store_with_a_type_at_two_versions(source)
    assert _behind(kb_client.connect(source))[1] == [(WEEKLY, 1, 2), (MONTHLY, 1, 2)]
    first, second = (tmp_path / each for each in ("first", "second"))
    assert _kb("export", str(first), cwd=source).returncode == 0

    _import_into_a_fresh_store(root, first)
    ran = _kb("export", str(second), cwd=root)

    assert (ran.returncode, ran.stdout, ran.stderr) == (0, "", "")
    assert _files(second) == _files(first) == _held_files(source)
    for file in _files(first):
        assert (second / file).read_bytes() == (first / file).read_bytes(), file


@scenario(
    FEATURE,
    'Exporting to something that is a file, not a directory, is refused',
)
def test_exporting_to_something_that_is_a_file_not_a_directory_is_refused():
    pass


@scenario(
    FEATURE,
    'Checking for import something that is not a directory is refused',
)
def test_checking_for_import_something_that_is_not_a_directory_is_refused():
    pass


@scenario(
    FEATURE,
    'Importing from something that is not a directory is refused',
)
def test_importing_from_something_that_is_not_a_directory_is_refused():
    pass


@scenario(
    FEATURE,
    'An import that waits longer than the store waits for another change is refused as busy',
)
def test_an_import_that_waits_longer_than_the_store_waits_for_another_change_is():
    pass


@scenario(
    FEATURE,
    'The operator exports the store while another change is being written',
)
def test_the_operator_exports_the_store_while_another_change_is_being_written():
    pass


BUSY = "the store was busy with another change"


@then("the import is rejected because the store was busy with another change")
def _import_rejected_as_busy(ran):
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr.startswith(f"kb import: refused: busy: {BUSY}"), ran.stderr


@then("the same import may be run again")
def _import_run_again(root, target, holding):
    holding.let_go()
    again = _kb_import(root, target)
    assert (again.returncode, again.stderr) == (0, "")
    assert held.names(root) == sorted([*_exported_names(target), TYPE_OF_TYPES])


@when("the operator exports the store to an empty directory", target_fixture="ran")
@when("the operator exports the store to a directory that is empty", target_fixture="ran")
def _kb_export_to_an_empty_directory(root, tmp_path):
    target = tmp_path / "exported"
    target.mkdir()
    return {"target": target, "ran": _kb("export", str(target), cwd=root)}


@then("the export is written")
def _the_export_is_written(root, ran):
    assert sorted(str(path.relative_to(ran["target"])) for path in ran["target"].rglob("*.yaml")) == sorted(
        _held_file(root, name) for name in held.names(root)
    )
    for name in held.names(root):
        assert (ran["target"] / _held_file(root, name)).read_text(encoding="utf-8") == held.text(root, name)


@then("the export is not refused because the store was busy with another change")
def _export_not_busy(ran):
    assert (ran["ran"].returncode, ran["ran"].stdout, ran["ran"].stderr) == (0, "", "")


# The operator's directory is refused by its shape: a file where a directory is wanted.

FILE_TEXT = "a file the operator named where a directory was wanted\n"


@given("a file where the export is to go, and no directory", target_fixture="target")
def _a_file_where_the_export_is_to_go(tmp_path, before):
    target = tmp_path / "exported"
    target.write_text(FILE_TEXT)
    before.update(target=held.everything_in(target))
    return target


@given("a file where a directory for import should be", target_fixture="target")
def _a_file_where_a_directory_for_import_should_be(tmp_path, root, before):
    target = tmp_path / "for-import"
    target.write_text(FILE_TEXT)
    before.update(started=held.holds(root), target=held.everything_in(target))
    return target


@when("the operator exports the store to that file", target_fixture="ran")
def _kb_export_to_a_file(root, target):
    return _kb("export", str(target), cwd=root)


@when("the operator checks that file for import", target_fixture="ran")
def _kb_check_a_file(root, target):
    return _kb("import", str(target), "--check", cwd=root)


@when("the operator imports that file, saying which role they are", target_fixture="ran")
def _kb_import_a_file(root, target):
    return _kb("import", str(target), cwd=root, env={"KB_ACTOR": OPERATOR})


@then("the export is rejected because export writes into a directory")
def _rejected_as_writing_into_a_directory(ran, target):
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr == f"kb export: refused: root: an export is written into a directory; {str(target)!r} is not a directory\n"


@then("the file is left as it was")
def _the_file_as_it_was(target, before):
    assert target.is_file() and held.everything_in(target) == before["target"]


@then(parsers.parse("the {command} is rejected because files for import are read from a directory"))
def _rejected_as_read_from_a_directory(ran, target, command):
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr == f"kb import: refused: root: an import is read from a directory; {str(target)!r} is not one\n"
