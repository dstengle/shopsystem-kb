"""Suite wiring. Step definitions live beside the scenarios they serve; shared Givens are added here by slice 1."""
import re
from pathlib import Path

import pytest
from pytest_bdd import given, then, when

from calls import CLIENT, DECISION_TYPE, MANGLED, create, define, everything_under, journal, listing
from kb import client as kb_client
from kb.contract import kb_pb2


def pytest_configure(config):
    """Register every @slice-<n> tag in the feature files as a marker, so -m slice-<n> selects a slice."""
    tags = set()
    for feature in Path(config.rootpath, "features").glob("*.feature"):
        tags.update(re.findall(r"@(slice-\d+(?:\.\d+)?)", feature.read_text()))
    for tag in sorted(tags):
        config.addinivalue_line("markers", f"{tag}: scenario of that slice in the plan")


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
    before.update(store=root, held=everything_under(root))
    return root


@given("a directory that sits inside a store", target_fixture="root")
def _directory_inside_a_store(root, before):
    _store_with_content(root)
    inside = root / "notes" / "drafts"
    inside.mkdir(parents=True)
    before.update(store=root, held=everything_under(root))
    return inside


@then("the store that is there holds what it held before")
@then("the store it sits inside holds what it held before")
def _store_holds_what_it_held(before):
    assert everything_under(before["store"]) == before["held"]


@given("someone edited the decision's file by hand and left it in a shape the store cannot read")
def _decision_file_mangled_by_hand(root, monkeypatch):
    """The decision a feature's Background holds, decision/price-reviews-happen-weekly, left unreadable, with the
    client working in the store and nothing naming it."""
    (root / "kb" / "decision" / "price-reviews-happen-weekly.yaml").write_text(MANGLED)
    monkeypatch.chdir(root)
    monkeypatch.delenv("KB_ROOT", raising=False)


@when("the client checks the store", target_fixture="checked")
def _check_the_store(client):
    return client.Validate(kb_pb2.ValidateRequest())


@then("that file is reported as a violation, naming the file")
def _reported_as_unreadable(checked):
    unreadable = [fault for fault in checked.violations if fault.rule == "unreadable"]
    assert [fault.artifact for fault in unreadable] == ["decision/price-reviews-happen-weekly"]
    assert "decision/price-reviews-happen-weekly.yaml cannot be read" in unreadable[0].message


@then("the check comes back with its answer rather than breaking off")
def _answers(checked):
    assert isinstance(checked, kb_pb2.ValidateResponse)
    assert not checked.faults, checked.faults


@then("the store holds no artifact it did not hold before")
def _no_new_artifact(root, client, attempt):
    assert [stub.id for stub in listing(client, "decision", ids_only=True).stubs] == attempt["names"]
    assert everything_under(root / "kb") == attempt["files"]


@then("the store's history holds no entry for it")
def _no_entry_in_history(client, attempt):
    assert len(journal(client).entries) == attempt["entries"]
