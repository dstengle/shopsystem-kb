"""The links the store keeps follow the types as they stand: a type changed to make a field a link, or to stop it being
one, changes what blocks a removal, what is counted as pointing in and what an inward walk reaches; and a set reads
each artifact's links as the set leaves it. Through the contract, each store under its own tmp_path."""
import copy

import pytest

from calls import CLIENT
from kb import client as kb_client
from kb.content import dumps
from kb.contract import kb_pb2

PLAIN = {"title": "Note", "version": 1, "schema": {
    "type": "object", "properties": {"title": {"type": "string"}, "about": {"type": "string"}}, "required": ["title"],
}}
LINKING = copy.deepcopy(PLAIN)
LINKING["schema"]["properties"]["about"]["ref"] = {"targets": ["tag"], "cardinality": "one", "parts": False,
                                                    "on_delete": "refuse"}
TAG = {"title": "Tag", "version": 1, "schema": {"type": "object", "properties": {"title": {"type": "string"}}}}


def _create(client, kind, title, content):
    made = client.Create(kb_pb2.CreateRequest(type=kind, title=title, content=dumps(content), actor=CLIENT, message="m"))
    assert not made.faults, made.faults
    return made.id


def _retype(client, defined, version):
    content = {key: value for key, value in defined.items() if key != "title"}
    written = client.Write(kb_pb2.WriteRequest(
        locator=kb_pb2.Locator(id="schema/note"), content=dumps({**content, "version": version}), actor=CLIENT,
        message="m",
    ))
    assert not written.faults, written.faults


def _delete(client, name):
    return client.Delete(kb_pb2.DeleteRequest(locator=kb_pb2.Locator(id=name), actor=CLIENT, message="m"))


@pytest.fixture
def client(tmp_path):
    root = tmp_path / "store"
    root.mkdir()
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    return client


def _with_a_note_about_a_tag(client, note_type):
    _create(client, "schema", TAG["title"], {key: value for key, value in TAG.items() if key != "title"})
    _create(client, "schema", note_type["title"], {key: value for key, value in note_type.items() if key != "title"})
    _create(client, "tag", "Pricing", {})
    _create(client, "note", "Weekly", {"about": "tag/pricing"})


def _inbound(client, name):
    summary = client.Read(kb_pb2.ReadRequest(locator=kb_pb2.Locator(id=name)))
    return [(each.type, each.field, each.count) for each in summary.inbound]


def _inward(client, name):
    walked = client.Refs(kb_pb2.RefsRequest(locator=kb_pb2.Locator(id=name), direction=kb_pb2.RefsRequest.IN, depth=1))
    return [each.stub.id for each in walked.reached]


def test_a_type_changed_to_make_a_field_a_link_blocks_removing_what_it_points_at(client):
    _with_a_note_about_a_tag(client, PLAIN)
    _retype(client, LINKING, 2)
    assert _inbound(client, "tag/pricing") == [("note", "about", 1)]
    assert _inward(client, "tag/pricing") == ["note/weekly"]
    refused = _delete(client, "tag/pricing")
    assert [(fault.artifact, fault.path, fault.rule) for fault in refused.faults] == [
        ("note/weekly", "about", "on_delete"),
    ]


def test_a_type_changed_in_the_same_set_as_a_removal_blocks_it(client):
    _with_a_note_about_a_tag(client, PLAIN)
    content = {key: value for key, value in LINKING.items() if key != "title"}
    applied = client.Apply(kb_pb2.ApplyRequest(operations=[
        kb_pb2.Operation(write=kb_pb2.Replacement(
            locator=kb_pb2.Locator(id="schema/note"), content=dumps({**content, "version": 2}))),
        kb_pb2.Operation(delete=kb_pb2.Removal(locator=kb_pb2.Locator(id="tag/pricing"))),
    ], actor=CLIENT, message="m"))
    assert [(fault.artifact, fault.rule) for fault in applied.faults] == [("note/weekly", "on_delete")]


def test_a_type_changed_to_stop_a_field_being_a_link_no_longer_blocks_removing_what_it_named(client):
    _with_a_note_about_a_tag(client, LINKING)
    _retype(client, PLAIN, 2)
    assert _inbound(client, "tag/pricing") == []
    assert _inward(client, "tag/pricing") == []
    assert not _delete(client, "tag/pricing").faults


def test_an_artifact_made_and_removed_in_one_set_does_not_hold_up_removing_its_type(client):
    _create(client, "schema", PLAIN["title"], {key: value for key, value in PLAIN.items() if key != "title"})
    applied = client.Apply(kb_pb2.ApplyRequest(operations=[
        kb_pb2.Operation(create=kb_pb2.Creation(type="note", title="Passing", content=dumps({}))),
        kb_pb2.Operation(delete=kb_pb2.Removal(locator=kb_pb2.Locator(id="note/passing"))),
        kb_pb2.Operation(delete=kb_pb2.Removal(locator=kb_pb2.Locator(id="schema/note"))),
    ], actor=CLIENT, message="m"))
    assert not applied.faults, applied.faults
