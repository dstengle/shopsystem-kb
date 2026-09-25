import copy

from pytest_bdd import given, scenarios, then, when

from calls import CLIENT, DECISION_TYPE, create, define, listing
from kb import client as kb_client
from kb.content import loads
from kb.contract import kb_pb2

scenarios("list-artifacts-of-a-kind.feature")

SECTIONS = [
    {"title": "Purpose", "body": "Keep the shop running.\n"},
    {"title": "Rationale", "body": "It was agreed.\n"},
]
WEEKLY = "decision/price-reviews-happen-weekly"
MONTHLY = "decision/prices-are-reviewed-monthly"
THURSDAYS = "decision/restock-on-thursdays"


@given("a store holding three decisions, one of them superseded", target_fixture="client")
def _store_with_three_decisions(root):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    decision_type = copy.deepcopy(DECISION_TYPE)
    decision_type["schema"]["properties"]["status"] = {"type": "string"}
    decision_type["schema"]["summary"] = ["supersedes", "status"]
    define(client, decision_type)
    create(client, "decision", {"title": "Prices are reviewed monthly", "status": "superseded", "sections": SECTIONS})
    create(client, "decision", {
        "title": "Price reviews happen weekly", "status": "accepted", "supersedes": MONTHLY, "sections": SECTIONS,
    })
    create(client, "decision", {"title": "Restock on Thursdays", "status": "accepted", "sections": SECTIONS})
    return client


@when("the client lists the decisions", target_fixture="listed")
def _list_the_decisions(client):
    return listing(client, "decision")


@then("the client is given a stub of each of the three")
def _a_stub_of_each(listed):
    assert not listed.faults, listed.faults
    assert [(stub.id, stub.type, stub.title, loads(stub.fields)) for stub in listed.stubs] == [
        (WEEKLY, "decision", "Price reviews happen weekly", {"supersedes": MONTHLY, "status": "accepted"}),
        (MONTHLY, "decision", "Prices are reviewed monthly", {"status": "superseded"}),
        (THURSDAYS, "decision", "Restock on Thursdays", {"status": "accepted"}),
    ]


@when("the client lists the decisions that are superseded", target_fixture="listed")
def _list_the_superseded(client):
    return listing(client, "decision", fields={"status": "superseded"})


@then("the client is given only the superseded one")
def _only_the_superseded(listed):
    assert not listed.faults, listed.faults
    assert [(stub.id, stub.title) for stub in listed.stubs] == [(MONTHLY, "Prices are reviewed monthly")]


@when("the client lists the decisions asking for names only", target_fixture="listed")
def _list_names_only(client):
    return listing(client, "decision", ids_only=True)


@then("the client is given three names and nothing else")
def _three_names(listed):
    assert not listed.faults, listed.faults
    assert list(listed.ids) == [WEEKLY, MONTHLY, THURSDAYS]
    assert not listed.stubs
