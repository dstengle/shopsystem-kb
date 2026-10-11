"""A kind names a type the store holds: an IRI the store holds an artifact at that is not a type is no kind, and a
list, a search or a walk restricted to it is refused as one restricted to an IRI nothing is held at is, with `kind`,
the IRI asked for given back and nothing else (spec/capabilities/name-what-is-asked-for.md; batch 32's review)."""
import pytest

from calls import DECISION_TYPE, create, define, iri, listing, refs, search, start_a_store
from kb import client as kb_client

SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with restocking.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]
WEEKLY = iri("decision", "price-reviews-happen-weekly")
MONTHLY = iri("decision", "stock-counts-happen-monthly")
NOTHING_HELD = iri("decision", "nothing-held-here")


@pytest.fixture
def client(root):
    start_a_store(root)
    client = kb_client.connect(root)
    define(client, DECISION_TYPE)
    create(client, "decision", {"title": "Price reviews happen weekly", "sections": SECTIONS}, at=WEEKLY)
    create(client, "decision", {"title": "Stock counts happen monthly", "sections": SECTIONS}, at=MONTHLY)
    return client


CALLS = {
    "list": lambda client, kind: listing(client, kind),
    "search": lambda client, kind: search(client, "restocking", type_name=kind),
    "follow": lambda client, kind: refs(client, MONTHLY, 1, inward=True, type_name=kind),
}


def _refusal(answered):
    """A refused call's faults, as artifact, place, rule and where its message begins."""
    return [(fault.artifact, fault.place, fault.rule, fault.message.split(";")[0]) for fault in answered.faults]


@pytest.mark.parametrize("call", CALLS)
def test_a_call_restricted_to_a_held_artifact_that_is_not_a_type_is_refused_for_its_kind(client, call):
    answered = CALLS[call](client, WEEKLY)
    assert answered.refused
    assert _refusal(answered) == [("", "", "kind", "a kind must name a type the store holds")]
    assert repr(WEEKLY) in answered.faults[0].message


@pytest.mark.parametrize("call", CALLS)
def test_it_is_refused_as_a_call_restricted_to_an_iri_nothing_is_held_at_is(client, call):
    held, unheld = CALLS[call](client, WEEKLY), CALLS[call](client, NOTHING_HELD)
    assert _refusal(held) == _refusal(unheld)
