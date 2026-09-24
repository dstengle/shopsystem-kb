from pytest_bdd import given, scenarios, then, when

from calls import CLIENT, DECISION_TYPE, create, define, read, write
from kb import client as kb_client
from kb.content import loads
from kb.contract import kb_pb2

scenarios("change-an-artifact.feature")

DECISION = "decision/price-reviews-happen-weekly"
SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]


@given("a store holding a decision with a purpose and a rationale, at its first version", target_fixture="client")
def _store_with_a_decision(root):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, DECISION_TYPE)
    create(client, "decision", {"title": "Price reviews happen weekly", "sections": SECTIONS})
    return client


@when("the client replaces the decision with content that has no purpose, saying which role and why", target_fixture="attempt")
def _replace_without_a_purpose(root, client):
    before = (root / "kb" / f"{DECISION}.yaml").read_bytes()
    response = write(client, DECISION, {"sections": SECTIONS[1:]}, message="Drop the purpose")
    return {"response": response, "before": before}


@then("the change is rejected because the sections the type requires must all be present, in order")
def _rejected_for_the_sections(attempt):
    refused = attempt["response"]
    assert refused.revision == 0
    assert [(fault.artifact, fault.path, fault.rule) for fault in refused.faults] == [(DECISION, "sections", "sections")]
    assert refused.faults[0].message.startswith("the sections the type requires must all be present, in order")


@then("reading the decision gives what it held before, at the version it held before")
def _as_it_was(root, client, attempt):
    assert read(client, DECISION).revision == 1
    assert (root / "kb" / f"{DECISION}.yaml").read_bytes() == attempt["before"]


@when("the client replaces the rationale of the decision, saying which role and why", target_fixture="changed")
def _replace_the_rationale(client):
    before = read(client, DECISION, whole=True)
    response = write(
        client, DECISION, {"title": "Rationale", "body": "Suppliers change their prices every week.\n"},
        message="Say why weekly", path="sections/rationale",
    )
    assert not response.faults, response.faults
    return {"response": response, "before": before, "after": read(client, DECISION, whole=True)}


@then("only that section changes")
def _only_the_rationale_changes(changed):
    assert changed["response"].revision == 2
    assert loads(changed["after"].content)["sections"] == [
        SECTIONS[0], {"title": "Rationale", "body": "Suppliers change their prices every week.\n"},
    ]


@then("the rest of the decision reads as before")
def _the_rest_as_before(changed):
    before, after = loads(changed["before"].content), loads(changed["after"].content)
    assert after["sections"][0] == before["sections"][0]
    assert {key: value for key, value in after.items() if key != "sections"} == {
        key: value for key, value in before.items() if key != "sections"
    }
    assert [(seen.id, seen.type, seen.title, seen.schema_version) for seen in (changed["before"], changed["after"])] == [
        (DECISION, "decision", "Price reviews happen weekly", 1),
    ] * 2
