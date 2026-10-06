"""While `kb serve` owns a store, every rpc that writes, asked of the store directly, is refused with `served`, naming
the server's address, and writes nothing, while every read is answered; a server killed without warning leaves the
store taking changes again; and a second server on a served store is refused before it listens, the first serving on
(the plan's decisions 1 to 4)."""
import pytest

from calls import (CLIENT, TAG_TYPE, answer, create, creating, define, replacing, removing, signature,
                   start_a_store)
from conftest import _kb
import held
import serving
from kb import client as kb_client
from kb.contract import kb_pb2

KEPT = "tag/kept"


def _started(root):
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, TAG_TYPE)
    create(client, "tag", {"title": "Kept"})
    return client


def _signed(message="Change something"):
    return signature(message, CLIENT)


WRITING = {
    "Create": lambda: creating("tag", "New", {}),
    "Replace": lambda: replacing(KEPT, {"summary": "Still kept."}),
    "Add": lambda: kb_pb2.AddRequest(locator=kb_pb2.Locator(id=KEPT, place="items"), content="{}\n",
                                     signature=_signed()),
    "Remove": lambda: removing(KEPT),
    "BatchCreate": lambda: kb_pb2.BatchCreateRequest(
        items=[kb_pb2.CreateItem(kind="tag", title="New", content="{}\n")], signature=_signed()),
    "BatchReplace": lambda: kb_pb2.BatchReplaceRequest(
        items=[kb_pb2.ReplaceItem(locator=kb_pb2.Locator(id=KEPT), content="summary: Still kept.\n")],
        signature=_signed()),
    "BatchAdd": lambda: kb_pb2.BatchAddRequest(
        items=[kb_pb2.AddItem(locator=kb_pb2.Locator(id=KEPT, place="items"), content="{}\n")], signature=_signed()),
    "BatchRemove": lambda: kb_pb2.BatchRemoveRequest(
        items=[kb_pb2.RemoveItem(locator=kb_pb2.Locator(id=KEPT))], signature=_signed()),
    "Snapshot": lambda: kb_pb2.SnapshotRequest(
        signature=kb_pb2.Signature(role="agent", execution="run-1", message="Say what was read"), artifacts=[KEPT]),
}

READING = {
    "Read": lambda: kb_pb2.ReadRequest(locator=kb_pb2.Locator(id=KEPT)),
    "Check": lambda: kb_pb2.CheckRequest(),
    "History": lambda: kb_pb2.HistoryRequest(),
    "Search": lambda: kb_pb2.SearchRequest(text="kept"),
    "Follow": lambda: kb_pb2.FollowRequest(locator=kb_pb2.Locator(id=KEPT)),
    "List": lambda: kb_pb2.ListRequest(kind="tag"),
}


@pytest.mark.parametrize("rpc", WRITING)
def test_every_rpc_that_writes_asked_of_a_served_store_directly_is_refused_as_served_and_writes_nothing(
        root, request, rpc):
    client = _started(root)
    address = serving.serving(root, request)
    before = held.holds(root), held.history(client)
    answered = answer(getattr(client, rpc)(WRITING[rpc]()))
    assert [(fault.rule, address in fault.message) for fault in answered.faults] == [("served", True)]
    assert (held.holds(root), held.history(client)) == before


@pytest.mark.parametrize("rpc", READING)
def test_every_read_asked_of_a_served_store_directly_is_answered(root, request, rpc):
    client = _started(root)
    serving.serving(root, request)
    answered = answer(getattr(client, rpc)(READING[rpc]()))
    assert not answered.refused, answered.faults


def test_a_store_whose_server_was_killed_without_warning_takes_a_change_asked_of_it_directly(root, request):
    client = _started(root)
    server = serving.started(root, request)
    assert server.said().startswith("serving\t")
    server.kill()
    before = len(held.history(client))
    answered = answer(client.Replace(replacing(KEPT, {"summary": "Still kept."})))
    assert not answered.refused, answered.faults
    assert len(held.history(client)) == before + 1


def test_a_second_server_on_a_served_store_is_refused_naming_the_first_and_the_first_serves_on(
        root, tmp_path, request, monkeypatch):
    client = _started(root)
    address = serving.serving(root, request)
    ran = _kb("serve", str(root), "--listen", "127.0.0.1:0", cwd=root)
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr.startswith("kb serve: refused: served: "), ran.stderr
    assert address in ran.stderr
    arranged = tmp_path / "arranged"
    serving.connection(arranged, address)
    monkeypatch.chdir(arranged)
    through_the_server = answer(kb_client.connect().Read(READING["Read"]()))
    assert through_the_server == answer(client.Read(READING["Read"]()))
    refused = answer(client.Replace(WRITING["Replace"]()))
    assert [(fault.rule, address in fault.message) for fault in refused.faults] == [("served", True)]
