import re

from pytest_bdd import given, parsers, scenarios, then, when

from calls import (
    CLIENT, DECISION_TYPE, WORK_ITEM_TYPE, apply, create, creation, define, journal, listing, read,
    removal, replacement, write,
)
import held
from kb import client as kb_client
from kb.content import loads
from kb.contract import kb_pb2

scenarios("make-several-changes-in-one-go.feature")

DECISION = "decision/price-reviews-happen-weekly"
WORK_ITEM = "work-item/move-the-review-to-mondays"
SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]


@given("a store holding a decision type and a work item", target_fixture="client")
def _store_with_a_decision_type_and_a_work_item(root):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, DECISION_TYPE)
    define(client, WORK_ITEM_TYPE)
    create(client, "work-item", {"title": "Move the review to Mondays"})
    return client


@when(
    "the client asks, in one go, for a decision to be created and the work item to point at it, in that order, "
    "saying which role and why",
    target_fixture="applied",
)
def _create_and_point_at_it(client):
    return apply(client, [
        creation("decision", "Price reviews happen weekly", {"sections": SECTIONS}),
        replacement(WORK_ITEM, {"decisions": [DECISION]}),
    ], message="Move price reviews to weekly")


@then("the client is given one name for the set, which the client never asked for")
def _given_a_name_for_the_set(applied):
    assert not applied.faults, applied.faults
    assert applied.batch
    assert "batch" not in kb_pb2.ApplyRequest.DESCRIPTOR.fields_by_name


@then("each change also comes back with its own result")
def _a_result_for_each_change(applied):
    assert [(result.id, result.revision) for result in applied.results] == [(DECISION, 1), (WORK_ITEM, 2)]


@then("the store's history shows the set as one change")
def _one_change_in_the_history(client, applied):
    in_set = [entry for entry in held.history(client) if entry.batch == applied.batch]
    assert [(entry.op, entry.artifact, entry.revision) for entry in in_set] == [
        ("create", DECISION, 1), ("write", WORK_ITEM, 2),
    ]
    assert {(entry.actor.role, entry.message) for entry in in_set} == {("client", "Move price reviews to weekly")}


@given("a set whose second change is missing a section its type requires", target_fixture="bad_set")
def _a_set_with_a_bad_second_change():
    return [
        creation("decision", "Price reviews happen weekly", {"sections": SECTIONS}),
        creation("decision", "Prices are reviewed monthly", {"sections": []}),
    ]


@when("the client asks for the set, saying which role and why", target_fixture="attempt")
def _ask_for_the_set(root, client, bad_set):
    before = held.holds(root)
    response = apply(client, bad_set, message="Record two decisions")
    return {"response": response, "before": before, "after": held.holds(root)}


@then("the set is rejected because a change in it does not fit its type")
def _set_rejected(attempt):
    refused = attempt["response"]
    assert (refused.batch, list(refused.results)) == ("", [])
    assert {(fault.artifact, fault.rule) for fault in refused.faults} == {("decision/prices-are-reviewed-monthly", "sections")}


@then("the store holds neither change")
def _neither_change_held(client, attempt):
    assert attempt["after"] == attempt["before"]
    for name in (DECISION, "decision/prices-are-reviewed-monthly"):
        assert [fault.rule for fault in read(client, name).faults] == ["not-found"]


@then("every fault in the set comes back, not only the first")
def _every_fault_back(attempt):
    assert [(fault.path, fault.message) for fault in attempt["response"].faults] == [
        ("sections", "the sections the type requires must all be present, in order; 'Purpose' is missing"),
        ("sections", "the sections the type requires must all be present, in order; 'Rationale' is missing"),
    ]


@then("the changes the history shows under the name the client was given for the set are exactly those two")
def _the_set_in_the_history(client, applied):
    assert not applied.faults, applied.faults
    shown = journal(client, batch=applied.batch)
    assert not shown.faults, shown.faults
    assert [(entry.op, entry.artifact, entry.revision, entry.batch) for entry in shown.entries] == [
        ("create", DECISION, 1, applied.batch), ("write", WORK_ITEM, 2, applied.batch),
    ]


@when("the client asks, in one go, for the work item to be changed twice, saying which role and why", target_fixture="applied")
def _change_the_work_item_twice(client):
    return apply(client, [replacement(WORK_ITEM, {"decisions": []}), replacement(WORK_ITEM, {})],
                 message="Change the work item twice")


@then("the store's history holds an entry for each of the two changes")
def _an_entry_for_each_change(client, applied):
    assert not applied.faults, applied.faults
    in_set = [entry for entry in held.history(client) if entry.batch == applied.batch]
    assert [(entry.op, entry.artifact) for entry in in_set] == [("write", WORK_ITEM), ("write", WORK_ITEM)]


@then("each entry records the version that change left behind")
def _each_entry_its_own_version(client, applied):
    in_set = [entry for entry in held.history(client) if entry.batch == applied.batch]
    assert [entry.revision for entry in in_set] == [2, 3]
    assert [(result.id, result.revision) for result in applied.results] == [(WORK_ITEM, 2), (WORK_ITEM, 3)]


@then("the work item's version has gone up by two")
def _two_versions_on(client):
    assert read(client, WORK_ITEM).revision == 3


MONTHLY = "decision/prices-are-reviewed-monthly"


def _nothing_by_that_name(root, client):
    return replacement(DECISION, {"sections": SECTIONS})


def _still_pointed_at(root, client):
    create(client, "decision", {"title": "Price reviews happen weekly", "sections": SECTIONS})
    assert not write(client, WORK_ITEM, {"decisions": [DECISION]}).faults
    return removal(DECISION)


SECOND_CHANGES = {
    "the second change names an artifact the store holds nothing under": _nothing_by_that_name,
    "the second change removes an artifact something still points at": _still_pointed_at,
}


@when(
    parsers.re(f"the client asks, in one go, for a set in which (?P<fault>{'|'.join(map(re.escape, SECOND_CHANGES))}), "
               "saying which role and why"),
    target_fixture="attempt",
)
def _ask_for_a_set_stopped(root, client, fault):
    second = SECOND_CHANGES[fault](root, client)
    before, history = held.holds(root), held.history(client)
    response = apply(client, [creation("decision", "Prices are reviewed monthly", {"sections": SECTIONS}), second],
                     message="Record a decision and change another")
    return {"response": response, "before": before, "after": held.holds(root), "history": history}


def _refused_with(attempt, faults):
    refused = attempt["response"]
    assert (refused.batch, list(refused.results)) == ("", [])
    assert [(fault.artifact, fault.path, fault.rule) for fault in refused.faults] == faults
    return refused.faults[0].message


@then("the set is rejected because the store holds nothing by that name, and the name asked for is given back")
def _rejected_for_nothing_there(attempt):
    assert DECISION in _refused_with(attempt, [(DECISION, "", "not-found")])


@then("the set is rejected because something still points at it")
def _rejected_for_a_link_in_the_way(attempt):
    assert WORK_ITEM in _refused_with(attempt, [(WORK_ITEM, "decisions/0", "on_delete")])


@then("the store holds none of the changes in the set")
def _none_of_the_set_held(client, attempt):
    assert attempt["after"] == attempt["before"]
    assert [fault.rule for fault in read(client, MONTHLY).faults] == ["not-found"]


@then("the store's history holds no entry for any of them")
def _no_entry_for_the_set(client, attempt):
    assert held.history(client) == attempt["history"]
    assert not [entry for entry in attempt["history"] if entry.artifact == MONTHLY]


@when("the client asks, in one go, for a set holding no changes at all, saying which role and why", target_fixture="attempt")
def _ask_for_an_empty_set(root, client):
    before = {
        "names": [stub.id for stub in listing(client, "decision", ids_only=True).stubs],
        "files": held.holds(root),
        "entries": len(journal(client).entries),
    }
    return {**before, "response": apply(client, [], message="Change nothing")}


@then("the set is rejected because a set must hold at least one change")
def _rejected_for_being_empty(attempt):
    assert _refused_with(attempt, [("", "", "operations")]).startswith("a set must hold at least one change")


REPLACED = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs now move daily.\n"},
]


@when(
    "the client asks, in one go, for the work item to point at a decision and that decision to be created, in that "
    "order, saying which role and why",
    target_fixture="applied",
)
def _point_at_it_and_create(client):
    return apply(client, [
        replacement(WORK_ITEM, {"decisions": [DECISION]}),
        creation("decision", "Price reviews happen weekly", {"sections": SECTIONS}),
    ], message="Move price reviews to weekly")


@when(
    "the client asks, in one go, for a decision to be created and that decision to be replaced, in that order, "
    "saying which role and why",
    target_fixture="applied",
)
def _create_and_replace(client):
    return apply(client, [
        creation("decision", "Price reviews happen weekly", {"sections": SECTIONS}),
        replacement(DECISION, {"sections": REPLACED}),
    ], message="Record a decision and revise it")


@when(
    "the client asks, in one go, for a decision to be replaced and that decision to be created, in that order, "
    "saying which role and why",
    target_fixture="attempt",
)
def _replace_and_create(root, client):
    before, history = held.holds(root), held.history(client)
    response = apply(client, [
        replacement(DECISION, {"sections": REPLACED}),
        creation("decision", "Price reviews happen weekly", {"sections": SECTIONS}),
    ], message="Revise a decision and record it")
    return {"response": response, "before": before, "after": held.holds(root), "history": history}


@then("the set lands, and the work item points at the new decision")
def _lands_pointing_at_the_new_decision(client, applied):
    assert not applied.faults, applied.faults
    assert applied.batch
    assert loads(read(client, WORK_ITEM, whole=True).content)["decisions"] == [DECISION]
    assert not read(client, DECISION).faults


@then("the set lands, and the decision holds the replacement")
def _lands_holding_the_replacement(client, applied):
    assert not applied.faults, applied.faults
    assert applied.batch
    assert loads(read(client, DECISION, whole=True).content)["sections"] == REPLACED


WEEKLY, DAILY = DECISION, "decision/price-reviews-happen-daily"


@given("the decision type lets a decision point at another decision")
def _decisions_may_point_at_decisions():
    assert DECISION_TYPE["schema"]["properties"]["supersedes"]["ref"]["targets"] == ["decision"]


@when(
    "the client asks, in one go, for two decisions to be created, each pointing at the other, "
    "saying which role and why",
    target_fixture="applied",
)
def _create_two_pointing_at_each_other(client):
    return apply(client, [
        creation("decision", "Price reviews happen weekly", {"supersedes": DAILY, "sections": SECTIONS}),
        creation("decision", "Price reviews happen daily", {"supersedes": WEEKLY, "sections": SECTIONS}),
    ], message="Record two decisions that point at each other")


@then("the set lands")
def _the_set_lands(applied):
    assert not applied.faults, applied.faults
    assert [(result.id, result.revision) for result in applied.results] == [(WEEKLY, 1), (DAILY, 1)]


@then("the store holds both decisions, each pointing at the other")
def _both_held_pointing_at_each_other(client):
    assert loads(read(client, WEEKLY, whole=True).content)["supersedes"] == DAILY
    assert loads(read(client, DAILY, whole=True).content)["supersedes"] == WEEKLY
