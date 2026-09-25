import hashlib
from datetime import datetime, timedelta

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from calls import CLIENT, DECISION_TYPE, apply, create, creation, define, journal, write
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


SECTIONS = [
    {"title": "Purpose", "body": "Keep the shop running.\n"},
    {"title": "Rationale", "body": "It was agreed.\n"},
]
TOGETHER = ["decision/restock-on-thursdays", "decision/count-the-till-nightly"]
ALONE = "decision/close-early-on-sundays"


@given("a store where two artifacts were changed in one go and a third was changed on its own")
def _two_together_and_one_alone(client):
    applied = apply(client, [
        creation("decision", "Restock on Thursdays", {"sections": SECTIONS}),
        creation("decision", "Count the till nightly", {"sections": SECTIONS}),
    ], message="Two decisions at once")
    assert not applied.faults, applied.faults
    create(client, "decision", {"title": "Close early on Sundays", "sections": SECTIONS}, message="One on its own")


@when("the client reads the journal", target_fixture="entries")
def _read_the_whole_journal(client):
    response = journal(client)
    assert not response.faults, response.faults
    return list(response.entries)


@then("the two entries from the one go name the same set of changes")
def _same_set(entries):
    together = [entry for entry in entries if entry.artifact in TOGETHER]
    assert [entry.artifact for entry in together] == TOGETHER
    assert together[0].batch == together[1].batch


@then("the entry for the change made on its own names itself as its own set")
def _its_own_set(entries):
    [alone] = [entry for entry in entries if entry.artifact == ALONE]
    assert alone.batch == alone.id


@then("the client can tell what landed together from the journal without reading anything else")
def _grouped_by_the_journal_alone(entries):
    sets = {}
    for entry in entries:
        sets.setdefault(entry.batch, []).append(entry.artifact)
    assert [artifacts for artifacts in sets.values() if len(artifacts) > 1] == [TOGETHER]


def _journal_of(client, **narrowed):
    response = journal(client, **narrowed)
    assert not response.faults, response.faults
    return [(entry.op, entry.artifact, entry.actor.role, entry.actor.execution) for entry in response.entries]


@when("the client reads the journal for the shopkeeper", target_fixture="narrowed")
def _for_the_shopkeeper(client):
    return _journal_of(client, role="shopkeeper")


@then("the client is given only the creation of the decision")
def _only_the_creation(narrowed):
    assert narrowed == [("create", DECISION, "shopkeeper", "")]


@when("the client reads the journal for that piece of work", target_fixture="narrowed")
def _for_the_piece_of_work(client):
    return _journal_of(client, execution="restock-run-12")


@then("the client is given only the change the agent made")
def _only_the_agents_change(narrowed):
    assert narrowed == [("write", DECISION, "agent", "restock-run-12")]


@when(parsers.parse("the client reads the journal since {day}"), target_fixture="narrowed")
def _since(client, day):
    return _journal_of(client, since=day)


@then("the client is given only the change made today")
def _only_todays_change(narrowed):
    assert narrowed == [("write", DECISION, "agent", "restock-run-12")]
