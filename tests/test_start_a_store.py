from datetime import datetime
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenario, scenarios, then, when

from calls import DECISION_TYPE, check, define, journal, moment, read, start_a_store, starting
import held
from kb import client as kb_client

scenarios("start-a-store.feature")


@scenario("keep-the-history.feature", "Starting a store and the first change after it keep separate entries at the same moment")
def test_starting_a_store_and_the_first_change_after_it_keep_separate_entries_at_the_same_moment():
    pass


@given("an empty directory", target_fixture="root")
def _empty_directory(tmp_path):
    root = tmp_path / "store"
    root.mkdir()
    return root


@pytest.fixture
def client(root):
    """A client over the store at root, for the steps that go on to use the store a scenario started."""
    return kb_client.connect(root)


@then(parsers.parse("the store's one history entry says it happened at {reading}"))
def _one_entry_at(client, reading):
    response = journal(client)
    assert not response.faults, response.faults
    assert [datetime.fromisoformat(entry.at) for entry in response.entries] == [moment(reading)]


@when("the client starts a store there, saying which role it is", target_fixture="started")
def _start_a_store(root, readied_clock):
    """Started through `kb.init`, with the clock the client was readied with, if it was."""
    return starting(root, clock=readied_clock.get("clock"))


@then("the store holds the one type that describes what a type is")
def _holds_the_metaschema(client):
    schema = read(client, "schema/schema")
    assert schema.id == "schema/schema"
    assert schema.kind == "schema"


@then("the store holds no other type and no content")
def _holds_nothing_else(root):
    assert held.names(root) == ["schema/schema"]


@then("the client can define its own types straight away")
def _can_define_a_type(client):
    defined = define(client, {
        "title": "Note",
        "version": 1,
        "schema": {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]},
    })
    assert defined.id == "schema/note"
    assert defined.revision == 1


@then(
    "that entry is the writing of the one type that describes what a type is, at its first version, "
    "with a fingerprint of what was written"
)
def _the_entry_is_the_metaschema_write(root, entry):
    assert (entry.op, entry.artifact, entry.place, entry.revision) == ("create", "schema/schema", "", 1)
    assert entry.digest == held.fingerprint(root, "schema/schema")


@when("the client starts a store there without saying which role it is", target_fixture="refused")
def _start_a_store_without_a_role(root):
    return starting(root, role="")


@then("starting the store is rejected because a store can only be started under a role")
def _rejected_without_a_role(refused):
    assert [(fault.rule, fault.message) for fault in refused.faults] == [
        ("actor", "a store can only be started under a role"),
    ]


@then("that directory holds no store")
def _no_store_there(root):
    """Nothing at all is made in the directory, which was empty."""
    assert held.holds_nothing(root)


@given("the client is working inside a store", target_fixture="working_in")
def _working_inside_a_store(tmp_path, monkeypatch):
    working_in = tmp_path / "shop"
    working_in.mkdir()
    start_a_store(working_in)
    monkeypatch.chdir(working_in)
    monkeypatch.delenv("KB_ROOT", raising=False)
    return {"root": working_in, "held": held.everything_in(working_in)}


@given("an empty directory elsewhere that sits inside no store", target_fixture="root")
def _empty_directory_elsewhere(tmp_path):
    root = tmp_path / "elsewhere"
    root.mkdir()
    return root


@pytest.fixture
def readied():
    """The client that starts a store elsewhere, readied as the step starting it is taken, unless a step readied it
    before."""
    return kb_client.connect()


@when("the client starts a store in that empty directory, saying which role it is", target_fixture="started")
def _start_a_store_in_the_named_directory(root):
    return starting(root)


@then("the store is made in the directory the client named")
def _made_where_named(started, root):
    assert not started.faults, started.faults
    assert held.holds_a_store(root)
    assert "schema/schema" in held.names(root)


@then("the store the client was working in is left as it was")
def _working_store_unchanged(working_in):
    assert held.everything_in(working_in["root"]) == working_in["held"]


@given("the client has nothing at all to name as the directory to start a store in", target_fixture="here")
def _nothing_to_name(tmp_path, monkeypatch):
    """The client works in an empty directory, so a store made where it works, for want of a name, would show."""
    here = tmp_path / "here"
    here.mkdir()
    monkeypatch.chdir(here)
    monkeypatch.delenv("KB_ROOT", raising=False)
    return {"before": held.everything_in(tmp_path)}


@when("the client starts a store naming nothing, saying which role it is", target_fixture="started")
def _start_a_store_naming_nothing():
    return starting("")


@then("starting the store is rejected because a store is started in a directory that was named and that exists")
def _rejected_as_named_nothing(started):
    assert [(fault.rule, fault.message) for fault in started.faults] == [
        ("root", "a store is started in a directory that was named and that exists; no directory was named"),
    ]


@then("no store is made anywhere")
def _no_store_anywhere(here, tmp_path):
    assert held.everything_in(tmp_path) == here["before"]


@given("a place on the disk where no directory exists", target_fixture="root")
def _a_place_with_no_directory(tmp_path):
    return tmp_path / "nowhere" / "store"


@then("starting the store is rejected because a store is started in a directory that exists")
def _rejected_as_not_there(started, root):
    assert [(fault.rule, fault.message) for fault in started.faults] == [
        ("root", f"a store is started in a directory that exists; {str(root)!r} does not"),
    ]


@then("nothing is made at that place")
def _nothing_made_there(root):
    assert not root.parent.exists()


FILE_TEXT = b"notes the store must not write through\n"


@given("a place on the disk holding a file rather than a directory", target_fixture="root")
def _a_place_holding_a_file(tmp_path):
    root = tmp_path / "store"
    root.write_bytes(FILE_TEXT)
    return root


@then("starting the store is rejected because a store is started in a directory, and what was named is not one")
def _rejected_as_not_a_directory(started, root):
    assert [(fault.rule, fault.message) for fault in started.faults] == [
        ("root", f"a store is started in a directory, and {str(root)!r} is not one"),
    ]


@then("that file is left as it was")
def _file_left_as_it_was(root):
    assert root.read_bytes() == FILE_TEXT


UNRELATED = {"README.md": b"# The shop\n", "src/till.py": b"print('open')\n"}


@given("a directory holding files that have nothing to do with a store", target_fixture="root")
def _directory_holding_other_files(root):
    for name, data in UNRELATED.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_bytes(data)
    return root


@then("the store is made inside that directory, in a place of its own")
def _made_in_a_place_of_its_own(started, root):
    assert not started.faults, started.faults
    assert held.holds_a_store(root)
    assert set(held.apart_from_the_store(root)) == {Path("README.md"), Path("src"), Path("src/till.py")}


@then("the files that were already there are left as they were, and none of them is the store's concern")
def _other_files_left_alone(client, root):
    apart = held.apart_from_the_store(root)
    for name, data in UNRELATED.items():
        assert apart[Path(name)] == data
    assert held.names(root) == ["schema/schema"]
    checked = check(client)
    assert (checked.faults, list(checked.violations), list(checked.stale)) == ([], [], [])


@then("starting the store is rejected because that directory already has a store inside it")
def _rejected_as_already_a_store(started, root):
    assert [(fault.rule, fault.message) for fault in started.faults] == [
        ("root", f"a store is never started over another; {str(root)!r} already has a store inside it"),
    ]


@given("a directory that already has a store inside it, made by an earlier kb", target_fixture="root")
def _directory_with_an_earlier_kbs_store(root, before):
    held.made_by_an_earlier_kb(root)
    before.update(held=held.bytes_held(root))
    return root


@given("a directory that already has a store inside it, made by a later kb", target_fixture="root")
def _directory_with_a_later_kbs_store(root, before):
    start_a_store(root)
    held.made_by_a_later_kb(root)
    before.update(held=held.bytes_held(root))
    return root


@then("the store that is there is left as it was")
def _earlier_store_left_as_it_was(root, before):
    assert held.bytes_held(root) == before["held"]


@then("starting the store is rejected because that directory is inside a store")
def _rejected_as_inside_a_store(started, root, before):
    assert [(fault.rule, fault.message) for fault in started.faults] == [
        ("root", f"stores do not nest; {str(root)!r} is inside the store at {str(before['store'])!r}"),
    ]


CORNERS = {
    "an empty folder where a store would go": "folder",
    "a file where a store would go": "file",
}


@given(parsers.re(f"a directory holding (?P<what>{'|'.join(CORNERS)})"), target_fixture="before")
def _a_directory_holding(root, what):
    held.occupy_the_place(root, CORNERS[what])
    return held.everything_in(root)


@then("starting the store is rejected because that directory already holds the place a store goes")
def _rejected_as_the_place_taken(started, root):
    assert [(fault.rule, fault.message) for fault in started.faults] == [
        ("root", f"a store goes in a place of its own, and {str(root)!r} already holds something in that place"),
    ]


@then("what was there is left as it was")
def _left_as_it_was(root, before):
    assert held.everything_in(root) == before


@given(
    "the client was readied to call a store while working where there was none and nothing named one",
    target_fixture="readied",
)
def _readied_where_there_was_none(tmp_path, monkeypatch):
    nowhere = tmp_path / "nowhere"
    nowhere.mkdir()
    monkeypatch.chdir(nowhere)
    monkeypatch.delenv("KB_ROOT", raising=False)
    return kb_client.connect()


@then("the client can read and write in it straight away")
def _reads_and_writes_there(readied, root, monkeypatch):
    monkeypatch.chdir(root)
    assert read(readied, "schema/schema").id == "schema/schema"
    defined = define(readied, DECISION_TYPE)
    assert not defined.faults, defined.faults
    assert read(readied, "schema/decision").revision == 1


def test_a_relative_root_from_a_removed_working_directory_is_refused_not_raised(tmp_path, monkeypatch):
    """slice 100.5: `store.vacant`'s `root.path.resolve()` used to let a `FileNotFoundError` escape once the
    working directory a relative root reads against was itself removed."""
    working_in = tmp_path / "gone"
    working_in.mkdir()
    monkeypatch.chdir(working_in)
    working_in.rmdir()

    started = starting(".")

    assert [(fault.rule, fault.message) for fault in started.faults] == [
        ("root", "a store is started in a directory that exists; whether '.' does depends on the working "
                 "directory, and it is gone"),
    ]


def test_a_relative_root_that_is_simply_missing_is_still_refused_as_before(tmp_path, monkeypatch):
    """The fix above must not change the ordinary refusal for a relative root that just is not there."""
    monkeypatch.chdir(tmp_path)

    started = starting("sub")

    assert [(fault.rule, fault.message) for fault in started.faults] == [
        ("root", "a store is started in a directory that exists; 'sub' does not"),
    ]


@given(parsers.parse("a store the client started, readied with a clock that reads {reading}"),
       target_fixture="client")
def _started_with_a_clock(root, reading):
    stood = moment(reading)
    start_a_store(root, lambda: stood)
    return kb_client.connect(root, clock=lambda: stood)


@when("the client defines its own type")
def _defines_its_own_type(client):
    defined = define(client, DECISION_TYPE)
    assert not defined.faults, defined.faults


@then(parsers.parse("the store's history holds two entries, both saying they happened at {reading}"))
def _two_entries_at(client, reading):
    assert [datetime.fromisoformat(entry.at) for entry in journal(client).entries] == [moment(reading)] * 2


@then("each names itself as its own set")
def _each_its_own_set(client):
    entries = journal(client).entries
    assert [entry.batch for entry in entries] == [entry.id for entry in entries]
    assert len({entry.batch for entry in entries}) == len(entries)
