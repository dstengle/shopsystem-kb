"""Many clients changing one artifact at the same moment, each on a thread of its own: every change lands, none
refused for the race, and the history gives the artifact's changes in the order they landed; and a change that says
the revision it read, drafted before another lands and landing after it, refused rather than drafted again onto what
it never read. Through the contract, each store under its own tmp_path."""
import threading

import pytest

import at_once
from calls import (
    DECISION_TYPE, add, adding, create, define, journal, read, removing, replace, replaced, replacing, start_a_store,
)
from kb import client as kb_client
from kb.contract import kb_pb2

WRITERS = 8
EACH = 15
LOG_TYPE = {"title": "Log", "version": 1, "schema": {
    "type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"],
    "parts": {"lines": {"items": {"type": "object", "properties": {"title": {"type": "string"}}}}},
}}


def test_every_change_of_many_writers_to_one_artifact_lands_and_the_history_keeps_their_order(root):
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, LOG_TYPE)
    create(client, "log", {"title": "Daily"})
    faults, start = [], threading.Barrier(WRITERS)

    def write(writer):
        own = kb_client.connect(root)
        start.wait()
        for count in range(EACH):
            added = add(own, "log/daily", "lines", {"title": f"Writer {writer} item {count}"})
            faults.extend(added.faults)

    threads = [threading.Thread(target=write, args=(writer,)) for writer in range(WRITERS)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert faults == []
    assert read(client, "log/daily").revision == 1 + WRITERS * EACH
    revisions = [entry.revision for entry in journal(client, artifact="log/daily").entries]
    assert revisions == list(range(1, 2 + WRITERS * EACH))


DECISION = "decision/price-reviews-happen-weekly"
SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"}, {"title": "Rationale", "body": "Weekly.\n"},
]
SAYING_REVISION_ONE = {
    "Replace": lambda: replacing(DECISION, {"sections": SECTIONS}, message="Replace what was read", revision=1),
    "Add": lambda: adding(DECISION, "options", {"title": "Go monthly"}, message="Add to what was read", revision=1),
    "Remove": lambda: removing(DECISION, message="Remove what was read", revision=1),
    "ReplaceMany": lambda: kb_pb2.ReplaceManyRequest(
        items=[replaced(DECISION, {"sections": SECTIONS}, revision=1)],
        signature=kb_pb2.Signature(role="client", message="Replace what was read"),
    ),
}


@pytest.mark.parametrize("rpc", sorted(SAYING_REVISION_ONE))
def test_a_change_saying_a_revision_drafted_before_another_lands_is_refused_not_drafted_again(root, rpc):
    """The held change is drafted while the decision stands at the revision it says, then held at its clock while
    another client replaces the decision; let go, the port finds the decision moved, and the change, drafted again
    under the write lock, is refused with rule `revision` naming where the decision stands, nothing of it written."""
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, DECISION_TYPE)
    create(client, "decision", {"title": "Price reviews happen weekly", "sections": SECTIONS})

    def first():
        another = [SECTIONS[0], {"title": "Rationale", "body": "Daily.\n"}]
        assert replace(client, DECISION, {"sections": another}, message="Another's").revision == 2

    landed = at_once.landed_second(at_once.OnAThread(root, rpc, SAYING_REVISION_ONE[rpc]()), first)
    assert landed.refused
    assert [(fault.artifact, fault.rule) for fault in landed.faults] == [(DECISION, "revision")]
    assert "stands at revision 2" in landed.faults[0].message
    assert read(client, DECISION).revision == 2
    history = journal(client, artifact=DECISION).entries
    assert [entry.message for entry in history] == ["Create an artifact", "Another's"]
