import copy

from pytest_bdd import given, parsers, scenarios, then, when

from calls import (
    CLIENT, PROCESS_TYPE, TAG_TYPE, WORK_ITEM_TYPE, create, define, read, refs, remove, tagged_decision_type, write,
)
from kb import client as kb_client
from kb.contract import kb_pb2

scenarios("follow-the-links.feature")

OLDER = "decision/prices-are-reviewed-monthly"
DECISION = "decision/price-reviews-happen-weekly"
OLDER_SECTIONS = [
    {"title": "Purpose", "body": "Keep prices current.\n"},
    {"title": "Rationale", "body": "Monthly was enough once.\n"},
]


@given("a store where a decision supersedes an older decision", target_fixture="client")
def _store_with_a_superseded_decision(root):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, TAG_TYPE)
    define(client, tagged_decision_type())
    define(client, WORK_ITEM_TYPE)
    create(client, "decision", {"title": "Prices are reviewed monthly", "sections": OLDER_SECTIONS})
    create(client, "decision", {
        "title": "Price reviews happen weekly",
        "supersedes": OLDER,
        "sections": [
            {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
            {"title": "Rationale", "body": "Costs move weekly.\n"},
        ],
    })
    return client


@given("two work items point at that decision")
def _two_work_items(client):
    create(client, "work-item", {"title": "Move the review to Mondays", "decisions": [DECISION]})
    create(client, "work-item", {"title": "Tell the pricing team", "decisions": [DECISION]})


@given(parsers.parse('the older decision is tagged "{tag}"'))
def _older_decision_tagged(client, tag):
    tagged = create(client, "tag", {"title": tag})
    changed = write(client, OLDER, {"tags": [tagged.id], "sections": OLDER_SECTIONS}, message="Tag it")
    assert not changed.faults, changed.faults


@when("the client follows the links out of the decision two steps", target_fixture="reached")
def _follow_two_steps_out(client):
    response = refs(client, DECISION, depth=2)
    assert not response.faults, response.faults
    return list(response.reached)


@then("the client is given the older decision and the tag")
def _older_decision_and_tag(reached):
    assert [(found.stub.id, found.stub.type, found.stub.title) for found in reached] == [
        (OLDER, "decision", "Prices are reviewed monthly"),
        ("tag/pricing", "tag", "pricing"),
    ]


@then("each of them comes with the route taken to it")
def _each_with_its_route(reached):
    assert {found.stub.id: [(hop.field, hop.id) for hop in found.route] for found in reached} == {
        OLDER: [("supersedes", OLDER)],
        "tag/pricing": [("supersedes", OLDER), ("tags", "tag/pricing")],
    }


WORK_ITEMS = ["work-item/move-the-review-to-mondays", "work-item/tell-the-pricing-team"]


@when("the client follows the links out of the decision", target_fixture="reached")
def _follow_out(client):
    response = refs(client, DECISION, depth=1)
    assert not response.faults, response.faults
    return list(response.reached)


@then("the client is given a stub of the older decision")
def _stub_of_the_older_decision(reached):
    assert [(found.stub.field, found.stub.id, found.stub.type, found.stub.title) for found in reached] == [
        ("supersedes", OLDER, "decision", "Prices are reviewed monthly"),
    ]


@when("the client follows the links into the decision", target_fixture="reached")
def _follow_in(client):
    response = refs(client, DECISION, depth=1, inward=True)
    assert not response.faults, response.faults
    return list(response.reached)


@then("the client is given a stub of each work item")
def _stub_of_each_work_item(reached):
    assert [(found.stub.field, found.stub.id, found.stub.type, found.stub.title) for found in reached] == [
        ("decisions", WORK_ITEMS[0], "work-item", "Move the review to Mondays"),
        ("decisions", WORK_ITEMS[1], "work-item", "Tell the pricing team"),
    ]
    assert [[(hop.field, hop.id) for hop in found.route] for found in reached] == [
        [("decisions", WORK_ITEMS[0])], [("decisions", WORK_ITEMS[1])],
    ]


@when(
    "the client follows the links into the decision, only through the link a work item uses, and only from work items",
    target_fixture="reached",
)
def _follow_in_narrowed(client):
    response = refs(client, DECISION, depth=1, inward=True, via="decisions", type_name="work-item")
    assert not response.faults, response.faults
    return list(response.reached)


@then("the client is given both work items and nothing else")
def _both_work_items(reached):
    assert [found.stub.id for found in reached] == WORK_ITEMS


PROCESS = "process/open-the-shop"
INTO_A_STEP = "work-item/check-the-till-float"


@given(
    "a store holding a process, and a work item that points at one step of that process rather than at the whole "
    "process"
)
def _a_work_item_pointing_into_a_process(client):
    define(client, PROCESS_TYPE)
    create(client, "process", {"title": "Open the shop", "steps": [{"title": "Unlock the door"}, {"title": "Count the till"}]})
    following = copy.deepcopy(WORK_ITEM_TYPE["schema"])
    following["properties"]["follows"] = {
        "type": "string", "ref": {"targets": ["process"], "cardinality": "one", "parts": True, "on_delete": "refuse"},
    }
    revised = write(client, "schema/work-item", {"version": 2, "schema": following}, message="Let work items follow a step")
    assert not revised.faults, revised.faults
    create(client, "work-item", {"title": "Check the till float", "follows": f"{PROCESS}#steps/count-the-till"})


@when("the client follows the links into the process", target_fixture="reached")
def _follow_into_the_process(client):
    response = refs(client, PROCESS, depth=1, inward=True)
    assert not response.faults, response.faults
    return list(response.reached)


@then("the client is given a stub of that work item")
def _a_stub_of_the_work_item(reached):
    assert [(found.stub.field, found.stub.id) for found in reached] == [("follows", INTO_A_STEP)]


@then("reading the process at a glance counts that work item among the things pointing at it")
def _counted_at_a_glance(client):
    summary = read(client, PROCESS)
    assert not summary.faults, summary.faults
    assert [(count.type, count.field, count.count) for count in summary.inbound] == [("work-item", "follows", 1)]


@then("removing the process is refused while that work item points into it")
def _removal_refused(client):
    refused = remove(client, PROCESS)
    assert [(fault.artifact, fault.path, fault.rule) for fault in refused.faults] == [(INTO_A_STEP, "follows", "on_delete")]
    assert read(client, PROCESS).revision == 1
