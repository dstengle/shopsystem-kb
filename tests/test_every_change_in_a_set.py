"""Every change in a set is checked, not only the last a set makes to an artifact: its content against its type as the
set leaves it, a type's version moved on from the version it acted on; and a change acting on what an earlier one left
unfit is refused with a typed fault. Through the contract, each store under its own tmp_path."""
import copy

import pytest

from calls import CLIENT, DECISION_TYPE, apply, create, creation, define, read, replacement
from kb import client as kb_client
from kb.content import dumps
from kb.contract import kb_pb2

DECISION = "decision/price-reviews-happen-weekly"
SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]


@pytest.fixture
def client(root):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, DECISION_TYPE)
    return client


def _faults(response):
    assert (response.batch, list(response.results)) == ("", [])
    return [(fault.artifact, fault.path, fault.rule) for fault in response.faults]


def _addition(artifact_id, collection, item):
    return kb_pb2.Operation(append=kb_pb2.Addition(
        locator=kb_pb2.Locator(id=artifact_id, path=collection), content=dumps(item),
    ))


def test_a_middle_change_that_does_not_fit_its_type_is_refused_with_its_fault(client):
    response = apply(client, [
        creation("decision", "Price reviews happen weekly", {"sections": SECTIONS}),
        replacement(DECISION, {"sections": [{"title": "Purpose"}, SECTIONS[1]]}),
        replacement(DECISION, {"sections": SECTIONS}),
    ])
    assert _faults(response) == [(DECISION, "sections/0", "required")]
    assert [fault.rule for fault in read(client, DECISION).faults] == ["not-found"]


def test_a_first_change_fixed_by_a_later_one_in_the_set_is_still_refused(client):
    response = apply(client, [
        creation("decision", "Price reviews happen weekly", {"sections": SECTIONS[:1]}),
        replacement(DECISION, {"sections": SECTIONS}),
    ])
    assert _faults(response) == [(DECISION, "sections", "sections")]
    assert [fault.rule for fault in read(client, DECISION).faults] == ["not-found"]


@pytest.mark.parametrize("written", ["one line", {"keep-weekly": {"title": "Keep weekly"}}])
def test_adding_to_a_collection_an_earlier_change_wrote_as_a_single_value_is_refused(client, written):
    create(client, "decision", {"title": "Price reviews happen weekly", "sections": SECTIONS})
    response = apply(client, [
        replacement(DECISION, {"sections": SECTIONS, "options": written}),
        _addition(DECISION, "options", {"title": "Go monthly"}),
    ])
    assert _faults(response) == [(DECISION, "options", "type"), (DECISION, "options", "collection")]


def test_changing_what_an_earlier_change_wrote_as_a_single_value_comes_back_typed(client):
    response = apply(client, [
        creation("decision", "Price reviews happen weekly", {"sections": SECTIONS, "options": 5}),
        replacement(DECISION, {"sections": SECTIONS, "options": 6}),
    ])
    assert _faults(response) == [(DECISION, "options", "type"), (DECISION, "options", "type")]


def test_a_type_changed_twice_in_a_set_moves_its_version_on_each_time(client):
    first, second = copy.deepcopy(DECISION_TYPE), copy.deepcopy(DECISION_TYPE)
    first["version"] = second["version"] = 2
    first["schema"]["properties"]["owner"] = {"type": "string"}
    second["schema"]["properties"]["outcome"] = {"type": "string"}
    content = [{key: value for key, value in each.items() if key != "title"} for each in (first, second)]
    response = apply(client, [replacement("schema/decision", each) for each in content])
    assert _faults(response) == [("schema/decision", "version", "version")]
    assert read(client, "schema/decision").revision == 1


@pytest.mark.parametrize("earlier, faults", [
    ({"version": "two"}, [("schema/decision", "version", "type")]),
    ({"schema": None}, [("schema/decision", "version", "version"), ("schema/decision", "", "required")]),
])
def test_a_type_changed_after_an_earlier_change_left_it_unfit_comes_back_typed(client, earlier, faults):
    content = {key: value for key, value in DECISION_TYPE.items() if key != "title"}
    changed = copy.deepcopy(content)
    changed["version"] = 2
    changed["schema"]["properties"]["owner"] = {"type": "string"}
    first = {key: value for key, value in {**content, **earlier}.items() if value is not None}
    response = apply(client, [replacement("schema/decision", first), replacement("schema/decision", changed)])
    assert _faults(response) == faults
    assert read(client, "schema/decision").revision == 1
