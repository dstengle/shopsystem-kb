import re

from pytest_bdd import given, scenarios, then, when

from calls import CLIENT, DECISION_TYPE, create, define
from kb import client as kb_client
from kb.contract import kb_pb2

scenarios("look-after-a-store.feature")

LONG_LINE = (
    "Costs move weekly, and a review that runs once a month lags them by three weeks on average, "
    "which is long enough to lose money on every shelf in the shop."
)


@given(
    "a store holding a decision whose purpose is one short line and which carries a list of options",
    target_fixture="decision_file",
)
def _store_with_a_short_decision(root):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, DECISION_TYPE)
    created = create(client, "decision", {
        "title": "Price reviews happen weekly",
        "sections": [
            {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
            {"title": "Rationale", "body": LONG_LINE + "\n"},
        ],
        "options": [
            {"title": "Keep weekly", "body": "Review every Monday."},
            {"title": "Go monthly", "body": "Review on the first of the month."},
        ],
    })
    return root / "kb" / f"{created.id}.yaml"


@when("the operator opens the decision's file", target_fixture="text")
def _open_the_file(decision_file):
    return decision_file.read_text()


@then("every piece of prose stands as a block of its own, however short it is")
def _prose_as_blocks(text):
    bodies = re.findall(r"^\s*body: (.*)$", text, re.M)
    assert len(bodies) == 4, text
    assert all(marker in ("|", "|-") for marker in bodies), text


@then("each list is written beneath the name it belongs to, indented under it")
def _lists_indented(text):
    assert re.search(r"^sections:\n  - title: Purpose$", text, re.M), text
    assert re.search(r"^options:\n  - id: keep-weekly$", text, re.M), text


@then("no line of prose has been broken to fit a width")
def _no_folding(text):
    assert ("\n      " + LONG_LINE + "\n") in text, text


@then("nothing in the file tells a reader how to build a value")
def _no_tags(text):
    assert not re.search(r"\s!\S", text), text


SAME_DECISION = {
    "title": "Price reviews happen weekly",
    "sections": [
        {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
        {"title": "Rationale", "body": "Costs move weekly.\n"},
    ],
    "options": [{"title": "Keep weekly", "body": "Review every Monday."}],
}


@given("two stores each given the same decision by the same client", target_fixture="files")
def _two_stores_with_the_same_decision(tmp_path):
    files = []
    for name in ("one", "two"):
        root = tmp_path / name
        root.mkdir()
        client = kb_client.connect(root)
        client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
        define(client, DECISION_TYPE)
        created = create(client, "decision", SAME_DECISION)
        files.append(root / "kb" / f"{created.id}.yaml")
    return files


@when("the operator compares the two decision files", target_fixture="comparison")
def _compare_the_files(files):
    return [path.read_bytes() for path in files]


@then("the two files are the same, byte for byte")
def _the_same_bytes(comparison):
    assert comparison[0] == comparison[1]
    assert len(comparison[0]) > 0
