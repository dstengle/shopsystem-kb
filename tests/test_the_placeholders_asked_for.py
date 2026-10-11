"""The placeholders as the client is given them (decisions 4 to 6 of batch 35), through the contract: one entry for
each IRI linked to and not held, a part a link names listed with it, in kb's order of names, each with its links in the
order of the names of the artifacts holding them; nothing left once the last link to an IRI goes; answered while
another change holds the store, and through a server as in process. The scenarios of query-the-store and
check-a-change pin what a placeholder is; these pin the listing's order and the read's standing as a read."""
from calls import DECISION_TYPE, NOTE_TYPE, create, define, iri, placeholders, remove, replace, start_a_store
import held
from kb import client as kb_client, testing as kb_testing

SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]
MONTHLY = iri("decision", "prices-are-reviewed-monthly")
YEARLY = iri("decision", "prices-are-reviewed-yearly")
DAILY = iri("decision", "prices-are-reviewed-daily")
WEEKLY = iri("decision", "prices-are-reviewed-weekly")


def _store(root):
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, DECISION_TYPE)
    define(client, NOTE_TYPE)
    return client


def _decision(client, title, supersedes):
    create(client, "decision", {"title": title, "supersedes": supersedes, "sections": SECTIONS})


def _given(asked):
    assert not asked.faults, asked.faults
    return [
        (each.id, each.part, [(link.artifact, link.field, link.place) for link in each.links])
        for each in asked.placeholders
    ]


def test_placeholders_come_in_the_order_of_their_names_a_part_after_its_iri_each_with_its_links_in_order(root):
    client = _store(root)
    _decision(client, "Prices are reviewed weekly", YEARLY)
    create(client, "note", {"title": "Why monthly", "about": f"{MONTHLY}#options/go-monthly"})
    create(client, "note", {"title": "A note", "about": YEARLY})
    _decision(client, "Prices are reviewed daily", MONTHLY)
    assert _given(placeholders(client)) == [
        (MONTHLY, "", [(DAILY, "supersedes", "supersedes")]),
        (MONTHLY, "options/go-monthly", [(iri("note", "why-monthly"), "about", "about")]),
        (YEARLY, "", [(WEEKLY, "supersedes", "supersedes"), (iri("note", "a-note"), "about", "about")]),
    ]


def test_an_iri_is_no_longer_given_once_the_last_link_to_it_goes(root):
    client = _store(root)
    _decision(client, "Prices are reviewed weekly", MONTHLY)
    _decision(client, "Prices are reviewed daily", MONTHLY)
    assert not replace(client, DAILY, {"sections": SECTIONS}).faults
    assert _given(placeholders(client)) == [(MONTHLY, "", [(WEEKLY, "supersedes", "supersedes")])]
    assert not remove(client, WEEKLY).faults
    assert _given(placeholders(client)) == []


def test_the_placeholders_are_given_while_another_change_holds_the_store(root, request, monkeypatch):
    client = _store(root)
    _decision(client, "Prices are reviewed weekly", MONTHLY)
    held.another_change_holds(root, request, monkeypatch)
    assert _given(placeholders(client)) == [(MONTHLY, "", [(WEEKLY, "supersedes", "supersedes")])]


def test_the_placeholders_are_given_through_a_server_as_in_process(root, tmp_path, monkeypatch):
    _decision(_store(root), "Prices are reviewed weekly", MONTHLY)
    arranged = tmp_path / "arranged"
    arranged.mkdir()
    with kb_testing.served(root, arranged):
        monkeypatch.chdir(arranged)
        through = placeholders(kb_client.connect())
        assert through == placeholders(kb_client.connect(root))
    assert _given(through) == [(MONTHLY, "", [(WEEKLY, "supersedes", "supersedes")])]
