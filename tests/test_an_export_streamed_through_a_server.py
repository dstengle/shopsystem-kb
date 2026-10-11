"""An export's stream through a server, in the cases no scenario names (the plan's decisions 2, 4 and 9, Review Focus
1 to 3): a change landing while a client reads an export slowly is not in it; a client that stops reading, however
it stops, leaves the server holding nothing, taking changes and stopping cleanly; a program that ends with a stream
unread ends; a server that stops or is killed partway ends the stream with `unreachable`, and one that cannot be
reached gives it as the stream's one message; and an export is answered while the server is writing a change and
holds another waiting.

A server sends ahead of a client that is not reading only as much as the connection takes, so over a store holding
one large artifact it is still partway through the stream, the store held at its one moment, while the client holds
the first message; how far it has read by then is the connection's affair, so the test of the one moment holds the
server's reading itself (`Slowly`). The servers here run in the test's own process unless a test kills one, so what a server holds
open is what this process holds open."""
import gc
import os
import sqlite3
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

import held
import serving
from calls import TAG_TYPE, answer, create, creating, define, export, filed, iri, journal, start_a_store
from kb import client as kb_client
from kb import export as kb_export
from kb import served, server
from kb.contract import kb_pb2

LARGE = 600_000  # characters in one artifact: more than a server sends ahead of a client that is not reading

# A client in a program of its own, working where the connection is found: it reads the first message of an export,
# says so, and waits for a line; given one, it ends as a program ends, the stream still unread.
PROGRAM = """
import sys
from kb import client
from kb.contract import kb_pb2
stream = client.connect().Export(kb_pb2.ExportRequest())
assert next(stream).WhichOneof("outcome") == "result"
print("partway", flush=True)
sys.stdin.readline()
"""


@pytest.fixture
def root(root):
    """A store holding the type for tags and a tag."""
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, TAG_TYPE)
    create(client, "tag", {"title": "Small"})
    return root


@pytest.fixture
def large(root):
    """The store holding a large tag too, so a server is partway through an export while its client holds the first
    message."""
    create(kb_client.connect(root), "tag", {"title": "Large", "summary": "x" * LARGE})


@pytest.fixture
def arranged(tmp_path, monkeypatch):
    """The directory the client works in, where a test writes the connection to its server."""
    arranged = tmp_path / "arranged"
    arranged.mkdir()
    monkeypatch.chdir(arranged)
    return arranged


@pytest.fixture
def hosting(root, arranged, request):
    """A server for the store in this process, the connection to it written where the client works."""
    hosting = serving.hosted(root, request, None)
    serving.connection(arranged, str(hosting.address))
    return hosting


@pytest.fixture
def nothing_lost(caplog, capfd, monkeypatch):
    """Checked when the test ends: no exception was left in a thread or in something let go, and nothing was logged
    or written to stderr, where grpc reports a call that failed inside the server."""
    lost = []
    monkeypatch.setattr(threading, "excepthook", lambda raised: lost.append(repr(raised.exc_value)))
    monkeypatch.setattr(sys, "unraisablehook", lambda raised: lost.append(repr(raised.exc_value)))
    yield
    gc.collect()
    assert (lost, [record.getMessage() for record in caplog.records], capfd.readouterr().err) == ([], [], "")


def _asked():
    """An export asked through the server, its stream not yet read."""
    return kb_client.connect().Export(kb_pb2.ExportRequest())


def _partway(root):
    """An export asked through the server and read as far as its first message, the server still partway through
    it."""
    stream = _asked()
    first = next(stream)
    assert first.result.WhichOneof("part") == "file"
    assert held.database_open(root) != []
    return first, stream


def _let_go(root):
    """Waits until the server holds the store open no longer."""
    deadline = time.monotonic() + serving.PATIENCE
    while held.database_open(root):
        assert time.monotonic() < deadline, "the server still holds the store open"
        time.sleep(0.005)


def _only_unreachable(message, address):
    """The message is a refusal for one reason, that the server at the address cannot be reached."""
    assert message.WhichOneof("outcome") == "refusal"
    assert [(fault.rule, address in fault.message) for fault in message.refusal.faults] == [("unreachable", True)]


class Slowly:
    """`export.taken` as the server calls it, but that it reads on past the second thing it gives only once let go:
    the server is held with files and the position still to read, however much the connection takes ahead of a
    client that is not reading."""

    def __init__(self):
        self._taken, self._go = kb_export.taken, threading.Event()

    def __call__(self, store, asked):
        for count, given in enumerate(self._taken(store, asked)):
            yield given
            if count == 1:
                assert self._go.wait(serving.PATIENCE), "the export was never let go on"

    def let_go(self):
        self._go.set()


def test_a_change_landing_while_an_export_is_read_slowly_through_a_server_is_not_in_it(
        root, hosting, nothing_lost, monkeypatch):
    client = kb_client.connect()
    before = export(client)
    slowly = Slowly()
    monkeypatch.setattr(kb_export, "taken", slowly)
    first, stream = _partway(root)
    changed = create(client, "tag", {"title": "Landed meanwhile"})
    slowly.let_go()
    read_slowly = answer([first, *stream])
    assert (read_slowly.files, read_slowly.position) == (before.files, before.position)
    after = export(client)
    assert filed(changed.id) in [place for place, _ in after.files]
    assert after.position == journal(client, artifact=changed.id).entries[-1].id != before.position


def _closes(stream):
    stream.close()


def _lets_go(stream):
    """Nothing: the test lets its own name for the stream go."""


def _in_a_program(arranged):
    """The client's program, started where the connection is found and waiting with its export partway."""
    clean = {key: value for key, value in os.environ.items() if key != "KB_ROOT"}
    program = subprocess.Popen([sys.executable, "-c", PROGRAM], cwd=arranged, env=clean, text=True,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert program.stdout.readline() == "partway\n", program.communicate()
    return program


def _killed(program):
    program.kill()
    program.communicate()


def _ended(program):
    """The program let run to its end, which it reaches, with nothing said, soon."""
    try:
        said = program.communicate("\n", timeout=serving.STOPPING)
    except subprocess.TimeoutExpired:
        _killed(program)
        raise AssertionError("the program did not end") from None
    assert (said, program.returncode) == (("", ""), 0)


def _what_a_stopped_client_leaves(root, hosting):
    """Nothing held: the store is let go, a change lands through the server and the log is free of readers, an
    export is answered whole, and the server stops and lets the store go."""
    _let_go(root)
    client = kb_client.connect()
    create(client, "tag", {"title": "Landed afterwards"})
    with sqlite3.connect(Path(root) / "kb" / "store.sqlite3") as other:
        assert other.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()[0] == 0  # no reader holds the log
    other.close()
    assert export(client).complete
    hosting.stop()
    assert held.database_open(root) == []
    served.owned(root).close()


@pytest.mark.parametrize("stops", [_closes, _lets_go])
def test_a_client_that_stops_reading_partway_through_a_server_leaves_nothing_held(
        root, large, hosting, nothing_lost, stops):
    _, stream = _partway(root)
    stops(stream)
    del stream
    gc.collect()
    _what_a_stopped_client_leaves(root, hosting)


@pytest.mark.parametrize("stops", [_ended, _killed])
def test_a_clients_program_that_stops_with_an_export_partway_leaves_nothing_held(
        root, large, arranged, hosting, nothing_lost, stops):
    program = _in_a_program(arranged)
    assert held.database_open(root) != []
    stops(program)
    _what_a_stopped_client_leaves(root, hosting)


def test_a_server_stopped_partway_through_an_export_ends_the_stream_with_unreachable_and_lets_the_store_go(
        root, large, hosting, nothing_lost, monkeypatch):
    monkeypatch.setattr(server, "GRACE", 0.1)
    first, stream = _partway(root)
    hosting.stop()
    assert held.database_open(root) == []
    served.owned(root).close()
    cut_short = answer([first, *stream])
    assert not cut_short.complete
    assert [message.WhichOneof("outcome") for message in cut_short.messages[:-1]] \
        == ["result"] * (len(cut_short.messages) - 1)
    _only_unreachable(cut_short.messages[-1], str(hosting.address))


def test_a_server_killed_partway_through_an_export_ends_the_stream_with_unreachable(
        root, large, arranged, request):
    serve = serving.started(root, request)
    address = serve.said().split("\t")[-1]
    serving.connection(arranged, address)
    stream = _asked()
    first = next(stream)
    assert first.result.WhichOneof("part") == "file"
    serve.kill()
    cut_short = answer([first, *stream])
    assert not cut_short.complete
    assert [message.WhichOneof("outcome") for message in cut_short.messages[:-1]] \
        == ["result"] * (len(cut_short.messages) - 1)
    _only_unreachable(cut_short.messages[-1], address)


def test_an_export_asked_of_an_address_nobody_listens_at_is_one_message_refused_as_unreachable(arranged):
    address = serving.closed_port()
    serving.connection(arranged, address)
    [only] = list(_asked())
    _only_unreachable(only, address)


def test_an_export_asked_of_a_server_that_answered_one_and_has_stopped_is_one_message_refused_as_unreachable(
        root, hosting):
    assert export(kb_client.connect()).complete
    hosting.stop()
    [only] = list(_asked())
    _only_unreachable(only, str(hosting.address))


def test_a_client_readied_with_a_clock_exports_through_a_server_as_it_does_in_process(root, hosting):
    """A clock is refused only for a change: an export is a read."""
    through = answer(kb_client.connect(clock=lambda: None).Export(kb_pb2.ExportRequest()))
    assert through.complete
    assert through.messages == export(kb_client.connect(root)).messages


def _on_a_thread(act):
    """The act begun on a thread; the thread, and what the act gave under `given` once it is joined."""
    gave = {}
    thread = threading.Thread(target=lambda: gave.update(given=act()), daemon=True)
    thread.start()
    return thread, gave


def _finished(thread, gave):
    thread.join(serving.PATIENCE)
    assert not thread.is_alive()
    return gave["given"]


def test_an_export_is_answered_through_a_server_that_is_writing_one_change_and_holds_another_waiting(
        root, arranged, request):
    gate = serving.Gate()
    hosting = serving.hosted(root, request, gate)
    serving.connection(arranged, str(hosting.address))
    gate.shut()
    try:
        written = _on_a_thread(lambda: kb_client.connect().Create(creating("tag", "Being written", {})))
        gate.holding()
        waiting = _on_a_thread(lambda: kb_client.connect().Create(creating("tag", "Waiting", {})))
        assert hosting.taking.arrived(2, serving.PATIENCE)
        exported = _finished(*_on_a_thread(lambda: export(kb_client.connect())))
    finally:
        gate.open()
    assert exported.complete
    assert sorted(place for place, _ in exported.files if "/tag/" in place) \
        == [filed(iri("tag", "small"))]
    for change in (written, waiting):
        assert not answer(_finished(*change)).refused
