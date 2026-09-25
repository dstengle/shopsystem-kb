import subprocess

from pytest_bdd import given, scenarios, then, when

from calls import (
    CLIENT, DECISION_TYPE, WORK_ITEM_TYPE, apply, create, creation, define, journal, read, replacement,
)
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


def _everything_under(directory):
    """Every file below a directory, with its bytes, so a step can tell whether anything was written."""
    return {path: path.read_bytes() for path in sorted(directory.rglob("*")) if path.is_file()}


@given("a set whose second change is missing a section its type requires", target_fixture="bad_set")
def _a_set_with_a_bad_second_change():
    return [
        creation("decision", "Price reviews happen weekly", {"sections": SECTIONS}),
        creation("decision", "Prices are reviewed monthly", {"sections": []}),
    ]


@when("the client asks for the set, saying which role and why", target_fixture="attempt")
def _ask_for_the_set(root, client, bad_set):
    before = _everything_under(root)
    response = apply(client, bad_set, message="Record two decisions")
    return {"response": response, "before": before, "after": _everything_under(root)}


@then("the set is rejected because a change in it does not fit its type")
def _set_rejected(attempt):
    refused = attempt["response"]
    assert (refused.batch, list(refused.results)) == ("", [])
    assert {(fault.artifact, fault.rule) for fault in refused.faults} == {("decision/prices-are-reviewed-monthly", "sections")}


@then("the store holds neither change")
def _neither_change_held(client, attempt):
    assert attempt["after"] == attempt["before"]
    for name in (DECISION, "decision/prices-are-reviewed-monthly"):
        assert [fault.rule for fault in read(client, name).faults] == ["not-found"]


@then("every fault in the set comes back, not only the first")
def _every_fault_back(attempt):
    assert [(fault.path, fault.message) for fault in attempt["response"].faults] == [
        ("sections", "the sections the type requires must all be present, in order; 'Purpose' is missing"),
        ("sections", "the sections the type requires must all be present, in order; 'Rationale' is missing"),
    ]


@then("the changes the history shows under the name the client was given for the set are exactly those two")
def _the_set_in_the_history(client, applied):
    assert not applied.faults, applied.faults
    shown = journal(client, batch=applied.batch)
    assert not shown.faults, shown.faults
    assert [(entry.op, entry.artifact, entry.revision, entry.batch) for entry in shown.entries] == [
        ("create", DECISION, 1, applied.batch), ("write", WORK_ITEM, 2, applied.batch),
    ]
