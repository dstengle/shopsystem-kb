import copy
import re

from pytest_bdd import given, parsers, scenario, then, when

from calls import CLIENT, DECISION_TYPE, create, define, listing, read, refs, search
from kb import client as kb_client
from kb.content import loads
from kb.contract import kb_pb2


@scenario("name-what-is-asked-for.feature", "Asking by a kind the store holds no type for is refused")
def test_asking_by_a_kind_the_store_holds_no_type_for_is_refused():
    pass


@scenario("query-the-store.feature", "The client lists every artifact of a kind")
def test_the_client_lists_every_artifact_of_a_kind():
    pass


@scenario("query-the-store.feature", "The client lists the artifacts matching a field")
def test_the_client_lists_the_artifacts_matching_a_field():
    pass


@scenario("query-the-store.feature", "The client lists names only")
def test_the_client_lists_names_only():
    pass


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
    assert [(stub.id, stub.kind, stub.title, loads(stub.fields)) for stub in listed.stubs] == [
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


CALLS = {
    'lists the artifacts of the kind "invoice"':
        lambda client: listing(client, "invoice"),
    "searches the prose for restocking among artifacts of that kind":
        lambda client: search(client, "restocking", type_name="invoice"),
    "follows the links into a decision, only from artifacts of that kind":
        lambda client: refs(client, MONTHLY, 1, inward=True, type_name="invoice"),
}


@given('a store that holds no type called "invoice"')
def _no_invoice_type(client):
    assert [fault.rule for fault in read(client, "schema/invoice").faults] == ["not-found"]


@when(parsers.re(f"the client (?P<call>{'|'.join(map(re.escape, CALLS))})"), target_fixture="answered")
def _ask_by_that_kind(client, call):
    return CALLS[call](client)


@then("the call is rejected because a kind must name a type the store holds, and the kind asked for is given back")
def _rejected_for_its_kind(answered):
    assert [(fault.artifact, fault.place, fault.rule) for fault in answered.faults] == [("", "", "kind")]
    assert "a kind must name a type the store holds" in answered.faults[0].message
    assert "'invoice'" in answered.faults[0].message
