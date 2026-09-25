import copy

from pytest_bdd import given, parsers, scenarios, then, when

from calls import CLIENT, DECISION_TYPE, create, define, everything_under, read, write
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
