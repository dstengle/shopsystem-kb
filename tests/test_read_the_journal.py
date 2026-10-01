import hashlib
from datetime import datetime, timedelta, timezone

import pytest
from pytest_bdd import given, parsers, scenario, then, when

from calls import (
    CLIENT, DECISION_TYPE, append, apply, create, creation, define, journal, moment, remove, snapshot, write,
)
from kb import client as kb_client
from kb import journal as kb_journal
from kb.contract import kb_pb2


@scenario("keep-the-history.feature", "Every change leaves an entry")
def test_every_change_leaves_an_entry():
    pass


@scenario("keep-the-history.feature", "The journal alone shows what landed together")
def test_the_journal_alone_shows_what_landed_together():
    pass


@scenario("keep-the-history.feature", "The client reads the journal for one role")
def test_the_client_reads_the_journal_for_one_role():
    pass


@scenario("keep-the-history.feature", "The client reads the journal for one piece of work")
def test_the_client_reads_the_journal_for_one_piece_of_work():
    pass


@scenario("keep-the-history.feature", "The client reads the journal since a time")
def test_the_client_reads_the_journal_since_a_time():
    pass


@scenario("keep-the-history.feature", "A client given a clock stamps each change it makes with the moment the clock gives")
def test_a_client_given_a_clock_stamps_each_change_it_makes_with_the_moment_the_clock_gives():
    pass


@scenario("keep-the-history.feature", "Changes stamped with the same moment each leave an entry of their own")
def test_changes_stamped_with_the_same_moment_each_leave_an_entry_of_their_own():
    pass


@scenario("keep-the-history.feature", "Sets of changes made at the same moment are told apart")
def test_sets_of_changes_made_at_the_same_moment_are_told_apart():
    pass


@scenario("keep-the-history.feature", "A moment the clock gives in another zone is kept as the same moment")
def test_a_moment_the_clock_gives_in_another_zone_is_kept_as_the_same_moment():
    pass


@scenario("keep-the-history.feature", "A moment the clock gives with no zone is recorded as that moment in UTC")
def test_a_moment_the_clock_gives_with_no_zone_is_recorded_as_that_moment_in_utc():
    pass


@scenario("keep-the-history.feature", "The history read since a time answers plainly whatever zone the clock gave")
def test_the_history_read_since_a_time_answers_plainly_whatever_zone_the_clock_gave():
    pass


@scenario("keep-the-history.feature", "Every way the history can be asked for is checked and answered plainly")
def test_every_way_the_history_can_be_asked_for_is_checked_and_answered_plainly():
    pass


@scenario("keep-the-history.feature", "A change aimed at one place records the place it changed")
def test_a_change_aimed_at_one_place_records_the_place_it_changed():
    pass


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


@when(parsers.re(r"the client reads the journal since (?P<day>\d{4}-\d{2}-\d{2})"), target_fixture="narrowed")
def _since(client, day):
    return _journal_of(client, since=day)


@then("the client is given only the change made today")
def _only_todays_change(narrowed):
    assert narrowed == [("write", DECISION, "agent", "restock-run-12")]


@when("the client reads the journal for a set of changes the history holds nothing under", target_fixture="asked")
def _for_an_unknown_set(client):
    return journal(client, batch="20260101T000000000000Z-1")


@when("the client reads the journal for a role nothing in the history was done under", target_fixture="asked")
def _for_an_unknown_role(client):
    return journal(client, role="auditor")


@when("the client reads the journal since something that cannot be read as a moment in time", target_fixture="asked")
def _since_what_is_no_time(client):
    return journal(client, since="last Tuesday")


@then("the client is given no entries and no fault")
def _nothing_and_no_fault(asked):
    assert (list(asked.entries), list(asked.faults)) == ([], [])


@then("the read is rejected because since names a moment in time")
def _rejected_since(asked):
    assert [(fault.rule, fault.path) for fault in asked.faults] == [("since", "")]
    assert "'last Tuesday'" in asked.faults[0].message
    assert list(asked.entries) == []


@given("a store where an agent replaced one section of a decision")
def _one_section_replaced(client):
    replaced = write(client, DECISION, {"title": "Rationale", "body": "Costs move every week.\n"},
                     message="Say it plainer", actor=AGENT, path="sections/rationale")
    assert not replaced.faults, replaced.faults


@then("the entry for that change names the place inside the decision that was changed")
def _names_the_place(entries):
    assert [(entry.op, entry.path, entry.message) for entry in entries][-1] == (
        "write", "sections/rationale", "Say it plainer",
    )


CHANGES = {
    "creates a second decision": lambda client, message: create(
        client, "decision", {"title": "Restock on Thursdays", "sections": SECTIONS}, message=message, actor=SHOPKEEPER,
    ),
    "changes the decision": lambda client, message: write(
        client, DECISION, {"sections": SECTIONS}, message=message, actor=SHOPKEEPER,
    ),
    "adds an item to one of the decision's collections": lambda client, message: append(
        client, DECISION, "options", {"title": "Every week"}, message=message, actor=SHOPKEEPER,
    ),
    "removes the decision": lambda client, message: remove(client, DECISION, message=message, actor=SHOPKEEPER),
    "makes several changes in one go": lambda client, message: apply(client, [
        creation("decision", "Restock on Thursdays", {"sections": SECTIONS}),
        creation("decision", "Count the till nightly", {"sections": SECTIONS}),
    ], message=message, actor=SHOPKEEPER),
    "snapshots what a piece of work read": lambda client, message: snapshot(
        client, "restock-run-12", [DECISION], message=message, role=SHOPKEEPER.role,
    ),
}


def _signed(change):
    """The role and message the client gives when it makes that change."""
    return SHOPKEEPER.role, f"The client {change}"


def _make(client, change):
    """That change, made by the shopkeeper under its own message."""
    return CHANGES[change](client, _signed(change)[1])


@when(parsers.re(f"the client (?P<change>{'|'.join(CHANGES)})"), target_fixture="the_change")
def _the_client_changes(client, change):
    """The change made, and the ids of the entries the journal held before it, so a Then can tell the entries it
    left."""
    before = {entry.id for entry in journal(client).entries}
    changed = _make(client, change)
    assert not changed.faults, changed.faults
    return {"change": change, "before": before}


def _left_by(client, the_change):
    left = [entry for entry in journal(client).entries if entry.id not in the_change["before"]]
    assert left, "the change left no entry"
    return left


@then(parsers.parse("every entry that change left in the journal says it happened at {reading}"))
def _every_entry_left_at(client, the_change, reading):
    left = _left_by(client, the_change)
    assert [datetime.fromisoformat(entry.at) for entry in left] == [moment(reading)] * len(left)


@then("every entry that change left is in the store's history, under the role and with the message the client gave")
def _every_entry_left_in_the_history(client, the_change):
    left = _left_by(client, the_change)
    assert [(entry.actor.role, entry.message) for entry in left] == [_signed(the_change["change"])] * len(left)


def _changed_five_times(client):
    for turn in range(1, 6):
        changed = write(client, DECISION, {"sections": [
            {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
            {"title": "Rationale", "body": f"Costs move weekly; said {turn} times.\n"},
        ]})
        assert not changed.faults, changed.faults
    return [("write", DECISION)] * 5


SECOND = "decision/restock-on-thursdays"


def _one_of_each(client):
    for change in ("creates a second decision", "changes the decision",
                   "adds an item to one of the decision's collections", "snapshots what a piece of work read"):
        made = _make(client, change)
        assert not made.faults, made.faults
    removed = remove(client, SECOND)
    assert not removed.faults, removed.faults
    return [("create", SECOND), ("write", DECISION), ("append", DECISION), ("snapshot", ""), ("delete", SECOND)]


def _snapshotted_twice(client):
    for _ in range(2):
        made = _make(client, "snapshots what a piece of work read")
        assert not made.faults, made.faults
    return [("snapshot", "")] * 2


def _created_a_second(client):
    made = _make(client, "creates a second decision")
    assert not made.faults, made.faults
    return [("create", SECOND)]


MADE = {
    "created a second decision": _created_a_second,
    "changed the decision five times, one change after another": _changed_five_times,
    "created a second decision, changed the decision, added an item to one of the decision's collections, "
    "snapshotted what a piece of work read, and removed the second decision": _one_of_each,
    "snapshotted what a piece of work read twice": _snapshotted_twice,
}


@given(parsers.re(f"the client has (?P<changes>{'|'.join(MADE)})$"), target_fixture="made")
def _the_client_has_made(client, changes):
    """The ids the journal held before, and each change made as the (op, artifact) its entry should carry."""
    before = {entry.id for entry in journal(client).entries}
    return {"before": before, "changes": MADE[changes](client)}


def _left(entries, made):
    return [entry for entry in entries if entry.id not in made["before"]]


@then(parsers.parse("there is one entry for each of those changes, each saying it happened at {reading}"))
def _one_entry_for_each_at(entries, made, reading):
    left = _left(entries, made)
    assert [(entry.op, entry.artifact) for entry in left] == made["changes"]
    assert [datetime.fromisoformat(entry.at) for entry in left] == [moment(reading)] * len(left)


@then("each of those changes names itself as its own set, and no two of them name the same set")
def _each_its_own_set(entries, made):
    left = _left(entries, made)
    assert [entry.batch for entry in left] == [entry.id for entry in left]
    assert len({entry.batch for entry in left}) == len(left)


FIRST_GO = ["decision/restock-on-thursdays", "decision/count-the-till-nightly"]
SECOND_GO = ["decision/close-early-on-sundays", "decision/order-flour-monthly"]


def _in_one_go(client, artifacts):
    applied = apply(client, [
        creation("decision", artifact.split("/")[1].replace("-", " ").capitalize(), {"sections": SECTIONS})
        for artifact in artifacts
    ])
    assert not applied.faults, applied.faults
    return applied.batch


@given("the client has made two changes in one go, then one change on its own, then two more changes in another go",
       target_fixture="goes")
def _two_goes_and_one_alone(client):
    """The name the client was given for each go, first and second."""
    first = _in_one_go(client, FIRST_GO)
    alone = write(client, DECISION, {"sections": SECTIONS})
    assert not alone.faults, alone.faults
    return [first, _in_one_go(client, SECOND_GO)]


def _sets_of(entries, artifacts):
    return [entry.batch for entry in entries if entry.artifact in artifacts]


@then("the two entries from the first go name one set, and the two entries from the second go name another")
def _each_go_one_set(entries):
    first, second = _sets_of(entries, FIRST_GO), _sets_of(entries, SECOND_GO)
    assert (len(first), len(set(first)), len(second), len(set(second))) == (2, 1, 2, 1)
    assert first[0] != second[0]


@then("the change made on its own names itself as its own set, apart from both")
def _alone_apart_from_both(entries):
    """The change on its own is the decision's latest entry, after the Background's two."""
    alone = [entry for entry in entries if entry.artifact == DECISION][-1]
    assert alone.batch == alone.id
    assert alone.batch not in _sets_of(entries, FIRST_GO + SECOND_GO)


@then("the name the client was given for each go finds exactly that go's two changes in the history")
def _each_name_finds_its_go(client, goes):
    found = [[entry.artifact for entry in journal(client, batch=name).entries] for name in goes]
    assert found == [FIRST_GO, SECOND_GO]


@when("the client reads the journal for the second decision", target_fixture="entries")
def _read_the_journal_for_the_second(client):
    response = journal(client, SECOND)
    assert not response.faults, response.faults
    return list(response.entries)


def _its_creation(entries):
    [created] = [entry for entry in entries if entry.op == "create"]
    return datetime.fromisoformat(created.at)


@then(parsers.parse("the entry for its creation says it happened at the same moment as {reading}"))
def _at_the_same_moment_as(entries, reading):
    assert _its_creation(entries) == moment(reading)


@then(parsers.parse("the entry gives that moment in UTC, as {reading}"))
def _given_in_utc_as(entries, reading):
    at = _its_creation(entries)
    assert (at, at.utcoffset()) == (moment(reading), timedelta(0))


@then(parsers.parse("the entry for its creation says it happened at {reading}, given in UTC"))
def _at_given_in_utc(entries, reading):
    at = _its_creation(entries)
    assert (at, at.utcoffset()) == (moment(reading).replace(tzinfo=timezone.utc), timedelta(0))


@when(parsers.parse("the client reads the journal for the second decision since {reading}"), target_fixture="asked")
def _for_the_second_since(client, reading):
    return journal(client, SECOND, since=moment(reading).isoformat())


@then("the client is given the creation of the second decision")
def _given_its_creation(asked):
    assert ([(entry.op, entry.artifact) for entry in asked.entries], list(asked.faults)) == ([("create", SECOND)], [])
