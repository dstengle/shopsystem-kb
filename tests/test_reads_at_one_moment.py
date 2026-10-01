"""Reads beside a writer: one client creates and removes one artifact over and over while another reads it and
snapshots it. Each read and each snapshot sees the store at one moment, so it finds the artifact whole or not at
all, and is never answered with a `store` fault. Through the contract, the store under the test's own tmp_path.

The reader lingers a moment after the store says it holds the artifact, so that the writer's next change has time
to land before the reader reads on: the window a read made one statement at a time leaves open."""
import threading
import time

from calls import CLIENT, TAG_TYPE, define, read, remove, request, snapshot
from kb import client as kb_client
from kb import sqlite_reads
from kb.contract import kb_pb2

ROUNDS = 300
LINGER = 0.002  # seconds the reader waits after finding the artifact held


def _lingering(monkeypatch, reader: threading.Thread):
    """The store's answer to whether it holds an artifact, given to the reader only after a pause when it does."""
    holds = sqlite_reads.Reads.holds

    def lingered(self, artifact_id):
        found = holds(self, artifact_id)
        if found and threading.current_thread() is reader:
            time.sleep(LINGER)
        return found
    monkeypatch.setattr(sqlite_reads.Reads, "holds", lingered)


def test_a_read_and_a_snapshot_beside_a_create_and_remove_loop_are_never_a_store_fault(root, monkeypatch):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, TAG_TYPE)
    done, faults, failed = threading.Event(), [], []

    def churn():
        own = kb_client.connect(root)
        while not done.is_set():
            failed.extend(request(own, "tag", "T", {}).faults)
            failed.extend(remove(own, "tag/t").faults)

    _lingering(monkeypatch, threading.current_thread())
    writer = threading.Thread(target=churn, daemon=True)
    writer.start()
    try:
        reader = kb_client.connect(root)
        for _ in range(ROUNDS):
            faults.extend(fault for fault in read(reader, "tag/t", whole=True).faults if fault.rule != "not-found")
            faults.extend(fault for fault in snapshot(reader, "x", ["tag/t"]).faults if fault.rule != "not-found")
    finally:
        done.set()
        writer.join(30)
    assert failed == []
    assert faults == []
