from pytest_bdd import given, parsers, scenarios, then, when

from calls import CLIENT, PROCESS_TYPE, append, create, define, everything_under, journal, read, write
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
PROCESS = "process/open-the-shop"
SHARED = "step/count-the-till"
STEPS = [
    {"id": "unlock-the-door", "title": "Unlock the door", "body": "Front door first."},
    {"id": "turn-on-the-lights", "title": "Turn on the lights", "body": "Shop floor, then the stockroom."},
]


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


def _steps(client):
    return loads(read(client, PROCESS, whole=True).content)["steps"]


def _added(client, content, collection="steps", artifact_id=PROCESS, message="Add a step before opening"):
    response = append(client, artifact_id, collection, content, message=message)
    assert not response.faults, response.faults
    return {"response": response, "sent": content}


@when("the client adds a step to the process, saying which role and why", target_fixture="added")
def _add_a_step(client):
    return _added(client, {"title": "Count the float", "body": "Every note and coin in the till."})


@then("the client is given the new item's name and the artifact's new version")
def _given_name_and_version(client, added):
    assert (added["response"].id, added["response"].revision) == ("count-the-float", 2)
    entry = journal(client, PROCESS).entries[-1]
    assert (entry.op, entry.path, entry.revision, entry.actor.role, entry.message) == (
        "append", "steps/count-the-float", 2, "client", "Add a step before opening",
    )


@then("the new item comes after the items already there")
def _after_the_others(client):
    assert _steps(client) == [
        *STEPS, {"id": "count-the-float", "title": "Count the float", "body": "Every note and coin in the till."},
    ]


@when(parsers.parse('the client adds a step titled "{title}" to the process, saying which role and why'), target_fixture="added")
def _add_a_titled_step(client, title):
    return _added(client, {"title": title})


@then("the name the client is given for the new item is made from that title")
def _named_from_its_title(client, added):
    assert added["response"].id == "count-what-is-on-the-shelf"
    assert _steps(client)[-1] == {"id": "count-what-is-on-the-shelf", "title": "Count what is on the shelf"}


@then("the client never said what the name should be")
def _never_said(added):
    assert "id" not in added["sent"]
    assert set(kb_pb2.AppendRequest.DESCRIPTOR.fields_by_name) == {"locator", "content", "actor", "message"}


@given("an artifact holding a collection whose items carry no title of their own")
def _checklist(client):
    define(client, CHECKLIST_TYPE)
    create(client, "checklist", {"title": "Closing checks", "checks": CHECKS})


@when("the client adds an item to that collection, saying which role and why", target_fixture="added")
def _add_a_check(client):
    return _added(client, {"says": "Alarm set"}, collection="checks", artifact_id=CHECKLIST, message="Set the alarm too")


@then("the name the client is given for the new item is made from its place in the collection")
def _named_from_its_place(client, added):
    assert added["response"].id == "4"
    checks = loads(read(client, CHECKLIST, whole=True).content)["checks"]
    assert [check["id"] for check in checks] == ["1", "2", "3", "4"]
    assert checks[3] == {"id": "4", "says": "Alarm set"}


@when("the client adds a step whose title is already used by a step of that process, saying which role and why", target_fixture="added")
def _add_a_step_with_a_used_title(client):
    return _added(client, {"title": "Unlock the door", "body": "The back door too."})


@then("the name the client is given for the new item is the name already taken with a number added")
def _numbered(client, added):
    assert added["response"].id == "unlock-the-door-2"
    assert _steps(client)[-1] == {"id": "unlock-the-door-2", "title": "Unlock the door", "body": "The back door too."}


@then("the step already there keeps the name it had")
def _first_keeps_its_name(client):
    assert _steps(client)[0] == STEPS[0]


@when("the client takes the first item out of that collection, saying which role and why", target_fixture="left")
def _take_the_first_out(client, named):
    response = write(client, CHECKLIST, {"checks": [named["2"], named["3"]]}, message="Lights are on a timer now")
    assert not response.faults, response.faults
    return loads(read(client, CHECKLIST, whole=True).content)["checks"]


@then("every item left keeps the name it was given when it was added")
def _left_keep_their_names(named, left):
    assert left == [named["2"], named["3"]]


@then("no item is named again from where it now sits")
def _not_named_from_its_place(left):
    assert [check["id"] for check in left] == ["2", "3"]
    assert left[0]["id"] != "1"


@when("the client adds a step that points at the shared step together with its settings, saying which role and why", target_fixture="added")
def _add_a_step_using_the_shared_one(client):
    return _added(client, {"title": "Count the till", "uses": SHARED, "settings": {"float": 150}})


@then("the settings are held by the new item")
def _settings_on_the_item(client, added):
    assert _steps(client)[-1] == {"id": "count-the-till", "title": "Count the till", "uses": SHARED, "settings": {"float": 150}}


@then("the shared step is unchanged")
def _shared_step_unchanged(client):
    shared = read(client, SHARED, whole=True)
    assert (shared.revision, loads(shared.content)) == (1, {"body": "Count every note and coin.\n"})


@when("the client adds a step whose content carries a name of its own, saying which role and why", target_fixture="attempt")
def _add_a_step_naming_itself(client):
    before = read(client, PROCESS, whole=True)
    response = append(client, PROCESS, "steps", {"id": "count-the-float", "title": "Count the float"})
    return {"response": response, "before": before}


@then(
    "the item is rejected because content holds only what the type declares, and the thing it carried that only the "
    "store settles is named back"
)
def _rejected_for_its_name(attempt):
    assert [(fault.artifact, fault.path, fault.rule) for fault in attempt["response"].faults] == [(PROCESS, "id", "identity")]
    assert "'count-the-float'" in attempt["response"].faults[0].message


@then("the process holds the steps it held before, at the version it held before")
def _process_as_it_was(client, attempt):
    after = read(client, PROCESS, whole=True)
    assert (after.revision, loads(after.content)) == (attempt["before"].revision, loads(attempt["before"].content))
    assert _steps(client) == STEPS


@when("the client adds a step to a process by a name the store holds nothing under, saying which role and why", target_fixture="attempt")
def _add_to_nothing(root, client):
    before = everything_under(root)
    response = append(client, "process/close-the-shop", "steps", {"title": "Lock the door"})
    return {"response": response, "before": before, "after": everything_under(root)}


@then("the item is rejected because the store holds nothing by that name, and the name asked for is given back")
def _rejected_for_nothing(attempt):
    assert [(fault.artifact, fault.rule) for fault in attempt["response"].faults] == [("process/close-the-shop", "not-found")]
    assert "'process/close-the-shop'" in attempt["response"].faults[0].message


@then("nothing is written anywhere in the store")
def _nothing_written(attempt):
    assert attempt["after"] == attempt["before"]


@when("the client adds a step that points at a shared step the store does not hold, saying which role and why", target_fixture="attempt")
def _add_a_step_pointing_nowhere(client):
    before = read(client, PROCESS, whole=True)
    response = append(client, PROCESS, "steps", {"title": "Count the change", "uses": "step/count-the-change"})
    return {"response": response, "before": before}


@then("the item is rejected because a link must land on a node of a kind the type allows")
def _rejected_for_its_link(attempt):
    assert [(fault.artifact, fault.path, fault.rule) for fault in attempt["response"].faults] == [
        (PROCESS, "steps/2/uses", "ref"),
    ]
    assert "'step/count-the-change'" in attempt["response"].faults[0].message
