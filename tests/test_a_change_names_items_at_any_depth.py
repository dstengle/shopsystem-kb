"""A change's rules for the names its items carry hold in a collection at any depth (fix round 1 of slice 179): a
name that is not a plain name, one two items of a collection carry, and one no item of that collection had are
refused inside an item as they are at the top, with the change's wording and the place named, and nothing is
written. A name that is not text is refused as one that is not a plain name, on a change and on a create. Through
the contract."""
import copy

import pytest

from calls import DECISION_TYPE, add, define, iri, read, replace, request, start_a_store
from kb import client as kb_client
from kb.content import loads

DECISION = iri("decision", "weekly-reviews")
SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]
KEPT = {"id": "keep", "title": "Keep weekly", "steps": [{"id": "ask", "title": "Ask the shop"}]}
PLAIN = "a name is a plain name of lower-case letters, digits and single hyphens; "
NOT_TEXT = "a name is text, and what was given is not"


def _the_type():
    """The decision type, each option of which may carry steps."""
    made = copy.deepcopy(DECISION_TYPE)
    made["schema"]["parts"]["options"]["items"]["parts"] = {
        "steps": {"items": {"type": "object", "properties": {"title": {"type": "string"}}}},
    }
    return made


@pytest.fixture
def client(root):
    start_a_store(root)
    client = kb_client.connect(root)
    define(client, _the_type())
    assert not request(client, "decision", "Weekly reviews", {"sections": SECTIONS, "options": [KEPT]}, at=DECISION).faults
    return client


def _whole(steps):
    return {"sections": SECTIONS, "options": [{**KEPT, "steps": steps}]}


def _refused(client, changed, expected):
    """The change is refused with those faults alone, each a place and a message, and the decision reads as before."""
    assert (changed.id, changed.revision) == ("", 0)
    assert [(fault.artifact, fault.place, fault.rule, fault.message) for fault in changed.faults] == [
        (DECISION, place, "item-name", message) for place, message in expected
    ]
    held = read(client, DECISION, whole=True)
    assert (held.revision, loads(held.content)["options"]) == (1, [KEPT])


def test_an_item_added_carrying_names_inside_it_is_refused_for_each(client):
    steps = [{"id": "Bad Name"}, {"id": "dup"}, {"id": "dup"}]
    _refused(client, add(client, DECISION, "options", {"title": "Go monthly", "steps": steps}), [
        ("options/1/steps/0/id", f"{PLAIN}'Bad Name' is not"),
        ("options/1/steps/1/id",
         "a name on an item names an item already in that collection; 'options/1/steps' held no item named 'dup'"),
        ("options/1/steps/2/id", "the items of a collection each have a name of their own; 'dup' is on more than one"),
    ])


def test_a_replacement_carrying_one_name_twice_inside_an_item_is_refused(client):
    steps = [{"id": "ask", "title": "Ask the shop"}, {"id": "ask", "title": "Ask again"}]
    _refused(client, replace(client, DECISION, _whole(steps)), [
        ("options/0/steps/1/id", "the items of a collection each have a name of their own; 'ask' is on more than one"),
    ])


def test_a_replacement_carrying_a_name_that_is_not_plain_inside_an_item_is_refused(client):
    _refused(client, replace(client, DECISION, _whole([{"id": "Ask The Shop!"}])), [
        ("options/0/steps/0/id", f"{PLAIN}'Ask The Shop!' is not"),
    ])


def test_a_replacement_carrying_a_name_no_item_inside_the_item_had_is_refused(client):
    _refused(client, replace(client, DECISION, _whole([{"id": "ask"}, {"id": "tell"}])), [
        ("options/0/steps/1/id",
         "a name on an item names an item already in that collection; 'options/0/steps' held no item named 'tell'"),
    ])


def test_a_part_replaced_carrying_one_name_twice_inside_it_is_refused(client):
    steps = [{"id": "ask"}, {"id": "ask"}]
    _refused(client, replace(client, DECISION, {"title": "Keep weekly", "steps": steps}, path="options/keep"), [
        ("options/0/steps/1/id", "the items of a collection each have a name of their own; 'ask' is on more than one"),
    ])


def test_an_item_inside_an_item_sent_back_with_its_name_keeps_it_and_one_without_is_named(client):
    changed = replace(client, DECISION, _whole([{"title": "Tell the shop"}, {"id": "ask", "title": "Ask the shop"}]))
    assert not changed.faults, changed.faults
    assert loads(read(client, DECISION, whole=True).content)["options"][0]["steps"] == [
        {"id": "tell-the-shop", "title": "Tell the shop"}, {"id": "ask", "title": "Ask the shop"},
    ]


@pytest.mark.parametrize("name", [["a"], {"a": 1}, 12, True, None], ids=["a list", "a mapping", "12", "true", "nothing"])
def test_a_name_that_is_not_text_is_refused_on_a_change_as_not_a_plain_name(client, name):
    top = {"sections": SECTIONS, "options": [{"id": name, "title": "Keep weekly"}]}
    _refused(client, replace(client, DECISION, top), [("options/0/id", PLAIN + NOT_TEXT)])
    _refused(client, replace(client, DECISION, _whole([{"id": name}])), [("options/0/steps/0/id", PLAIN + NOT_TEXT)])
    _refused(client, add(client, DECISION, "options", {"title": "Go monthly", "steps": [{"id": name}]}), [
        ("options/1/steps/0/id", PLAIN + NOT_TEXT),
    ])


@pytest.mark.parametrize("name", [["a"], 12, None], ids=["a list", "12", "nothing"])
def test_a_name_that_is_not_text_is_refused_on_a_create_saying_a_name_is_text(client, name):
    other = iri("decision", "monthly-reviews")
    created = request(client, "decision", "Monthly", {"sections": SECTIONS, "options": [{"id": name, "title": "Go"}]}, at=other)
    assert [(fault.artifact, fault.place, fault.rule, fault.message) for fault in created.faults] == [(
        other, "options/0/id", "item-name",
        f"a part's name is a plain name of lower-case letters, digits and single hyphens; {NOT_TEXT}",
    )]
