import copy
import re

from pytest_bdd import given, parsers, scenario, scenarios, then, when

from calls import (
    CLIENT, DECISION_TYPE, NOTE_TYPE, append, apply, creation, define, create, journal, listing, read, refs,
    remove, replacement, request, write,
)
import at_once
import held
from kb import canonical, client as kb_client
from kb.content import dumps, loads
from kb.contract import kb_pb2

scenarios("sign-a-change.feature")


@scenario("change-the-store.feature", "The client changes an artifact")
def test_the_client_changes_an_artifact():
    pass


@scenario("change-the-store.feature", "The client changes one node inside an artifact")
def test_the_client_changes_one_node_inside_an_artifact():
    pass


@scenario("change-the-store.feature", "The client changes one item of a collection")
def test_the_client_changes_one_item_of_a_collection():
    pass


@scenario("change-the-store.feature", "A replacement that leaves out an item something links into is refused")
def test_a_replacement_that_leaves_out_an_item_something_links_into_is_refused():
    pass


@scenario("change-the-store.feature", "The clock fails during a change")
def test_the_clock_fails_during_a_change():
    pass


@scenario("change-the-store.feature", "Two clients replace one artifact at the same time")
def test_two_clients_replace_one_artifact_at_the_same_time():
    pass


@scenario("check-a-change.feature", "Changing an artifact that is behind its type brings it up to date")
def test_changing_an_artifact_that_is_behind_its_type_brings_it_up_to_date():
    pass


@scenario("check-a-change.feature", "Changing an artifact that is behind its type with content the current version will not have is refused")
def test_changing_an_artifact_that_is_behind_its_type_with_content_the_current_version_will_not_have_is_refused():
    pass


@scenario("check-a-change.feature", "A change that would break the type leaves the artifact as it was")
def test_a_change_that_would_break_the_type_leaves_the_artifact_as_it_was():
    pass


@scenario("hand-over-content.feature", "A change whose content settles what only the store settles is refused")
def test_a_change_whose_content_settles_what_only_the_store_settles_is_refused():
    pass


@scenario("name-artifacts-and-items.feature", "Items sent back with their names are the same items, and one without a name is new")
def test_items_sent_back_with_their_names_are_the_same_items_and_one_without_a_name_is_new():
    pass


@scenario("name-artifacts-and-items.feature", "Every way an item's name can be wrong on a change is refused")
def test_every_way_an_item_s_name_can_be_wrong_on_a_change_is_refused():
    pass


@scenario("name-what-is-asked-for.feature", "A change aimed at a name that is not a plain name writes nothing")
def test_a_change_aimed_at_a_name_that_is_not_a_plain_name_writes_nothing():
    pass


@scenario("name-what-is-asked-for.feature", "Changing something the store does not hold is refused")
def test_changing_something_the_store_does_not_hold_is_refused():
    pass


@scenario("name-what-is-asked-for.feature", "Every way the place a change is aimed at can be wrong is refused")
def test_every_way_the_place_a_change_is_aimed_at_can_be_wrong_is_refused():
    pass


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
    before = held.text(root, DECISION)
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
    assert read(client, DECISION).revision == canonical.load(attempt["before"])["revision"]
    assert held.text(root, DECISION) == attempt["before"]


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


@when("the client replaces the decision, saying which role and why", target_fixture="changed")
def _replace_the_decision(client):
    response = write(client, DECISION, {"sections": [
        SECTIONS[0], {"title": "Rationale", "body": "Suppliers change their prices every week.\n"},
    ]}, message="Say why weekly")
    return response


@given("the client was readied with a clock that fails when it is asked the time", target_fixture="client")
def _readied_with_a_failing_clock(root, before):
    """A client over the store at root whose clock raises whenever it is read; what the store holds is taken first."""
    def fails():
        raise RuntimeError("the clock has stopped")

    before.update(held=held.holds(root))
    return kb_client.connect(root, clock=fails)


@then("the client is given a fault")
def _given_a_fault(changed):
    assert isinstance(changed, kb_pb2.WriteResponse)
    assert changed.revision == 0
    assert len(changed.faults) == 1, changed.faults


@then("the store holds what it held before")
def _holds_what_it_held(root, before):
    assert held.holds(root) == before["held"]


@then("the version goes up by one")
def _version_up_by_one(client, changed):
    assert changed.revision == 2
    assert read(client, DECISION).revision == 2


@then("the artifact records the current version of its type")
def _records_the_current_version(root, client):
    current = held.artifact(root, "schema/decision")["version"]
    assert read(client, DECISION).schema_version == current


def _stale(client):
    """The names the store's check lists as behind their type."""
    return [stale.artifact for stale in client.Validate(kb_pb2.ValidateRequest()).stale]


def _decision_type_at_version_2(client, schema):
    """The decision type changed to its second version, so the decision, checked against the first, is behind it."""
    changed = write(client, "schema/decision", {"version": 2, "schema": schema}, message="Decision type, version 2")
    assert not changed.faults, changed.faults
    assert read(client, DECISION).schema_version == 1
    assert _stale(client) == [DECISION]


@given("a decision last checked against an older version of the decision type, which still fits the current version")
def _behind_a_type_it_still_fits(client):
    _decision_type_at_version_2(client, DECISION_TYPE["schema"])


@given("a decision last checked against an older version of the decision type")
def _behind_a_type_that_now_wants_an_owner(client):
    schema = copy.deepcopy(DECISION_TYPE["schema"])
    schema["properties"]["owner"] = {"type": "string"}
    schema["required"] = ["title", "owner"]
    _decision_type_at_version_2(client, schema)


@when(
    "the client replaces the decision with content that fits the current version of its type, saying which role and why",
    target_fixture="changed",
)
def _replace_with_content_that_fits(client):
    response = write(client, DECISION, {"sections": SECTIONS}, message="Bring it up to date")
    assert not response.faults, response.faults
    return response


@then("the decision records the current version of its type")
def _records_version_2(client):
    assert read(client, DECISION).schema_version == 2


@then("it is no longer listed as behind its type")
def _no_longer_stale(client):
    assert DECISION not in _stale(client)


@when(
    "the client replaces the decision with content that does not fit the current version of its type, "
    "saying which role and why",
    target_fixture="attempt",
)
def _replace_with_content_that_does_not_fit(root, client):
    before = held.text(root, DECISION)
    return {"response": write(client, DECISION, {"sections": SECTIONS}, message="No owner"), "before": before}


@then(
    "the change is rejected because the content does not fit the current version of its type, "
    "like any change that does not fit"
)
def _rejected_by_the_current_version(attempt):
    refused = attempt["response"]
    assert refused.revision == 0
    assert [(fault.artifact, fault.path, fault.rule) for fault in refused.faults] == [(DECISION, "", "required")]


@then("it is still listed as behind its type")
def _still_stale(client):
    assert _stale(client) == [DECISION]


@when(
    "the client replaces the decision with content carrying a version of its own, saying which role and why",
    target_fixture="attempt",
)
def _replace_with_a_version_of_its_own(root, client):
    before = held.text(root, DECISION)
    response = write(client, DECISION, {"revision": 7, "sections": SECTIONS}, message="Set the version")
    return {"response": response, "before": before}


@then(
    "the change is rejected because content holds only what the type declares, "
    "and the thing it carried that only the store settles is named back"
)
def _rejected_for_a_version_inside(attempt):
    refused = attempt["response"]
    assert refused.revision == 0
    assert [(fault.artifact, fault.path, fault.rule) for fault in refused.faults] == [(DECISION, "revision", "identity")]
    assert "revision: 7" in refused.faults[0].message


@when(
    "the client replaces an artifact by a name the store holds nothing under, saying which role and why",
    target_fixture="attempt",
)
def _replace_a_name_the_store_lacks(root, client):
    before = held.holds(root)
    response = write(client, "decision/nothing-of-the-sort", {"sections": SECTIONS}, message="Change it")
    return {"response": response, "before": before, "after": held.holds(root)}


@then("the change is rejected because the store holds nothing by that name, and the name asked for is given back")
def _rejected_as_not_held(attempt):
    refused = attempt["response"]
    assert refused.revision == 0
    assert [(fault.artifact, fault.rule) for fault in refused.faults] == [("decision/nothing-of-the-sort", "not-found")]
    assert "decision/nothing-of-the-sort" in refused.faults[0].message


@then("nothing is written anywhere in the store")
def _nothing_written_in_the_store(attempt):
    assert attempt["after"] == attempt["before"]


@when(parsers.parse('the client replaces an artifact named "{name}", saying which role and why'), target_fixture="attempt")
def _replace_by_a_name(client, tmp_path, name):
    before = held.everything_in(tmp_path)
    response = write(client, name, {"sections": SECTIONS}, message="Change it")
    return {"response": response, "before": before, "after": held.everything_in(tmp_path)}


@then("the change is rejected because a name is a kind and a plain name of lower-case letters, digits and single hyphens")
def _rejected_as_not_a_plain_name(attempt):
    refused = attempt["response"]
    assert refused.revision == 0
    assert [fault.rule for fault in refused.faults] == ["locator"]
    assert "plain name" in refused.faults[0].message


@then("nothing is written anywhere, inside the store or outside it")
def _nothing_written_anywhere(attempt):
    assert attempt["after"] == attempt["before"]


PURPOSE = {"title": "Purpose", "body": "Keep prices in step with what they cost us.\n"}
MISPLACED = {
    "replaces a place inside the decision the decision holds nothing under":
        lambda client: write(client, DECISION, PURPOSE, path="sections/nowhere"),
    "replaces a place inside the decision that runs on past a piece of prose":
        lambda client: write(client, DECISION, PURPOSE, path="sections/purpose/body/first"),
    "replaces a place inside the decision beginning at the decision's own version":
        lambda client: write(client, DECISION, PURPOSE, path="revision"),
    "adds an item at a place inside the decision that is not a collection":
        lambda client: append(client, DECISION, "sections/purpose", {"title": "Go monthly"}),
}


@when(
    parsers.re(f"the client (?P<call>{'|'.join(map(re.escape, MISPLACED))}), saying which role and why"),
    target_fixture="attempt",
)
def _aim_at_a_wrong_place(root, client, call):
    before = held.text(root, DECISION)
    return {"response": MISPLACED[call](client), "before": before}


@then("the change is rejected because the decision holds nothing at that place")
def _rejected_for_nothing_there(attempt):
    faults = attempt["response"].faults
    assert [(fault.artifact, fault.rule) for fault in faults] == [(DECISION, "not-found")]
    assert f"holds nothing at {faults[0].path!r}" in faults[0].message


@then("the change is rejected because a place inside an artifact never names what only the store settles")
def _rejected_for_a_settled_place(attempt):
    faults = attempt["response"].faults
    assert [(fault.artifact, fault.path, fault.rule) for fault in faults] == [(DECISION, "revision", "identity")]
    assert faults[0].message.startswith("a place inside an artifact never names what only the store settles")


@then("the change is rejected because an item is added to a collection, and that place is not one")
def _rejected_for_no_collection(attempt):
    faults = attempt["response"].faults
    assert [(fault.artifact, fault.path, fault.rule) for fault in faults] == [(DECISION, "sections/purpose", "collection")]
    assert faults[0].message.startswith("an item is added to a collection")


OPTIONS = [{"title": "Keep weekly", "body": "Review every Monday."}, {"title": "Go monthly", "body": "Review on the first."}]


@given("the decision carries two options")
def _two_options(client):
    response = write(client, DECISION, {"sections": SECTIONS, "options": OPTIONS}, message="Weigh two options")
    assert not response.faults, response.faults
    assert [option["id"] for option in loads(read(client, DECISION, whole=True).content)["options"]] == [
        "keep-weekly", "go-monthly",
    ]


HANDED_BACK = {
    "one of which carries a name no option of that decision has": ["keep-weekly", "go-fortnightly"],
    "both of which carry the same name": ["keep-weekly", "keep-weekly"],
    "one of which carries a name that is not a plain name": ["keep-weekly", "Go Monthly!"],
}


@when(
    parsers.re(f"the client replaces the decision with options (?P<items>{'|'.join(map(re.escape, HANDED_BACK))}), saying which role and why"),
    target_fixture="attempt",
)
def _replace_with_misnamed_options(root, client, items):
    before = held.text(root, DECISION)
    options = [{"id": name, **option} for name, option in zip(HANDED_BACK[items], OPTIONS)]
    response = write(client, DECISION, {"sections": SECTIONS, "options": options}, message="Rename the options")
    return {"response": response, "before": before}


def _misnamed(attempt, message):
    faults = attempt["response"].faults
    assert [(fault.artifact, fault.path, fault.rule) for fault in faults] == [(DECISION, "options/1/id", "item-name")]
    assert faults[0].message.startswith(message)


@then("the change is rejected because a name on an item names an item already in that collection")
def _rejected_for_an_unknown_name(attempt):
    _misnamed(attempt, "a name on an item names an item already in that collection")


@then("the change is rejected because the items of a collection each have a name of their own")
def _rejected_for_a_repeated_name(attempt):
    _misnamed(attempt, "the items of a collection each have a name of their own")


@then("the change is rejected because a name is a plain name of lower-case letters, digits and single hyphens")
def _rejected_for_a_name_not_plain(attempt):
    _misnamed(attempt, "a name is a plain name of lower-case letters, digits and single hyphens")


MONTHLY = {"title": "Go monthly", "body": "Review on the first Monday of the month."}


@when("the client replaces one of the options, saying which role and why", target_fixture="changed")
def _replace_one_option(client):
    define(client, NOTE_TYPE)
    create(client, "note", {"title": "Why monthly", "about": f"{DECISION}#options/go-monthly"})
    before = read(client, DECISION, whole=True)
    response = write(client, DECISION, MONTHLY, message="Say when monthly", path="options/go-monthly")
    assert not response.faults, response.faults
    return {"response": response, "before": before, "after": read(client, DECISION, whole=True)}


@then("only that option changes")
def _only_that_option_changes(changed):
    before, after = loads(changed["before"].content), loads(changed["after"].content)
    assert changed["response"].revision == changed["before"].revision + 1
    assert after["options"][0] == before["options"][0]
    assert {key: value for key, value in after.items() if key != "options"} == {
        key: value for key, value in before.items() if key != "options"
    }
    assert {key: value for key, value in after["options"][1].items() if key != "id"} == MONTHLY


@then("it keeps the name it was given when it was created")
def _keeps_its_name(changed):
    assert [option["id"] for option in loads(changed["after"].content)["options"]] == ["keep-weekly", "go-monthly"]


@then("anything pointing at it still lands on it")
def _still_lands(client):
    assert list(client.Validate(kb_pb2.ValidateRequest()).violations) == []
    inward = refs(client, DECISION, 1, inward=True)
    assert [(reached.stub.id, reached.route[0].field) for reached in inward.reached] == [("note/why-monthly", "about")]


@when(
    "the client replaces the decision, sending both options back with the names they were given and a third option "
    "with no name, saying which role and why",
    target_fixture="changed",
)
def _send_both_back_and_a_third(client):
    options = [{"id": "keep-weekly", **OPTIONS[0]}, {"id": "go-monthly", **OPTIONS[1]}, {"title": "Go fortnightly"}]
    response = write(client, DECISION, {"sections": SECTIONS, "options": options}, message="Add a third option")
    assert not response.faults, response.faults
    return {"response": response, "after": loads(read(client, DECISION, whole=True).content)}


@then("the two options are the same items as before, keeping their names")
def _the_same_two(changed):
    assert changed["after"]["options"][:2] == [{"id": "keep-weekly", **OPTIONS[0]}, {"id": "go-monthly", **OPTIONS[1]}]


@then("the third option is new and is given a name of its own")
def _the_third_named(changed):
    assert changed["after"]["options"][2] == {"id": "go-fortnightly", "title": "Go fortnightly"}


ANOTHER = ("decision", "Another", {"sections": SECTIONS})

BLANK = " \t "

UNSIGNED = {
    "creates another decision": lambda client, actor, message: request(client, *ANOTHER, message=message, actor=actor),
    "replaces the decision": lambda client, actor, message: write(
        client, DECISION, {"sections": SECTIONS}, message=message, actor=actor),
    "adds an option to the decision": lambda client, actor, message: append(
        client, DECISION, "options", {"title": "Go fortnightly"}, message=message, actor=actor),
    "removes the decision": lambda client, actor, message: remove(client, DECISION, message=message, actor=actor),
    "asks, in one go, for another decision to be created and the decision to be replaced":
        lambda client, actor, message: apply(
            client, [creation(*ANOTHER), replacement(DECISION, {"sections": SECTIONS})], message=message, actor=actor),
}

SAYING = {
    "saying why but not which role it is": (kb_pb2.Actor(role=""), "Say why"),
    "saying which role it is but not why": (CLIENT, ""),
    "saying why but giving a role that is only blank space": (kb_pb2.Actor(role=BLANK), "Say why"),
    "saying which role it is but giving as its reason only blank space": (CLIENT, BLANK),
}


def _names(client):
    return [stub.id for stub in listing(client, "decision", ids_only=True).stubs]


@when(
    parsers.re(
        f"the client (?P<call>{'|'.join(map(re.escape, UNSIGNED))}), (?P<saying>{'|'.join(map(re.escape, SAYING))})"
    ),
    target_fixture="attempt",
)
def _change_unsigned(root, client, call, saying):
    before = {
        "before": held.text(root, DECISION),
        "names": _names(client),
        "files": held.holds(root),
        "entries": len(journal(client).entries),
    }
    actor, message = SAYING[saying]
    return {**before, "response": UNSIGNED[call](client, actor, message)}


UNSIGNED_REASONS = {
    "every entry in the history names the role that made it": "actor",
    "every entry in the history says why it was made": "message",
}


@then(parsers.re("the change is rejected because (?P<reason>" + "|".join(map(re.escape, UNSIGNED_REASONS)) + ")"))
def _rejected_for_its_signature(attempt, reason):
    refused = attempt["response"]
    assert [(fault.artifact, fault.path, fault.rule) for fault in refused.faults] == [("", "", UNSIGNED_REASONS[reason])]
    assert refused.faults[0].message.startswith(reason)
    if "revision" in refused.DESCRIPTOR.fields_by_name:
        assert refused.revision == 0


LINKED_OPTION = f"{DECISION}#options/keep-weekly"
LEAVING_IT_OUT = {
    "replaces the decision with content that leaves that option out":
        lambda client: write(client, DECISION, {"sections": SECTIONS, "options": OPTIONS[1:]}, message="Drop weekly"),
    "replaces the decision's collection of options with one that leaves it out":
        lambda client: write(client, DECISION, OPTIONS[1:], message="Drop weekly", path="options"),
}


@given("another artifact links into one of those options")
def _a_note_links_into_an_option(client):
    define(client, NOTE_TYPE)
    create(client, "note", {"title": "Why weekly", "about": LINKED_OPTION})


@when(
    parsers.re(f"the client (?P<call>{'|'.join(map(re.escape, LEAVING_IT_OUT))}), saying which role and why"),
    target_fixture="attempt",
)
def _leave_the_linked_option_out(root, client, call):
    before = held.text(root, DECISION)
    return {"response": LEAVING_IT_OUT[call](client), "before": before}


@then("the change is rejected because something still points at that item")
def _rejected_while_pointed_at(root, attempt):
    assert {fault.rule for fault in attempt["response"].faults} == {"on_delete"}
    assert held.text(root, DECISION) == attempt["before"]


@then("the client is given each link into that option")
def _each_link_into_the_option(attempt):
    faults = attempt["response"].faults
    assert [(fault.artifact, fault.path) for fault in faults] == [("note/why-weekly", "about")]
    assert f"'{LINKED_OPTION}'" in faults[0].message


ONE_RATIONALE = {"title": "Rationale", "body": "Suppliers change their prices every week.\n"}
DIFFERENT_RATIONALE = {"title": "Rationale", "body": "Customers compare prices every week.\n"}


def _replacing(rationale, message):
    return kb_pb2.WriteRequest(
        locator=kb_pb2.Locator(id=DECISION), content=dumps({"sections": [SECTIONS[0], rationale]}), actor=CLIENT,
        message=message,
    )


@given(
    "one client is replacing the decision with one rationale while another replaces it with a different rationale, "
    "each saying which role and why",
    target_fixture="racing",
)
def _replacing_at_once():
    return {
        "one": _replacing(ONE_RATIONALE, "Say it is the suppliers"),
        "different": _replacing(DIFFERENT_RATIONALE, "Say it is the customers"),
    }


@when("the client with the different rationale lands its change second", target_fixture="landed")
def _different_rationale_lands_second(root, racing):
    landed = {}

    def first():
        landed["one"] = kb_client.connect(root).Write(racing["one"])
        assert not landed["one"].faults, landed["one"].faults
    landed["different"] = at_once.landed_second(at_once.OnAThread(root, "Write", racing["different"]), first)
    return landed


@then("each replacement left a version of its own, and the decision's version has gone up by two")
def _a_version_each(client, landed):
    assert not landed["different"].faults, landed["different"].faults
    assert (landed["one"].revision, landed["different"].revision) == (2, 3)
    assert read(client, DECISION).revision == 3


@then("both replacements are in the history")
def _both_in_the_history(client):
    entries = journal(client, DECISION).entries
    assert [(entry.op, entry.revision, entry.message) for entry in entries[-2:]] == [
        ("write", 2, "Say it is the suppliers"), ("write", 3, "Say it is the customers"),
    ]


@then("the decision holds the different rationale")
def _holds_the_different_rationale(client):
    assert loads(read(client, DECISION, whole=True).content)["sections"] == [SECTIONS[0], DIFFERENT_RATIONALE]


@scenario(
    "change-the-store.feature",
    'A change that waits longer than the store waits for another change is refused as busy',
)
def test_a_change_that_waits_longer_than_the_store_waits_for_another_change_is():
    pass


@scenario(
    "change-the-store.feature",
    'A read while another change is being written is not refused as busy',
)
def test_a_read_while_another_change_is_being_written_is_not_refused_as_busy():
    pass


BUSY = "the store was busy with another change"


@then("the change is rejected because the store was busy with another change")
def _rejected_as_busy(changed):
    assert changed.revision == 0
    assert [(fault.artifact, fault.path, fault.rule) for fault in changed.faults] == [("", "", "busy")]
    assert changed.faults[0].message.startswith(BUSY)


@then("the same change may be made again")
def _made_again(client, holding):
    holding.let_go()
    again = _replace_the_decision(client)
    assert (list(again.faults), again.revision) == ([], 2)
