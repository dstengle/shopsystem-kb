"""The steps of operate-a-store that back a store up and restore a backup, bound by test_look_after_a_store.py.

What a backup holds is read only through the contract: the backup restored by the operator's `kb restore` in a
directory of its own, and that store read as a client reads any store."""
import pytest
from pytest_bdd import given, then, when

from calls import DECISION_TYPE, create, define, journal, listing, read, replace, snapshot, start_a_store
from conftest import _kb
from kb import client as kb_client

DECISIONS = ("decision/price-reviews-happen-weekly", "decision/prices-are-reviewed-monthly")


def _sections(rationale):
    return {"sections": [
        {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
        {"title": "Rationale", "body": rationale},
    ]}


@given("a store holding a type for decisions and two decisions, one of them replaced since it was made",
       target_fixture="root")
def _a_store_with_a_replaced_decision(root):
    """The decision type, two decisions, and the first of them replaced: its rationale rewritten."""
    start_a_store(root)
    client = kb_client.connect(root)
    define(client, DECISION_TYPE)
    create(client, "decision", {"title": "Price reviews happen weekly", **_sections("Costs move weekly.\n")})
    create(client, "decision", {"title": "Prices are reviewed monthly", **_sections("Costs settle monthly.\n")})
    replaced = replace(client, DECISIONS[0], _sections("Suppliers reprice weekly.\n"))
    assert not replaced.refused, replaced.faults
    return root


@given("a piece of work has snapshotted what it read")
def _snapshotted(root):
    taken = snapshot(kb_client.connect(root), "restock-2026-10", list(DECISIONS))
    assert not taken.refused, taken.faults


@when("the operator backs up the store", target_fixture="backup")
def _backs_up(root, tmp_path):
    """kb backup run in the store, the backup written beside the directory the store sits in."""
    file = tmp_path / "store.backup"
    return {"file": file, "ran": _kb("backup", str(file), cwd=root)}


@given("a backup of a store holding a type for decisions and two decisions, one of them replaced since it was made, "
       "and a snapshot of what a piece of work read", target_fixture="backup")
def _a_backup_of_a_replaced_decision_and_a_snapshot(tmp_path):
    backed_up = tmp_path / "backed-up"
    backed_up.mkdir()
    _a_store_with_a_replaced_decision(backed_up)
    _snapshotted(backed_up)
    return _backed_up(backed_up, tmp_path)


def _backed_up(store, tmp_path):
    """The store backed up by the operator, and the backup made: its file, and the store it is of."""
    backup = {**_backs_up(store, tmp_path), "store": store}
    assert (backup["ran"].returncode, backup["ran"].stderr) == (0, ""), backup["ran"].stderr
    return backup


@pytest.fixture
def restored():
    """A store restored from a backup, under `place`, and the store backed up, under `from`, once a step has restored
    one."""
    return {}


@when("the operator restores that backup in that directory", target_fixture="ran")
def _restores(backup, root, tmp_path, restored):
    """kb restore, run outside the directory with no KB_ACTOR set."""
    restored.update({"place": root, "from": backup["store"]})
    return _kb("restore", str(backup["file"]), str(root), cwd=tmp_path)


def everything(root):
    """Every artifact the store holds, by name, read whole as the contract gives it."""
    client = kb_client.connect(root)
    kinds = {"schema", *(name.split("/", 1)[1] for name in listing(client, "schema", ids_only=True).ids)}
    return {name: read(client, name, whole=True).response
            for kind in sorted(kinds) for name in listing(client, kind, ids_only=True).ids}


def histories(root):
    """The history of each decision, as the contract gives it."""
    client = kb_client.connect(root)
    return {name: journal(client, artifact=name).response for name in DECISIONS}


def the_journal(root):
    """Every entry of the store's journal, as the contract gives it."""
    return list(journal(kb_client.connect(root)).entries)


@then("the backup holds everything the store holds")
def _backup_holds_everything(backup, root, tmp_path_factory, restored):
    """The backup restored by the operator in a directory of its own, and that store read."""
    assert (backup["ran"].returncode, backup["ran"].stderr) == (0, ""), backup["ran"].stderr
    place = tmp_path_factory.mktemp("restored")
    ran = _kb("restore", str(backup["file"]), str(place), cwd=place)
    assert (ran.returncode, ran.stderr) == (0, ""), ran.stderr
    restored.update({"place": place, "from": root})
    _holds_everything(restored)


@then("it holds everything the store backed up held")
def _holds_everything(restored):
    held = everything(restored["from"])
    assert set(held) >= {"schema/decision", *DECISIONS}
    assert everything(restored["place"]) == held


@then("it holds the history of each decision")
def _holds_each_history(restored):
    assert histories(restored["place"]) == histories(restored["from"])


@then("it holds every entry of the store's journal, the snapshot included")
@then("it holds every entry of the backed-up store's journal, the snapshot included")
def _holds_the_journal(restored):
    entries = the_journal(restored["from"])
    assert "snapshot" in [entry.op for entry in entries]
    assert the_journal(restored["place"]) == entries


@given("a backup of a store whose last entry is the replacing of a decision", target_fixture="backup")
def _a_backup_ending_with_a_replace(tmp_path):
    backed_up = tmp_path / "backed-up"
    backed_up.mkdir()
    _a_store_with_a_replaced_decision(backed_up)
    return _backed_up(backed_up, tmp_path)


@then("the restored store's history ends with the replacing of that decision")
def _history_ends_with_the_replace(restored):
    last = the_journal(restored["from"])[-1]
    assert (last.op, last.artifact, last.revision) == ("write", DECISIONS[0], 2), last
    assert the_journal(restored["place"])[-1] == last
