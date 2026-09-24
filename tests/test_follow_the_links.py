import copy

from pytest_bdd import given, parsers, scenarios, then, when

from calls import CLIENT, DECISION_TYPE, WORK_ITEM_TYPE, create, define, refs, write
from kb import client as kb_client
from kb.contract import kb_pb2

scenarios("follow-the-links.feature")

OLDER = "decision/prices-are-reviewed-monthly"
DECISION = "decision/price-reviews-happen-weekly"
OLDER_SECTIONS = [
    {"title": "Purpose", "body": "Keep prices current.\n"},
    {"title": "Rationale", "body": "Monthly was enough once.\n"},
]
TAG_TYPE = {
    "title": "Tag",
    "version": 1,
    "schema": {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]},
}


def _tagged_decision_type():
    """The decision type, whose artifacts may also carry tags."""
    decision_type = copy.deepcopy(DECISION_TYPE)
    decision_type["schema"]["properties"]["tags"] = {
        "type": "array",
        "items": {"type": "string"},
        "ref": {"targets": ["tag"], "cardinality": "many", "parts": False, "on_delete": "refuse"},
    }
    return decision_type


@given("a store where a decision supersedes an older decision", target_fixture="client")
def _store_with_a_superseded_decision(root):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, TAG_TYPE)
    define(client, _tagged_decision_type())
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
