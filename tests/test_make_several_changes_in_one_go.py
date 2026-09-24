import subprocess

from pytest_bdd import given, scenarios, then, when

from calls import CLIENT, DECISION_TYPE, WORK_ITEM_TYPE, apply, create, creation, define, replacement
from kb import canonical, client as kb_client
from kb.contract import kb_pb2

scenarios("make-several-changes-in-one-go.feature")

DECISION = "decision/price-reviews-happen-weekly"
WORK_ITEM = "work-item/move-the-review-to-mondays"
SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]


def _git(root, *args):
    return subprocess.run(["git", "-C", str(root / "kb"), *args], capture_output=True, text=True, check=True).stdout


def _journal(root):
    """Every journal entry in the store, oldest first."""
    return [canonical.load(path.read_text()) for path in sorted((root / "kb" / "journal").rglob("*.yaml"))]


@given("a store holding a decision type and a work item", target_fixture="client")
def _store_with_a_decision_type_and_a_work_item(root):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, DECISION_TYPE)
    define(client, WORK_ITEM_TYPE)
    create(client, "work-item", {"title": "Move the review to Mondays"})
    return client


@when(
    "the client asks, in one go, for a decision to be created and the work item to point at it, in that order, "
    "saying which role and why",
    target_fixture="applied",
)
def _create_and_point_at_it(client):
    return apply(client, [
        creation("decision", "Price reviews happen weekly", {"sections": SECTIONS}),
        replacement(WORK_ITEM, {"decisions": [DECISION]}),
    ], message="Move price reviews to weekly")


@then("the client is given one name for the set, which the client never asked for")
def _given_a_name_for_the_set(applied):
    assert not applied.faults, applied.faults
    assert applied.batch
    assert "batch" not in kb_pb2.ApplyRequest.DESCRIPTOR.fields_by_name


@then("each change also comes back with its own result")
def _a_result_for_each_change(applied):
    assert [(result.id, result.revision) for result in applied.results] == [(DECISION, 1), (WORK_ITEM, 2)]


@then("the store's history shows the set as one change")
def _one_change_in_the_history(root, applied):
    in_set = [entry for entry in _journal(root) if entry["batch"] == applied.batch]
    assert [(entry["op"], entry["artifact"], entry["revision"]) for entry in in_set] == [
        ("create", DECISION, 1), ("write", WORK_ITEM, 2),
    ]
    assert _git(root, "log", "-1", "--format=%an%x09%s").strip() == "client\tMove price reviews to weekly"
    in_commit = set(_git(root, "show", "--name-only", "--format=", "HEAD").split())
    assert {f"{DECISION}.yaml", f"{WORK_ITEM}.yaml"} <= in_commit
    assert len([name for name in in_commit if name.startswith("journal/")]) == 2
