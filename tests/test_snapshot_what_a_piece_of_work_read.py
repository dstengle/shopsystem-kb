import re

from pytest_bdd import given, parsers, scenarios, then, when

from calls import CLIENT, DECISION_TYPE, PROCESS_TYPE, create, define, journal, snapshot, write
import held
from kb import client as kb_client
from kb.contract import kb_pb2

scenarios("snapshot-what-work-read.feature")

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
    return snapshot(client, EXECUTION, [DECISION, PROCESS], message="Read before restocking")


@then("the journal holds one entry listing each of them with the version read and a fingerprint of it")
def _one_entry_listing_each(client, root, snapshotted):
    assert not snapshotted.faults, snapshotted.faults
    [entry] = [entry for entry in journal(client).entries if entry.op == "snapshot"]
    fingerprint = {name: held.fingerprint(root, name) for name in (DECISION, PROCESS)}
    assert [(read.artifact, read.revision, read.digest) for read in entry.read] == [
        (DECISION, 3, fingerprint[DECISION]), (PROCESS, 1, fingerprint[PROCESS]),
    ]
    assert (entry.actor.role, entry.actor.execution, entry.message) == ("agent", EXECUTION, "Read before restocking")


@then("the client is given the name of that entry")
def _given_the_entry(client, snapshotted):
    [entry] = [entry for entry in journal(client).entries if entry.op == "snapshot"]
    assert snapshotted.entry == entry.id


SAID = "Read before restocking"
BLANK = " \t "

WRONGLY = {
    "the decision and the process without naming the piece of work": ("", [DECISION, PROCESS], "agent", SAID),
    "the decision and an artifact the store holds nothing under": (
        EXECUTION, [DECISION, "decision/never-made"], "agent", SAID),
    "the decision and the process without saying which role it is": (EXECUTION, [DECISION, PROCESS], "", SAID),
    "the decision and the process without saying why": (EXECUTION, [DECISION, PROCESS], "agent", ""),
    "the decision and the process giving a role that is only blank space": (EXECUTION, [DECISION, PROCESS], BLANK, SAID),
    "the decision and the process giving as its reason only blank space": (EXECUTION, [DECISION, PROCESS], "agent", BLANK),
}


@when(
    parsers.re(f"the client snapshots (?P<request>{'|'.join(map(re.escape, WRONGLY))})"), target_fixture="snapshotted",
)
def _snapshot_wrongly(client, request):
    execution, artifacts, role, message = WRONGLY[request]
    return snapshot(client, execution, artifacts, message=message, role=role)


REASONS = {
    "a snapshot records what a named piece of work read": [("", "", "actor")],
    "the store holds nothing by that name, and the name asked for is given back": [
        ("decision/never-made", "", "not-found"),
    ],
    "every entry in the history names the role that made it": [("", "", "actor")],
    "every entry in the history says why it was made": [("", "", "message")],
    "the store was busy with another change": [("", "", "busy")],
}


@then(parsers.parse("the snapshot is rejected because {reason}"))
def _snapshot_rejected(snapshotted, reason):
    assert snapshotted.entry == ""
    assert [(fault.artifact, fault.path, fault.rule) for fault in snapshotted.faults] == REASONS[reason]
    if REASONS[reason][0][2] in ("actor", "message", "busy"):
        assert snapshotted.faults[0].message.startswith(reason)


@then("the journal holds no entry for it")
def _no_entry_for_it(client):
    assert [entry for entry in journal(client).entries if entry.op == "snapshot"] == []


@then("the same snapshot may be asked for again")
def _asked_for_again(client, holding):
    holding.let_go()
    again = _snapshot(client)
    assert not again.faults, again.faults
    [entry] = [entry for entry in journal(client).entries if entry.op == "snapshot"]
    assert again.entry == entry.id
