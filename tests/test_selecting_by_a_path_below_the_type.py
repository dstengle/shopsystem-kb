"""A list and a follow select by the path below the type (decision/path-selection-is-a-segment-prefix): an artifact's
IRI less its own type's, matched by whole segments, so `plan` selects `plan` and `plan/a` and never `planning`;
across every type but the type that describes types when a list names no kind, and beside the kind when it names
one; a path that is not one refused for its shape before anything is looked up; a list by neither a kind nor a path
refused as a list with no kind was. Through the contract."""
import copy

import pytest

import kb.testing as kb_testing
from calls import (
    DECISION_TYPE, TAG_TYPE, TYPE_OF_TYPES, WORK_ITEM_TYPE, create, define, iri, listing, refs, start_a_store,
    targets, type_iri, version_iri,
)
from kb import client as kb_client
from kb.content import loads
from kb.contract import kb_pb2

SECTIONS = [
    {"title": "Purpose", "body": "Keep the shop running.\n"},
    {"title": "Rationale", "body": "It was agreed.\n"},
]
DECISIONS = ("plan", "plan/a", "plan/a/b", "planning", "plan-b", "plan.b", "old/plan")
WORK_ITEMS = ("plan", "plan/a", "plans/a")
ROADMAP = iri("decision", "roadmap")
NOT_HELD = (iri("work-item", "plan/ghost"), iri("work-item", "planning/ghost"))
NO_KIND = "a kind is named by its type's IRI, an IRI of kb's grammar; '' is not"


def leading_decision_type():
    """The decision type, whose artifacts may also lead to decisions and work items."""
    decision_type = copy.deepcopy(DECISION_TYPE)
    decision_type["schema"]["properties"]["leads"] = {
        "type": "array",
        "items": {"type": "string"},
        "ref": {"targets": targets("decision", "work-item"), "cardinality": "many", "parts": False, "on_delete": "refuse"},
    }
    return decision_type


def at(kind, paths):
    return [iri(kind, path) for path in paths]


@pytest.fixture
def client(root):
    """A store holding decisions and work items at paths below their types that share whole segments and parts of
    one, each work item pointing at the decision at `plan`, and a decision at `roadmap` that leads to every other
    and to two IRIs under the work items' type that the store does not hold."""
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, leading_decision_type())
    define(client, WORK_ITEM_TYPE)
    for each in at("decision", DECISIONS):
        create(client, "decision", {"title": each, "sections": SECTIONS}, at=each)
    for each in at("work-item", WORK_ITEMS):
        create(client, "work-item", {"title": each, "decisions": [iri("decision", "plan")]}, at=each)
    leads = [*at("decision", DECISIONS), *at("work-item", WORK_ITEMS), *NOT_HELD]
    create(client, "decision", {"title": "Roadmap", "leads": leads, "sections": SECTIONS}, at=ROADMAP)
    return client


def names(listed):
    assert not listed.faults, listed.faults
    return list(listed.ids)


def reached(followed):
    assert not followed.faults, followed.faults
    return [found.stub.id for found in followed.reached]


def refusal(answered):
    return [(fault.artifact, fault.place, fault.rule, fault.message) for fault in answered.faults]


def test_a_list_by_a_path_selects_whole_segments_across_every_type_in_the_order_of_names(client):
    assert names(listing(client, "", ids_only=True, path="plan")) == [
        iri("decision", "plan/a/b"), iri("decision", "plan/a"), iri("decision", "plan"),
        iri("work-item", "plan/a"), iri("work-item", "plan"),
    ]


@pytest.mark.parametrize("path, selected", [
    ("plan/a", [iri("decision", "plan/a/b"), iri("decision", "plan/a"), iri("work-item", "plan/a")]),
    ("plan/a/b", [iri("decision", "plan/a/b")]),
    ("planning", [iri("decision", "planning")]),
    ("plan.b", [iri("decision", "plan.b")]),
    ("old", [iri("decision", "old/plan")]),
    ("pla", []),
    ("a", []),
    ("plan/a/b/c", []),
    ("decision", []),
    ("decision/plan", []),
])
def test_a_list_by_a_path_matches_the_whole_path_or_its_first_segments_and_never_part_of_a_segment(client, path, selected):
    assert names(listing(client, "", ids_only=True, path=path)) == selected


def test_a_list_by_a_kind_and_a_path_gives_what_both_select(client):
    assert names(listing(client, "work-item", ids_only=True, path="plan")) == [
        iri("work-item", "plan/a"), iri("work-item", "plan"),
    ]
    assert names(listing(client, "decision", ids_only=True, path="plans")) == []
    with_fields = listing(client, "", fields={"title": iri("work-item", "plan/a")}, ids_only=True, path="plan")
    assert names(with_fields) == [iri("work-item", "plan/a")]


def test_a_list_across_types_gives_each_stub_through_its_own_artifacts_type(client):
    listed = listing(client, "", path="plan/a")
    assert not listed.faults, listed.faults
    assert [(stub.id, stub.type, stub.title, loads(stub.fields)) for stub in listed.stubs] == [
        (iri("decision", "plan/a/b"), version_iri("decision"), iri("decision", "plan/a/b"), {}),
        (iri("decision", "plan/a"), version_iri("decision"), iri("decision", "plan/a"), {}),
        (iri("work-item", "plan/a"), version_iri("work-item"), iri("work-item", "plan/a"),
         {"decisions": [iri("decision", "plan")]}),
    ]


def test_a_list_by_a_path_alone_never_gives_a_type_nor_an_iri_not_held(client):
    """A type may sit under the IRI of the type that describes types, and so have a path below its own type; an
    IRI linked to and not held is no artifact, whatever type it sits under."""
    under_the_type_of_types = f"{TYPE_OF_TYPES}/plan"
    define(client, {**copy.deepcopy(TAG_TYPE), "title": "Plan"}, at=under_the_type_of_types)
    listed = names(listing(client, "", ids_only=True, path="plan"))
    assert under_the_type_of_types not in listed and NOT_HELD[0] not in listed
    assert len(listed) == 5
    assert names(listing(client, TYPE_OF_TYPES, ids_only=True, path="plan")) == [under_the_type_of_types]


MALFORMED = ["/plan", "plan/", "plan//a", "/", "Plan", "plan a", "plan/..", "..", "plan_a", "plan%", "plan#a",
             "plan@1", "-plan", "plan.", "https://shop.example/kb/decision/plan"]


def not_a_path(path):
    return [("", "", "locator", (
        f"a path below a type is plain segments joined by single slashes, as pricing or pricing/discounts; {path!r} is not"
    ))]


@pytest.mark.parametrize("path", MALFORMED)
def test_a_list_by_what_is_not_a_path_is_refused_for_its_shape_before_anything_is_looked_up(client, path):
    assert refusal(listing(client, "", path=path)) == not_a_path(path)
    assert refusal(listing(client, "invoice", path=path)) == not_a_path(path)


@pytest.mark.parametrize("path", MALFORMED)
def test_a_follow_narrowed_to_what_is_not_a_path_is_refused_for_its_shape_before_anything_is_looked_up(client, path):
    assert refusal(refs(client, ROADMAP, 1, path=path)) == not_a_path(path)
    assert refusal(refs(client, iri("decision", "none-held"), 1, type_name="invoice", path=path)) == not_a_path(path)


def test_a_kind_and_a_path_that_both_fail_to_convert_are_each_refused(client):
    listed = client.List(kb_pb2.ListRequest(kind="not an iri", path="Not/A Path"))
    assert [fault.rule for fault in listed.refusal.faults] == ["locator", "locator"]
    assert listed.refusal.faults[1].message == not_a_path("Not/A Path")[0][3]
    followed = client.Follow(kb_pb2.FollowRequest(locator=kb_pb2.Locator(id="nowhere"), kind="not an iri", path="/"))
    assert [fault.rule for fault in followed.refusal.faults] == ["locator", "locator", "locator"]
    assert followed.refusal.faults[2].message == not_a_path("/")[0][3]


def test_a_list_by_neither_a_kind_nor_a_path_is_refused_as_a_list_with_no_kind(client):
    assert refusal(listing(client, "")) == [("", "", "locator", NO_KIND)]
    assert refusal(listing(client, "", fields={"title": "Roadmap"}, ids_only=True)) == [("", "", "locator", NO_KIND)]


def test_a_list_by_a_path_and_a_kind_the_store_holds_no_type_for_is_refused_for_the_kind(client):
    refused = listing(client, "invoice", path="plan")
    assert [(fault.artifact, fault.place, fault.rule) for fault in refused.faults] == [("", "", "kind")]
    assert repr(type_iri("invoice")) in refused.faults[0].message


def test_a_follow_narrowed_to_a_path_keeps_whole_segments_whatever_the_type_and_an_iri_not_held_by_its_nearest_type(client):
    """An IRI not held has no type of its own: its path is read below the nearest held type it sits under, and it
    is given as it is without a path, the IRI alone, marked as not held."""
    followed = refs(client, ROADMAP, 1, path="plan")
    assert reached(followed) == [
        iri("decision", "plan"), iri("decision", "plan/a"), iri("decision", "plan/a/b"),
        iri("work-item", "plan"), iri("work-item", "plan/a"), NOT_HELD[0],
    ]
    assert followed.reached[-1].stub == kb_pb2.Stub(field="leads", id=NOT_HELD[0], not_held=True)
    assert reached(refs(client, ROADMAP, 1, path="plan/a")) == [
        iri("decision", "plan/a"), iri("decision", "plan/a/b"), iri("work-item", "plan/a"),
    ]
    assert reached(refs(client, ROADMAP, 1, path="pla")) == []


def test_a_follow_narrowed_to_a_kind_and_a_path_keeps_what_both_select(client):
    assert reached(refs(client, ROADMAP, 1, type_name="work-item", path="plan")) == [
        iri("work-item", "plan"), iri("work-item", "plan/a"),
    ]


def test_a_follow_narrowed_to_a_path_does_not_narrow_the_artifact_followed_from(client):
    assert reached(refs(client, ROADMAP, 1, path="roadmap")) == []
    assert reached(refs(client, iri("decision", "plan"), 1, inward=True, path="plan")) == [
        iri("work-item", "plan/a"), iri("work-item", "plan"),
    ]
    assert reached(refs(client, iri("decision", "plan"), 1, inward=True, path="roadmap")) == [ROADMAP]


def test_a_list_and_a_follow_by_a_path_are_answered_through_a_server_as_in_process(client, root, tmp_path, monkeypatch):
    arranged = tmp_path / "arranged"
    arranged.mkdir()
    with kb_testing.served(root, arranged):
        monkeypatch.chdir(arranged)
        through = kb_client.connect()
        listed = listing(through, "", path="plan")
        assert listed.stubs == listing(kb_client.connect(root), "", path="plan").stubs
        followed = refs(through, ROADMAP, 1, path="plan")
        assert followed.reached == refs(kb_client.connect(root), ROADMAP, 1, path="plan").reached
        assert refusal(listing(through, "", path="/plan")) == not_a_path("/plan")
    assert [stub.id for stub in listed.stubs] == [
        iri("decision", "plan/a/b"), iri("decision", "plan/a"), iri("decision", "plan"),
        iri("work-item", "plan/a"), iri("work-item", "plan"),
    ]
    assert len(followed.reached) == 6
