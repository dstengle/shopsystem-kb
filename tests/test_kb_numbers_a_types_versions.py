"""kb numbers a type's versions, whatever number its client sends: a define makes the first, and each change the next
after the highest held, so two changes to one type made at once make two versions, neither lost. Through the
contract, each store under its own tmp_path; the versions held read through the port."""
import copy

import pytest

import at_once
from calls import NOTE_TYPE, define, read, replace, replacing, start_a_store, type_iri
from kb import client as kb_client, store, values
from kb.content import loads

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
