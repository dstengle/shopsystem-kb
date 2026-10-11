"""Plain tests through the contract that the check reports a link no write would accept as a `ref` violation,
also at a place where a link into a part its held target lacks waits: only that waiting link is a placeholder and no
violation (decision 5 of batch 35's plan); whatever else stands at its place is reported. Each such link is put behind
the store's back, since the store refuses to write it."""
import pytest

from calls import DECISION_TYPE, NOTE_TYPE, check, create, define, iri, start_a_store
import held
from kb import client as kb_client

SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]
YEARLY = iri("decision", "prices-are-reviewed-yearly")
NOTE, OTHER_NOTE = iri("note", "why-yearly"), iri("note", "another-note")
ELSEWHERE = "https://elsewhere.example/thing"  # an IRI under no type the store holds
# A link the note's field does not allow: to a held artifact of another kind, and to an IRI under no held type.
UNLANDED = pytest.mark.parametrize("target", [OTHER_NOTE, ELSEWHERE], ids=["a-kind-not-allowed", "under-no-type"])


def _store_with_two_notes_and_a_decision(root, about):
    """A client over a store holding a note about what is given, another note, and a decision of one option."""
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, DECISION_TYPE)
    define(client, NOTE_TYPE)
    create(client, "note", {"title": "Why yearly", "about": about})
    create(client, "note", {"title": "Another note"})
    create(client, "decision", {
        "title": "Prices are reviewed yearly", "sections": SECTIONS, "options": [{"title": "Go monthly"}],
    })
    return client


def _plant_a_link(root, target):
    """The note's link changed by hand to one its field does not allow."""
    note = held.artifact(root, NOTE)
    note["about"] = target
    held.plant(root, NOTE, note)


def _violations(checked):
    assert not checked.faults, checked.faults
    return [(fault.artifact, fault.place, fault.rule) for fault in checked.violations]


@UNLANDED
def test_the_check_reports_a_link_that_does_not_land_where_nothing_waits(root, target):
    client = _store_with_two_notes_and_a_decision(root, about=f"{YEARLY}#options/go-monthly")
    assert _violations(check(client)) == []
    _plant_a_link(root, target)
    checked = check(client)
    assert _violations(checked) == [(NOTE, "about", "ref")]
    assert list(checked.placeholders) == []


@UNLANDED
def test_the_check_reports_a_link_that_does_not_land_where_a_link_into_a_lacking_part_waits(root, target):
    """The note was written about an option the decision, created since, lacks: that link waits. The link put in its
    place by hand is a violation; the link the store still holds as waiting there stays listed."""
    client = _store_with_two_notes_and_a_decision(root, about=f"{YEARLY}#options/go-yearly")
    assert _violations(check(client)) == []
    _plant_a_link(root, target)
    checked = check(client)
    assert _violations(checked) == [(NOTE, "about", "ref")]
    assert [
        (each.id, [(link.artifact, link.place, link.part) for link in each.links]) for each in checked.placeholders
    ] == [(YEARLY, [(NOTE, "about", "options/go-yearly")])]
