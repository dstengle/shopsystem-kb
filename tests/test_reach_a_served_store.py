"""A store reached through a server: the client finds the connection to it where it works, and each call goes over
the network to the server, on a port the system picks (tests/serving.py): `kb serve` run as a program where a step
says the operator runs it, and otherwise a server hosted in the test's own process, whose clock and lock a step
watches."""
import threading
import time
from datetime import datetime, timezone

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from calls import (
    DECISION_TYPE, TAG_TYPE, answer, create, creating, define, journal, next_version, read, removing, replace,
    start_a_store, tagged_decision_type,
)
import serving
from kb import canonical, client as kb_client, content
from kb.contract import kb_pb2

scenarios("reach-a-served-store.feature")

DECISION = "decision/price-reviews-happen-weekly"
SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]
TAG = "tag/clearance"
TAGGED = "decision/clearance-runs-monthly"
READ = kb_pb2.ReadRequest(locator=kb_pb2.Locator(id=DECISION))


@given("a store holding a decision with a purpose and a rationale, at its first version", target_fixture="client")
def _store_with_a_decision(root):
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, DECISION_TYPE)
    create(client, "decision", {"title": "Price reviews happen weekly", "sections": SECTIONS})
    return client


@given("a server serves that store, and the client works where the connection to that server is found",
       target_fixture="arranged")
@given("a server the operator runs with kb serve serves that store, and the client works where the connection to "
       "that server is found", target_fixture="arranged")
def _served_and_working_where_the_connection_is(root, tmp_path, request, monkeypatch):
    arranged = tmp_path / "arranged"
    connection = serving.connection(arranged, serving.serving(root, request))
    monkeypatch.chdir(arranged)
    return {"connection": connection, "bytes": connection.read_bytes()}


@pytest.fixture
def hosting():
    """The server a step hosts in this process, and the gate its clock is."""
    return {"gate": serving.Gate()}


@given("the store also holds a tag nothing points at")
def _a_loose_tag(client):
    define(client, TAG_TYPE)
    next_version(client, "decision", tagged_decision_type())
    create(client, "tag", {"title": "Clearance"})


@given("a server serves that store", target_fixture="address")
def _served(root, request, hosting):
    hosting["server"] = serving.hosted(root, request, hosting["gate"])
    return str(hosting["server"].address)


@given("one client reaching the server is removing the tag while another reaching it is creating a decision that "
       "points at it, each saying which role and why", target_fixture="racing")
def _removing_while_linking_through_the_server(tmp_path, address, monkeypatch):
    arranged = tmp_path / "arranged"
    serving.connection(arranged, address)
    monkeypatch.chdir(arranged)
    return {
        "removing": removing(TAG, message="Nothing is on clearance"),
        "creating": creating("decision", "Clearance runs monthly", message="Say how often", content={
            "tags": [TAG],
            "sections": [
                {"title": "Purpose", "body": "Clear old stock.\n"},
                {"title": "Rationale", "body": "Stock ages monthly.\n"},
            ],
        }),
    }


def _on_a_thread(rpc, request_sent):
    """The call made by a client of its own, working where the connection is found, on a thread; what it was
    answered, once joined."""
    answered = {}
    thread = threading.Thread(
        target=lambda: answered.update(response=getattr(kb_client.connect(), rpc)(request_sent)), daemon=True,
    )
    thread.start()
    return thread, answered


@when("the creation of the decision arrives at the server first", target_fixture="raced")
def _creation_arrives_first(racing, hosting):
    """The creation held inside the server, at its clock, while the removal arrives at it; then let go."""
    gate, arrivals = hosting["gate"], serving.Arrivals(hosting["server"].taking)
    hosting["server"].taking = arrivals
    gate.shut()
    creating_thread, created = _on_a_thread("Create", racing["creating"])
    gate.holding()
    removing_thread, removed = _on_a_thread("Remove", racing["removing"])
    finished = threading.Thread(target=lambda: (removing_thread.join(), arrivals.second.set()), daemon=True)
    finished.start()
    assert arrivals.second.wait(serving.PATIENCE), "the removal never arrived at the server"
    gate.open()
    for thread in (creating_thread, removing_thread):
        thread.join(serving.PATIENCE)
        assert not thread.is_alive()
    return {"created": answer(created["response"]), "removed": answer(removed["response"])}


STOPPED = {
    "having been stopped by the operator": serving.Serving.stop,
    "its process having been killed without warning": serving.Serving.kill,
}


@given(parsers.parse("a server served that store and has since stopped, {how}"))
def _served_and_stopped(root, request, how):
    server = serving.started(root, request)
    assert server.said().startswith("serving\t")
    STOPPED[how](server)
    assert server.process.poll() is not None


@given("the client is working in the directory the store sits in")
def _working_where_the_store_is(root, monkeypatch):
    monkeypatch.chdir(root)


@when("the client reads the decision", target_fixture="shown")
def _read_the_decision():
    return answer(kb_client.connect().Read(READ))


@then("the removal is rejected because something still points at it")
def _removal_rejected(raced):
    assert not raced["created"].faults, raced["created"].faults
    assert [fault.rule for fault in raced["removed"].faults] == ["on_delete"], raced["removed"].faults


@then("the store holds the tag and the decision that points at it")
def _tag_and_decision_held():
    client = kb_client.connect()
    assert not read(client, TAG).faults
    assert content.loads(read(client, TAGGED, whole=True).content)["tags"] == [TAG]


@then("the client is given what a client that reaches that store in process is given for the same read")
def _given_what_in_process_gives(root, shown):
    assert not shown.refused, shown.faults
    assert shown == answer(kb_client.connect(root).Read(READ))


@then("the client is given the decision")
def _given_the_decision(shown):
    assert not shown.refused, shown.faults
    assert (shown.id, shown.title) == (DECISION, "Price reviews happen weekly")


@pytest.fixture
def machine_clock():
    """A reading of the machine's clock taken before the call the When makes; `after()` reads it again."""
    return {"before": datetime.now(timezone.utc)}


@when("the client replaces the decision, saying which role and why", target_fixture="changed")
def _replace_the_decision(machine_clock, readied_clock):
    """Made by a client working where the connection is found, with the clock it was readied with, if any."""
    return replace(kb_client.connect(clock=readied_clock.get("clock")), DECISION, {"sections": [
        SECTIONS[0], {"title": "Rationale", "body": "Suppliers change their prices every week.\n"},
    ]}, message="Say why weekly")


@then("the change is rejected because the store is served, and the server's address is named back")
def _refused_as_served(changed, address):
    assert changed.refused
    assert [(fault.rule, address in fault.message) for fault in changed.faults] == [("served", True)], changed.faults


@then("every entry that change left in the journal says it happened at the moment the machine's clock gave")
def _stamped_by_the_machines_clock(changed, machine_clock):
    after = datetime.now(timezone.utc)
    assert not changed.faults, changed.faults
    entry = journal(kb_client.connect(), artifact=DECISION).entries[-1]
    assert machine_clock["before"] <= datetime.fromisoformat(entry.at) <= after, (machine_clock["before"], entry.at)


@then("the change is rejected because the clock belongs to a client that reaches its store in process")
def _refused_as_a_clock(changed):
    assert changed.refused
    assert [fault.rule for fault in changed.faults] == ["clock"], changed.faults


@then("the change is not refused because the store is served")
def _not_refused_as_served(changed):
    assert "served" not in [fault.rule for fault in changed.faults], changed.faults


@then("the directory the store sits in holds no connection to a server")
def _no_connection_beside_the_store(root):
    assert not (root / "kb" / "server.yaml").exists()


@then("the connection the client reached the server through is left as it was")
def _connection_as_it_was(arranged):
    assert arranged["connection"].read_bytes() == arranged["bytes"]


def test_kb_root_naming_a_directory_holding_the_connection_to_a_server_reaches_that_server(
        root, tmp_path, request, monkeypatch):
    """KB_ROOT is read as the working directory is: a directory holding the connection reaches its server (the
    plan's decision 11)."""
    _store_with_a_decision(root)
    arranged = tmp_path / "arranged"
    serving.connection(arranged, serving.serving(root, request))
    monkeypatch.setenv("KB_ROOT", str(arranged))
    shown = _read_the_decision()
    assert not shown.refused, shown.faults
    assert shown == answer(kb_client.connect(root).Read(READ))


CONNECTIONS = {
    "cannot be read": b"address: [127.0.0.1:50051\n",
    "names no address": canonical.dump({"host": "127.0.0.1"}).encode("utf-8"),
}


@given(parsers.parse("the client is working where the connection to a server is found, and that connection {state}"),
       target_fixture="connection")
def _working_where_a_connection_leads_nowhere(tmp_path, monkeypatch, state):
    arranged = tmp_path / "arranged"
    connection = serving.connection(arranged, "127.0.0.1:1")
    connection.write_bytes(CONNECTIONS[state])
    monkeypatch.chdir(arranged)
    return connection


@then("the read is rejected because the connection cannot be read or names no address, and the connection is named "
      "back")
def _refused_as_a_connection_leading_nowhere(shown, connection):
    assert shown.refused
    assert [(fault.rule, str(connection) in fault.message) for fault in shown.faults] == [("connection", True)], \
        shown.faults


@given("the client is working where the connection to a server is found, and no server was ever at the address it "
       "names", target_fixture="address")
def _working_where_a_connection_names_nothing(tmp_path, monkeypatch):
    arranged = tmp_path / "arranged"
    address = serving.closed_port()
    serving.connection(arranged, address)
    monkeypatch.chdir(arranged)
    return address


@given("the client is working where the connection to a server is found, and the server at the address it names "
       "answered a read and has stopped", target_fixture="address")
def _working_where_a_connection_names_a_stopped_server(root, tmp_path, request, monkeypatch):
    hosting = serving.hosted(root, request, None)
    address = str(hosting.address)
    arranged = tmp_path / "arranged"
    serving.connection(arranged, address)
    monkeypatch.chdir(arranged)
    assert not answer(kb_client.connect().Read(READ)).refused
    hosting.stop()
    return address


@then("the read is rejected because the server cannot be reached, and the address is named back")
def _refused_as_unreachable(shown, address):
    assert shown.refused
    assert [(fault.rule, address in fault.message) for fault in shown.faults] == [("unreachable", True)], shown.faults


SOON = 10.0  # seconds within which a call to something that never answers comes back refused


def test_a_connection_naming_a_listener_that_accepts_and_never_answers_is_refused_as_unreachable_soon(
        tmp_path, request, monkeypatch):
    """Something at the address that accepts and says nothing is not a server that can be reached: the call comes
    back refused with `unreachable` within a few seconds, never hanging (the plan's Review Focus 4)."""
    address = serving.silent(request)
    arranged = tmp_path / "arranged"
    serving.connection(arranged, address)
    monkeypatch.chdir(arranged)
    began = time.monotonic()
    shown = _read_the_decision()
    assert time.monotonic() - began < SOON
    assert [(fault.rule, address in fault.message) for fault in shown.faults] == [("unreachable", True)], shown.faults
