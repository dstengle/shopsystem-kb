"""The one boundary every call runs inside: the store a client given a root finds there, and what an exception that
escapes the domain becomes, each with nothing written. Through the contract, each store under its own tmp_path."""
import sqlite3

import pytest

from calls import TAG_TYPE, create, define, read, request, start_a_store, starting
import held
from kb import client as kb_client, drafting, sqlite_store


def _started(root):
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, TAG_TYPE)
    create(client, "tag", {"title": "Kept"})
    return client


def _creating(client):
    return request(client, "tag", "New", {}, message="Tag something")


def test_a_client_given_a_root_that_holds_no_store_is_told_so_and_nothing_is_made_there(root):
    answered = read(kb_client.connect(root), "tag/kept")
    assert [(fault.rule, str(root) in fault.message) for fault in answered.faults] == [("store", True)]
    assert "holds no store" in answered.faults[0].message
    assert list(root.iterdir()) == []


def test_a_client_given_a_root_whose_marker_stands_without_its_database_is_told_the_database_cannot_be_read(root):
    _started(root)
    held.take_away_the_database(root)
    answered = read(kb_client.connect(root), "tag/kept")
    assert [fault.rule for fault in answered.faults] == ["unreadable"]


def test_a_clock_that_raises_is_a_clock_fault_naming_no_artifact_and_writing_nothing(root):
    _started(root)
    before = held.holds(root)

    def clock():
        raise RuntimeError("the clock has stopped")
    answered = _creating(kb_client.connect(root, clock=clock))
    assert [(fault.rule, fault.artifact, fault.place) for fault in answered.faults] == [("clock", "", "")]
    assert held.holds(root) == before
    assert held.names(root) == sorted(["schema/schema", "schema/tag", "tag/kept"])


ESCAPING = {
    "an exception of its own": (RuntimeError("something kb did not foresee"), "store"),
    "the database's": (sqlite3.OperationalError("disk I/O error"), "unreadable"),
}


@pytest.mark.parametrize("escaping", sorted(ESCAPING))
def test_an_exception_escaping_the_domain_becomes_one_fault_and_writes_nothing(root, monkeypatch, escaping):
    client = _started(root)
    before = held.holds(root)
    error, rule = ESCAPING[escaping]

    def raising(*args, **kwargs):
        raise error
    monkeypatch.setattr(drafting, "drafted", raising)
    answered = _creating(client)
    assert [(fault.rule, fault.artifact, fault.place) for fault in answered.faults] == [(rule, "", "")]
    assert str(error) in answered.faults[0].message
    assert held.holds(root) == before


def test_a_database_error_starting_a_store_is_an_unreadable_fault_and_leaves_nothing(root, monkeypatch):
    def failing(path):
        raise sqlite3.OperationalError("disk I/O error")
    monkeypatch.setattr(sqlite_store, "make", failing)
    answered = starting(root)
    assert [(fault.rule, fault.artifact, fault.place) for fault in answered.faults] == [("unreadable", "", "")]
    assert list(root.iterdir()) == []
