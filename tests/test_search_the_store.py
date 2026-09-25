from pytest_bdd import given, scenarios, then, when

from calls import CLIENT, DECISION_TYPE, create, define, search
from kb import client as kb_client
from kb.contract import kb_pb2

scenarios("search-the-store.feature")

PROCESS_TYPE = {
    "title": "Process",
    "version": 1,
    "schema": {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]},
}


@given("a store where two decisions and a process mention restocking in their prose", target_fixture="client")
def _store_mentioning_restocking(root):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, DECISION_TYPE)
    define(client, PROCESS_TYPE)
    create(client, "decision", {
        "title": "Restock on Thursdays",
        "sections": [
            {"title": "Purpose", "body": "Keep the shelves full before the weekend.\n"},
            {"title": "Rationale", "body": "Restocking on Thursday means restocking once, and Friday restocking is too late.\n"},
        ],
    })
    create(client, "decision", {
        "title": "Price reviews happen weekly",
        "sections": [
            {"title": "Purpose", "body": "Keep prices in step with costs, restocking included.\n"},
            {"title": "Rationale", "body": "Costs move weekly.\n"},
        ],
    })
    create(client, "process", {
        "title": "Open the shop",
        "sections": [
            {"title": "Before opening", "body": "Unlock, then check whether restocking is due.\n"},
        ],
    })
    create(client, "decision", {
        "title": "Restocking needs two people",
        "sections": [
            {"title": "Purpose", "body": "Keep the stockroom safe.\n"},
            {"title": "Rationale", "body": "Heavy boxes need a second pair of hands.\n"},
        ],
    })
    return client


@when("the client searches the prose for restocking", target_fixture="found")
def _search_the_prose(client):
    response = search(client, "restocking")
    assert not response.faults, response.faults
    return list(response.matches)


@then("each result comes with the title of the section it matched and a snippet of it")
def _section_and_snippet(found):
    assert {(match.stub.id, match.section) for match in found} == {
        ("decision/restock-on-thursdays", "Rationale"),
        ("decision/price-reviews-happen-weekly", "Purpose"),
        ("process/open-the-shop", "Before opening"),
    }
    assert all("restocking" in match.snippet.lower() for match in found)


@then("the one whose section mentions restocking most often comes first")
def _most_often_first(found):
    assert (found[0].stub.id, found[0].section) == ("decision/restock-on-thursdays", "Rationale")


@when("the client searches the prose for restocking among decisions only", target_fixture="found")
def _search_the_decisions(client):
    response = search(client, "restocking", type_name="decision")
    assert not response.faults, response.faults
    return list(response.matches)


@then("the client is given the two decisions and not the process")
def _the_two_decisions(found):
    assert {match.stub.id for match in found} == {"decision/restock-on-thursdays", "decision/price-reviews-happen-weekly"}
    assert all(match.stub.type == "decision" for match in found)


@when("the client searches the fields and the prose for restocking", target_fixture="found")
def _search_fields_and_prose(client):
    response = search(client, "restocking", everywhere=True)
    assert not response.faults, response.faults
    return list(response.matches)


@then("the client is also given a decision whose title mentions restocking")
def _the_decision_by_its_title(found):
    assert [(match.stub.id, match.field, match.section, match.snippet) for match in found if match.field] == [
        ("decision/restocking-needs-two-people", "title", "", "Restocking needs two people"),
    ]
    assert {(match.stub.id, match.section) for match in found if not match.field} == {
        ("decision/restock-on-thursdays", "Rationale"),
        ("decision/price-reviews-happen-weekly", "Purpose"),
        ("process/open-the-shop", "Before opening"),
    }
