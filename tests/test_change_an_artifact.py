import copy
import re

from pytest_bdd import given, parsers, scenarios, then, when

from calls import (
    CLIENT, DECISION_TYPE, append, apply, creation, define, create, everything_under, journal, listing, read, refs,
    remove, replacement, request, write,
)
from kb import canonical, client as kb_client
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
    assert read(client, DECISION).revision == canonical.load(attempt["before"].decode())["revision"]
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


@when("the client replaces the decision, saying which role and why", target_fixture="changed")
def _replace_the_decision(client):
    response = write(client, DECISION, {"sections": [
        SECTIONS[0], {"title": "Rationale", "body": "Suppliers change their prices every week.\n"},
    ]}, message="Say why weekly")
    assert not response.faults, response.faults
    return response


@then("the version goes up by one")
def _version_up_by_one(client, changed):
    assert changed.revision == 2
    assert read(client, DECISION).revision == 2


@then("the artifact records the current version of its type")
def _records_the_current_version(root, client):
    current = canonical.load((root / "kb" / "schema" / "decision.yaml").read_text())["version"]
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
    before = (root / "kb" / f"{DECISION}.yaml").read_bytes()
    return {"response": write(client, DECISION, {"sections": SECTIONS}, message="No owner"), "before": before}


@then(
    "the change is rejected because the content does not fit the current version of its type, "
    "like any change that does not fit"
)
def _rejected_by_the_current_version(attempt):
    refused = attempt["response"]
    assert refused.revision == 0
    assert [(fault.artifact, fault.path, fault.rule) for fault in refused.faults] == [(DECISION, "", "required")]
    assert "'owner' is a required property" in refused.faults[0].message


@then("it is still listed as behind its type")
def _still_stale(client):
    assert _stale(client) == [DECISION]


@when(
    "the client replaces the decision with content carrying a version of its own, saying which role and why",
    target_fixture="attempt",
)
def _replace_with_a_version_of_its_own(root, client):
    before = (root / "kb" / f"{DECISION}.yaml").read_bytes()
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
    before = everything_under(root / "kb")
    response = write(client, "decision/nothing-of-the-sort", {"sections": SECTIONS}, message="Change it")
    return {"response": response, "before": before, "after": everything_under(root / "kb")}


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
    before = everything_under(tmp_path)
    response = write(client, name, {"sections": SECTIONS}, message="Change it")
    return {"response": response, "before": before, "after": everything_under(tmp_path)}


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
    before = (root / "kb" / f"{DECISION}.yaml").read_bytes()
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
    before = (root / "kb" / f"{DECISION}.yaml").read_bytes()
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


NOTE_TYPE = {
    "title": "Note",
    "version": 1,
    "schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "about": {
                "type": "string",
                "ref": {"targets": ["decision"], "cardinality": "one", "parts": True, "on_delete": "refuse"},
            },
        },
        "required": ["title"],
    },
}
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
    "saying why but giving a role that is only blank space": (kb_pb2.Actor(role="   "), "Say why"),
    "saying which role it is but giving as its reason only blank space": (CLIENT, "   "),
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
        "before": (root / "kb" / f"{DECISION}.yaml").read_bytes(),
        "names": _names(client),
        "files": everything_under(root / "kb"),
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
