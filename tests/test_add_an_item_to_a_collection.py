from pytest_bdd import given, scenarios, then, when

from calls import CLIENT, PROCESS_TYPE, create, define, read, write
from kb import client as kb_client
from kb.content import loads
from kb.contract import kb_pb2

scenarios("add-an-item-to-a-collection.feature")

STEP_TYPE = {
    "title": "Step",
    "version": 1,
    "schema": {
        "type": "object",
        "properties": {"title": {"type": "string"}, "body": {"type": "string"}},
        "required": ["title"],
    },
}
CHECKLIST_TYPE = {
    "title": "Checklist",
    "version": 1,
    "schema": {
        "type": "object",
        "properties": {"title": {"type": "string"}},
        "required": ["title"],
        "parts": {
            "checks": {
                "items": {"type": "object", "properties": {"says": {"type": "string"}}, "required": ["says"]},
            }
        },
    },
}
FINDING_TYPE = {
    "title": "Finding",
    "version": 1,
    "schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "check": {
                "type": "string",
                "ref": {"targets": ["checklist"], "cardinality": "one", "parts": True, "on_delete": "refuse"},
            },
        },
        "required": ["title"],
    },
}
CHECKLIST = "checklist/closing-checks"
FINDING = "finding/the-till-was-short"
CHECKS = [{"says": "Lights off"}, {"says": "Till counted"}, {"says": "Door locked"}]


@given("a store holding a process with two steps and a shared step other processes use", target_fixture="client")
def _store_with_a_process(root):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, STEP_TYPE)
    define(client, PROCESS_TYPE)
    create(client, "step", {"title": "Count the till", "body": "Count every note and coin.\n"})
    create(client, "process", {"title": "Open the shop", "steps": [
        {"title": "Unlock the door", "body": "Front door first."},
        {"title": "Turn on the lights", "body": "Shop floor, then the stockroom."},
    ]})
    return client


@given(
    "an artifact holding a collection whose items carry no title of their own, each named by its place when it was added",
    target_fixture="named",
)
def _checklist_named_by_place(client):
    define(client, CHECKLIST_TYPE)
    define(client, FINDING_TYPE)
    create(client, "checklist", {"title": "Closing checks", "checks": CHECKS})
    create(client, "finding", {"title": "The till was short", "check": f"{CHECKLIST}#checks/2"})
    checks = loads(read(client, CHECKLIST, whole=True).content)["checks"]
    assert checks == [{"id": str(place), **check} for place, check in enumerate(CHECKS, start=1)]
    return {check["id"]: check for check in checks}


@when("the client puts the items of that collection in a different order, saying which role and why", target_fixture="reordered")
def _reorder_the_checks(client, named):
    reordered = [named["3"], named["1"], named["2"]]
    response = write(client, CHECKLIST, {"checks": reordered}, message="Lock up before the lights")
    assert not response.faults, response.faults
    return loads(read(client, CHECKLIST, whole=True).content)["checks"]


@then("every item keeps the name it was given when it was added")
def _names_kept(named, reordered):
    assert [check["id"] for check in reordered] == ["3", "1", "2"]
    assert all(check == named[check["id"]] for check in reordered)


@then("anything pointing at one of them still lands on the same item")
def _link_still_lands(client, named, reordered):
    assert loads(read(client, FINDING, whole=True).content)["check"] == f"{CHECKLIST}#checks/2"
    assert next(check for check in reordered if check["id"] == "2") == {"id": "2", "says": "Till counted"}
    assert not client.Validate(kb_pb2.ValidateRequest()).violations
