"""Many clients changing one artifact at the same moment, each on a thread of its own: every change lands, none
refused for the race, and the history gives the artifact's changes in the order they landed. Through the contract,
each store under its own tmp_path."""
import threading

from calls import CLIENT, add, create, define, journal, read
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
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
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
