"""Every change in a set is checked, not only the last a set makes to an artifact: its content against its type as the
set leaves it, a type's version moved on from the version it acted on; and a change acting on what an earlier one left
unfit is refused with a typed fault; an IRI two creates carry refused beside every other fault of the set, and a
create that links to its own IRI landing. Through the contract, and, for a set of more than one kind of change, which
the contract does not take, through kb.write's own `land`; each store under its own tmp_path."""
import copy

import pytest

from calls import (
    DECISION_TYPE, check, create, create_many, created, define, iri, read, replace_many, replaced, start_a_store, type_iri,
)
from kb import changes, client as kb_client, signatures, store, values, write
from kb.content import dumps, loads
from kb.signatures import Signed

DECISION = iri("decision", "price-reviews-happen-weekly")
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
    response = replace_many(client, [replaced(type_iri("decision"), each) for each in content])
    assert _faults(response) == [(type_iri("decision"), "version", "version")]
    assert read(client, type_iri("decision")).revision == 1


@pytest.mark.parametrize("earlier, faults", [
    ({"version": "two"}, [(type_iri("decision"), "version", "type")]),
    ({"schema": None}, [(type_iri("decision"), "", "required"), (type_iri("decision"), "version", "version")]),
])
def test_a_type_changed_after_an_earlier_change_left_it_unfit_comes_back_typed(client, earlier, faults):
    content = {key: value for key, value in DECISION_TYPE.items() if key != "title"}
    changed = copy.deepcopy(content)
    changed["version"] = 2
    changed["schema"]["properties"]["owner"] = {"type": "string"}
    first = {key: value for key, value in {**content, **earlier}.items() if value is not None}
    response = replace_many(client, [replaced(type_iri("decision"), first), replaced(type_iri("decision"), changed)])
    assert _faults(response) == faults
    assert read(client, type_iri("decision")).revision == 1


WEEKLY, MONTHLY = iri("decision", "weekly-price-reviews"), iri("decision", "monthly-price-reviews")


def test_an_iri_carried_twice_is_refused_beside_every_other_fault_of_the_set(client):
    refused = create_many(client, [
        created("decision", "Price reviews happen weekly", {"sections": SECTIONS}, at=WEEKLY),
        created("decision", "Price reviews happen daily", {"sections": SECTIONS}, at=WEEKLY),
        created("decision", "Prices are reviewed monthly", {"sections": SECTIONS[:1]}, at=MONTHLY),
    ])
    assert _faults(refused) == [(WEEKLY, "", "identity"), (MONTHLY, "sections", "sections")]
    assert repr(WEEKLY) in refused.faults[0].message
    assert read(client, WEEKLY).faults


def test_an_iri_carried_twice_is_refused_when_another_create_of_the_set_does_not_convert(client):
    refused = create_many(client, [
        created("decision", "Price reviews happen weekly", {"sections": SECTIONS}, at=WEEKLY),
        created("decision", "Price reviews happen daily", {"sections": SECTIONS}, at=WEEKLY),
        created("Not A Kind", "Prices are reviewed monthly", {"sections": SECTIONS}, at=MONTHLY),
    ])
    assert [(fault.artifact, fault.rule) for fault in refused.faults][0] == (WEEKLY, "identity")
    assert [fault.rule for fault in refused.faults] == ["identity", "locator"]
    assert repr(WEEKLY) in refused.faults[0].message


def test_a_create_in_a_set_that_links_to_its_own_iri_lands_the_link_resolving_within_the_set(client):
    landed = create_many(client, [
        created("decision", "Price reviews happen weekly", {"supersedes": WEEKLY, "sections": SECTIONS}, at=WEEKLY),
    ])
    assert not landed.refused, landed.faults
    assert [(result.id, result.revision) for result in landed.results] == [(WEEKLY, 1)]
    assert loads(read(client, WEEKLY, whole=True).content)["supersedes"] == WEEKLY
    assert not check(client).violations


def _sound(title, at=WEEKLY):
    return created("decision", title, {"sections": SECTIONS}, at=at)


def _carried_twice(refused, at=WEEKLY):
    """The faults saying the set carries an IRI more than once, each of them naming it and not the store."""
    found = [fault for fault in refused.faults if fault.rule == "identity"]
    assert all(fault.artifact == at and repr(at) in fault.message for fault in found)
    assert all("set" in fault.message and "store" not in fault.message for fault in found)
    return found


def test_two_sound_creates_at_one_iri_are_refused_for_it_once_on_the_second(client):
    refused = create_many(client, [_sound("Price reviews happen weekly"), _sound("Price reviews happen daily")])
    assert _faults(refused) == [(WEEKLY, "", "identity")]
    assert len(_carried_twice(refused)) == 1
    assert read(client, WEEKLY).faults


def test_an_iri_carried_twice_is_refused_when_the_first_create_at_it_is_refused_for_a_fault_of_its_own(client):
    refused = create_many(client, [_sound(""), _sound("Price reviews happen daily")])
    assert _faults(refused) == [(WEEKLY, "title", "title"), (WEEKLY, "", "identity")]
    assert len(_carried_twice(refused)) == 1


@pytest.mark.parametrize("wrong, rule", [
    (created("Not A Kind", "Price reviews happen daily", {"sections": SECTIONS}, at=WEEKLY), "locator"),
    (created("decision", "Price reviews happen daily", {"sections": SECTIONS}, at=WEEKLY, version=7), "version"),
])
def test_an_iri_carried_twice_is_refused_on_a_later_create_that_names_a_wrong_type_version(client, wrong, rule):
    refused = create_many(client, [_sound("Price reviews happen weekly"), wrong])
    assert [fault.rule for fault in refused.faults] == ["identity", rule]
    assert len(_carried_twice(refused)) == 1


@pytest.mark.parametrize("wrong, rule", [
    (created("Not A Kind", "Price reviews happen daily", {"sections": SECTIONS}, at=WEEKLY), "locator"),
    (created("decision", "Price reviews happen daily", {"sections": SECTIONS}, at=WEEKLY, version=7), "version"),
])
def test_an_iri_carried_twice_is_refused_after_a_create_that_names_a_wrong_type_version(client, wrong, rule):
    refused = create_many(client, [wrong, _sound("Price reviews happen weekly")])
    assert [fault.rule for fault in refused.faults] == [rule, "identity"]
    assert len(_carried_twice(refused)) == 1


def test_an_iri_carried_three_times_is_refused_once_on_each_create_after_the_first(client):
    refused = create_many(client, [_sound("Weekly"), _sound("Daily"), _sound("Monthly")])
    assert _faults(refused) == [(WEEKLY, "", "identity"), (WEEKLY, "", "identity")]
    assert len(_carried_twice(refused)) == 2
