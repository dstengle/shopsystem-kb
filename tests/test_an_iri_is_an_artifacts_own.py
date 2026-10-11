"""An artifact's IRI belongs to the type its create names and to one artifact at a time, through the contract: a
create at exactly its type's IRI, or at an IRI a type is held at, is refused with `identity` (Review Focus 2 and 3 of
batch 32); where types nest, an IRI belongs to the nearest type it sits under (decision 9); a type's own IRI is its
client's to choose, but never one already held; and a removed IRI's history gives both lives (decision 8)."""
import copy

import pytest

from calls import (
    DECISION_TYPE, TAG_TYPE, TYPES, create, define, iri, journal, read, remove, replace, request, start_a_store,
    type_iri,
)
import held
from kb import client as kb_client

SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]
DECISION = type_iri("decision")
MINOR = iri("decision", "minor")
MINOR_TYPE = {**copy.deepcopy(DECISION_TYPE), "title": "Minor decision"}


@pytest.fixture
def client(root):
    start_a_store(root)
    client = kb_client.connect(root)
    define(client, DECISION_TYPE)
    return client


def _decision(client, at, kind="decision"):
    return request(client, kind, "Price reviews happen weekly", {"sections": SECTIONS}, at=at)


def _refused(root, client, at, kind="decision"):
    """The faults a create at an IRI is refused with, as artifact, rule and where its message begins, nothing
    written."""
    before = held.holds(root)
    refused = _decision(client, at, kind)
    assert held.holds(root) == before
    return [(fault.artifact, fault.rule, fault.message.split(";")[0]) for fault in refused.faults]


def test_a_create_at_exactly_its_types_iri_is_refused(root, client):
    assert _refused(root, client, DECISION) == [
        (DECISION, "identity", "an artifact's IRI sits under its type's IRI"),
        (DECISION, "identity", "an IRI names one artifact"),
    ]
    assert read(client, DECISION).title == "Decision"


def test_a_create_at_an_iri_a_type_is_held_at_is_refused(root, client):
    define(client, TAG_TYPE, at=iri("decision", "tag"))
    assert _refused(root, client, iri("decision", "tag")) == [
        (iri("decision", "tag"), "identity", "an IRI names one artifact"),
    ]
    assert read(client, iri("decision", "tag")).title == "Tag"


def test_a_create_under_a_type_the_store_does_not_hold_is_refused(root, client):
    at = "https://elsewhere.example/decision/a"
    assert _refused(root, client, at) == [(at, "identity", "an artifact's IRI sits under its type's IRI")]


def test_an_iri_under_two_held_types_belongs_to_the_nearer(root, client):
    define(client, MINOR_TYPE, at=MINOR)
    at = MINOR + "/a"
    assert _refused(root, client, at) == [(at, "identity", "an artifact's IRI sits under its type's IRI")]
    assert not _decision(client, at, kind=MINOR).faults
    assert not _decision(client, iri("decision", "b")).faults


def test_a_types_iri_need_not_sit_under_any_type_but_is_never_one_already_held(root, client):
    create(client, "decision", {"title": "Price reviews happen weekly", "sections": SECTIONS}, at=iri("decision", "a"))
    before = held.holds(root)
    for taken in (DECISION, iri("decision", "a")):
        refused = request(client, TYPES, "Tag", {"version": 1, "schema": TAG_TYPE["schema"]}, at=taken)
        assert [(fault.artifact, fault.rule) for fault in refused.faults] == [(taken, "identity")]
        assert refused.faults[0].message.startswith("an IRI names one artifact")
    assert held.holds(root) == before


def test_the_history_of_an_iri_used_again_gives_both_lives_in_the_order_they_landed(client):
    at = iri("decision", "a")
    assert not _decision(client, at).faults
    assert not replace(client, at, {"sections": SECTIONS}, message="Touch it").faults
    assert not remove(client, at).faults
    again = _decision(client, at)
    assert (again.id, again.revision) == (at, 1)
    assert [(entry.op, entry.revision) for entry in journal(client, at).entries] == [
        ("create", 1), ("write", 2), ("delete", 3), ("create", 1),
    ]
