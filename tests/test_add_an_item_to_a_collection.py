import copy
import re

from pytest_bdd import given, parsers, scenario, then, when

from calls import PROCESS_TYPE, add, adding, answer, create, define, journal, read, replace, start_a_store, check
import at_once
import held
from kb import client as kb_client
from kb.content import loads
from kb.contract import kb_pb2


@scenario("change-the-store.feature", "The client adds an item to a collection")
def test_the_client_adds_an_item_to_a_collection():
    pass


@scenario("change-the-store.feature", "An item that uses another artifact keeps its settings on itself")
def test_an_item_that_uses_another_artifact_keeps_its_settings_on_itself():
    pass


@scenario("change-the-store.feature", "The client adds an item to a collection inside an item")
def test_the_client_adds_an_item_to_a_collection_inside_an_item():
    pass


@scenario(
    "change-the-store.feature",
    "Several clients on one machine change one store at the same time, none saying the version it read",
)
def test_several_clients_on_one_machine_change_one_store_at_the_same_time_none_saying_the_version_it_read():
    pass


@scenario("check-a-change.feature", "An item pointing at something that is not there is refused")
def test_an_item_pointing_at_something_that_is_not_there_is_refused():
    pass


@scenario("check-a-change.feature", "An item missing something its own type requires is refused")
def test_an_item_missing_something_its_own_type_requires_is_refused():
    pass


@scenario("hand-over-content.feature", "An item whose content settles what only the store settles is refused")
def test_an_item_whose_content_settles_what_only_the_store_settles_is_refused():
    pass


@scenario("name-artifacts-and-items.feature", "The name of a new item comes from its title")
def test_the_name_of_a_new_item_comes_from_its_title():
    pass


@scenario("name-artifacts-and-items.feature", "An item of a kind that carries no title is named by its place")
def test_an_item_of_a_kind_that_carries_no_title_is_named_by_its_place():
    pass


@scenario("name-artifacts-and-items.feature", "A second item with a title already used in the collection gets a name of its own")
def test_a_second_item_with_a_title_already_used_in_the_collection_gets_a_name_of_its_own():
    pass


@scenario("name-artifacts-and-items.feature", "Taking an item out does not rename the items left")
def test_taking_an_item_out_does_not_rename_the_items_left():
    pass


@scenario("name-artifacts-and-items.feature", "Putting items in a different order does not rename them")
def test_putting_items_in_a_different_order_does_not_rename_them():
    pass


@scenario("name-artifacts-and-items.feature", "An item's title becomes its name by the same rules as an artifact's title")
def test_an_item_s_title_becomes_its_name_by_the_same_rules_as_an_artifact_s_title():
    pass


@scenario("name-what-is-asked-for.feature", "Adding an item to something the store does not hold is refused")
def test_adding_an_item_to_something_the_store_does_not_hold_is_refused():
    pass


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
    start_a_store(root)
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
    response = replace(client, CHECKLIST, {"checks": reordered}, message="Lock up before the lights")
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
    assert not check(client).violations


def _steps(client):
    return loads(read(client, PROCESS, whole=True).content)["steps"]


def _added(client, content, collection="steps", artifact_id=PROCESS, message="Add a step before opening"):
    response = add(client, artifact_id, collection, content, message=message)
    assert not response.faults, response.faults
    return {"response": response, "sent": content}


@when("the client adds a step to the process, saying which role and why", target_fixture="added")
def _add_a_step(client):
    return _added(client, {"title": "Count the float", "body": "Every note and coin in the till."})


@then("the client is given the new item's name and the artifact's new version")
def _given_name_and_version(client, added):
    assert (added["response"].id, added["response"].revision) == ("count-the-float", 2)
    entry = journal(client, PROCESS).entries[-1]
    assert (entry.op, entry.place, entry.revision, entry.actor.role, entry.message) == (
        "append", "steps/count-the-float", 2, "client", "Add a step before opening",
    )


@then("the new item comes after the items already there")
def _after_the_others(client):
    assert _steps(client) == [
        *STEPS, {"id": "count-the-float", "title": "Count the float", "body": "Every note and coin in the till."},
    ]


@when(parsers.parse('the client adds a step titled "{title}" to the process, saying which role and why'), target_fixture="added")
def _add_a_titled_step(client, title):
    return {"response": add(client, PROCESS, "steps", {"title": title}), "sent": {"title": title}}


TITLES = {"the number 12 rather than text": 12, "the yes-or-no true rather than text": True}


@when(
    parsers.re(f"the client adds a step titled (?P<title>{'|'.join(map(re.escape, TITLES))}) to the process, "
               "saying which role and why"),
    target_fixture="added",
)
def _add_a_step_titled_other_than_text(client, title):
    return _added(client, {"title": TITLES[title]})


@then("the name the client is given for the new item is made from that title")
def _named_from_its_title(client, added):
    assert added["response"].id == "count-what-is-on-the-shelf"
    assert _steps(client)[-1] == {"id": "count-what-is-on-the-shelf", "title": "Count what is on the shelf"}


@then("the client never said what the name should be")
def _never_said(added):
    assert "id" not in added["sent"]
    assert set(kb_pb2.AddRequest.DESCRIPTOR.fields_by_name) == {"locator", "content", "signature", "revision"}


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
    response = replace(client, CHECKLIST, {"checks": [named["2"], named["3"]]}, message="Lights are on a timer now")
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
    response = add(client, PROCESS, "steps", {"id": "count-the-float", "title": "Count the float"})
    return {"response": response, "before": before}


@then(
    "the item is rejected because content holds only what the type declares, and the thing it carried that only the "
    "store settles is named back"
)
def _rejected_for_its_name(attempt):
    assert [(fault.artifact, fault.place, fault.rule) for fault in attempt["response"].faults] == [(PROCESS, "id", "identity")]
    assert "'count-the-float'" in attempt["response"].faults[0].message


@then("the process holds the steps it held before, at the version it held before")
def _process_as_it_was(client, attempt):
    after = read(client, PROCESS, whole=True)
    assert (after.revision, loads(after.content)) == (attempt["before"].revision, loads(attempt["before"].content))


@when("the client adds a step to a process by a name the store holds nothing under, saying which role and why", target_fixture="attempt")
def _add_to_nothing(root, client):
    before = held.holds(root)
    response = add(client, "process/close-the-shop", "steps", {"title": "Lock the door"})
    return {"response": response, "before": before, "after": held.holds(root)}


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
    response = add(client, PROCESS, "steps", {"title": "Count the change", "uses": "step/count-the-change"})
    return {"response": response, "before": before}


@then("the item is rejected because a link must land on a node of a kind the type allows")
def _rejected_for_its_link(attempt):
    assert [(fault.artifact, fault.place, fault.rule) for fault in attempt["response"].faults] == [
        (PROCESS, "steps/2/uses", "ref"),
    ]
    assert "'step/count-the-change'" in attempt["response"].faults[0].message


def _steps_must_name_a_role(client):
    """The process type at its next version, whose steps must each name a role, and the process's two steps given
    one, so the process fits it."""
    staffed = copy.deepcopy(PROCESS_TYPE["schema"])
    step = staffed["parts"]["steps"]["items"]
    step["properties"]["role"] = {"type": "string"}
    step["required"] = ["title", "role"]
    assert not replace(client, "schema/process", {"version": 2, "schema": staffed}, message="Steps name a role").faults
    staffed_steps = [{**STEPS[0], "role": "opener"}, {**STEPS[1], "role": "opener"}]
    assert not replace(client, PROCESS, {"steps": staffed_steps}, message="Say who does each step").faults


@when("the client adds a step with no role named, where a step must name a role, saying which role and why", target_fixture="attempt")
def _add_a_step_naming_no_role(client):
    _steps_must_name_a_role(client)
    before = read(client, PROCESS, whole=True)
    response = add(client, PROCESS, "steps", {"title": "Count the float"})
    return {"response": response, "before": before}


@then("the item is rejected because the content does not fit the type")
def _rejected_for_its_type(attempt):
    faults = attempt["response"].faults
    assert [(fault.artifact, fault.place, fault.rule) for fault in faults] == [(PROCESS, "steps/2", "required")]
    assert "'role'" in faults[0].message


@given("the steps of the process each carry a collection of checks of their own", target_fixture="before")
def _steps_carry_checks(client):
    checked = copy.deepcopy(PROCESS_TYPE["schema"])
    checked["parts"]["steps"]["items"]["parts"] = {
        "checks": {"items": {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]}},
    }
    assert not replace(client, "schema/process", {"version": 2, "schema": checked}, message="Steps carry checks").faults
    steps = [{**STEPS[0], "checks": [{"title": "Key turns"}]}, {**STEPS[1], "checks": [{"title": "Every bulb lit"}]}]
    assert not replace(client, PROCESS, {"steps": steps}, message="Give each step its checks").faults
    return loads(read(client, PROCESS, whole=True).content)


@when("the client adds a check to the first step of the process, saying which role and why", target_fixture="added")
def _add_a_check_to_the_first_step(client):
    return _added(client, {"title": "Door stays open"}, collection="steps/unlock-the-door/checks", message="Prop the door")


@then("the client is given the new check's name and the artifact's new version")
def _given_the_checks_name_and_version(client, added):
    assert (added["response"].id, added["response"].revision) == ("door-stays-open", 3)
    entry = journal(client, PROCESS).entries[-1]
    assert (entry.op, entry.place, entry.revision) == ("append", "steps/unlock-the-door/checks/door-stays-open", 3)


@then("the rest of the process is unchanged")
def _rest_unchanged(client, before):
    after = loads(read(client, PROCESS, whole=True).content)
    added = after["steps"][0]["checks"].pop()
    assert added == {"title": "Door stays open", "id": "door-stays-open"}
    assert after == before


@then("the item is rejected because a title must leave something to make a name from")
def _rejected_for_an_empty_name(client, added):
    response = added["response"]
    assert [(fault.artifact, fault.place, fault.rule) for fault in response.faults] == [(PROCESS, "title", "title")]
    assert "leave something to make a name from" in response.faults[0].message
    assert [step["id"] for step in _steps(client)] == ["unlock-the-door", "turn-on-the-lights"]


@then(parsers.parse('the name the client is given for the new item is made from the text "{text}"'))
def _named_from_the_text(client, added, text):
    assert added["response"].id == text
    assert _steps(client)[-1] == {"id": text, "title": text}


OTHER_STEP = {"title": "Count the float", "body": "Every note and coin in the till."}
DIFFERENT_STEP = {"title": "Check the card reader", "body": "Run a test payment."}
CLIENTS = {
    "two clients in one program": lambda root, tmp_path, request: at_once.OnAThread(root, "Add", request),
    "two clients in two separate programs on the same machine": lambda root, tmp_path, request: at_once.InAnotherProgram(
        root, "Add", request, tmp_path / "gate",
    ),
}


def _adding(content, message):
    return adding(PROCESS, "steps", content, message=message)


@given(
    parsers.re(f"(?P<clients>{'|'.join(map(re.escape, CLIENTS))}), one adding a step to the process while the other "
               "adds a different step, each saying which role and why and neither saying the version it read the "
               "process at"),
    target_fixture="racing",
)
def _clients_adding_steps(root, tmp_path, clients):
    return {
        "held": CLIENTS[clients](root, tmp_path, _adding(DIFFERENT_STEP, "Check the reader before opening")),
        "other": kb_client.connect(root),
    }


@when("the client adding the different step lands its change second", target_fixture="landed")
def _different_step_lands_second(racing):
    def first():
        response = answer(racing["other"].Add(_adding(OTHER_STEP, "Count the float before opening")))
        assert not response.faults, response.faults
    return at_once.landed_second(racing["held"], first)


@then("the process holds both new steps")
def _both_new_steps(client, landed):
    assert not landed.faults, landed.faults
    assert {"count-the-float", "check-the-card-reader"} <= {step["id"] for step in _steps(client)}


@then("the different step comes after the other new step, and both come after the steps already there")
def _in_the_order_they_landed(client, landed):
    assert landed.revision == 3
    assert _steps(client) == [
        *STEPS, {"id": "count-the-float", **OTHER_STEP}, {"id": "check-the-card-reader", **DIFFERENT_STEP},
    ]
