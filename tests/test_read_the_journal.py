import hashlib
from datetime import datetime, timedelta

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from calls import CLIENT, DECISION_TYPE, create, define, journal, write
from kb import client as kb_client
from kb import journal as kb_journal
from kb.contract import kb_pb2

scenarios("read-the-journal.feature")

DECISION = "decision/price-reviews-happen-weekly"
SHOPKEEPER = kb_pb2.Actor(role="shopkeeper")
AGENT = kb_pb2.Actor(role="agent", execution="restock-run-12")


@given(parsers.parse("today is {day}"), target_fixture="clock")
def _today_is(monkeypatch, day):
    """kb stamps each entry from journal.now. Here it reads this clock, which moves on a second at every stamp so no
    two entries share one; a step sets the clock back to make a change on an earlier day."""
    clock = {"today": datetime.fromisoformat(f"{day}T09:00:00+00:00")}
    clock["at"] = clock["today"]

    def now():
        clock["at"] += timedelta(seconds=1)
        return clock["at"]

    monkeypatch.setattr(kb_journal, "now", now)
    return clock


@pytest.fixture
def written():
    """The bytes of the decision's file after each change, in order, for the fingerprints."""
    return []


@given(
    "a store where the shopkeeper created a decision on 2026-09-21 "
    "and an agent working on a named piece of work changed it today",
    target_fixture="client",
)
def _store_with_a_decision_changed_today(root, clock, written):
    clock["at"] = datetime.fromisoformat("2026-09-21T09:00:00+00:00")
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, DECISION_TYPE)
    create(client, "decision", {
        "title": "Price reviews happen weekly",
        "sections": [
            {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
            {"title": "Rationale", "body": "Costs move weekly.\n"},
        ],
    }, message="Review prices weekly", actor=SHOPKEEPER)
    written.append((root / "kb" / f"{DECISION}.yaml").read_bytes())
    clock["at"] = clock["today"]
    changed = write(client, DECISION, {"sections": [
        {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
        {"title": "Rationale", "body": "Costs move weekly, and the suppliers say so.\n"},
    ]}, message="Say why weekly", actor=AGENT)
    assert not changed.faults, changed.faults
    written.append((root / "kb" / f"{DECISION}.yaml").read_bytes())
    return client


@when("the client reads the journal for that decision", target_fixture="entries")
def _read_the_journal_for_the_decision(client):
    response = journal(client, DECISION)
    assert not response.faults, response.faults
    return list(response.entries)


@then("there is one entry for each change")
def _one_entry_for_each_change(entries):
    assert [(entry.op, entry.artifact) for entry in entries] == [("create", DECISION), ("write", DECISION)]


@then(
    "each entry says when it happened, which role made it, for which piece of work, what it did, to which artifact "
    "and place in it, the version it left behind, a fingerprint of what was written, the message given, "
    "and which set of changes it landed with"
)
def _each_entry_says_everything(entries, written):
    assert [
        (entry.at[:10], entry.actor.role, entry.actor.execution, entry.op, entry.artifact, entry.path,
         entry.revision, entry.schema_version, entry.message)
        for entry in entries
    ] == [
        ("2026-09-21", "shopkeeper", "", "create", DECISION, "", 1, 1, "Review prices weekly"),
        ("2026-09-23", "agent", "restock-run-12", "write", DECISION, "", 2, 1, "Say why weekly"),
    ]
    assert [entry.digest for entry in entries] == [hashlib.sha256(text).hexdigest() for text in written]
    assert [entry.batch for entry in entries] == [entry.id for entry in entries]
