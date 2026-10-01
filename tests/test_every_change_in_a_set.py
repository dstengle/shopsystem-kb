"""Every change in a set is checked, not only the last a set makes to an artifact: its content against its type as the
set leaves it, a type's version moved on from the version it acted on; and a change acting on what an earlier one left
unfit is refused with a typed fault; a key two creates carry refused beside every other fault of the set. Through
the contract, and, for a set of more than one kind of change, which the contract does not take, through kb.write's
own `land`; each store under its own tmp_path."""
import copy

import pytest

from calls import DECISION_TYPE, create, create_many, created, define, read, replace_many, replaced, start_a_store
from kb import changes, client as kb_client, signatures, store, values, write
from kb.content import dumps
from kb.signatures import Signed

DECISION = "decision/price-reviews-happen-weekly"
SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]


@pytest.fixture
def client(root):
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, DECISION_TYPE)
    return client


def _faults(response):
    assert response.refused
    return [(fault.artifact, fault.place, fault.rule) for fault in response.faults]


def _with_the_decision(client):
    create(client, "decision", {"title": "Price reviews happen weekly", "sections": SECTIONS})


def test_a_middle_change_that_does_not_fit_its_type_is_refused_with_its_fault(client):
    _with_the_decision(client)
    response = replace_many(client, [
        replaced(DECISION, {"sections": SECTIONS}),
        replaced(DECISION, {"sections": [{"title": "Purpose"}, SECTIONS[1]]}),
        replaced(DECISION, {"sections": SECTIONS}),
    ])
    assert _faults(response) == [(DECISION, "sections/0", "required")]
    assert read(client, DECISION).revision == 1


def test_a_first_change_fixed_by_a_later_one_in_the_set_is_still_refused(client):
    _with_the_decision(client)
    response = replace_many(client, [
        replaced(DECISION, {"sections": SECTIONS[:1]}),
        replaced(DECISION, {"sections": SECTIONS}),
    ])
    assert _faults(response) == [(DECISION, "sections", "sections")]
    assert read(client, DECISION).revision == 1


def _landed(root, operations) -> list:
    """A set of changes of more than one kind landed through kb.write; the faults it was refused for."""
    with store.opened(root) as held:
        try:
            write.land(held, operations, Signed(signatures.Actor("client", ""), "Change a decision"))
        except values.Refused as refused:
            return [(fault.artifact, fault.place, fault.rule) for fault in refused.faults]
    return []


@pytest.mark.parametrize("written", ["one line", {"keep-weekly": {"title": "Keep weekly"}}])
def test_adding_to_a_collection_an_earlier_change_wrote_as_a_single_value_is_refused(root, client, written):
    _with_the_decision(client)
    decision = values.artifact_id(DECISION)
    faults = _landed(root, [
        changes.Replace(values.Locator(decision, ()), values.content(dumps({"sections": SECTIONS, "options": written}))),
        changes.Add(values.Locator(decision, ("options",)), values.item(dumps({"title": "Go monthly"}))),
    ])
    assert faults == [(DECISION, "options", "type"), (DECISION, "options", "collection")]


def test_changing_what_an_earlier_change_wrote_as_a_single_value_comes_back_typed(client):
    _with_the_decision(client)
    response = replace_many(client, [
        replaced(DECISION, {"sections": SECTIONS, "options": 5}),
        replaced(DECISION, {"sections": SECTIONS, "options": 6}),
    ])
    assert _faults(response) == [(DECISION, "options", "type"), (DECISION, "options", "type")]


def test_a_type_changed_twice_in_a_set_moves_its_version_on_each_time(client):
    first, second = copy.deepcopy(DECISION_TYPE), copy.deepcopy(DECISION_TYPE)
    first["version"] = second["version"] = 2
    first["schema"]["properties"]["owner"] = {"type": "string"}
    second["schema"]["properties"]["outcome"] = {"type": "string"}
    content = [{key: value for key, value in each.items() if key != "title"} for each in (first, second)]
    response = replace_many(client, [replaced("schema/decision", each) for each in content])
    assert _faults(response) == [("schema/decision", "version", "version")]
    assert read(client, "schema/decision").revision == 1


@pytest.mark.parametrize("earlier, faults", [
    ({"version": "two"}, [("schema/decision", "version", "type")]),
    ({"schema": None}, [("schema/decision", "", "required"), ("schema/decision", "version", "version")]),
])
def test_a_type_changed_after_an_earlier_change_left_it_unfit_comes_back_typed(client, earlier, faults):
    content = {key: value for key, value in DECISION_TYPE.items() if key != "title"}
    changed = copy.deepcopy(content)
    changed["version"] = 2
    changed["schema"]["properties"]["owner"] = {"type": "string"}
    first = {key: value for key, value in {**content, **earlier}.items() if value is not None}
    response = replace_many(client, [replaced("schema/decision", first), replaced("schema/decision", changed)])
    assert _faults(response) == faults
    assert read(client, "schema/decision").revision == 1


def test_a_key_carried_twice_is_refused_beside_every_other_fault_of_the_set(client):
    refused = create_many(client, [
        created("decision", "Price reviews happen weekly", {"sections": SECTIONS}, key="pricing"),
        created("decision", "Price reviews happen daily", {"sections": SECTIONS[:1]}, key="pricing"),
    ])
    assert _faults(refused) == [("decision/price-reviews-happen-daily", "sections", "sections"), ("", "", "ref")]
    assert "'pricing'" in refused.faults[1].message


def test_a_key_carried_twice_is_refused_when_one_of_its_creates_does_not_convert(client):
    refused = create_many(client, [
        created("decision", "Price reviews happen weekly", {"sections": SECTIONS}, key="pricing"),
        created("Not A Kind", "Price reviews happen daily", {"sections": SECTIONS}, key="pricing"),
    ])
    assert [fault.rule for fault in refused.faults] == ["kind", "ref"]
    assert "'pricing'" in refused.faults[1].message
