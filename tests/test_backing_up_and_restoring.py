"""A store backed up and restored, in the cases no scenario names: sets still in the database's write-ahead log are in
the backup, and a restored store is a store like any other, changed and served at once."""
from pathlib import Path

import grpc

from calls import DECISION_TYPE, check, create, define, start_a_store
from conftest import _kb
import serving
import stopping
import held
import signal
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


def test_a_backup_cut_short_is_refused_as_unreadable_and_nothing_is_made(tmp_path, root):
    start_a_store(root)
    define(kb_client.connect(root), DECISION_TYPE)
    create(kb_client.connect(root), "decision", WEEKLY)
    backup = tmp_path / "store.backup"
    ran = _kb("backup", str(backup), cwd=root)
    assert (ran.returncode, ran.stderr) == (0, ""), ran.stderr
    whole = backup.read_bytes()
    backup.write_bytes(whole[: len(whole) // 2])
    into = tmp_path / "restored"
    into.mkdir()
    ran = _kb("restore", str(backup), str(into), cwd=tmp_path)
    assert (ran.returncode, ran.stdout) == (2, "")
    [line] = ran.stderr.splitlines()
    assert line.startswith("kb restore: refused: unreadable: "), line
    assert "Traceback" not in ran.stderr
    assert list(into.iterdir()) == []


def test_a_restore_interrupted_exits_without_a_traceback_and_leaves_no_store(tmp_path, root):
    """Ctrl-C during `kb restore`: it ends as an interrupt ends a program, non-zero, with no traceback, and leaves
    nothing, what it staged taken away."""
    source = tmp_path / "source"
    source.mkdir()
    start_a_store(source)
    define(kb_client.connect(source), DECISION_TYPE)
    backup = tmp_path / "store.backup"
    assert _kb("backup", str(backup), cwd=source).returncode == 0
    ran = stopping.stopped_restore(root, backup, signal.SIGINT)
    assert ran.returncode == -signal.SIGINT
    assert "Traceback" not in ran.stderr, ran.stderr
    assert held.holds_nothing(root)


def test_a_backup_in_a_directory_that_does_not_exist_is_refused_naming_the_place(tmp_path, root):
    """The place's directory is not made, and the refusal names the place, not the store."""
    start_a_store(root)
    place = tmp_path / "nowhere" / "store.backup"
    ran = _kb("backup", str(place), cwd=root)
    assert (ran.returncode, ran.stdout) == (2, "")
    [line] = ran.stderr.splitlines()
    assert line.startswith(f"kb backup: refused: root: a backup cannot be written at {str(place)!r}: "), line
    assert not place.parent.exists()


def test_a_backup_over_a_dangling_link_is_refused_and_the_link_left(tmp_path, root):
    start_a_store(root)
    place = tmp_path / "store.backup"
    place.symlink_to(tmp_path / "missing")
    ran = _kb("backup", str(place), cwd=root)
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr == f"kb backup: refused: root: a backup never overwrites; {str(place)!r} already holds something\n"
    assert place.is_symlink() and not (tmp_path / "missing").exists()


def test_a_copy_that_fails_in_the_backups_place_is_refused_naming_it_and_leaves_nothing(tmp_path, root, monkeypatch):
    """The file the copy may grow to is cut short, so the write into the backup fails; the store is not at fault."""
    import resource
    start_a_store(root)
    define(kb_client.connect(root), DECISION_TYPE)
    place = tmp_path / "store.backup"
    signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
    soft, hard = resource.getrlimit(resource.RLIMIT_FSIZE)
    resource.setrlimit(resource.RLIMIT_FSIZE, (4096, hard))
    try:
        ran = _kb("backup", str(place), cwd=root)
    finally:
        resource.setrlimit(resource.RLIMIT_FSIZE, (soft, hard))
        signal.signal(signal.SIGXFSZ, signal.SIG_DFL)
    assert (ran.returncode, ran.stdout) == (2, "")
    [line] = ran.stderr.splitlines()
    assert line.startswith(f"kb backup: refused: root: a backup cannot be written at {str(place)!r}: "), line
    assert not place.exists()
