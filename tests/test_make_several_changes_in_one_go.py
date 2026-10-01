import copy
import re

from pytest_bdd import given, parsers, scenarios, then, when

from calls import (
    CLIENT, DECISION_TYPE, WORK_ITEM_TYPE, add_many, added, create, create_many, created, define, journal, listing,
    read, refs, remove_many, removed, replace, replace_many, replaced,
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


NEW_WORK_ITEM = "work-item/review-prices-on-mondays"


@when(
    "the client asks, in one go, for a decision and a work item to be created, in that order, saying which role and why",
    target_fixture="applied",
)
def _create_a_decision_and_a_work_item(client):
    return create_many(client, [
        created("decision", "Price reviews happen weekly", {"sections": SECTIONS}),
        created("work-item", "Review prices on Mondays", {}),
    ], message="Move price reviews to weekly")


@when("the client asks, in one go, for a decision to be created, saying which role and why", target_fixture="sets")
def _create_a_decision_in_one_go(client):
    return [create_many(client, [created("decision", "Price reviews happen weekly", {"sections": SECTIONS})],
                        message="Record a decision")]


@when(
    "the client then asks, in one go, for the work item to be replaced so that it points at that decision, "
    "saying which role and why"
)
def _then_replace_the_work_item_in_one_go(client, sets):
    sets.append(replace_many(client, [replaced(WORK_ITEM, {"decisions": [DECISION]})], message="Point at it"))


@then("both sets land")
def _both_sets_land(sets):
    assert [(each.refused, bool(each.batch)) for each in sets] == [(False, True), (False, True)], sets


@then("the history shows two sets, the create's and the replacement's")
def _two_sets_in_the_history(client, sets):
    shown = [[(entry.op, entry.artifact, entry.revision) for entry in held.history(client) if entry.batch == each.batch]
             for each in sets]
    assert shown == [[("create", DECISION, 1)], [("write", WORK_ITEM, 2)]]
    assert sets[0].batch != sets[1].batch


@then("the client is given one name for the set, which the client never asked for")
def _given_a_name_for_the_set(applied):
    assert not applied.refused, applied.faults
    assert applied.batch
    assert "batch" not in kb_pb2.CreateManyRequest.DESCRIPTOR.fields_by_name


@then("each change also comes back with its own result")
def _a_result_for_each_change(applied):
    assert [(result.id, result.revision) for result in applied.results] == [(DECISION, 1), (NEW_WORK_ITEM, 1)]


@then("the store's history shows the set as one change")
def _one_change_in_the_history(client, applied):
    in_set = [entry for entry in held.history(client) if entry.batch == applied.batch]
    assert [(entry.op, entry.artifact, entry.revision) for entry in in_set] == [
        ("create", DECISION, 1), ("create", NEW_WORK_ITEM, 1),
    ]
    assert {(entry.actor.role, entry.message) for entry in in_set} == {("client", "Move price reviews to weekly")}


@given("a set whose second change is missing a section its type requires", target_fixture="bad_set")
def _a_set_with_a_bad_second_change():
    return [
        created("decision", "Price reviews happen weekly", {"sections": SECTIONS}),
        created("decision", "Prices are reviewed monthly", {"sections": []}),
    ]


@when("the client asks for the set, saying which role and why", target_fixture="attempt")
def _ask_for_the_set(root, client, bad_set):
    before = held.holds(root)
    response = create_many(client, bad_set, message="Record two decisions")
    return {"response": response, "before": before, "after": held.holds(root)}


@then("the set is rejected because a change in it does not fit its type")
def _set_rejected(attempt):
    refused = attempt["response"]
    assert refused.refused
    assert {(fault.artifact, fault.rule) for fault in refused.faults} == {("decision/prices-are-reviewed-monthly", "sections")}


@then("the store holds neither change")
def _neither_change_held(client, attempt):
    assert attempt["after"] == attempt["before"]
    for name in (DECISION, "decision/prices-are-reviewed-monthly"):
        assert [fault.rule for fault in read(client, name).faults] == ["not-found"]


@then("every fault in the set comes back, not only the first")
def _every_fault_back(attempt):
    assert [(fault.place, fault.message) for fault in attempt["response"].faults] == [
        ("sections", "the sections the type requires must all be present, in order; 'Purpose' is missing"),
        ("sections", "the sections the type requires must all be present, in order; 'Rationale' is missing"),
    ]


@then("the changes the history shows under the name the client was given for the set are exactly those two")
def _the_set_in_the_history(client, applied):
    assert not applied.refused, applied.faults
    shown = journal(client, batch=applied.batch)
    assert not shown.faults, shown.faults
    assert [(entry.op, entry.artifact, entry.revision, entry.batch) for entry in shown.entries] == [
        ("create", DECISION, 1, applied.batch), ("create", NEW_WORK_ITEM, 1, applied.batch),
    ]


@when("the client asks, in one go, for the work item to be changed twice, saying which role and why", target_fixture="applied")
def _change_the_work_item_twice(client):
    return replace_many(client, [replaced(WORK_ITEM, {"decisions": []}), replaced(WORK_ITEM, {})],
                        message="Change the work item twice")


@then("the store's history holds an entry for each of the two changes")
def _an_entry_for_each_change(client, applied):
    assert not applied.refused, applied.faults
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


def _nothing_by_that_name(client):
    """A set of replacements whose second names a decision the store does not hold."""
    return lambda message: replace_many(client, [
        replaced(WORK_ITEM, {"decisions": []}), replaced(DECISION, {"sections": SECTIONS}),
    ], message=message)


def _still_pointed_at(client):
    """A set of removals whose second removes the decision the work item points at."""
    create(client, "decision", {"title": "Prices are reviewed monthly", "sections": SECTIONS})
    create(client, "decision", {"title": "Price reviews happen weekly", "sections": SECTIONS})
    assert not replace(client, WORK_ITEM, {"decisions": [DECISION]}).faults
    return lambda message: remove_many(client, [removed(MONTHLY), removed(DECISION)], message=message)


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
    ask = SECOND_CHANGES[fault](client)
    return _attempted(root, client, lambda: ask("Change two artifacts"))


def _refused_with(attempt, faults):
    refused = attempt["response"]
    assert refused.refused
    assert [(fault.artifact, fault.place, fault.rule) for fault in refused.faults] == faults
    return refused.faults[0].message


@then("the set is rejected because the store holds nothing by that name, and the name asked for is given back")
def _rejected_for_nothing_there(attempt):
    assert DECISION in _refused_with(attempt, [(DECISION, "", "not-found")])


@then("the set is rejected because something still points at it")
def _rejected_for_a_link_in_the_way(attempt):
    assert WORK_ITEM in _refused_with(attempt, [(WORK_ITEM, "decisions/0", "on_delete")])


@then("the store holds none of the changes in the set")
def _none_of_the_set_held(attempt):
    assert attempt["after"] == attempt["before"]


@then("the store's history holds no entry for any of them")
def _no_entry_for_the_set(client, attempt):
    assert held.history(client) == attempt["history"]


@when("the client asks, in one go, for a set holding no changes at all, saying which role and why", target_fixture="attempt")
def _ask_for_an_empty_set(root, client):
    before = {
        "names": [stub.id for stub in listing(client, "decision", ids_only=True).stubs],
        "files": held.holds(root),
        "entries": len(journal(client).entries),
    }
    return {**before, "response": create_many(client, [], message="Change nothing")}


@then("the set is rejected because a set must hold at least one change")
def _rejected_for_being_empty(attempt):
    assert _refused_with(attempt, [("", "", "operations")]).startswith("a set must hold at least one change")


KEYED_CREATES = {
    "a decision to be created carrying a key and a work item to be created pointing at it by that key": lambda: [
        created("decision", "Price reviews happen weekly", {"sections": SECTIONS}, key="weekly"),
        created("work-item", "Review prices on Mondays", {"decisions": ["@weekly"]}),
    ],
    "a work item to be created pointing at a decision by the key its create carries and that decision to be created "
    "with it": lambda: [
        created("work-item", "Review prices on Mondays", {"decisions": ["@weekly"]}),
        created("decision", "Price reviews happen weekly", {"sections": SECTIONS}, key="weekly"),
    ],
}


@when(
    parsers.re(f"the client asks, in one go, for (?P<creates>{'|'.join(map(re.escape, KEYED_CREATES))}), in that "
               "order, saying which role and why"),
    target_fixture="applied",
)
def _create_pointing_by_key(client, creates):
    return create_many(client, KEYED_CREATES[creates](), message="Move price reviews to weekly")


@then("the set lands, and the new work item points at the new decision")
def _lands_pointing_by_key(client, applied):
    assert not applied.refused, applied.faults
    assert loads(read(client, NEW_WORK_ITEM, whole=True).content)["decisions"] == [DECISION]
    assert not read(client, DECISION).faults


WEEKLY, DAILY = DECISION, "decision/price-reviews-happen-daily"


@given("the decision type lets a decision point at another decision")
def _decisions_may_point_at_decisions():
    assert DECISION_TYPE["schema"]["properties"]["supersedes"]["ref"]["targets"] == ["decision"]


@when(
    "the client asks, in one go, for two decisions to be created, each carrying a key and pointing at the other by "
    "the key the other's create carries, saying which role and why",
    target_fixture="applied",
)
def _create_two_pointing_at_each_other(client):
    return create_many(client, [
        created("decision", "Price reviews happen weekly", {"supersedes": "@daily", "sections": SECTIONS}, key="weekly"),
        created("decision", "Price reviews happen daily", {"supersedes": "@weekly", "sections": SECTIONS}, key="daily"),
    ], message="Record two decisions that point at each other")


@then("the set lands")
def _the_set_lands(applied):
    assert not applied.refused, applied.faults
    assert [(result.id, result.revision) for result in applied.results] == [(WEEKLY, 1), (DAILY, 1)]


@then("the store holds both decisions, each pointing at the other")
def _both_held_pointing_at_each_other(client):
    assert loads(read(client, WEEKLY, whole=True).content)["supersedes"] == DAILY
    assert loads(read(client, DAILY, whole=True).content)["supersedes"] == WEEKLY


@then("the set is rejected because the store was busy with another change")
def _set_rejected_as_busy(applied):
    assert applied.refused
    assert [(fault.artifact, fault.place, fault.rule) for fault in applied.faults] == [("", "", "busy")]
    assert applied.faults[0].message.startswith("the store was busy with another change")


@then("the same set may be asked for again")
def _asked_for_again(client, holding):
    holding.let_go()
    again = _create_a_decision_and_a_work_item(client)
    assert not again.refused, again.faults
    assert [(result.id, result.revision) for result in again.results] == [(DECISION, 1), (NEW_WORK_ITEM, 1)]


@given("work items may carry a collection of tasks, each of which may point at a decision")
def _work_items_carry_tasks(client):
    schema = copy.deepcopy(WORK_ITEM_TYPE["schema"])
    schema["parts"] = {"tasks": {"items": {
        "type": "object",
        "properties": {"title": {"type": "string"}, "decision": DECISION_TYPE["schema"]["properties"]["supersedes"]},
        "required": ["title"],
    }}}
    assert not replace(client, "schema/work-item", {"version": 2, "schema": schema}).faults


LINKED_TO_THE_KEY = {
    "in its content": ({"decisions": ["@weekly"]}, lambda content: content["decisions"][0]),
    "inside one of its tasks": (
        {"tasks": [{"title": "Move the meeting", "decision": "@weekly"}]}, lambda content: content["tasks"][0]["decision"],
    ),
}


@when(
    parsers.re(
        "the client asks, in one go, for a decision to be created carrying a key of the client's choosing and a work "
        f"item to be created with a link to that key (?P<where>{'|'.join(map(re.escape, LINKED_TO_THE_KEY))}), saying "
        "which role and why"
    ),
    target_fixture="applied",
)
def _create_linking_to_a_key(client, where):
    return create_many(client, [
        created("decision", "Price reviews happen weekly", {"sections": SECTIONS}, key="weekly"),
        created("work-item", "Review prices on Mondays", LINKED_TO_THE_KEY[where][0]),
    ], message="Move price reviews to weekly")


@then(parsers.re(
    f"the new work item points, (?P<where>{'|'.join(map(re.escape, LINKED_TO_THE_KEY))}), at the decision that create "
    "made"
))
def _points_at_the_decision_made(client, applied, where):
    assert not applied.refused, applied.faults
    made = applied.results[0].id
    assert [found.stub.id for found in refs(client, made, 1, inward=True).reached] == [NEW_WORK_ITEM]
    assert LINKED_TO_THE_KEY[where][1](loads(read(client, NEW_WORK_ITEM, whole=True).content)) == made


@then("the link holds the name the store gave the decision, not the key")
def _holds_the_name_not_the_key(root, applied):
    assert applied.results[0].id == DECISION
    assert "@weekly" not in held.text(root, NEW_WORK_ITEM)
    assert DECISION in held.text(root, NEW_WORK_ITEM)


THREE_TITLES = ["Price reviews happen weekly", "Prices are rounded to the cent", "Discounts end on Sundays"]


@when("the client asks, in one go, for three decisions with titles of their own to be created, saying which role and why",
      target_fixture="applied")
def _create_three_decisions(client):
    return create_many(client, [created("decision", title, {"sections": SECTIONS}) for title in THREE_TITLES],
                       message="Record three decisions")


@then("the client is given a result for each create, in the order of the set")
def _a_result_for_each_create(applied):
    assert not applied.refused, applied.faults
    assert [result.revision for result in applied.results] == [1, 1, 1]


@then("each result gives the name the store gave the decision made by the create in that place")
def _each_result_names_its_decision(client, applied):
    assert [read(client, result.id).title for result in applied.results] == THREE_TITLES
    assert [result.id for result in applied.results] == [
        "decision/price-reviews-happen-weekly", "decision/prices-are-rounded-to-the-cent", "decision/discounts-end-on-sundays",
    ]


def _attempted(root, client, ask):
    """What a set the store may refuse did: its answer, and the store and its history before and after."""
    before, history = held.holds(root), held.history(client)
    response = ask()
    return {"response": response, "before": before, "after": held.holds(root), "history": history}


@when(
    "the client asks, in one go, for a decision and a work item to be created, the work item pointing at a key no "
    "create in the set carries, saying which role and why",
    target_fixture="attempt",
)
def _create_pointing_at_a_key_nothing_carries(root, client):
    return _attempted(root, client, lambda: create_many(client, [
        created("decision", "Price reviews happen weekly", {"sections": SECTIONS}, key="weekly"),
        created("work-item", "Review prices on Mondays", {"decisions": ["@monthly"]}),
    ], message="Move price reviews to weekly")) | {"key": "'@monthly'"}


@then("the set is rejected because the link lands on nothing")
def _rejected_landing_on_nothing(attempt):
    assert attempt["response"].refused
    assert [(fault.artifact, fault.place, fault.rule) for fault in attempt["response"].faults] == [
        (NEW_WORK_ITEM, "decisions/0", "ref"),
    ]


@then("the key is given back")
def _the_key_given_back(attempt):
    assert attempt["key"] in attempt["response"].faults[0].message


@when("the client asks, in one go, for two decisions to be created, both carrying the same key, saying which role and why",
      target_fixture="attempt")
def _create_two_with_one_key(root, client):
    return {**_attempted(root, client, lambda: create_many(client, [
        created("decision", "Price reviews happen weekly", {"sections": SECTIONS}, key="pricing"),
        created("decision", "Price reviews happen daily", {"sections": SECTIONS}, key="pricing"),
    ], message="Record two decisions")), "key": "'pricing'"}


@then("the set is rejected because a key names one create in the set")
def _rejected_for_a_key_carried_twice(attempt):
    assert attempt["response"].refused
    faults = attempt["response"].faults
    assert [(fault.artifact, fault.place, fault.rule) for fault in faults] == [("", "", "ref")]
    assert faults[0].message.startswith("a key names one create in the set")


@when(
    "the client asks, in one go, for a decision to be created carrying a key and a work item to be created pointing "
    "at that key together with a place inside the decision, saying which role and why",
    target_fixture="attempt",
)
def _create_pointing_at_a_place_by_key(root, client):
    return {**_attempted(root, client, lambda: create_many(client, [
        created("decision", "Price reviews happen weekly", {"sections": SECTIONS}, key="weekly"),
        created("work-item", "Review prices on Mondays", {"decisions": ["@weekly#purpose"]}),
    ], message="Move price reviews to weekly")), "reference": "'@weekly#purpose'"}


@then("the reference is given back")
def _the_reference_given_back(attempt):
    assert attempt["reference"] in attempt["response"].faults[0].message


SECOND_WORK_ITEM = "work-item/print-the-new-price-labels"


@given("the store also holds a second work item, and work items carry a collection of tasks")
def _a_second_work_item_and_tasks(client):
    _work_items_carry_tasks(client)
    create(client, "work-item", {"title": "Print the new price labels"})


@given(
    "the client read the work item at its first version, and another client has since replaced it",
    target_fixture="moved",
)
def _read_then_replaced_by_another(root, client):
    seen = read(client, WORK_ITEM).revision
    assert seen == 1
    since = replace(kb_client.connect(root), WORK_ITEM, {"decisions": []}, message="Point at no decision")
    assert since.revision == seen + 1
    return {"seen": seen, "stands_at": since.revision, "held": held.holds(root)}


SAYING_WHAT_WAS_READ = {
    "the work item and the second work item to be replaced": lambda client, seen: replace_many(client, [
        replaced(WORK_ITEM, {}, revision=seen), replaced(SECOND_WORK_ITEM, {}),
    ], message="Replace both work items"),
    "a task to be added to the work item and one to the second work item": lambda client, seen: add_many(client, [
        added(WORK_ITEM, "tasks", {"title": "Move the meeting"}, revision=seen),
        added(SECOND_WORK_ITEM, "tasks", {"title": "Order the labels"}),
    ], message="Give each work item a task"),
    "the work item and the second work item to be removed": lambda client, seen: remove_many(client, [
        removed(WORK_ITEM, revision=seen), removed(SECOND_WORK_ITEM),
    ], message="Remove both work items"),
}


@when(
    parsers.re(
        f"the client asks, in one go, for (?P<changes>{'|'.join(map(re.escape, SAYING_WHAT_WAS_READ))}), the change to "
        "the work item saying the version the client read it at, saying which role and why"
    ),
    target_fixture="applied",
)
def _ask_saying_what_was_read(client, moved, changes):
    return SAYING_WHAT_WAS_READ[changes](client, moved["seen"])


@then("the set is rejected because the artifact moved since it was read")
def _set_rejected_as_moved(applied):
    assert applied.refused
    assert [(fault.artifact, fault.place, fault.rule) for fault in applied.faults] == [(WORK_ITEM, "", "revision")]
    assert applied.faults[0].message.startswith("the artifact moved since it was read")


@then("the version the work item stands at is given back")
def _given_where_the_work_item_stands(applied, moved):
    assert f"stands at revision {moved['stands_at']}" in applied.faults[0].message


@then("nothing of the set is written")
def _nothing_of_the_set_written(root, moved):
    assert held.holds(root) == moved["held"]


SECOND_SAYING = {"the version the first replacement leaves": 2, "the version the work item stood at before the set": 1}


@when(
    parsers.re(
        f"the client asks, in one go, for the work item to be replaced twice, the second replacement saying "
        f"(?P<version>{'|'.join(map(re.escape, SECOND_SAYING))}), saying which role and why"
    ),
    target_fixture="applied",
)
def _replace_twice_the_second_saying(client, version):
    assert read(client, WORK_ITEM).revision == 1
    return replace_many(client, [
        replaced(WORK_ITEM, {"decisions": []}), replaced(WORK_ITEM, {}, revision=SECOND_SAYING[version]),
    ], message="Change the work item twice")


@then("the set lands, and the work item's version has gone up by two")
def _lands_two_versions_on(client, applied):
    assert not applied.refused, applied.faults
    assert [(result.id, result.revision) for result in applied.results] == [(WORK_ITEM, 2), (WORK_ITEM, 3)]
    assert read(client, WORK_ITEM).revision == 3
