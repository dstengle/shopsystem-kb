"""A store whose database cannot be read, damaged behind its back or missing beside its marker, refuses every call and
the operator's commands with one fault, writing nothing anywhere."""
import os
import re
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenario, then, when

from calls import DECISION_TYPE, PROCESS_TYPE, TAG_TYPE, create, define, request, start_a_store
from conftest import _kb
import held
import serving
from kb import client as kb_client
from kb.contract import kb_pb2

FEATURE = "answer-a-damaged-file.feature"


@scenario(
    FEATURE,
    "A store whose database cannot be read, because it is damaged or missing beside its marker, refuses every call "
    "and command that needs it",
)
def test_a_store_whose_database_cannot_be_read_refuses_every_call_and_command():
    pass


SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]


@given("a store holding a decision, a process and a tag, each of a kind the store holds a type for",
       target_fixture="client")
def _store_with_a_decision_a_process_and_a_tag(root):
    client = kb_client.connect(root)
    start_a_store(root)
    for type_content in (DECISION_TYPE, PROCESS_TYPE, TAG_TYPE):
        define(client, type_content)
    create(client, "decision", {"title": "Price reviews happen weekly", "sections": SECTIONS})
    create(client, "process", {"title": "Open the shop", "steps": [{"title": "Unlock"}, {"title": "Count the float"}]})
    create(client, "tag", {"title": "Pricing"})
    return client


DAMAGES = {
    "was damaged behind the store's back": held.damage_the_database,
    "is missing, while the store's marker is still there": held.take_away_the_database,
}


@given(parsers.re(f"the store's database (?P<damage>{'|'.join(map(re.escape, DAMAGES))})"))
def _database_damaged(root, damage):
    DAMAGES[damage](root)


READ_ONLY = {"lies in a directory that is read-only": "directory", "is a file that is read-only": "file"}


@given(parsers.re(f"the store's database (?P<what>{'|'.join(map(re.escape, READ_ONLY))})"))
def _database_read_only(root, request, what):
    assert os.geteuid() != 0, "the suite runs as root, so chmod would not make anything read-only"
    request.addfinalizer(held.make_read_only(root, READ_ONLY[what]))


@pytest.fixture
def where(root):
    """Where the operator works and what it is told: inside the store with nothing set, or, when a Given has set KB_ROOT
    to name the store, where the process works, told so."""
    if "KB_ROOT" in os.environ:
        return {"cwd": Path.cwd(), "env": {"KB_ROOT": os.environ["KB_ROOT"]}}
    return {"cwd": root, "env": {}}


@given("an empty directory outside the store", target_fixture="empty")
def _an_empty_directory(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    return empty


CREATES_A_DECISION = "creates a decision with a title and both required sections, saying which role and why"


def _answered(root, before, act):
    """What the store held before anything is done, byte for byte, then what doing it answers."""
    before.update(held=held.bytes_held(root))
    return act()


@when(f"the client {CREATES_A_DECISION}", target_fixture="answered")
def _the_client_creates_a_decision(client, root, before):
    return _answered(root, before, lambda: request(client, "decision", "Close early on Sundays", {"sections": SECTIONS}))


def _unreadable(rule, message):
    assert rule == "unreadable"
    assert "kb/store.sqlite3" in message


@then("what was asked is rejected because the store's database cannot be read, and the database is named")
def _rejected_as_unreadable(answered):
    if hasattr(answered, "faults"):
        [fault] = answered.faults
        assert (fault.artifact, fault.place) == ("", "")
        _unreadable(fault.rule, fault.message)
    else:
        [line] = answered.stderr.splitlines()
        _unreadable(*line.split(": ", 3)[2:4])


def _earlier(rule, message):
    assert rule == "unreadable"
    assert "made by an earlier version of kb" in message


@then("what was asked is rejected because the store was made by an earlier version of kb")
def _rejected_as_earlier(answered):
    if hasattr(answered, "faults"):
        [fault] = answered.faults
        assert (fault.artifact, fault.place) == ("", "")
        _earlier(fault.rule, fault.message)
    else:
        [line] = answered.stderr.splitlines()
        _earlier(*line.split(": ", 3)[2:4])


@then("the fault says to start a new store and import the old one's files")
def _says_how_to_move(answered):
    message = answered.faults[0].message if hasattr(answered, "faults") else answered.stderr
    assert "start a new store and import the old one's files" in message


@then("nothing is written in the store")
def _nothing_written_in_the_store(root, before):
    assert held.bytes_held(root) == before["held"]


@then("the fault is given as any other fault is given, never breaking off")
def _given_as_any_other_fault(answered):
    if hasattr(answered, "faults"):
        assert type(getattr(answered, "response", answered)).__module__ == kb_pb2.__name__
        assert answered.faults
    else:
        assert answered.returncode == 2
        assert re.fullmatch(r"kb (validate|export|import): refused: unreadable: .*\n", answered.stderr), answered.stderr


@then("nothing is written in the store, nor in the empty directory, which stays as it was")
def _nothing_written(root, before, empty):
    assert held.bytes_held(root) == before["held"]
    assert empty.is_dir() and held.holds_nothing(empty)


@when("the operator runs kb export in that store, aimed at the empty directory", target_fixture="answered")
def _kb_export(root, before, empty, where):
    return _answered(root, before, lambda: _kb("export", str(empty), **where))


@given(
    "a store holding a decision, a process and a tag, made by an earlier kb in a form this kb cannot read",
    target_fixture="client",
)
def _store_made_by_an_earlier_kb(root):
    client = _store_with_a_decision_a_process_and_a_tag(root)
    held.made_by_an_earlier_kb(root)
    return client


@given(parsers.re("the store is found (?P<how>upward from the working directory|through KB_ROOT naming it)"),
       target_fixture="client")
def _store_found(root, tmp_path, monkeypatch, how):
    """The client readied with no root, so it finds the store as a call is made; the operator told the same way."""
    if how.startswith("upward"):
        monkeypatch.chdir(root)
    else:
        outside = tmp_path / "outside"
        outside.mkdir()
        monkeypatch.chdir(outside)
        monkeypatch.setenv("KB_ROOT", str(root))
    return kb_client.connect()


@scenario(
    FEATURE,
    'A store whose database cannot be opened for writing, because the directory, the file or the mount it is on is read-only, refuses every call and command that needs it',
)
def test_a_store_whose_database_cannot_be_opened_for_writing_because_the_direct():
    pass


@scenario(
    FEATURE,
    'A store found that was made by an earlier kb, in a form this kb cannot read, refuses every call and command that needs it',
)
def test_a_store_found_that_was_made_by_an_earlier_kb_in_a_form_this_kb_cannot():
    pass


@scenario(
    FEATURE,
    "A store found whose marker names a form of store this kb does not know, one a later kb made, refuses every call "
    "and command that needs it",
)
def test_a_store_found_whose_marker_names_a_form_a_later_kb_made_refuses_every_call():
    pass


@given(
    "a store holding a decision, a process and a tag, whose marker names a form of store this kb does not know, one a "
    "later kb made",
    target_fixture="client",
)
def _store_made_by_a_later_kb(root):
    client = _store_with_a_decision_a_process_and_a_tag(root)
    held.made_by_a_later_kb(root)
    return client


def _later(rule, message):
    assert rule == "unreadable"
    assert "made by a later version of kb, which is needed to read it" in message


@then("what was asked is rejected because the store was made by a later version of kb, which is needed to read it")
def _rejected_as_later(answered):
    if hasattr(answered, "faults"):
        [fault] = answered.faults
        assert (fault.artifact, fault.place) == ("", "")
        _later(fault.rule, fault.message)
    else:
        [line] = answered.stderr.splitlines()
        _later(*line.split(": ", 3)[2:4])


@then("the store is not opened")
def _not_opened(root, before):
    assert sorted(held.bytes_held(root)) == sorted(before["held"])


@scenario(
    FEATURE,
    "A store found whose marker cannot be read at all refuses every call and command that needs it, as for a later "
    "kb's store",
)
def test_a_store_found_whose_marker_cannot_be_read_at_all_refuses_every_call():
    pass


@given("a store holding a decision, a process and a tag, whose marker cannot be read at all", target_fixture="client")
def _store_whose_marker_cannot_be_read(root):
    client = _store_with_a_decision_a_process_and_a_tag(root)
    held.with_a_marker_that_cannot_be_read(root)
    return client


@scenario(FEATURE, "The operator runs kb serve on a store whose database cannot be read")
def test_the_operator_runs_kb_serve_on_a_store_whose_database_cannot_be_read():
    pass


@when("the operator runs kb serve on that directory, giving an address", target_fixture="answered")
def _kb_serve_giving_an_address(root):
    return _kb("serve", str(root), "--listen", serving.closed_port(), cwd=root)


@then("serving the store is rejected because the store's database cannot be read, and the database is named")
def _serving_rejected_as_unreadable(answered):
    assert (answered.returncode, answered.stdout) == (2, "")
    [line] = answered.stderr.splitlines()
    assert line.startswith("kb serve: refused: ")
    _unreadable(*line.split(": ", 3)[2:4])
