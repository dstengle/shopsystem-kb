"""Plain tests through the contract of what the check says of a link into a part of an IRI, written before anything
was held there, once an artifact created there lacks that part: the link still lands on nothing, so the check lists
it among the placeholders, with its part, and not among the violations (decision 5 of batch 35's plan)."""
from calls import DECISION_TYPE, NOTE_TYPE, check, create, define, iri, placeholders, start_a_store
from kb import client as kb_client

SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]
MONTHLY = iri("decision", "prices-are-reviewed-monthly")
NOTE = iri("note", "why-monthly")


def _store_with_a_note_into_an_option_of_a_decision_created_without_it(root):
    """A client over a store holding a note about an option of a decision, written while the decision was not held,
    and that decision, created since with another option only."""
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, DECISION_TYPE)
    define(client, NOTE_TYPE)
    create(client, "note", {"title": "Why monthly", "about": f"{MONTHLY}#options/go-monthly"})
    create(client, "decision", {
        "title": "Prices are reviewed monthly", "sections": SECTIONS, "options": [{"title": "Go yearly"}],
    })
    return client


def test_the_check_lists_a_link_into_a_part_its_held_artifact_lacks_as_a_placeholder_and_no_violation(root):
    client = _store_with_a_note_into_an_option_of_a_decision_created_without_it(root)
    checked = check(client)
    assert not checked.faults, checked.faults
    assert list(checked.violations) == []
    assert [
        (each.id, [(link.artifact, link.field, link.place, link.part) for link in each.links])
        for each in checked.placeholders
    ] == [(MONTHLY, [(NOTE, "about", "about", "options/go-monthly")])]


def test_the_check_lists_the_placeholders_the_client_is_given_when_it_asks_for_them(root):
    client = _store_with_a_note_into_an_option_of_a_decision_created_without_it(root)
    create(client, "decision", {
        "title": "Prices are reviewed daily", "sections": SECTIONS, "supersedes": iri("decision", "not-held"),
    })
    assert list(check(client).placeholders) == list(placeholders(client).placeholders)
    assert len(check(client).placeholders) == 2
