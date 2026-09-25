import hashlib

from pytest_bdd import given, scenarios, then, when

from calls import CLIENT, DECISION_TYPE, PROCESS_TYPE, create, define, journal, snapshot, write
from kb import client as kb_client
from kb.contract import kb_pb2

scenarios("snapshot-what-a-piece-of-work-read.feature")

DECISION = "decision/price-reviews-happen-weekly"
PROCESS = "process/open-the-shop"
EXECUTION = "restock-run-12"


def _sections(rationale):
    return [{"title": "Purpose", "body": "Keep prices in step with costs.\n"}, {"title": "Rationale", "body": rationale}]


@given("a store holding a decision at its third version and a process at its first", target_fixture="client")
def _store_with_a_decision_and_a_process(root):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, DECISION_TYPE)
    define(client, PROCESS_TYPE)
    create(client, "decision", {"title": "Price reviews happen weekly", "sections": _sections("Costs move.\n")})
    for rationale in ("Costs move weekly.\n", "Costs move weekly, and the suppliers say so.\n"):
        changed = write(client, DECISION, {"sections": _sections(rationale)})
        assert not changed.faults, changed.faults
    create(client, "process", {"title": "Open the shop", "steps": [{"title": "Unlock the door"}]})
    return client


@when("the client snapshots the decision and the process for a piece of work", target_fixture="snapshotted")
def _snapshot(client):
    response = snapshot(client, EXECUTION, [DECISION, PROCESS], message="Read before restocking")
    assert not response.faults, response.faults
    return response


@then("the journal holds one entry listing each of them with the version read and a fingerprint of it")
def _one_entry_listing_each(client, root):
    [entry] = [entry for entry in journal(client).entries if entry.op == "snapshot"]
    fingerprint = {name: hashlib.sha256((root / "kb" / f"{name}.yaml").read_bytes()).hexdigest() for name in (DECISION, PROCESS)}
    assert [(read.artifact, read.revision, read.digest) for read in entry.read] == [
        (DECISION, 3, fingerprint[DECISION]), (PROCESS, 1, fingerprint[PROCESS]),
    ]
    assert (entry.actor.role, entry.actor.execution, entry.message) == ("agent", EXECUTION, "Read before restocking")


@then("the client is given the name of that entry")
def _given_the_entry(client, snapshotted):
    [entry] = [entry for entry in journal(client).entries if entry.op == "snapshot"]
    assert snapshotted.entry == entry.id
