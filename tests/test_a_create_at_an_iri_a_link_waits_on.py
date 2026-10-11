"""A create at an IRI made at once with a create of an artifact linking to that IRI, which the store does not yet hold
(Review Focus 1 of batch 35, through the contract): whichever lands first, both land, the link is on the artifact
created there, the linking artifact reads with its link landing on something held, and removing what it links to is
refused for the link."""
import pytest

import at_once
from calls import DECISION_TYPE, answer, creating, define, iri, read, refs, remove, start_a_store, version_iri
from kb import client as kb_client
from kb.contract import kb_pb2

TARGET = iri("decision", "price-reviews-happen-monthly")
LINKING = iri("decision", "price-reviews-happen-weekly")
SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]
MADE = {
    "the artifact at the IRI": creating("decision", "Price reviews happen monthly", {"sections": SECTIONS}),
    "the artifact linking to it": creating(
        "decision", "Price reviews happen weekly", {"supersedes": TARGET, "sections": SECTIONS},
    ),
}


@pytest.mark.parametrize("first", sorted(MADE))
def test_a_create_at_an_iri_and_a_create_linking_to_it_made_at_once_both_land_the_link_on_what_was_created(root, first):
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, DECISION_TYPE)
    [second] = set(MADE) - {first}

    def landing_first():
        landed = answer(client.Create(MADE[first]))
        assert not landed.faults, landed.faults

    landed = at_once.landed_second(at_once.OnAThread(root, "Create", MADE[second]), landing_first)
    assert not landed.faults, landed.faults

    assert [each.stub.id for each in refs(client, TARGET, 1, inward=True).reached] == [LINKING]
    shown = read(client, LINKING)
    assert not shown.faults, shown.faults
    assert list(shown.references) == [kb_pb2.Stub(
        field="supersedes", id=TARGET, type=version_iri("decision", 1), title="Price reviews happen monthly",
        fields="{}\n",
    )]
    refused = remove(client, TARGET)
    assert [(fault.rule, fault.artifact) for fault in refused.faults] == [("on_delete", LINKING)], refused.faults
