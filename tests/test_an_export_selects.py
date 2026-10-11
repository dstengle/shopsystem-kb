"""An export through the contract selects by the path below the type, by a kind, or by both
(decision/export-selections-combine, decision/path-selection-is-a-segment-prefix): a path by whole segments of each
artifact's IRI below its own type's, so `plan` selects `plan` and `plan/a` and never `planning`, whatever the type;
a kind, the artifacts conforming to any version of its type; both, what both select. Each file a selection gives is,
byte for byte, the file the whole export gives at the same moment, and the position is the store's whatever was
selected. What is not a path, or no kind, is refused as a list refuses it, the stream's one message."""
import pytest

import kb.testing as kb_testing
from calls import (
    DECISION_TYPE, NOTE_TYPE, WORK_ITEM_TYPE, create, define, export, filed, iri, listing, next_version, request,
    start_a_store, type_iri,
)
from kb import client as kb_client

SECTIONS = [
    {"title": "Purpose", "body": "Keep the shop running.\n"},
    {"title": "Rationale", "body": "It was agreed.\n"},
]
DECISIONS = ("plan", "plan/a", "plan/a/b", "planning", "plan-b", "plan.b", "old/plan")
WORK_ITEMS = ("plan", "plan/a", "plans/a")
NOTES_TYPE = iri("decision", "notes")
NOTE = f"{NOTES_TYPE}/plan/a"


def at(kind, paths):
    return [iri(kind, path) for path in paths]


@pytest.fixture
def client(root):
    """A store holding decisions and work items at paths below their types that share whole segments and parts of
    one."""
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, DECISION_TYPE)
    define(client, WORK_ITEM_TYPE)
    for each in at("decision", DECISIONS):
        create(client, "decision", {"title": each, "sections": SECTIONS}, at=each)
    for each in at("work-item", WORK_ITEMS):
        create(client, "work-item", {"title": each, "decisions": [iri("decision", "plan")]}, at=each)
    return client


def places(exported):
    """The places of a whole export's files, in no order."""
    assert exported.complete, exported.faults
    return sorted(place for place, _ in exported.files)


def of(names):
    return sorted(filed(name) for name in names)


def test_an_export_by_a_path_selects_whole_segments_across_every_type_and_no_types_file(client):
    assert places(export(client, path="plan")) == of([
        *at("decision", ("plan", "plan/a", "plan/a/b")), *at("work-item", ("plan", "plan/a")),
    ])


@pytest.mark.parametrize("path, selected", [
    ("plan/a", [iri("decision", "plan/a"), iri("decision", "plan/a/b"), iri("work-item", "plan/a")]),
    ("plan/a/b", [iri("decision", "plan/a/b")]),
    ("planning", [iri("decision", "planning")]),
    ("plan.b", [iri("decision", "plan.b")]),
    ("old", [iri("decision", "old/plan")]),
    ("plans", [iri("work-item", "plans/a")]),
    ("pla", []),
    ("a", []),
    ("plan/a/b/c", []),
    ("decision", []),
    ("decision/plan", []),
])
def test_an_export_by_a_path_matches_the_whole_path_or_its_first_segments_and_never_part_of_a_segment(client, path, selected):
    assert places(export(client, path=path)) == of(selected)


def test_an_export_by_a_kind_and_a_path_gives_what_both_select(client):
    assert places(export(client, "decision", "plan")) == of(at("decision", ("plan", "plan/a", "plan/a/b")))
    assert places(export(client, "work-item", "plan")) == of(at("work-item", ("plan", "plan/a")))
    assert places(export(client, "work-item", "planning")) == []


def test_an_export_by_a_kind_gives_that_types_artifacts_and_no_other_file(client):
    assert places(export(client, "work-item")) == of(at("work-item", WORK_ITEMS))
    assert places(export(client, "decision")) == of(at("decision", DECISIONS))


@pytest.mark.parametrize("type_name, path", [("", "plan"), ("decision", ""), ("decision", "plan"), ("", "pla")])
def test_a_selected_exports_files_are_byte_for_byte_the_whole_exports_and_its_position_the_stores(client, type_name, path):
    whole = export(client)
    selected = export(client, type_name, path)
    assert selected.complete, selected.faults
    assert selected.files == [file for file in whole.files if file in selected.files]
    assert all(text.encode() == dict(whole.files)[place].encode() for place, text in selected.files)
    assert selected.position == whole.position


def test_an_export_by_a_kind_gives_the_artifacts_conforming_to_every_version_of_its_type(client):
    """A decision made under each of the type's three versions: all of them are that type's artifacts."""
    made = [iri("decision", "plan")]
    for number in (1, 2):
        assert not next_version(client, "decision", {**DECISION_TYPE, "version": number}).faults
        made.append(iri("decision", f"made-under/{number + 1}"))
        create(client, "decision", {"title": made[-1], "sections": SECTIONS}, at=made[-1])
    assert not request(client, "decision", "late", {"sections": SECTIONS}, at=iri("decision", "made-under/late"),
                       version=1).faults
    exported = export(client, "decision")
    assert places(exported) == of([*at("decision", DECISIONS), *made[1:], iri("decision", "made-under/late")])
    assert places(export(client, "decision", "made-under")) == of([*made[1:], iri("decision", "made-under/late")])
    assert exported.files == [file for file in export(client).files if file in exported.files]


@pytest.fixture
def nested(client):
    """The same store, holding also a type whose IRI sits under the decision type's, and a note of it."""
    define(client, NOTE_TYPE, at=NOTES_TYPE)
    create(client, NOTES_TYPE, {"title": "A note"}, at=NOTE)
    return client


def test_an_artifact_under_a_nested_type_is_selected_by_its_path_below_its_own_type(nested):
    assert filed(NOTE) in places(export(nested, path="plan"))
    assert filed(NOTE) in places(export(nested, path="plan/a"))
    assert places(export(nested, path="notes")) == []
    assert places(export(nested, path="notes/plan")) == []


def test_an_artifact_under_a_nested_type_is_of_its_own_kind_and_not_the_kind_it_sits_under(nested):
    assert places(export(nested, NOTES_TYPE)) == [filed(NOTE)]
    assert places(export(nested, NOTES_TYPE, "plan")) == [filed(NOTE)]
    assert places(export(nested, "decision")) == of(at("decision", DECISIONS))
    assert places(export(nested, "decision", "notes")) == []


MALFORMED = ["/plan", "plan/", "plan//a", "/", "Plan", "plan a", "plan/..", "..", "plan_a", "plan%", "plan#a",
             "plan@1", "-plan", "plan.", "https://shop.example/kb/decision/plan"]


def refusal(answered):
    return [(fault.artifact, fault.place, fault.rule, fault.message) for fault in answered.faults]


def refused_alone(exported):
    """The faults of an export that gave one message, its refusal, and so no file and no position."""
    assert len(exported.messages) == 1 and exported.refused and not exported.files
    return refusal(exported)


@pytest.mark.parametrize("path", MALFORMED)
def test_an_export_by_what_is_not_a_path_is_refused_as_a_list_is_before_any_file_is_given(client, path):
    faults = refused_alone(export(client, path=path))
    assert [(rule, message) for _, _, rule, message in faults] == [("locator", (
        f"a path below a type is plain segments joined by single slashes, as pricing or pricing/discounts; {path!r} is not"
    ))]
    assert faults == refusal(listing(client, "", path=path))
    assert faults == refused_alone(export(client, "invoice", path))


@pytest.mark.parametrize("kind", ["invoice", iri("decision", "plan"), "https://shop.example/kb/Not A Kind"])
def test_an_export_by_a_kind_that_names_no_held_type_is_refused_as_a_list_is_before_any_file_is_given(client, kind):
    """A kind the store holds no type for, an IRI it holds an artifact at that is not a type, and what is no IRI."""
    faults = refused_alone(export(client, kind))
    assert faults == refusal(listing(client, kind))
    assert refused_alone(export(client, kind, "plan")) == refusal(listing(client, kind, path="plan"))
    assert len(faults) == 1


def test_an_export_by_a_kind_and_a_path_that_both_fail_to_convert_is_refused_for_each(client):
    faults = refused_alone(export(client, "https://shop.example/kb/Not A Kind", "/plan"))
    assert [rule for _, _, rule, _ in faults] == ["locator", "locator"]
    assert faults == refusal(listing(client, "https://shop.example/kb/Not A Kind", path="/plan"))


def test_an_export_selected_through_a_server_is_the_one_given_in_process(client, root, tmp_path, monkeypatch):
    arranged = tmp_path / "arranged"
    arranged.mkdir()
    selections = [("", "plan"), ("decision", ""), ("decision", "plan"), ("work-item", "plans/a"), ("", "pla")]
    refusals = [("invoice", ""), ("", "/plan"), ("invoice", "plan")]
    with kb_testing.served(root, arranged):
        monkeypatch.chdir(arranged)
        through = [export(kb_client.connect(), *selection) for selection in [*selections, *refusals]]
    in_process = [export(kb_client.connect(root), *selection) for selection in [*selections, *refusals]]
    assert [given.messages for given in through] == [given.messages for given in in_process]
    assert all(given.complete for given in through[:len(selections)])
    assert [len(given.files) for given in through[:len(selections)]] == [5, 7, 3, 1, 0]
    assert all(refused_alone(given) for given in through[len(selections):])
