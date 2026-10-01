"""Suite wiring. Step definitions live beside the scenarios they serve; shared Givens are added here by slice 1."""
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, then, when

from calls import CLIENT, DECISION_TYPE, create, define, journal, listing, moment, next_version
import held
from kb import client as kb_client, store
from kb.contract import kb_pb2


def pytest_configure(config):
    """Register every @slice-<n> tag in the feature files as a marker, so -m slice-<n> selects a slice."""
    tags = set()
    for feature in Path(config.rootpath, "features").glob("*.feature"):
        tags.update(re.findall(r"@(slice-\d+(?:\.\d+)?)", feature.read_text()))
    for tag in sorted(tags):
        config.addinivalue_line("markers", f"{tag}: scenario of that slice in the plan")


def _guard_starts(rootpath, base_temp):
    """Where the guard looks for a store, upward from each: the checkout, the system's temporary directory, and
    pytest's own base temp root, wherever `--basetemp` or `TMPDIR` puts it. A seam a demonstration can point
    elsewhere without touching where the real ones sit."""
    return (rootpath, Path(tempfile.gettempdir()), base_temp)


def _refuse_a_store_above(starts):
    """Refuse to run rather than reach a store outside the suite's own temporary directories: one is never found by
    looking upward, discovery's own way, from any of `starts`."""
    for start in starts:
        found = store.find_above(start)
        if found is not None:
            pytest.exit(
                f"refusing to run: a store was found at {found!s}, above {start!s}; "
                f"no test may reach a store outside its own temporary directory",
                returncode=1,
            )


@pytest.fixture(scope="session", autouse=True)
def _no_store_outside_the_suite(request, tmp_path_factory):
    """The guard, before the first test: pytest's public base temp is one of the places it looks."""
    _refuse_a_store_above(_guard_starts(request.config.rootpath, tmp_path_factory.getbasetemp()))


@pytest.fixture(autouse=True)
def _works_under_its_own_tmp_path(tmp_path, monkeypatch):
    """Every test starts working in a directory under its own tmp_path, restored after, with KB_ROOT cleared unless
    the test sets it, so discovery from the working directory never reaches outside it. A Given that finds or names
    a store of its own chdirs, or sets KB_ROOT, afterward and keeps working."""
    working = tmp_path / "working"
    working.mkdir()
    monkeypatch.chdir(working)
    monkeypatch.delenv("KB_ROOT", raising=False)


@pytest.fixture
def root(tmp_path):
    """The directory a store is started in; the store is its kb/ subdirectory."""
    root = tmp_path / "store"
    root.mkdir()
    return root


@given("a store", target_fixture="client")
def _a_store(root):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    return client


@given(parsers.parse("the client was readied with a clock that reads {reading}"), target_fixture="client")
def _readied_with_a_clock(root, reading):
    """A client over the store at root whose clock stands still at that moment, given in the zone the step names."""
    stood = moment(reading)
    return kb_client.connect(root, clock=lambda: stood)


@pytest.fixture
def before():
    """What a store held before a scenario's When, filled in by the Given that made it: the store's root, and every
    file below it with its bytes."""
    return {}


def _store_with_content(root):
    """A store started in root, holding the decision type and a decision."""
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, DECISION_TYPE)
    create(client, "decision", {
        "title": "Price reviews happen weekly",
        "sections": [
            {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
            {"title": "Rationale", "body": "Costs move weekly.\n"},
        ],
    })


@given("a directory that already has a store inside it, with content in that store", target_fixture="root")
def _directory_with_a_store_inside(root, before):
    _store_with_content(root)
    before.update(store=root, held=held.everything_in(root))
    return root


@given("a directory that sits inside a store", target_fixture="root")
def _directory_inside_a_store(root, before):
    _store_with_content(root)
    inside = root / "notes" / "drafts"
    inside.mkdir(parents=True)
    before.update(store=root, held=held.everything_in(root))
    return inside


@then("the store that is there holds what it held before")
@then("the store it sits inside holds what it held before")
def _store_holds_what_it_held(before):
    assert held.everything_in(before["store"]) == before["held"]


@when("the client checks the store", target_fixture="checked")
def _check_the_store(client):
    return client.Validate(kb_pb2.ValidateRequest())


@then("the store holds no artifact it did not hold before")
def _no_new_artifact(root, client, attempt):
    assert [stub.id for stub in listing(client, "decision", ids_only=True).stubs] == attempt["names"]
    assert held.holds(root) == attempt["files"]


@then("the store's history holds no entry for it")
def _no_entry_in_history(client, attempt):
    assert len(journal(client).entries) == attempt["entries"]


@pytest.fixture
def starter():
    """The role a scenario's store was started under."""
    return CLIENT.role


@then(
    parsers.parse('the store\'s history holds one entry, under that role, with the message "{message}"'),
    target_fixture="entry",
)
def _one_entry_under_the_role(client, starter, message):
    """The one entry in the store's history, under the role the store was started under."""
    [entry] = held.history(client)
    assert (entry.actor.role, entry.message) == (starter, message)
    return entry


# The operator's command line, and the Givens that set where the operator works and which store, if any, is named.

KB = Path(sys.executable).with_name("kb")
OPERATOR = "operator"


def _kb(*args, cwd, env=None):
    """kb's own console command, run as the operator runs it: in a directory, with KB_ROOT and KB_ACTOR set only when
    a step sets them."""
    clean = {key: value for key, value in os.environ.items() if key not in ("KB_ROOT", "KB_ACTOR")}
    return subprocess.run([str(KB), *args], cwd=cwd, env={**clean, **(env or {})}, capture_output=True, text=True)


def _store_needing_attention(root):
    """A store a client filled: two decisions behind the decision type, and one of them, edited by hand, missing the
    body of its purpose."""
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, DECISION_TYPE)
    for title in ("Price reviews happen weekly", "Prices are reviewed monthly"):
        create(client, "decision", {"title": title, "sections": [
            {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
            {"title": "Rationale", "body": "Costs move weekly.\n"},
        ]})
    next_version(client, "decision", DECISION_TYPE)
    monthly = held.artifact(root, "decision/prices-are-reviewed-monthly")
    del monthly["sections"][0]["body"]
    held.plant(root, "decision/prices-are-reviewed-monthly", monthly)
    return root


@given("a store, with the operator working in a folder deep inside the directory it sits in", target_fixture="where")
def _working_deep_inside(root):
    deep = _store_needing_attention(root) / "notes" / "2026" / "september"
    deep.mkdir(parents=True)
    return {"cwd": deep, "env": {}}


@given("a store, with the operator working outside any store and KB_ROOT naming that one", target_fixture="where")
def _outside_with_kb_root(root, tmp_path):
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    return {"cwd": outside, "env": {"KB_ROOT": str(_store_needing_attention(root))}}


@given("the operator is working outside any store and nothing names one", target_fixture="where")
def _outside_with_nothing_named(tmp_path):
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    return {"cwd": outside, "env": {}}


@given(
    "the operator is working outside any store, with KB_ROOT naming a directory that holds no store",
    target_fixture="where",
)
def _outside_with_kb_root_naming_no_store(tmp_path):
    outside, empty = tmp_path / "elsewhere", tmp_path / "empty"
    outside.mkdir()
    empty.mkdir()
    return {"cwd": outside, "env": {"KB_ROOT": str(empty)}}


@given("the operator is working inside a store, with KB_ROOT naming a different store", target_fixture="where")
def _inside_one_naming_another(root, tmp_path):
    other = tmp_path / "other"
    other.mkdir()
    kb_client.connect(other).Init(kb_pb2.InitRequest(root=str(other), actor=CLIENT))
    return {"cwd": _store_needing_attention(root), "env": {"KB_ROOT": str(other)}}
