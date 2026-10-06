"""A store a client's own tests serve with kb's double, `kb.testing.served`, in the test's own process on a port the
system picks, the connection written in a directory the test names; whatever the double still serves when a test
ends is let go then, passed or failed."""
import contextlib
import re
from datetime import datetime

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from calls import DECISION_TYPE, answer, create, define, journal, moment, start_a_store
import calls
import serving
from kb import canonical, client as kb_client, testing as kb_testing
from kb.contract import kb_pb2

scenarios("serve-a-store-for-tests.feature")

DECISION = "decision/price-reviews-happen-weekly"
SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]
READ = kb_pb2.ReadRequest(locator=kb_pb2.Locator(id=DECISION))


@pytest.fixture
def tests(request):
    """The client's tests, as the blocks the double serves a store around; whatever is still open when the test
    ends is closed then."""
    stack = contextlib.ExitStack()
    request.addfinalizer(stack.close)
    return stack


@given("a store the client started, holding a decision")
def _started_holding_a_decision(root):
    start_a_store(root)
    client = kb_client.connect(root)
    define(client, DECISION_TYPE)
    created = create(client, "decision", {"title": "Price reviews happen weekly", "sections": SECTIONS})
    assert not created.faults, created.faults


@given("a directory other than the one the store sits in", target_fixture="other")
def _another_directory(tmp_path):
    other = tmp_path / "other"
    other.mkdir()
    return other


@given("the client is serving the store for its tests, naming that other directory to hold the connection",
       target_fixture="address")
@when("the client serves the store for its tests, naming that other directory to hold the connection",
      target_fixture="address")
def _serves_for_its_tests(root, other, tests):
    return tests.enter_context(kb_testing.served(root, other))


@then("the client is given the address the store is served at")
def _given_the_address(address, other):
    assert re.fullmatch(r"127\.0\.0\.1:[0-9]+", address), address
    assert canonical.load((other / "kb" / "server.yaml").read_text(encoding="utf-8")) == {"address": address}


@then("a client working in that other directory reads the decision through a server at that address")
def _reads_through_the_server(other, monkeypatch):
    monkeypatch.chdir(other)
    shown = answer(kb_client.connect().Read(READ))
    assert not shown.refused, shown.faults
    assert (shown.id, shown.title) == (DECISION, "Price reviews happen weekly")


class Broken(Exception):
    """What breaks a client's tests off, raised inside the block the store is served around."""


def _passed(tests):
    tests.close()


def _broken_off(tests):
    with pytest.raises(Broken):
        with tests:
            raise Broken("the client's tests broke off")


ENDED = {"passed": _passed, "broken off with an error": _broken_off}


@when(parsers.parse("the client's tests are done with the store, having {ended}"))
def _done_with_the_store(tests, ended):
    ENDED[ended](tests)


@then("the server at the address the client was given no longer answers")
def _no_longer_answers(address, tmp_path, monkeypatch):
    asking = tmp_path / "asking"
    serving.connection(asking, address)
    monkeypatch.chdir(asking)
    shown = answer(kb_client.connect().Read(READ))
    assert [(fault.rule, address in fault.message) for fault in shown.faults] == [("unreachable", True)], shown.faults


@then("that other directory no longer holds the connection")
def _no_connection_left(other):
    assert not (other / "kb" / "server.yaml").exists()


@given(parsers.parse("the client is serving the store for its tests with a clock that reads {reading}, naming that "
                     "other directory to hold the connection"), target_fixture="address")
def _serving_with_a_clock(root, other, tests, reading):
    stood = moment(reading)
    return tests.enter_context(kb_testing.served(root, other, clock=lambda: stood))


@given("a client working in that other directory, readied with no clock of its own", target_fixture="client")
def _working_in_the_other_directory(other, monkeypatch):
    monkeypatch.chdir(other)
    return kb_client.connect()


@when("that client creates a second decision", target_fixture="the_change")
def _creates_a_second_decision(client):
    """The decision created, and the ids of the entries the journal held before it."""
    before = {entry.id for entry in journal(client).entries}
    created = create(client, "decision", {"title": "Restock on Thursdays", "sections": SECTIONS})
    assert not created.faults, created.faults
    return {"before": before}


@then(parsers.parse("every entry that change left in the journal says it happened at {reading}"))
def _every_entry_left_at(client, the_change, reading):
    left = [entry for entry in journal(client).entries if entry.id not in the_change["before"]]
    assert left, "the change left no entry"
    assert [datetime.fromisoformat(entry.at) for entry in left] == [moment(reading)] * len(left)


def test_the_double_takes_away_the_kb_directory_it_made_for_the_connection_and_leaves_one_that_was_there(root, tmp_path):
    """On exit the double removes `kb/` under the directory holding the connection when it made it and nothing else
    is left there, and leaves a `kb/` that was there before, with what else it holds (the plan's decision 15)."""
    _started_holding_a_decision(root)
    bare, kept = tmp_path / "bare", tmp_path / "kept"
    bare.mkdir()
    (kept / "kb").mkdir(parents=True)
    (kept / "kb" / "notes.txt").write_text("the client's own\n", encoding="utf-8")
    with kb_testing.served(root, bare):
        assert (bare / "kb" / "server.yaml").is_file()
    with kb_testing.served(root, kept):
        assert (kept / "kb" / "server.yaml").is_file()
    assert list(bare.iterdir()) == []
    assert sorted(path.name for path in (kept / "kb").iterdir()) == ["notes.txt"]


def test_the_double_lets_the_store_go_on_exit_so_it_takes_changes_directly_again(root, tmp_path):
    """While the double serves, a change asked of the store directly is refused as served; once its block ends the
    lock is let go and the change lands (the plan's decision 3)."""
    _started_holding_a_decision(root)
    direct = kb_client.connect(root)
    with kb_testing.served(root, tmp_path) as address:
        refused = calls.request(direct, "decision", "Restock on Thursdays", {"sections": SECTIONS})
        assert [(fault.rule, address in fault.message) for fault in refused.faults] == [("served", True)]
    landed = calls.request(direct, "decision", "Restock on Thursdays", {"sections": SECTIONS})
    assert not landed.faults, landed.faults
