"""A store reached through a server: the client finds the connection to it where it works, and each call goes over
the network to the server, on a port the system picks (tests/serving.py): `kb serve` run as a program where a step
says the operator runs it, and otherwise a server hosted in the test's own process, whose clock and lock a step
watches."""
import threading

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from calls import (
    DECISION_TYPE, TAG_TYPE, answer, create, creating, define, next_version, read, removing, replace, start_a_store,
    tagged_decision_type,
)
import serving
from kb import client as kb_client, content
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


@when("the client replaces the decision, saying which role and why", target_fixture="changed")
def _replace_the_decision():
    return replace(kb_client.connect(), DECISION, {"sections": [
        SECTIONS[0], {"title": "Rationale", "body": "Suppliers change their prices every week.\n"},
    ]}, message="Say why weekly")


@then("the change is rejected because the store is served, and the server's address is named back")
def _refused_as_served(changed, address):
    assert changed.refused
    assert [(fault.rule, address in fault.message) for fault in changed.faults] == [("served", True)], changed.faults


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
