"""A store backed up and restored, in the cases no scenario names: sets still in the database's write-ahead log are in
the backup, and a restored store is a store like any other, changed and served at once."""
from pathlib import Path

import grpc

from calls import DECISION_TYPE, check, create, define, start_a_store
from conftest import _kb
import serving
from kb import client as kb_client, store
from kb.contract import kb_pb2, kb_pb2_grpc

WEEKLY = {"title": "Price reviews happen weekly", "sections": [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]}


def _backed_up_and_restored(source, tmp_path):
    """The store at source backed up by the operator, and the backup restored by the operator in a new directory; the
    backup one file, with nothing made beside it by either."""
    backup = tmp_path / "store.backup"
    ran = _kb("backup", str(backup), cwd=source)
    assert (ran.returncode, ran.stderr) == (0, ""), ran.stderr
    restored = tmp_path / "restored"
    restored.mkdir()
    ran = _kb("restore", str(backup), str(restored), cwd=tmp_path)
    assert (ran.returncode, ran.stderr) == (0, ""), ran.stderr
    assert sorted(each.name for each in tmp_path.iterdir() if each.name.startswith(backup.name)) == [backup.name]
    return restored


def test_a_backup_holds_the_sets_the_write_ahead_log_holds_not_yet_checkpointed(tmp_path, root):
    """A connection held open keeps SQLite from checkpointing the log when the client's closes, so the decision
    landed is in the log alone when the backup is made; the restored store holds it."""
    start_a_store(root)
    client = kb_client.connect(root)
    define(client, DECISION_TYPE)
    with store.opened(root) as holding:
        assert holding.ids()
        create(client, "decision", WEEKLY)
        log = Path(root) / "kb" / "store.sqlite3-wal"
        assert log.is_file() and log.stat().st_size > 0
        restored = _backed_up_and_restored(root, tmp_path)
    assert kb_client.connect(restored).Read(kb_pb2.ReadRequest(
        locator=kb_pb2.Locator(id="decision/price-reviews-happen-weekly"), whole=kb_pb2.ReadRequest.Whole(),
    )).WhichOneof("outcome") == "result"


def test_a_restored_store_is_changed_and_served_at_once(tmp_path, root, request):
    start_a_store(root)
    define(kb_client.connect(root), DECISION_TYPE)
    restored = _backed_up_and_restored(root, tmp_path)
    created = create(kb_client.connect(restored), "decision", WEEKLY)
    assert (created.id, created.revision) == ("decision/price-reviews-happen-weekly", 1)
    hosting = serving.hosted(restored, request, clock=None)
    with grpc.insecure_channel(str(hosting.address)) as channel:
        listed = kb_pb2_grpc.KbStub(channel).List(kb_pb2.ListRequest(kind="decision", form=kb_pb2.ListRequest.IDS))
    assert list(listed.result.ids) == ["decision/price-reviews-happen-weekly"]


def test_a_backup_of_a_freshly_started_store_restores_to_a_store_that_checks_clean(tmp_path, root):
    start_a_store(root)
    restored = _backed_up_and_restored(root, tmp_path)
    checked = check(kb_client.connect(restored))
    assert not checked.refused, checked.faults
    assert (list(checked.violations), list(checked.stale)) == ([], [])
    assert [entry.op for entry in kb_client.connect(restored).History(kb_pb2.HistoryRequest()).result.entries] == \
        [entry.op for entry in kb_client.connect(root).History(kb_pb2.HistoryRequest()).result.entries]
