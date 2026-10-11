"""A type is not removed while a link waits on an IRI under it that the store does not hold
(decision/a-types-place-is-settled-by-what-sits-under-it), and that holds at landing: a link landing under the type at
the same moment as its removal never leaves both landed. Only a link whose IRI's nearest held type is the removed one
stands in the way (decision/an-iri-belongs-to-its-nearest-type). Through the contract, each store under its own
tmp_path; the two changes made at once by two clients on one machine, landed in the order the test chooses."""
import pytest

import at_once
from calls import (
    TAG_TYPE, check, create, creating, define, iri, listing, placeholders, read, remove, removed, remove_many, removing,
    start_a_store, tagged_decision_type, targets, type_iri,
)
from kb import client as kb_client

SECTIONS = [{"title": "Purpose", "body": "Ship what is ready.\n"}, {"title": "Rationale", "body": "Small steps.\n"}]
TAG, DECISION = iri("tag", "pricing"), iri("decision", "ship-weekly")
MINOR_TYPE, MINOR_TAG = iri("tag", "minor"), iri("tag", "minor/pricing")
TAGS = {"type": "array", "items": {"type": "string"}, "ref": {
    "targets": targets("tag"), "cardinality": "many", "parts": False, "on_delete": "refuse",
}}
# A tag that may itself carry tags, and a type built on the tag type's first version.
TAG_CARRYING_TAGS = {"title": "Tag", "version": 1, "schema": {
    "type": "object", "properties": {"title": {"type": "string"}, "tags": TAGS}, "required": ["title"],
}}
LABEL_ON_TAG = {"title": "Label", "version": 1, "schema": {
    "type": "object", "allOf": [{"$ref": f"kb:{type_iri('tag')}@1"}], "properties": {"title": {"type": "string"}},
}}


def tagged(title, *tags):
    """A decision carrying the tags given, as a create takes it."""
    return {"title": title, "tags": list(tags), "sections": SECTIONS}


@pytest.fixture
def client(root):
    """A store holding a tag type with no artifacts of its kind and a decision type whose decisions carry tags."""
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, TAG_TYPE)
    define(client, tagged_decision_type())
    return client


def standing_in_the_way(refused, type_id=type_iri("tag")):
    """The artifacts a refused removal of a type names, each fault saying the type cannot be removed."""
    assert all(fault.rule == "on_delete" and fault.place == "" for fault in refused.faults), refused.faults
    assert all(repr(type_id) in fault.message for fault in refused.faults)
    return [fault.artifact for fault in refused.faults]


def test_a_removal_landing_after_a_link_landed_under_the_type_is_refused_naming_what_holds_the_link(root, client):
    """The removal is drafted while nothing waits under the type, and held; the decision's create lands; the removal,
    drafted again while it holds the write lock, is refused there, before the clock is read a second time."""
    removal = at_once.OnAThread(root, "Remove", removing(type_iri("tag")))
    landed = at_once.landed_second(removal, lambda: create(client, "decision", tagged("Ship weekly", TAG)))
    assert standing_in_the_way(landed) == [DECISION]
    assert removal.drafts == 1
    assert not read(client, type_iri("tag")).faults
    assert [each.id for each in placeholders(client).placeholders] == [TAG]
    assert not check(client).violations


def test_a_link_landing_after_the_removal_of_the_type_it_would_wait_under_is_refused(root, client):
    """The create is drafted while the tag type is held, and held; the removal lands; the create, its link to an IRI
    then under no held type, is refused as a link that lands on nothing is, and nothing of it is written."""
    linking = creating("decision", "Ship weekly", {"tags": [TAG], "sections": SECTIONS})
    creating_it = at_once.OnAThread(root, "Create", linking)

    def first():
        assert not remove(client, type_iri("tag")).faults

    landed = at_once.landed_second(creating_it, first)
    assert [(fault.artifact, fault.place, fault.rule) for fault in landed.faults] == [(DECISION, "tags/0", "ref")]
    assert read(client, DECISION).faults and read(client, type_iri("tag")).faults
    assert list(placeholders(client).placeholders) == []
    assert not check(client).violations


def test_the_refusal_names_each_artifact_holding_a_waiting_link_once_beside_the_artifacts_of_the_kind(root):
    """A tag that links to two tags not held is of the type's kind and holds waiting links: it is named once, in
    kb's order with the decision that holds one."""
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, TAG_CARRYING_TAGS)
    define(client, tagged_decision_type())
    create(client, "tag", {"title": "Held", "tags": [TAG, iri("tag", "costs")]})
    create(client, "tag", {"title": "Plain"})
    create(client, "decision", tagged("Ship weekly", TAG, TAG))
    refused = remove(client, type_iri("tag"))
    assert standing_in_the_way(refused) == [DECISION, iri("tag", "held"), iri("tag", "plain")]
    assert not read(client, type_iri("tag")).faults


def test_the_refusal_names_what_holds_a_waiting_link_beside_the_types_that_read_the_type(client):
    define(client, LABEL_ON_TAG)
    create(client, "decision", tagged("Ship weekly", TAG))
    assert standing_in_the_way(remove(client, type_iri("tag"))) == [DECISION, type_iri("label")]


def test_a_link_waiting_under_a_nearer_held_type_does_not_stand_in_the_way_of_removing_the_outer_one(client):
    """The decision's link waits under the type at `tag/minor`, its nearest; the tag type itself goes, and the link
    still waits under a held type."""
    held = dict(tagged_decision_type(), title="Held")
    held["schema"] = dict(held["schema"], properties=dict(held["schema"]["properties"], tags=dict(TAGS, ref=dict(
        TAGS["ref"], targets=[type_iri("tag"), MINOR_TYPE],
    ))))
    define(client, held)
    define(client, dict(TAG_TYPE, title="Minor"), at=MINOR_TYPE)
    create(client, "held", tagged("Ship weekly", MINOR_TAG))
    assert not remove(client, type_iri("tag")).faults
    assert [each.id for each in placeholders(client).placeholders] == [MINOR_TAG]
    assert not check(client).violations
    assert standing_in_the_way(remove(client, MINOR_TYPE), MINOR_TYPE) == [iri("held", "ship-weekly")]


def test_a_set_removing_the_type_with_all_that_holds_a_link_waiting_under_it_lands(client):
    create(client, "decision", tagged("Ship weekly", TAG))
    landed = remove_many(client, [removed(DECISION), removed(type_iri("tag"))])
    assert not landed.faults, landed.faults
    assert list(listing(client, "decision", ids_only=True).ids) == []
    assert read(client, type_iri("tag")).faults


def test_a_type_is_removed_once_the_last_link_waiting_under_it_has_gone(client):
    create(client, "decision", tagged("Ship weekly", TAG))
    assert standing_in_the_way(remove(client, type_iri("tag"))) == [DECISION]
    assert not remove(client, DECISION).faults
    assert not remove(client, type_iri("tag")).faults
