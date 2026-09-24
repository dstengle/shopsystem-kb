from pytest_bdd import given, parsers, scenarios, then, when

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
    return client


@when(parsers.parse("the client searches the prose for {text}"), target_fixture="found")
def _search_the_prose(client, text):
    response = search(client, text)
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
