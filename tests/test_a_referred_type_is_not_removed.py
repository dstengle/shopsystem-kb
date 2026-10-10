"""A type a held version of another type reads, by a `kb:` reference to a shape or by being built on it, is not
removed (decision/a-referred-type-is-not-removed): every version of a type is kept as made, so what one reads stays
too. Through the contract, each store under its own tmp_path."""
import pytest

from calls import (
    change_type, check, create, define, iri, kb_ref, read, remove, remove_many, removed, request, start_a_store,
    type_iri,
)
from kb import client as kb_client

SHAPED = {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"], "$defs": {
    "label": {"type": "string", "maxLength": 5},
}}
PLAIN = {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]}
LABELLED = {**PLAIN, "properties": {**PLAIN["properties"], "label": {"$ref": kb_ref("tool", 1, "#/$defs/label")}}}
BUILT_ON = {**PLAIN, "allOf": [{"$ref": kb_ref("tool", 1)}]}
READS = {"refers to a shape of it": LABELLED, "is built on it": BUILT_ON}
ON_DELETE = "", "on_delete"


@pytest.fixture
def client(root):
    start_a_store(root)
    return kb_client.connect(root)


def _refused(response):
    return [(fault.artifact, fault.place, fault.rule) for fault in response.faults]


def _a_tool_type_and_a_note_type(client, *versions):
    """A tool type, and a note type made with the first schema given and changed to each after it."""
    define(client, {"title": "Tool", "schema": SHAPED})
    define(client, {"title": "Note", "schema": versions[0]})
    for later in versions[1:]:
        assert not change_type(client, "note", later).faults


@pytest.mark.parametrize("reads", sorted(READS))
def test_after_the_refused_removal_the_store_checks_with_no_fault_of_its_own(client, reads):
    _a_tool_type_and_a_note_type(client, READS[reads])
    create(client, "note", {"title": "X"})
    assert _refused(remove(client, type_iri("tool"))) == [(type_iri("note"), *ON_DELETE)]
    assert not request(client, "note", "Y", {}).faults
    assert not change_type(client, "note", {**READS[reads], "description": "As before"}).faults
    checked = check(client)
    assert (checked.faults, list(checked.violations)) == ([], [])


@pytest.mark.parametrize("left", ["an artifact of its first version", "no artifact"])
def test_a_type_whose_first_version_read_it_and_whose_second_does_not_still_stands_in_the_way(client, left):
    """Every version is kept as made: the first is still held, with or without an artifact conforming to it."""
    define(client, {"title": "Tool", "schema": SHAPED})
    define(client, {"title": "Note", "schema": LABELLED})
    if left == "an artifact of its first version":
        create(client, "note", {"title": "X", "label": "short"})
    assert not change_type(client, "note", PLAIN).faults
    refused = remove(client, type_iri("tool"))
    assert _refused(refused) == [(type_iri("note"), *ON_DELETE)]
    assert repr(type_iri("tool")) in refused.faults[0].message
    assert not read(client, f"{type_iri('tool')}@1", whole=True).faults
    assert not request(client, "note", "Y", {"label": "brief"}, version=1).faults
    misfit = request(client, "note", "Z", {"label": "far too long"}, version=1)
    assert [(fault.place, fault.rule) for fault in misfit.faults] == [("label", "maxLength")]
    checked = check(client)
    assert (checked.faults, list(checked.violations)) == ([], [])


def test_each_referring_type_is_named_once_beside_the_artifacts_of_the_kind_in_the_order_of_names(client):
    """Two versions of the note type read the tool type, and a version of the label type is built on it."""
    _a_tool_type_and_a_note_type(client, LABELLED, {**LABELLED, "description": "Again"})
    define(client, {"title": "Label", "schema": BUILT_ON})
    create(client, "tool", {"title": "Scale"})
    assert _refused(remove(client, type_iri("tool"))) == [
        (type_iri("label"), *ON_DELETE), (type_iri("note"), *ON_DELETE), (iri("tool", "scale"), *ON_DELETE),
    ]


@pytest.mark.parametrize("order", [("note", "tool"), ("tool", "note")])
def test_a_set_that_removes_the_referring_type_with_the_type_it_reads_lands(client, order):
    """The removal is judged against what the whole set leaves, whichever comes first in it."""
    _a_tool_type_and_a_note_type(client, LABELLED, PLAIN)
    landed = remove_many(client, [removed(type_iri(each)) for each in order])
    assert not landed.faults, landed.faults
    for each in ("note", "tool"):
        assert [fault.rule for fault in read(client, type_iri(each)).faults] == ["not-found"]
    checked = check(client)
    assert (checked.faults, list(checked.violations), list(checked.stale)) == ([], [], [])


def test_a_set_that_removes_the_type_read_and_another_but_not_the_referring_type_is_refused_whole(client):
    _a_tool_type_and_a_note_type(client, LABELLED, PLAIN)
    define(client, {"title": "Tag", "schema": PLAIN})
    refused = remove_many(client, [removed(type_iri("tag")), removed(type_iri("tool"))])
    assert _refused(refused) == [(type_iri("note"), *ON_DELETE)]
    assert not read(client, type_iri("tag")).faults


def test_a_type_only_its_own_later_version_reads_is_removed_as_before(client):
    define(client, {"title": "Tool", "schema": SHAPED})
    own = {**SHAPED, "properties": {**SHAPED["properties"], "label": {"$ref": kb_ref("tool", 1, "#/$defs/label")}}}
    assert not change_type(client, "tool", own).faults
    assert not remove(client, type_iri("tool")).faults
    assert [fault.rule for fault in read(client, type_iri("tool")).faults] == ["not-found"]


def test_once_the_referring_type_is_removed_the_type_it_read_is_removed(client):
    _a_tool_type_and_a_note_type(client, LABELLED, PLAIN)
    assert not remove(client, type_iri("note")).faults
    assert not remove(client, type_iri("tool")).faults
