"""A create may name the parts it carries (decision 5 of batch 38): a part's `id` in a create's content is the name the
client gives it, kept when it is a plain name no other part of its collection carries; one that is not plain, and one
two parts of a collection carry, are each refused, naming the place, beside what else is wrong with the content, and
nothing is written. A part given no name is named by the store, the given names taken first (Review Focus 4)."""
import copy

import pytest

from calls import DECISION_TYPE, define, iri, read, request, start_a_store
import held
from kb import client as kb_client
from kb.content import loads

SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]
DECISION = iri("decision", "weekly-reviews")

# Decisions whose options may each carry steps of their own: a collection inside an item.
NESTED_TYPE = copy.deepcopy(DECISION_TYPE)
NESTED_TYPE["schema"]["parts"]["options"]["items"]["parts"] = {
    "steps": {"items": {"type": "object", "properties": {"title": {"type": "string"}}}},
}


@pytest.fixture
def client(root):
    start_a_store(root)
    client = kb_client.connect(root)
    define(client, NESTED_TYPE)
    return client


def _create(client, options, sections=SECTIONS):
    return request(client, "decision", "Weekly reviews", {"sections": sections, "options": options}, at=DECISION)


def _options(client):
    return loads(read(client, DECISION, whole=True).content)["options"]


def _told(response):
    return [(fault.artifact, fault.place, fault.rule) for fault in response.faults]


def test_a_part_keeps_the_name_its_create_gives_it(client):
    created = _create(client, [{"id": "keep-weekly", "title": "Review prices every week"}])
    assert not created.faults, created.faults
    assert _options(client) == [{"id": "keep-weekly", "title": "Review prices every week"}]


def test_a_part_inside_a_part_keeps_the_name_its_create_gives_it(client):
    created = _create(client, [{"title": "Go monthly", "steps": [{"id": "tell-the-shops", "title": "Write round"}]}])
    assert not created.faults, created.faults
    assert _options(client) == [
        {"id": "go-monthly", "title": "Go monthly", "steps": [{"id": "tell-the-shops", "title": "Write round"}]},
    ]


def test_a_name_the_store_would_have_given_another_part_stands_and_that_part_is_numbered_on(client):
    """Review Focus 4: the given names are taken first, wherever their parts stand, so a minted name is never one."""
    created = _create(client, [
        {"title": "Keep weekly"}, {"id": "keep-weekly", "title": "Go monthly"}, {"title": "Keep weekly"},
    ])
    assert not created.faults, created.faults
    assert [option["id"] for option in _options(client)] == ["keep-weekly-2", "keep-weekly", "keep-weekly-3"]


def test_a_name_two_parts_of_one_collection_carry_is_refused_on_the_second_and_nothing_is_written(root, client):
    before = held.holds(root)
    refused = _create(client, [{"id": "keep-weekly", "title": "Keep weekly"}, {"id": "keep-weekly", "title": "Go monthly"}])
    assert _told(refused) == [(DECISION, "options/1/id", "item-name")]
    assert refused.faults[0].message == "a part's name is unique in its collection; 'keep-weekly' is on more than one"
    assert held.holds(root) == before


def test_a_name_that_is_not_a_plain_name_is_refused_and_nothing_is_written(root, client):
    before = held.holds(root)
    refused = _create(client, [{"title": "Keep weekly"}, {"id": "Keep Weekly!", "title": "Go monthly"}])
    assert _told(refused) == [(DECISION, "options/1/id", "item-name")]
    assert refused.faults[0].message == (
        "a part's name is a plain name of lower-case letters, digits and single hyphens; 'Keep Weekly!' is not"
    )
    assert held.holds(root) == before


def test_a_name_that_is_not_text_is_refused_as_not_a_plain_name(client):
    refused = _create(client, [{"id": ["keep-weekly"], "title": "Keep weekly"}, {"id": 12, "title": "Go monthly"}])
    assert _told(refused) == [(DECISION, "options/0/id", "item-name"), (DECISION, "options/1/id", "item-name")]
    assert all(fault.message.startswith("a part's name is a plain name") for fault in refused.faults)


def test_the_same_name_in_two_collections_is_two_names(client):
    created = _create(client, [
        {"id": "first", "title": "Keep weekly", "steps": [{"id": "first", "title": "Ask"}]},
        {"id": "second", "title": "Go monthly", "steps": [{"id": "first", "title": "Ask"}]},
    ])
    assert not created.faults, created.faults
    assert [(option["id"], option["steps"][0]["id"]) for option in _options(client)] == [
        ("first", "first"), ("second", "first"),
    ]


def test_a_name_inside_a_part_is_refused_by_the_rule_of_its_own_collection(client):
    refused = _create(client, [
        {"title": "Keep weekly", "steps": [{"id": "ask", "title": "Ask"}, {"id": "ask", "title": "Ask again"}]},
    ])
    assert _told(refused) == [(DECISION, "options/0/steps/1/id", "item-name")]
    assert "'ask'" in refused.faults[0].message


def test_a_parts_name_is_refused_beside_what_else_is_wrong_with_the_content(client):
    refused = _create(client, [{"id": "Keep Weekly!", "title": "Keep weekly"}], sections=SECTIONS[:1])
    assert sorted(fault.rule for fault in refused.faults) == ["item-name", "sections"]
