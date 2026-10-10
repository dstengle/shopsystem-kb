"""The links the store keeps are those each artifact's own version of its type declares: a type changed to make a field
a link, or to stop it being one, changes nothing of what blocks a removal, what is counted as pointing in or what an
inward walk reaches for an artifact left at its earlier version; and a set reads each artifact's links as the set
leaves it. Through the contract, and, for a set of more than one kind of change, which
the contract does not take, through kb.write's own `land`; each store under its own tmp_path."""
import copy

import pytest

from calls import iri, read, refs, remove, replace, request, start_a_store, targets, type_iri, version_iri
from kb import changes, client as kb_client, signatures, store, values, write
from kb.content import dumps
from kb.signatures import Signed

PLAIN = {"title": "Note", "version": 1, "schema": {
    "type": "object", "properties": {"title": {"type": "string"}, "about": {"type": "string"}}, "required": ["title"],
}}
LINKING = copy.deepcopy(PLAIN)
LINKING["schema"]["properties"]["about"]["ref"] = {"targets": targets("tag"), "cardinality": "one", "parts": False,
                                                    "on_delete": "refuse"}
TAG = {"title": "Tag", "version": 1, "schema": {"type": "object", "properties": {"title": {"type": "string"}}}}


def _create(client, kind, title, content):
    made = request(client, kind, title, content, message="m")
    assert not made.faults, made.faults
    return made.id


def _retype(client, defined, version):
    content = {key: value for key, value in defined.items() if key != "title"}
    written = replace(client, type_iri("note"), {**content, "version": version}, message="m")
    assert not written.faults, written.faults


def _delete(client, name):
    return remove(client, name, message="m")


@pytest.fixture
def where(tmp_path):
    root = tmp_path / "store"
    root.mkdir()
    return root


@pytest.fixture
def client(where):
    root = where
    client = kb_client.connect(root)
    start_a_store(root)
    return client


def _with_a_note_about_a_tag(client, note_type):
    _create(client, "schema", TAG["title"], {key: value for key, value in TAG.items() if key != "title"})
    _create(client, "schema", note_type["title"], {key: value for key, value in note_type.items() if key != "title"})
    _create(client, "tag", "Pricing", {})
    _create(client, "note", "Weekly", {"about": iri("tag", "pricing")})


def _inbound(client, name):
    summary = read(client, name)
    return [(each.kind, each.field, each.count) for each in summary.inbound]


def _inward(client, name):
    walked = refs(client, name, 1, inward=True)
    return [each.stub.id for each in walked.reached]


def test_a_type_changed_to_make_a_field_a_link_leaves_a_note_of_its_earlier_version_holding_plain_text(client):
    _with_a_note_about_a_tag(client, PLAIN)
    _retype(client, LINKING, 2)
    assert read(client, iri("note", "weekly")).type == version_iri("note", 1)
    assert _inbound(client, iri("tag", "pricing")) == []
    assert _inward(client, iri("tag", "pricing")) == []
    assert not _delete(client, iri("tag", "pricing")).faults
    assert [fault.rule for fault in read(client, iri("tag", "pricing")).faults] == ["not-found"]


def _landed(root, operations) -> list:
    """A set of changes of more than one kind landed through kb.write; the faults it was refused for."""
    with store.opened(root) as held:
        try:
            write.land(held, operations, Signed(signatures.Actor("client", ""), "m"))
        except values.Refused as refused:
            return [(fault.artifact, fault.rule) for fault in refused.faults]
    return []


def _whole(name):
    return values.Locator(values.artifact_id(name), ())


def _stored_links_into(root, name) -> list:
    """The artifacts the store keeps a link from into the one named."""
    with store.opened(root) as held:
        return [str(each.source) for each in held.links_in(values.artifact_id(name))]


def test_a_type_changed_in_the_same_set_as_a_removal_does_not_block_it(where, client):
    _with_a_note_about_a_tag(client, PLAIN)
    content = {key: value for key, value in LINKING.items() if key != "title"}
    faults = _landed(where, [
        changes.Replace(_whole(type_iri("note")), values.content(dumps({**content, "version": 2}))),
        changes.Remove(_whole(iri("tag", "pricing"))),
    ])
    assert faults == []
    assert [fault.rule for fault in read(client, iri("tag", "pricing")).faults] == ["not-found"]
    assert read(client, iri("note", "weekly")).type == version_iri("note", 1)
    assert _stored_links_into(where, iri("tag", "pricing")) == []


def test_a_type_changed_to_stop_a_field_being_a_link_still_blocks_removing_what_a_note_of_its_earlier_version_names(client):
    _with_a_note_about_a_tag(client, LINKING)
    _retype(client, PLAIN, 2)
    assert _inbound(client, iri("tag", "pricing")) == [(type_iri("note"), "about", 1)]
    assert _inward(client, iri("tag", "pricing")) == [iri("note", "weekly")]
    refused = _delete(client, iri("tag", "pricing"))
    assert [(fault.artifact, fault.place, fault.rule) for fault in refused.faults] == [
        (iri("note", "weekly"), "about", "on_delete"),
    ]


def test_an_artifact_made_and_removed_in_one_set_does_not_hold_up_removing_its_type(where, client):
    _create(client, "schema", PLAIN["title"], {key: value for key, value in PLAIN.items() if key != "title"})
    passing = values.artifact_id(iri("note", "passing"))
    assert _landed(where, [
        changes.Create(passing, values.version(version_iri("note")), "Passing", (), values.content(dumps({}))),
        changes.Remove(_whole(iri("note", "passing"))),
        changes.Remove(_whole(type_iri("note"))),
    ]) == []


def test_an_artifact_made_at_an_earlier_version_in_the_same_set_as_a_removal_links_as_that_version_declares(where, client):
    """The note's version holds plain text where the type now makes a link, so nothing it carries blocks the removal."""
    _with_a_note_about_a_tag(client, PLAIN)
    _retype(client, LINKING, 2)
    plain = values.artifact_id(iri("note", "plain"))
    about = values.content(dumps({"about": iri("tag", "pricing")}))
    assert _landed(where, [
        changes.Create(plain, values.version(version_iri("note", 1)), "Plain", (), about),
        changes.Remove(_whole(iri("tag", "pricing"))),
    ]) == []
    assert read(client, iri("note", "plain")).type == version_iri("note", 1)
