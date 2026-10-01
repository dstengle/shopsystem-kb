"""A type that changes between a change's draft and its landing: the change is drafted again against the type as it
now stands, so what it links is held as links, whichever type of its composition moved. Through the contract, two
clients on one machine, each store under its own tmp_path."""
import copy

import pytest

import at_once
from calls import CLIENT, TAG_TYPE, create, creating, define, refs, remove, replace, replacing
from kb import client as kb_client
from kb.contract import kb_pb2

ABOUT = {"type": "string"}
LINKED = {"type": "string", "ref": {"targets": ["tag"], "cardinality": "one", "parts": False, "on_delete": "refuse"}}


def _typed(title, properties, built_on=None, version=1):
    schema = {"type": "object", "properties": {"title": {"type": "string"}, **properties}, "required": ["title"]}
    if built_on:
        schema["allOf"] = [{"$ref": f"kb:schema/{built_on}"}]
    return {"title": title, "version": version, "schema": schema}


TYPES = {
    "its kind's type": ([_typed("Note", {"about": ABOUT})], _typed("Note", {"about": LINKED}, version=2)),
    "the type its type is built on": (
        [_typed("Base", {"about": ABOUT}), _typed("Note", {}, built_on="base")],
        _typed("Base", {"about": LINKED}, version=2),
    ),
}


@pytest.mark.parametrize("moved", sorted(TYPES))
def test_a_change_drafted_before_a_type_it_reads_moved_lands_with_the_links_the_type_now_makes(root, moved):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    held_types, next_type = copy.deepcopy(TYPES[moved])
    for type_content in [TAG_TYPE, *held_types]:
        define(client, type_content)
    create(client, "tag", {"title": "A"})
    made = creating("note", "X", {"about": "tag/a"}, message="Note what it is about")
    moved_id = f"schema/{next_type.pop('title').lower()}"

    def first():
        written = replace(client, moved_id, next_type, message="Make it a link")
        assert not written.faults, written.faults

    landed = at_once.landed_second(at_once.OnAThread(root, "Create", made), first)
    assert not landed.faults, landed.faults
    assert [each.stub.id for each in refs(client, "tag/a", 1, inward=True).reached] == ["note/x"]
    assert [fault.rule for fault in remove(client, "tag/a").faults] == ["on_delete"]
    validated = client.Validate(kb_pb2.ValidateRequest())
    assert (list(validated.violations), list(validated.stale)) == ([], [])


@pytest.mark.parametrize("moved", sorted(TYPES))
def test_an_artifact_made_while_a_type_it_reads_is_drafted_anew_is_held_to_its_links(root, moved):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    held_types, next_type = copy.deepcopy(TYPES[moved])
    for type_content in [TAG_TYPE, *held_types]:
        define(client, type_content)
    create(client, "tag", {"title": "A"})
    create(client, "note", {"title": "Before", "about": "tag/a"})
    moved_id = f"schema/{next_type.pop('title').lower()}"
    writing = replacing(moved_id, next_type, message="Make it a link")

    def first():
        made = create(client, "note", {"title": "Meanwhile", "about": "tag/a"})
        assert not made.faults, made.faults

    landed = at_once.landed_second(at_once.OnAThread(root, "Replace", writing), first)
    assert not landed.faults, landed.faults
    assert [each.stub.id for each in refs(client, "tag/a", 1, inward=True).reached] == ["note/before", "note/meanwhile"]
    refused = remove(client, "tag/a")
    assert sorted(fault.artifact for fault in refused.faults) == ["note/before", "note/meanwhile"]


def test_a_type_changed_while_a_type_built_on_it_moved_relinks_through_the_types_as_they_now_stand(root):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    for type_content in [TAG_TYPE, _typed("Base", {"about": ABOUT}), _typed("Note", {}, built_on="base")]:
        define(client, type_content)
    create(client, "tag", {"title": "A"})
    create(client, "note", {"title": "X", "about": "tag/a"})
    linked_base = _typed("Base", {"about": LINKED}, version=2)
    del linked_base["title"]
    writing = replacing("schema/base", linked_base, message="Make it a link")
    standing_alone = _typed("Note", {"about": ABOUT}, version=2)
    del standing_alone["title"]

    def first():
        written = replace(client, "schema/note", standing_alone, message="Stand alone")
        assert not written.faults, written.faults

    landed = at_once.landed_second(at_once.OnAThread(root, "Replace", writing), first)
    assert not landed.faults, landed.faults
    assert refs(client, "tag/a", 1, inward=True).reached == []
    assert not remove(client, "tag/a").faults
