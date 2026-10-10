"""kb numbers a type's versions, whatever number its client sends: a define makes the first, and each change the next
after the highest held, so two changes to one type made at once make two versions, neither lost. Through the
contract, each store under its own tmp_path; the versions held read through the port. A version is fixed once made:
it reads at its own IRI as it was made however often its type changes since, and a set that changes a type reads its
earlier versions as the store keeps them."""
import copy

import pytest

import at_once
from calls import (
    NOTE_TYPE, change_type, define, kb_ref, read, replace, replace_many, replaced, replacing, start_a_store, type_iri,
    version_iri,
)
from kb import client as kb_client, store, values
from kb.content import dumps, loads

NOTE = type_iri("note")


def _note(number):
    return values.Version(values.Kind(NOTE), number)


def _with(field):
    """What a change to the note type sends, adding a field, at the number a client that read the first would give."""
    schema = copy.deepcopy(NOTE_TYPE["schema"])
    schema["properties"][field] = {"type": "string"}
    return {"version": 2, "schema": schema}


@pytest.mark.parametrize("sent", [7, 0])
def test_a_type_defined_with_a_number_of_its_clients_stands_at_its_first_version(root, sent):
    client = kb_client.connect(root)
    start_a_store(root)
    defined = define(client, {**NOTE_TYPE, "version": sent})
    assert not defined.faults, defined.faults
    assert loads(read(client, NOTE, whole=True).content) == {"version": 1, "schema": NOTE_TYPE["schema"]}
    with store.opened(root) as held:
        assert held.type_version(_note(1)).content["version"] == 1
        with pytest.raises(KeyError):
            held.type_version(_note(sent))


def test_two_changes_to_a_type_made_at_once_make_two_versions_and_neither_is_lost(root):
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, NOTE_TYPE)
    held_back = at_once.OnAThread(root, "Replace", replacing(NOTE, _with("owner"), message="Give a note an owner"))

    def first():
        written = replace(client, NOTE, _with("outcome"), message="Give a note an outcome")
        assert not written.faults, written.faults

    landed = at_once.landed_second(held_back, first)
    assert not landed.faults, landed.faults
    assert loads(read(client, NOTE, whole=True).content) == {**_with("owner"), "version": 3}
    with store.opened(root) as held:
        made = [held.type_version(_note(number)) for number in (1, 2, 3)]
    assert [(each.revision, each.content["version"]) for each in made] == [(1, 1), (2, 2), (3, 3)]
    assert [each.content["schema"] for each in made] == [
        NOTE_TYPE["schema"], _with("outcome")["schema"], _with("owner")["schema"],
    ]


def test_a_version_reads_at_its_iri_exactly_as_it_was_made_after_its_type_changed_twice(root):
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, NOTE_TYPE)
    defined = read(client, NOTE, whole=True)
    first, second = _with("outcome")["schema"], _with("owner")["schema"]
    for schema in (first, second):
        changed = change_type(client, "note", schema)
        assert not changed.faults, changed.faults
    as_defined = read(client, version_iri("note", 1), whole=True)
    assert as_defined.content == dumps({"version": 1, "schema": NOTE_TYPE["schema"]}) == defined.content
    assert (as_defined.id, as_defined.type, as_defined.title, as_defined.revision) == (
        version_iri("note", 1), defined.type, "Note", 1,
    )
    as_first_changed = read(client, version_iri("note", 2), whole=True)
    assert as_first_changed.content == dumps({"version": 2, "schema": first})
    assert (as_first_changed.id, as_first_changed.title, as_first_changed.revision) == (version_iri("note", 2), "Note", 2)
    assert loads(read(client, NOTE, whole=True).content) == {"version": 3, "schema": second}


def test_a_set_that_changes_a_type_reads_its_earlier_version_as_the_store_keeps_it(root):
    """A type that refers to a shape of the note type's first version, written again in the set that changes the
    note type: the reference names a version the store keeps, as it does when the two are changed one by one."""
    client = kb_client.connect(root)
    start_a_store(root)
    shaped = {**NOTE_TYPE["schema"], "$defs": {"label": {"type": "string"}}}
    define(client, {"title": "Note", "schema": shaped})
    memo = {"type": "object", "properties": {"title": {"type": "string"}, "label": {"$ref": kb_ref("note", 1, "#/$defs/label")}}}
    define(client, {"title": "Memo", "schema": memo})
    written = replace_many(client, [
        replaced(NOTE, {"schema": shaped}), replaced(type_iri("memo"), {"schema": memo}),
    ])
    assert not written.faults, written.faults
    assert [loads(read(client, type_iri(kind), whole=True).content)["version"] for kind in ("note", "memo")] == [2, 2]
    assert not read(client, version_iri("note", 1)).faults
