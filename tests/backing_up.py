"""The steps of operate-a-store that back a store up and restore a backup, bound by test_look_after_a_store.py.

What a backup holds is read only through the contract: the backup restored by the operator's `kb restore` in a
directory of its own, and that store read as a client reads any store."""
import contextlib
import sqlite3
import threading

import pytest
from pytest_bdd import given, parsers, then, when

import at_once
import serving
from calls import (DECISION_TYPE, a_decision_type_and_a_decision, answer, create, created, creating, define,
                   journal, listing, read, replace, signature, snapshot, start_a_store)
from conftest import _kb
from kb import client as kb_client
from kb import sqlite_search, store
from kb.contract import kb_pb2

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
@when("the operator restores that file in that directory", target_fixture="ran")
def _restores(backup, root, tmp_path, restored):
    """kb restore, run outside the directory with no KB_ACTOR set."""
    restored.update({"place": root, "from": backup.get("store")})
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


# A backup made while the store is written to.

LANDING = ("decision/stock-is-counted-weekly", "decision/stock-is-counted-monthly", "decision/stock-is-counted-yearly")


@given("a store holding a type for decisions")
def _a_store_with_the_decision_type(root):
    start_a_store(root)
    define(kb_client.connect(root), DECISION_TYPE)


@given("a store holding a type for decisions and a decision")
def _a_store_with_a_decision(root):
    start_a_store(root)
    a_decision_type_and_a_decision(kb_client.connect(root))


class MidLanding:
    """A set landing on a thread of its own, held inside its landing transaction once the first of its artifacts is
    written, the store's write lock held and the rest of the set not yet written, until it is let go."""

    def __init__(self, root, request, monkeypatch):
        self._written, self._go = threading.Event(), threading.Event()
        searchable = sqlite_search.searchable

        def written_then_held(db, name, kind, rows):
            searchable(db, name, kind, rows)
            if name in LANDING and not self._written.is_set():
                self._written.set()
                assert self._go.wait(at_once.PATIENCE), "the landing set was never let go"

        monkeypatch.setattr(sqlite_search, "searchable", written_then_held)
        self._answers = []
        self._thread = threading.Thread(target=lambda: self._answers.append(answer(
            kb_client.connect(root).BatchCreate(request))), daemon=True)

    def hold(self):
        self._thread.start()
        assert self._written.wait(at_once.PATIENCE), "the set never began to land"

    def let_go(self):
        """The set let go to finish landing, once it is held or whatever became of it."""
        self._go.set()

    def release(self):
        """The set let go to finish landing; its answer."""
        self.let_go()
        self._thread.join(at_once.PATIENCE)
        assert not self._thread.is_alive(), "the set never finished landing"
        [landed] = self._answers
        return landed


@given("a client is landing a set that makes three decisions", target_fixture="landing")
def _landing_three_decisions(root, request, monkeypatch):
    """A set of three creates, held inside its landing once the first of them is written."""
    items = [created("decision", f"Stock is counted {every}", _sections(f"Stock moves {every}.\n"))
             for every in ("weekly", "monthly", "yearly")]
    landing = MidLanding(root, kb_pb2.BatchCreateRequest(items=items, signature=signature("Count stock")), monkeypatch)
    request.addfinalizer(landing.let_go)
    landing.hold()
    return landing


@when("the operator backs up the store while that set is landing", target_fixture="backup")
def _backs_up_while_landing(root, tmp_path, landing):
    """The store backed up while the set is held part written; then the set let go to finish landing."""
    backup = _backed_up(root, tmp_path)
    landed = landing.release()
    assert not landed.refused, landed.faults
    return backup


@then("the backup holds either all three decisions of that set, with their history and journal entries, or none of "
      "them")
def _all_or_none(backup, root, tmp_path_factory):
    place = tmp_path_factory.mktemp("restored")
    ran = _kb("restore", str(backup["file"]), str(place), cwd=place)
    assert (ran.returncode, ran.stderr) == (0, ""), ran.stderr
    landed, entries = everything(root), the_journal(root)
    assert set(LANDING) <= set(landed)
    if set(LANDING) <= set(everything(place)):
        assert (everything(place), the_journal(place)) == (landed, entries)
        assert _histories(place, LANDING) == _histories(root, LANDING)
    else:
        before = {name: content for name, content in landed.items() if name not in LANDING}
        assert everything(place) == before
        assert the_journal(place) == [entry for entry in entries if entry.artifact not in LANDING]


def _histories(root, names):
    client = kb_client.connect(root)
    return {name: journal(client, artifact=name).response for name in names}


class Writers:
    """Clients in this program, each writing decisions on a thread of its own, one after another, until stopped;
    every answer each was given kept, and a signal each time one is answered."""

    def __init__(self, root, count):
        self._root, self._stopping, self._answered = root, threading.Event(), threading.Condition()
        self.answers = [[] for _ in range(count)]
        self._threads = [threading.Thread(target=self._write, args=(writer,), daemon=True) for writer in range(count)]
        for thread in self._threads:
            thread.start()

    def _write(self, writer):
        client = kb_client.connect(self._root)
        while not self._stopping.is_set():
            written = len(self.answers[writer])
            answered = answer(client.Create(creating("decision", f"Writer {writer} decides {written}",
                                                     _sections(f"Writer {writer} wrote it.\n"), "Write a decision")))
            with self._answered:
                self.answers[writer].append(answered)
                self._answered.notify_all()

    def counts(self):
        with self._answered:
            return [len(answers) for answers in self.answers]

    def each_answered_beyond(self, counts):
        """Waits until every writer has been answered more often than the counts given."""
        with self._answered:
            assert self._answered.wait_for(
                lambda: all(len(answers) > count for answers, count in zip(self.answers, counts)), at_once.PATIENCE,
            ), f"the writers stopped writing: {self.counts()} answers, {counts} before"

    def stop(self):
        self._stopping.set()
        for thread in self._threads:
            thread.join(at_once.PATIENCE)
        assert not any(thread.is_alive() for thread in self._threads), "a writer never finished"


@given("clients are writing decisions to the store", target_fixture="writers")
def _clients_writing(root, request):
    """Three clients writing, each answered at least once before the step ends; stopped when the test ends."""
    writers = Writers(root, 3)
    request.addfinalizer(writers.stop)
    writers.each_answered_beyond([0, 0, 0])
    return writers


@then("the backup is made")
def _backup_made(backup):
    assert (backup["ran"].returncode, backup["ran"].stderr) == (0, ""), backup["ran"].stderr
    assert backup["file"].is_file()


@then("the clients go on writing")
def _clients_go_on(writers):
    """Each writer is answered again after the backup was made."""
    writers.each_answered_beyond(writers.counts())


@then("none of their changes is refused because of the backup")
def _none_refused(writers):
    writers.stop()
    refused = [answer.faults for answers in writers.answers for answer in answers if answer.refused]
    assert refused == []


@then("the backup is not refused because the store was busy with another change")
def _backup_not_busy(backup):
    assert "busy" not in backup["ran"].stderr
    assert backup["ran"].returncode == 0, backup["ran"].stderr


@given("a server serves that store", target_fixture="address")
def _a_server_serves_it(root, request):
    """`kb serve` run on the store; the address it serves at."""
    return serving.serving(root, request)


@then("the server goes on serving: a caller reaching it is answered from that store")
def _server_goes_on(root, address):
    serving.answered_at(root, address)


# A restore refuses what it cannot make a store of, and makes nothing.

@given("a backup of a store", target_fixture="backup")
def _a_backup_of_a_store(tmp_path):
    backed_up = tmp_path / "backed-up"
    backed_up.mkdir()
    start_a_store(backed_up)
    define(kb_client.connect(backed_up), DECISION_TYPE)
    return _backed_up(backed_up, tmp_path)


@given("a file that is not a backup kb made", target_fixture="backup")
def _a_file_that_is_not_a_backup(tmp_path):
    file = tmp_path / "notes.backup"
    file.write_text("Prices are reviewed monthly.\n")
    return {"file": file}


def _made_by(tmp_path, form):
    """A backup of a store, its header saying the store was of the form given."""
    backup = _a_backup_of_a_store(tmp_path)
    with contextlib.closing(sqlite3.connect(backup["file"])) as copy:
        copy.execute(f"PRAGMA user_version = {form}")
    return backup


@given("a backup made by an earlier kb", target_fixture="backup")
def _a_backup_made_by_an_earlier_kb(tmp_path):
    return _made_by(tmp_path, store.STORE_FORM - 1)


@given("a backup made by a later kb", target_fixture="backup")
def _a_backup_made_by_a_later_kb(tmp_path):
    return _made_by(tmp_path, store.STORE_FORM + 1)


def _refused_restore(ran, rule, message):
    assert (ran.returncode, ran.stdout) == (2, "")
    [line] = ran.stderr.splitlines()
    assert line.startswith(f"kb restore: refused: {rule}: "), line
    assert message in line, line


@then("restoring is rejected because that directory already has a store inside it")
def _restore_rejected_as_already_a_store(ran, root):
    _refused_restore(ran, "root", f"a store is never restored over another; {str(root)!r} already has a store inside it")


@then("restoring is rejected because that directory is inside a store")
def _restore_rejected_as_inside_a_store(ran, root, before):
    _refused_restore(ran, "root", f"stores do not nest; {str(root)!r} is inside the store at {str(before['store'])!r}")


@then("restoring is rejected because a store can only be restored in a directory kb can write, and the directory is "
      "named")
def _restore_rejected_as_not_writable(ran, root):
    _refused_restore(ran, "root", f"a store is restored in a directory kb can write, and {str(root)!r} is not one")


@then("restoring is rejected because it is not a backup")
def _restore_rejected_as_not_a_backup(ran, backup):
    _refused_restore(ran, "unreadable", f"{str(backup['file'])!r} is not a backup kb made")


@then("restoring is rejected because this kb cannot read a store an earlier kb made")
def _restore_rejected_as_earlier(ran, backup):
    _refused_restore(ran, "unreadable", f"{str(backup['file'])!r} was made by an earlier kb, which this kb cannot read")


@then("restoring is rejected because a later version of kb is needed to read it")
def _restore_rejected_as_later(ran, backup):
    _refused_restore(ran, "unreadable",
                     f"{str(backup['file'])!r} was made by a later version of kb, which is needed to read it")


# A restore stopped before it finished.

@given("a backup of a store holding a type for decisions and a decision", target_fixture="backup")
def _a_backup_of_a_decision(tmp_path):
    backed_up = tmp_path / "backed-up"
    backed_up.mkdir()
    start_a_store(backed_up)
    a_decision_type_and_a_decision(kb_client.connect(backed_up))
    return _backed_up(backed_up, tmp_path)


@then("it holds everything the store backed up held, its history and its journal included")
def _holds_everything_with_history_and_journal(restored):
    held = everything(restored["from"])
    assert {"schema/decision", "decision/price-reviews-happen-weekly"} <= set(held)
    assert everything(restored["place"]) == held
    assert the_journal(restored["place"]) == the_journal(restored["from"])


# A backup refuses where it cannot be made.

PLACES = {
    "a file holding something": lambda place: place.write_text("Prices are reviewed monthly.\n"),
    "an empty file": lambda place: place.touch(),
    "an empty directory": lambda place: place.mkdir(),
    "a directory holding something": lambda place: (place.mkdir(), (place / "notes.txt").write_text("Weekly.\n")),
}


@given(parsers.re(f"(?P<what>{'|'.join(PLACES)}) at the place the backup would be written"), target_fixture="place")
def _something_at_the_place(what, tmp_path):
    place = tmp_path / "store.backup"
    PLACES[what](place)
    return {"file": place, "before": _everything_at(place)}


def _everything_at(place):
    """What stands at the place, each path with its bytes (a directory's with none)."""
    return {path.relative_to(place.parent): path.read_bytes() if path.is_file() else None
            for path in [place, *sorted(place.rglob("*"))]}


@when("the operator backs up the store to that place", target_fixture="ran")
def _backs_up_to(root, place):
    return _kb("backup", str(place["file"]), cwd=root)


@then("the backup is rejected because a backup never overwrites")
def _backup_rejected_as_overwriting(ran, place):
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr == f"kb backup: refused: root: a backup never overwrites; {str(place['file'])!r} already holds something\n"


@then("what is at that place is left as it was")
def _left_as_it_was(place):
    assert _everything_at(place["file"]) == place["before"]


# kb backup finds the store as kb validate does.

from conftest import (_inside_one_naming_another, _outside_with_kb_root, _outside_with_kb_root_naming_no_store,  # noqa: E402
                      _store_needing_attention, _working_deep_inside)
import held  # noqa: E402


@given("a folder deep inside the directory a store sits in", target_fixture="where")
def _a_folder_deep_inside(root):
    return _working_deep_inside(root)


@given("outside any store, with KB_ROOT naming a store", target_fixture="where")
def _outside_naming_a_store(root, tmp_path):
    return _outside_with_kb_root(root, tmp_path)


@given("outside any store, with nothing naming one", target_fixture="where")
def _outside_naming_nothing(tmp_path):
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    return {"cwd": outside, "env": {}}


@given("outside any store, with KB_ROOT naming a directory that holds no store", target_fixture="where")
def _outside_naming_no_store(tmp_path):
    return _outside_with_kb_root_naming_no_store(tmp_path)


@given("inside one store, with KB_ROOT naming a different store", target_fixture="where")
def _inside_naming_another(root, tmp_path):
    return _inside_one_naming_another(root, tmp_path)


def _inside_a_store(root, damage):
    _store_needing_attention(root)
    damage(root)
    return {"cwd": root, "env": {}}


@given("inside a store made by an earlier kb", target_fixture="where")
def _inside_an_earlier_kbs_store(root):
    return _inside_a_store(root, held.made_by_an_earlier_kb)


@given("inside a store made by a later kb", target_fixture="where")
def _inside_a_later_kbs_store(root):
    return _inside_a_store(root, held.made_by_a_later_kb)


@given("inside a store whose database cannot be read", target_fixture="where")
def _inside_an_unreadable_store(root):
    return _inside_a_store(root, held.damage_the_database)


@when("the operator runs kb backup there", target_fixture="ran")
def _kb_backup_there(where, tmp_path):
    """kb backup run where the operator works, the backup to be written beside the directory it is run from."""
    file = tmp_path / "there.backup"
    return {"file": file, "where": where, "ran": _kb("backup", str(file), cwd=where["cwd"], env=where["env"])}


@then("the store kb validate would check there is the one backed up")
def _the_store_validate_checks_is_backed_up(ran, tmp_path_factory):
    """The backup restored in a directory of its own holds what kb validate, run there, checks."""
    assert (ran["ran"].returncode, ran["ran"].stderr) == (0, ""), ran["ran"].stderr
    where = ran["where"]
    checked = _kb("validate", cwd=where["cwd"], env=where["env"])
    place = tmp_path_factory.mktemp("restored")
    restored = _kb("restore", str(ran["file"]), str(place), cwd=place)
    assert (restored.returncode, restored.stderr) == (0, ""), restored.stderr
    again = _kb("validate", cwd=place)
    assert (again.returncode, again.stdout, again.stderr) == (checked.returncode, checked.stdout, checked.stderr)
    assert checked.returncode == 1 and checked.stdout.startswith("violation\t")


@then("the backup is rejected for the same reason kb validate, run there, is rejected")
def _rejected_as_validate_is(ran):
    where, backed_up = ran["where"], ran["ran"]
    checked = _kb("validate", cwd=where["cwd"], env=where["env"])
    assert (backed_up.returncode, backed_up.stdout) == (2, "")
    assert (checked.returncode, checked.stdout) == (2, "")
    assert backed_up.stderr.replace("kb backup:", "kb validate:", 1) == checked.stderr
    assert not ran["file"].exists()


# A backup is made where the store's files are, not through a server.

@given("the operator is working in a directory holding a connection to a server and no store",
       target_fixture="where")
def _working_beside_a_connection(root):
    root.mkdir(exist_ok=True)
    return {"cwd": root, "env": {}}


@given("that server serves a store")
def _that_server_serves_a_store(where, tmp_path, request):
    """A store of its own served by `kb serve`; the connection in the directory the operator works in names it."""
    served = tmp_path / "served"
    served.mkdir()
    start_a_store(served)
    where["address"] = serving.serving(served, request)
    serving.connection(where["cwd"], where["address"])


@then("the backup is rejected because a backup is made where the store's files are, not through a server")
def _rejected_as_a_connection(ran):
    backed_up, where = ran["ran"], ran["where"]
    assert (backed_up.returncode, backed_up.stdout) == (2, "")
    assert backed_up.stderr == (
        "kb backup: refused: store: these commands run where the store is, not through a server: "
        f"{where['cwd']} holds the connection to the server at {where['address']}\n")
    assert not ran["file"].exists()
