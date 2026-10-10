"""A type that changes between a change's draft and its landing: the change is drafted again against the type as it
now stands, so what it links is held as links. A type built on another names the version of it it reads (kb.v2), so
of an artifact's composition only its kind's type can move under a change. Through the contract, two clients on one
machine, each store under its own tmp_path."""
import copy

import pytest

import at_once
from calls import (
    TAG_TYPE, check, create, define, iri, refs, remove, replace, replacing, start_a_store, targets,
    type_iri,
)
from kb import client as kb_client

ABOUT = {"type": "string"}
LINKED = {"type": "string", "ref": {"targets": targets("tag"), "cardinality": "one", "parts": False, "on_delete": "refuse"}}


def _typed(title, properties, version=1):
    schema = {"type": "object", "properties": {"title": {"type": "string"}, **properties}, "required": ["title"]}
    return {"title": title, "version": version, "schema": schema}


TYPES = {
    "its kind's type": ([_typed("Note", {"about": ABOUT})], _typed("Note", {"about": LINKED}, version=2)),
}


@pytest.mark.parametrize("moved", sorted(TYPES))
def test_a_change_drafted_before_a_type_it_reads_moved_lands_with_the_links_the_type_now_makes(root, moved):
    client = kb_client.connect(root)
    start_a_store(root)
    held_types, next_type = copy.deepcopy(TYPES[moved])
    for type_content in [TAG_TYPE, *held_types]:
        define(client, type_content)
    create(client, "tag", {"title": "A"})
    create(client, "note", {"title": "X"})
    made = replacing(iri("note", "x"), {"about": iri("tag", "a")}, message="Note what it is about")
    moved_id = type_iri(next_type.pop('title').lower())

    def first():
        written = replace(client, moved_id, next_type, message="Make it a link")
        assert not written.faults, written.faults

    landed = at_once.landed_second(at_once.OnAThread(root, "Replace", made), first)
    assert not landed.faults, landed.faults
    assert [each.stub.id for each in refs(client, iri("tag", "a"), 1, inward=True).reached] == [iri("note", "x")]
    assert [fault.rule for fault in remove(client, iri("tag", "a")).faults] == ["on_delete"]
    validated = check(client)
    assert (list(validated.violations), list(validated.stale)) == ([], [])


@pytest.mark.parametrize("moved", sorted(TYPES))
def test_an_artifact_made_while_a_type_it_reads_is_drafted_anew_is_held_to_its_links(root, moved):
    client = kb_client.connect(root)
    start_a_store(root)
    held_types, next_type = copy.deepcopy(TYPES[moved])
    for type_content in [TAG_TYPE, *held_types]:
        define(client, type_content)
    create(client, "tag", {"title": "A"})
    create(client, "note", {"title": "Before", "about": iri("tag", "a")})
    moved_id = type_iri(next_type.pop('title').lower())
    writing = replacing(moved_id, next_type, message="Make it a link")

    def first():
        made = create(client, "note", {"title": "Meanwhile", "about": iri("tag", "a")})
        assert not made.faults, made.faults

    landed = at_once.landed_second(at_once.OnAThread(root, "Replace", writing), first)
    assert not landed.faults, landed.faults
    assert [each.stub.id for each in refs(client, iri("tag", "a"), 1, inward=True).reached] == [iri("note", "before"), iri("note", "meanwhile")]
    refused = remove(client, iri("tag", "a"))
    assert sorted(fault.artifact for fault in refused.faults) == [iri("note", "before"), iri("note", "meanwhile")]
