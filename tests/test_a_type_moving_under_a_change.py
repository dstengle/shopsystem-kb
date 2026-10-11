"""A type that changes between a change's draft and its landing. A type built on another names the version of it it
reads (kb.v2), which is held as it was made whatever the other type moves on to, so a type an artifact's type is built
on moving changes nothing of what the artifact is checked against or links. Through the contract, two clients on one
machine, each store under its own tmp_path. A change naming no version keeps its artifact at the
version it conforms to, and a create is held to the version of its type it names, content and links, whatever the
type stands at or moves to meanwhile; a type's change restates the links of no artifact, made before it or while it
was being written."""
import copy

import pytest

import at_once
from calls import (
    TAG_TYPE, TYPES as TYPE_OF_TYPES, change_type, check, create, creating, define, iri, kb_ref, read, refs, remove,
    removing, replace, replaced, replacing, request, signature, start_a_store, targets, type_iri, version_iri,
)
from kb import client as kb_client
from kb.contract import kb_pb2

ABOUT = {"type": "string"}
LINKED = {"type": "string", "ref": {"targets": targets("tag"), "cardinality": "one", "parts": False, "on_delete": "refuse"}}


def _typed(title, properties, built_on=None, version=1):
    """A type with the fields given beside a title, built on the first version of another when one is named."""
    schema = {"type": "object", "properties": {"title": {"type": "string"}, **properties}, "required": ["title"]}
    if built_on:
        schema["allOf"] = [{"$ref": kb_ref(built_on, 1)}]
    return {"title": title, "version": version, "schema": schema}


TYPES = {
    "its kind's type": ([_typed("Note", {"about": ABOUT})], _typed("Note", {"about": LINKED}, version=2)),
    "the type its type is built on": (
        [_typed("Base", {"about": ABOUT}), _typed("Note", {}, built_on="base")],
        _typed("Base", {"about": LINKED}, version=2),
    ),
}


@pytest.mark.parametrize("moved", sorted(TYPES))
def test_a_change_naming_no_version_drafted_before_its_type_moved_lands_with_the_links_its_own_version_makes(root, moved):
    """The later version makes `about` a link; the note keeps the version it conforms to, where it is none, as it is
    none in the first version of the base the note's type is built on."""
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
    assert read(client, iri("note", "x")).type == version_iri("note", 1)
    assert [each.stub.id for each in refs(client, iri("tag", "a"), 1, inward=True).reached] == []


KEPT = {
    "a link in the earlier version and not in the later": (LINKED, ABOUT, [iri("note", "before"), iri("note", "meanwhile")]),
    "a link in the later version and not in the earlier": (ABOUT, LINKED, []),
}


@pytest.mark.parametrize("case", sorted(KEPT))
def test_artifacts_made_before_and_while_their_type_is_changed_keep_the_links_their_own_version_makes(root, case):
    """Both notes conform to the earlier version, the one made meanwhile naming it: the change of the type, drafted
    before that note was made and landed after it, restates the links of neither."""
    earlier, later, linking = KEPT[case]
    client = kb_client.connect(root)
    start_a_store(root)
    for type_content in [TAG_TYPE, _typed("Note", {"about": earlier})]:
        define(client, type_content)
    create(client, "tag", {"title": "A"})
    create(client, "note", {"title": "Before", "about": iri("tag", "a")})
    writing = replacing(type_iri("note"), {"schema": _typed("Note", {"about": later})["schema"]}, message="Change it")

    def first():
        made = request(client, "note", "Meanwhile", {"about": iri("tag", "a")}, version=1)
        assert not made.faults, made.faults

    landed = at_once.landed_second(at_once.OnAThread(root, "Replace", writing), first)
    assert not landed.faults, landed.faults
    assert read(client, type_iri("note"), whole=True).revision == 2
    for name in ("before", "meanwhile"):
        assert read(client, iri("note", name)).type == version_iri("note", 1)
    assert [each.stub.id for each in refs(client, iri("tag", "a"), 1, inward=True).reached] == linking
    refused = remove(client, iri("tag", "a"))
    assert sorted(fault.artifact for fault in refused.faults) == linking


def test_a_create_drafted_naming_a_version_its_type_then_moved_on_from_lands_at_the_version_it_named(root):
    """The later version makes `about` a link; what the create carries there fits only the version it names."""
    client = kb_client.connect(root)
    start_a_store(root)
    for type_content in [TAG_TYPE, _typed("Note", {"about": ABOUT})]:
        define(client, type_content)
    made = creating("note", "Meanwhile", {"about": "the float"}, message="Note what it is about", version=1)

    def first():
        written = replace(client, type_iri("note"), {"schema": _typed("Note", {"about": LINKED})["schema"]})
        assert not written.faults, written.faults

    landed = at_once.landed_second(at_once.OnAThread(root, "Create", made), first)
    assert not landed.faults, landed.faults
    assert read(client, type_iri("note"), whole=True).revision == 2
    assert read(client, iri("note", "meanwhile"), whole=True).type == version_iri("note", 1)


LINKS = {
    "a link in the version named and not in the latest": (LINKED, ABOUT, [iri("note", "x")]),
    "a link in the latest and not in the version named": (ABOUT, LINKED, []),
}


@pytest.mark.parametrize("case", sorted(LINKS))
def test_a_create_naming_an_earlier_version_carries_the_links_that_version_makes(root, case):
    earlier, later, reached = LINKS[case]
    client = kb_client.connect(root)
    start_a_store(root)
    for type_content in [TAG_TYPE, _typed("Note", {"about": earlier})]:
        define(client, type_content)
    assert not replace(client, type_iri("note"), {"schema": _typed("Note", {"about": later})["schema"]}).faults
    create(client, "tag", {"title": "A"})
    made = request(client, "note", "X", {"about": iri("tag", "a")}, version=1)
    assert not made.faults, made.faults
    assert read(client, iri("note", "x")).type == version_iri("note", 1)
    assert [each.stub.id for each in refs(client, iri("tag", "a"), 1, inward=True).reached] == reached
    assert [fault.rule for fault in remove(client, iri("tag", "a")).faults] == ["on_delete"] * len(reached)


def test_a_create_naming_an_earlier_version_is_held_to_the_links_that_version_makes(root):
    client = kb_client.connect(root)
    start_a_store(root)
    """The earlier version makes `about` a link and `beside` none, the later the other way round; the store holds
    neither tag, so each link the note makes is one to an IRI not held, under the tag type its field allows."""
    for type_content in [TAG_TYPE, _typed("Note", {"about": LINKED, "beside": ABOUT})]:
        define(client, type_content)
    later = _typed("Note", {"about": ABOUT, "beside": LINKED})["schema"]
    assert not replace(client, type_iri("note"), {"schema": later}).faults
    made = request(client, "note", "X", {"about": iri("tag", "a"), "beside": iri("tag", "b")}, version=1)
    assert not made.faults, made.faults
    assert read(client, iri("note", "x")).type == version_iri("note", 1)
    linked = refs(client, iri("note", "x"), 1)
    assert [(each.stub.field, each.stub.id) for each in linked.reached] == [("about", iri("tag", "a"))]


def test_a_type_changed_while_a_type_built_on_it_moved_lands_and_restates_no_links(root):
    """The base's change, which makes `about` plain, is drafted before the type built on its first version moves on
    and lands after it: both land, and the note, of the version built on the base's first, links as that makes it."""
    client = kb_client.connect(root)
    start_a_store(root)
    for type_content in [TAG_TYPE, _typed("Base", {"about": LINKED}), _typed("Note", {}, built_on="base")]:
        define(client, type_content)
    create(client, "tag", {"title": "A"})
    create(client, "note", {"title": "X", "about": iri("tag", "a")})
    writing = replacing(type_iri("base"), {"schema": _typed("Base", {"about": ABOUT})["schema"]}, message="Make it plain")

    def first():
        moved_on = _typed("Note", {"body": {"type": "string"}}, built_on="base")
        written = replace(client, type_iri("note"), {"schema": moved_on["schema"]}, message="Give it a body")
        assert not written.faults, written.faults

    landed = at_once.landed_second(at_once.OnAThread(root, "Replace", writing), first)
    assert not landed.faults, landed.faults
    assert [read(client, type_iri(each), whole=True).revision for each in ("base", "note")] == [2, 2]
    assert read(client, iri("note", "x")).type == version_iri("note", 1)
    assert [each.stub.id for each in refs(client, iri("tag", "a"), 1, inward=True).reached] == [iri("note", "x")]
    assert [fault.rule for fault in remove(client, iri("tag", "a")).faults] == ["on_delete"]


def test_a_type_built_on_a_bases_first_version_creates_and_reads_as_before_once_the_base_changes(root):
    """The base's second version requires an owner and makes `about` plain: the type built on its first version reads
    neither, so a note with no owner is created, links through `about`, reads back and checks."""
    client = kb_client.connect(root)
    start_a_store(root)
    for type_content in [TAG_TYPE, _typed("Base", {"about": LINKED}), _typed("Note", {}, built_on="base")]:
        define(client, type_content)
    create(client, "tag", {"title": "A"})
    later = _typed("Base", {"about": ABOUT, "owner": {"type": "string"}})["schema"]
    assert not change_type(client, "base", {**later, "required": ["title", "owner"]}).faults
    made = request(client, "note", "X", {"about": iri("tag", "a")})
    assert not made.faults, made.faults
    read_back = read(client, iri("note", "x"), whole=True, depth=1)
    assert not read_back.faults, read_back.faults
    assert read_back.type == version_iri("note", 1)
    assert [each.stub.id for each in refs(client, iri("tag", "a"), 1, inward=True).reached] == [iri("note", "x")]
    assert [fault.rule for fault in remove(client, iri("tag", "a")).faults] == ["on_delete"]
    refused = request(client, "note", "Y", {"about": iri("note", "x")})
    assert [(fault.place, fault.rule) for fault in refused.faults] == [("about", "ref")]
    checked = check(client)
    assert (checked.faults, list(checked.violations), list(checked.stale)) == ([], [], [])


SHAPED = {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"], "$defs": {
    "label": {"type": "string", "maxLength": 5},
}}


def _labelled(version):
    """A note type whose `label` is the shape a version of the tool type defines."""
    return _typed("Note", {"label": {"$ref": kb_ref("tool", version, "#/$defs/label")}})["schema"]


PLAIN = _typed("Note", {})["schema"]


def _a_note_of_the_first_of_two_versions(client, first_version, second_version, content):
    """A tool type, a note type at its second version, and a note conforming to its first."""
    for type_content in [{"title": "Tool", "schema": SHAPED}, {"title": "Note", "schema": first_version}]:
        define(client, type_content)
    assert not request(client, "note", "X", content, version=1).faults
    assert not change_type(client, "note", second_version).faults


def test_a_change_is_not_drafted_again_when_a_type_only_a_later_version_of_its_type_reads_moved(root):
    """The note conforms to its type's first version, which refers to no other type; the second refers to a shape of
    the tool type, which changes between the note's change being drafted and its landing. Nothing the change read
    moved, so it lands as drafted."""
    client = kb_client.connect(root)
    start_a_store(root)
    _a_note_of_the_first_of_two_versions(client, PLAIN, _labelled(1), {})
    held = at_once.OnAThread(root, "Replace", replacing(iri("note", "x"), {}, message="Write it again"))

    def first():
        written = change_type(client, "tool", {**SHAPED, "$defs": {"label": {"type": "string", "maxLength": 9}}})
        assert not written.faults, written.faults

    landed = at_once.landed_second(held, first)
    assert not landed.faults, landed.faults
    assert read(client, iri("note", "x")).revision == 2
    assert held.drafts == 1


def test_a_type_only_the_version_a_change_conforms_to_reads_is_not_removed_under_it(root):
    """The note conforms to its type's first version, which refers to a shape of the tool type's first version; the
    second refers to no other type. The tool type's removal, asked between the note's change being drafted and its
    landing, is refused naming the note type, whose first version is still held: the change lands as drafted, a note
    of that version still creates and is still held to the shape, and the store checks."""
    client = kb_client.connect(root)
    start_a_store(root)
    _a_note_of_the_first_of_two_versions(client, _labelled(1), PLAIN, {"label": "short"})
    held = at_once.OnAThread(root, "Replace", replacing(iri("note", "x"), {"label": "again"}, message="Write it again"))

    def first():
        removed = remove(client, type_iri("tool"))
        assert [(fault.artifact, fault.place, fault.rule) for fault in removed.faults] == [
            (type_iri("note"), "", "on_delete"),
        ]

    landed = at_once.landed_second(held, first)
    assert not landed.faults, landed.faults
    assert read(client, iri("note", "x")).revision == 2
    assert held.drafts == 1
    assert not request(client, "note", "Y", {"label": "brief"}, version=1).faults
    misfit = request(client, "note", "Z", {"label": "far too long"}, version=1)
    assert [(fault.place, fault.rule) for fault in misfit.faults] == [("label", "maxLength")]
    checked = check(client)
    assert (checked.faults, list(checked.violations)) == ([], [])


def test_a_type_is_not_removed_when_a_type_reading_it_was_defined_while_its_removal_was_drafted(root):
    """The tool type's removal is drafted while no other type reads it; a note type referring to a shape of its first
    version is defined before the removal lands. The removal is refused naming the note type, which still creates,
    is still held to the shape, and checks."""
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, {"title": "Tool", "schema": SHAPED})
    held = at_once.OnAThread(root, "Remove", removing(type_iri("tool")))

    def first():
        define(client, {"title": "Note", "schema": _labelled(1)})

    landed = at_once.landed_second(held, first)
    assert [(fault.artifact, fault.place, fault.rule) for fault in landed.faults] == [(type_iri("note"), "", "on_delete")]
    assert not read(client, version_iri("tool", 1), whole=True).faults
    assert not request(client, "note", "X", {"label": "short"}).faults
    misfit = request(client, "note", "Y", {"label": "far too long"})
    assert [(fault.place, fault.rule) for fault in misfit.faults] == [("label", "maxLength")]
    checked = check(client)
    assert (checked.faults, list(checked.violations), list(checked.stale)) == ([], [], [])


READS = {
    "refers to a shape of it": (_labelled(1), "schema/properties/label/$ref"),
    "is built on it": (_typed("Note", {}, built_on="tool")["schema"], "schema/allOf/0/$ref"),
}
PLAINLY = [replaced(type_iri("note"), {"schema": {**PLAIN, "description": "Plainly"}})]


def _defined(schema):
    return "Create", creating(TYPE_OF_TYPES, "Note", {"schema": schema}, message="Define Note")


def _changed(schema):
    return "Replace", replacing(type_iri("note"), {"schema": schema}, message="Change a type")


def _changed_twice(schema):
    """A set changing the note type twice: the version its first change makes reads the tool type, the one it is
    left standing at does not."""
    items = [replaced(type_iri("note"), {"schema": schema}), *PLAINLY]
    return "BatchReplace", kb_pb2.BatchReplaceRequest(items=items, signature=signature("Change a type twice"))


WRITTEN = {
    "defined": (_defined, None),
    "changed": (_changed, 1),
    "changed twice in one set, the first reading it": (_changed_twice, 1),
}


@pytest.mark.parametrize("reads", sorted(READS))
@pytest.mark.parametrize("written", sorted(WRITTEN))
def test_a_type_reading_a_type_removed_while_it_was_being_written_does_not_land(root, written, reads):
    """The note type's new version is drafted while the tool type is held, and the tool type is removed before it
    lands: the removal lands, nothing then reading the tool type, and the note type's define or change is drafted
    again and refused as a type naming a version not held is, nothing of it written. The store checks."""
    schema, place = READS[reads]
    asked, standing = WRITTEN[written]
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, {"title": "Tool", "schema": SHAPED})
    if standing:
        define(client, {"title": "Note", "schema": PLAIN})
    held = at_once.OnAThread(root, *asked(schema))

    def first():
        removed = remove(client, type_iri("tool"))
        assert not removed.faults, removed.faults

    landed = at_once.landed_second(held, first)
    assert [(fault.artifact, fault.place, fault.rule) for fault in landed.faults] == [(type_iri("note"), place, "shape")]
    assert [fault.rule for fault in read(client, type_iri("tool")).faults] == ["not-found"]
    note_type = read(client, type_iri("note"), whole=True)
    assert (note_type.revision if standing else [fault.rule for fault in note_type.faults]) == (standing or ["not-found"])
    checked = check(client)
    assert (checked.faults, list(checked.violations), list(checked.stale)) == ([], [], [])


@pytest.mark.parametrize("reads", sorted(READS))
@pytest.mark.parametrize("written", ["defined", "changed"])
def test_a_type_reading_a_type_that_moved_on_while_it_was_being_written_lands_reading_the_version_it_names(
    root, written, reads,
):
    """Every version is kept as made: the tool type changing under the note type's define or change takes nothing
    the note type reads, so it is drafted again, a type it reads having moved, and lands."""
    schema, _ = READS[reads]
    asked, standing = WRITTEN[written]
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, {"title": "Tool", "schema": SHAPED})
    if standing:
        define(client, {"title": "Note", "schema": PLAIN})
    held = at_once.OnAThread(root, *asked(schema))

    def first():
        moved = change_type(client, "tool", {**SHAPED, "description": "Moved on"})
        assert not moved.faults, moved.faults

    landed = at_once.landed_second(held, first)
    assert not landed.faults, landed.faults
    assert held.drafts == 2
    assert not request(client, "note", "X", {}).faults
    checked = check(client)
    assert (checked.faults, list(checked.violations)) == ([], [])
