"""An export's stream in the client's own process, in the cases no scenario names (the plan's decisions 2 and 8,
Review Focus 1 to 3): a change landing while a client reads an export slowly is not in it; a client that stops
reading leaves the store let go; every refusal every rpc gives arrives as the stream's one message, and a failure after
files were given as its last; and a store restored from a backup gives the backed-up store's position."""
import gc
import os
import sqlite3
from pathlib import Path

import pytest

import held
from calls import TAG_TYPE, answer, check, create, define, export, filed, iri, journal, start_a_store
from conftest import _kb
from kb import client as kb_client
from kb import sqlite_reads
from kb.contract import kb_pb2


@pytest.fixture
def client(root):
    """Over a store holding the type for tags and three tags."""
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, TAG_TYPE)
    for title in ("First", "Second", "Third"):
        create(client, "tag", {"title": title})
    return client


def _asked(client):
    return client.Export(kb_pb2.ExportRequest())


def _open_in(root):
    """The files this process holds open under the store's place."""
    place, found = str(Path(root).resolve() / "kb"), []
    for descriptor in os.listdir("/proc/self/fd"):
        try:
            found.append(os.readlink(f"/proc/self/fd/{descriptor}"))
        except OSError:  # the descriptor the listing itself was read through
            continue
    return sorted(name for name in found if name.startswith(place))


def test_a_change_landing_while_an_export_is_read_slowly_is_not_in_it_and_the_position_is_the_one_before(root, client):
    before = export(client)
    stream = _asked(client)
    first = next(stream)
    changed = create(kb_client.connect(root), "tag", {"title": "Landed meanwhile"})
    read_slowly = answer([first, *stream])
    assert (read_slowly.files, read_slowly.position) == (before.files, before.position)
    after = export(client)
    assert filed(changed.id) in [place for place, _ in after.files]
    assert after.position == journal(client, artifact=changed.id).entries[-1].id != before.position


@pytest.mark.parametrize("stops", ["closes the stream", "lets the stream go"])
def test_a_client_that_stops_reading_partway_leaves_the_store_let_go(root, client, stops):
    stream = _asked(client)
    assert next(stream).result.WhichOneof("part") == "file"
    assert _open_in(root) != []  # the store is held while the stream is read
    if stops == "closes the stream":
        stream.close()
    del stream
    gc.collect()
    assert _open_in(root) == []
    create(client, "tag", {"title": "Landed at once"})
    with sqlite3.connect(Path(root) / "kb" / "store.sqlite3") as other:
        assert other.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()[0] == 0  # no reader holds the log
    other.close()
    assert not export(client).refused


def test_an_export_read_to_its_end_leaves_the_store_let_go(root, client):
    assert export(client).complete
    assert _open_in(root) == []


REFUSED = {
    "a damaged database": held.damage_the_database,
    "a later kb's store": held.made_by_a_later_kb,
    "an earlier kb's store": held.made_by_an_earlier_kb,
    "a marker that cannot be read": held.with_a_marker_that_cannot_be_read,
    "the database taken away": held.take_away_the_database,
}


@pytest.mark.parametrize("why", REFUSED)
def test_each_refusal_every_rpc_gives_is_the_streams_one_message(root, client, why):
    REFUSED[why](root)
    before = held.bytes_held(root)
    refused = export(client)
    assert [message.WhichOneof("outcome") for message in refused.messages] == ["refusal"]
    assert refused.faults and refused.faults == check(client).faults
    assert held.bytes_held(root) == before
    assert _open_in(root) == []


def test_no_store_found_is_the_streams_one_message(tmp_path):
    nowhere = tmp_path / "nowhere"
    nowhere.mkdir()
    client = kb_client.connect(nowhere)
    refused = export(client)
    assert [message.WhichOneof("outcome") for message in refused.messages] == ["refusal"]
    assert refused.faults and refused.faults == check(client).faults
    assert list(nowhere.iterdir()) == []


def test_a_failure_after_files_were_given_ends_the_stream_with_a_refusal_and_no_end(root, client, monkeypatch):
    def fails(self):
        raise sqlite3.DatabaseError("database disk image is malformed")
    monkeypatch.setattr(sqlite_reads.Reads, "landed_last", fails)
    cut_short = export(client)
    assert [message.WhichOneof("outcome") for message in cut_short.messages] == ["result"] * 5 + ["refusal"]
    assert len(cut_short.files) == 5 and not cut_short.complete
    assert [fault.rule for fault in cut_short.faults] == ["unreadable"]
    assert _open_in(root) == []


def test_a_store_restored_from_a_backup_gives_the_backed_up_stores_position(root, client, tmp_path):
    backed_up = export(client)
    backup = tmp_path / "store.backup"
    ran = _kb("backup", str(backup), cwd=root)
    assert (ran.returncode, ran.stderr) == (0, ""), ran.stderr
    create(client, "tag", {"title": "Made since the backup"})
    restored = tmp_path / "restored"
    restored.mkdir()
    ran = _kb("restore", str(backup), str(restored), cwd=tmp_path)
    assert (ran.returncode, ran.stderr) == (0, ""), ran.stderr
    given = export(kb_client.connect(restored))
    assert (given.position, given.files) == (backed_up.position, backed_up.files)
    assert export(client).position != backed_up.position
