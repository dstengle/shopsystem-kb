import yaml
from pytest_bdd import given, scenarios, then, when

from calls import CLIENT, DECISION_TYPE, create, define, read, request
from kb import client as kb_client
from kb.contract import kb_pb2

scenarios("create-an-artifact.feature")

SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly, so a monthly review lags them.\n"},
]
OPTIONS = [
    {"title": "Keep weekly", "body": "Review every Monday."},
    {"title": "Go monthly", "body": "Review on the first of the month."},
]


@given(
    "a store holding a decision type whose artifacts require a purpose then a rationale, "
    "may link to the decision they supersede, and may carry a collection of options",
    target_fixture="client",
)
def _store_with_decision_type(root):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, DECISION_TYPE)
    return client


@when(
    "the client creates a decision with a title, both required sections and two options, saying which role and why",
    target_fixture="created",
)
def _create_decision(client):
    return create(client, "decision", {
        "title": "Price reviews happen weekly",
        "sections": SECTIONS,
        "options": OPTIONS,
    }, message="Move price reviews to weekly")


@then("the client is given the name the artifact keeps for life and its first version")
def _given_name_and_first_version(created):
    assert created.id == "decision/price-reviews-happen-weekly"
    assert created.revision == 1


@then("the artifact records the version of the type it was checked against")
def _records_schema_version(client, created):
    assert read(client, created.id).schema_version == 1


@then("reading it back gives what was written, in the order the type declares")
def _read_back_in_declared_order(root, client, created):
    stubs = read(client, created.id).parts
    assert [(stub.collection, stub.id, stub.title) for stub in stubs] == [
        ("options", "keep-weekly", "Keep weekly"),
        ("options", "go-monthly", "Go monthly"),
    ]
    on_disk = yaml.safe_load((root / "kb" / "decision" / "price-reviews-happen-weekly.yaml").read_text())
    assert list(on_disk) == ["id", "type", "schema_version", "revision", "title", "sections", "options"]
    assert on_disk["sections"] == SECTIONS
    assert on_disk["options"] == [
        {"id": "keep-weekly", **OPTIONS[0]},
        {"id": "go-monthly", **OPTIONS[1]},
    ]


@when(
    "the client creates a decision whose content carries a title as well as the title given alongside it, "
    "saying which role and why",
    target_fixture="refused",
)
def _create_with_a_title_inside(client):
    return request(client, "decision", "Price reviews happen weekly", {
        "title": "Price reviews, weekly",
        "sections": SECTIONS,
    }, message="Move price reviews to weekly")


@then(
    "the artifact is rejected because a title is given alongside the content, never inside it, "
    "and the title the content carried is named back"
)
def _rejected_for_a_title_inside(refused):
    assert (refused.id, refused.revision) == ("", 0)
    assert [(fault.path, fault.rule) for fault in refused.faults] == [("title", "identity")]
    assert "Price reviews, weekly" in refused.faults[0].message
