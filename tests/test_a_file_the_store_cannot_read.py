import re

from pytest_bdd import given, parsers, then, when, scenarios

from calls import (
    CLIENT, DECISION_TYPE, PROCESS_TYPE, TAG_TYPE, append, create, define, everything_under, listing, refs, remove,
    search, write,
)
from kb import client as kb_client
from kb.contract import kb_pb2

scenarios("a-file-the-store-cannot-read.feature")

DECISION = "decision/price-reviews-happen-weekly"
SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]

CALLS = {
    "replaces the decision, saying which role and why":
        lambda client: write(client, DECISION, {"sections": SECTIONS}),
    "adds an item to a collection of the decision, saying which role and why":
        lambda client: append(client, DECISION, "options", {"title": "Go monthly"}),
    "removes the decision, saying which role and why":
        lambda client: remove(client, DECISION),
    "lists the decisions":
        lambda client: listing(client, "decision"),
    "searches the prose for a word that decision holds":
        lambda client: search(client, "weekly"),
    "follows the links into the decision":
        lambda client: refs(client, DECISION, 1, inward=True),
    "follows the links out of the decision":
        lambda client: refs(client, DECISION, 1),
}


@given("a store holding a decision, a process and a tag, each of a kind the store holds a type for",
       target_fixture="client")
def _store_with_a_decision_a_process_and_a_tag(root):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    for type_content in (DECISION_TYPE, PROCESS_TYPE, TAG_TYPE):
        define(client, type_content)
    create(client, "decision", {"title": "Price reviews happen weekly", "sections": SECTIONS})
    create(client, "process", {"title": "Open the shop", "steps": [{"title": "Unlock"}, {"title": "Count the float"}]})
    create(client, "tag", {"title": "Pricing"})
    return client


@when(parsers.re(f"the client (?P<call>{'|'.join(map(re.escape, CALLS))})"), target_fixture="answered")
def _the_client_calls(client, root, before, call):
    before.update(held=everything_under(root))
    return CALLS[call](client)


@then("the call is rejected because that file cannot be read, and the file is named")
def _rejected_as_unreadable(answered):
    assert [(fault.artifact, fault.rule) for fault in answered.faults] == [(DECISION, "unreadable")]
    assert f"{DECISION}.yaml cannot be read" in answered.faults[0].message


@then("the client is given that fault as it is given any other, the call never breaking off")
def _given_as_any_other_fault(answered):
    assert type(answered).__module__ == kb_pb2.__name__
    assert answered.faults


@then("nothing is written anywhere in the store")
def _nothing_written(root, before):
    assert everything_under(root) == before["held"]
