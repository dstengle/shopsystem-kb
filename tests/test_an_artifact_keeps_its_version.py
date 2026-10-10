"""An artifact keeps the version of its type it conforms to until a replacement names a later one
(decision/an-artifact-keeps-its-version): a change naming no version leaves it there and is checked, content and
links, against that version, whatever its type stands at; a replacement naming a later version of its own type moves it
there and is checked against that; one naming an earlier version, a version of another type or a version not held is
refused with rule `version`. Through the contract, each store under its own tmp_path."""
import pytest

from calls import (
    DECISION_TYPE, TAG_TYPE, add, add_many, added, create, define, iri, next_version, read, refs, replace,
    replace_many, replaced, request, start_a_store, targets, type_iri, version_iri,
)
from kb import client as kb_client
from kb.content import loads

DECISION = iri("decision", "price-reviews-happen-weekly")
PURPOSE = {"title": "Purpose", "body": "Keep prices in step with costs.\n"}
RATIONALE = {"title": "Rationale", "body": "Costs move weekly.\n"}
CONSEQUENCES = {"title": "Consequences", "body": "Prices change on Mondays.\n"}
EARLIER, LATER = version_iri("decision", 1), version_iri("decision", 2)
OPTION = {"title": "Go monthly", "body": "Review once a month.\n"}


def _a_decision(root, sections, conforming_to=1, latest=("Purpose", "Rationale", "Consequences")):
    """A store holding two versions of the decision type, the later requiring the sections given, a tag type, and a
    decision with the sections given conforming to the version given."""
    client = kb_client.connect(root)
    start_a_store(root)
    for type_content in [DECISION_TYPE, TAG_TYPE]:
        define(client, type_content)
    assert not next_version(client, "decision", DECISION_TYPE, list(latest)).faults
    made = request(client, "decision", "Price reviews happen weekly", {"sections": sections}, version=conforming_to)
    assert not made.faults, made.faults
    return client


NAMING_NONE = {
    "a replacement": lambda client: replace(client, DECISION, {"sections": [PURPOSE, RATIONALE]}),
    "a section set": lambda client: replace(client, DECISION, RATIONALE, path="sections/rationale"),
    "an item added": lambda client: add(client, DECISION, "options", OPTION),
    "a replacement in a set": lambda client: replace_many(client, [replaced(DECISION, {"sections": [PURPOSE, RATIONALE]})]),
    "an item added in a set": lambda client: add_many(client, [added(DECISION, "options", OPTION)]),
}


@pytest.mark.parametrize("change", sorted(NAMING_NONE))
def test_a_change_naming_no_version_keeps_the_artifact_at_the_version_it_conforms_to(root, change):
    """The later version requires a section the decision lacks; the change fits only the version it conforms to."""
    client = _a_decision(root, [PURPOSE, RATIONALE])
    changed = NAMING_NONE[change](client)
    assert not changed.faults, changed.faults
    found = read(client, DECISION, whole=True)
    assert (found.type, found.revision) == (EARLIER, 2)


def test_a_change_naming_no_version_is_checked_against_the_version_its_artifact_conforms_to(root):
    """The later version requires one section only; what fits it and not the earlier one is refused."""
    client = _a_decision(root, [PURPOSE, RATIONALE], latest=("Purpose",))
    refused = replace(client, DECISION, {"sections": [PURPOSE]})
    assert [fault.rule for fault in refused.faults] == ["sections"]
    found = read(client, DECISION, whole=True)
    assert (found.type, found.revision) == (EARLIER, 1)


MOVING = {
    "alone": lambda client, content: replace(client, DECISION, content, version=LATER),
    "in a set": lambda client, content: replace_many(client, [replaced(DECISION, content, version=LATER)]),
}


@pytest.mark.parametrize("sent", sorted(MOVING))
def test_a_replacement_naming_a_later_version_of_its_type_moves_the_artifact_to_it(root, sent):
    client = _a_decision(root, [PURPOSE, RATIONALE])
    moved = MOVING[sent](client, {"sections": [PURPOSE, RATIONALE, CONSEQUENCES]})
    assert not moved.faults, moved.faults
    found = read(client, DECISION, whole=True)
    assert (found.id, found.type, found.revision) == (DECISION, LATER, 2)
    assert [section["title"] for section in loads(found.content)["sections"]] == ["Purpose", "Rationale", "Consequences"]


@pytest.mark.parametrize("sent", sorted(MOVING))
def test_a_replacement_naming_a_later_version_is_checked_against_the_version_it_names(root, sent):
    client = _a_decision(root, [PURPOSE, RATIONALE])
    refused = MOVING[sent](client, {"sections": [PURPOSE, RATIONALE]})
    assert [fault.rule for fault in refused.faults] == ["sections"]
    found = read(client, DECISION, whole=True)
    assert (found.type, found.revision) == (EARLIER, 1)


def test_an_artifact_moved_to_a_later_version_stays_there_and_is_held_to_it(root):
    client = _a_decision(root, [PURPOSE, RATIONALE])
    assert not replace(client, DECISION, {"sections": [PURPOSE, RATIONALE, CONSEQUENCES]}, version=LATER).faults
    refused = replace(client, DECISION, {"sections": [PURPOSE, RATIONALE]})
    assert [fault.rule for fault in refused.faults] == ["sections"]
    assert not add(client, DECISION, "options", OPTION).faults
    found = read(client, DECISION, whole=True)
    assert (found.type, found.revision) == (LATER, 3)


def test_a_replacement_naming_the_version_its_artifact_conforms_to_leaves_it_there(root):
    client = _a_decision(root, [PURPOSE, RATIONALE])
    kept = replace(client, DECISION, {"sections": [PURPOSE, RATIONALE]}, version=EARLIER)
    assert not kept.faults, kept.faults
    found = read(client, DECISION, whole=True)
    assert (found.type, found.revision) == (EARLIER, 2)


NOT_LATER = {
    "an earlier version of its type": EARLIER,
    "a version of another type": version_iri("tag", 1),
    "a version of its type the store does not hold": version_iri("decision", 3),
    "a version of a type the store does not hold": version_iri("invoice", 1),
}
REFUSED = {
    "alone": lambda client, content, version: replace(client, DECISION, content, version=version),
    "in a set": lambda client, content, version: replace_many(client, [replaced(DECISION, content, version=version)]),
}


@pytest.mark.parametrize("sent", sorted(REFUSED))
@pytest.mark.parametrize("named", sorted(NOT_LATER))
def test_a_replacement_naming_a_version_its_artifact_cannot_move_to_is_refused(root, named, sent):
    content = {"sections": [PURPOSE, RATIONALE, CONSEQUENCES]}
    client = _a_decision(root, content["sections"], conforming_to=2)
    before = read(client, DECISION, whole=True)
    refused = REFUSED[sent](client, content, NOT_LATER[named])
    assert [(fault.artifact, fault.rule) for fault in refused.faults] == [(DECISION, "version")]
    assert repr(NOT_LATER[named]) in refused.faults[0].message
    assert read(client, DECISION, whole=True) == before


@pytest.mark.parametrize("sent", sorted(REFUSED))
def test_a_replacement_naming_what_is_not_a_version_s_iri_is_refused_as_a_create_naming_one_is(root, sent):
    client = _a_decision(root, [PURPOSE, RATIONALE])
    named = type_iri("decision")
    refused = REFUSED[sent](client, {"sections": [PURPOSE, RATIONALE]}, named)
    created = request(client, "decision", "Another", {"sections": [PURPOSE, RATIONALE]}, version="").faults
    assert [fault.rule for fault in refused.faults] == [fault.rule for fault in created] == ["locator"]
    assert refused.faults[0].message == created[0].message.replace(repr(version_iri("decision", "")), repr(named))
    assert read(client, DECISION, whole=True).revision == 1



def _a_note_about_a_tag(root, earlier, later):
    """A store holding a tag and a note about it, the note conforming to the first version of its type, in which
    `about` is as `earlier` says, while the type stands at its second, in which it is as `later` says."""
    client = kb_client.connect(root)
    start_a_store(root)
    for about in [None, earlier]:
        properties = {"title": {"type": "string"}, **({"about": about} if about else {})}
        define(client, {"title": "Tag" if about is None else "Note", "version": 1, "schema": {
            "type": "object", "properties": properties, "required": ["title"],
        }})
    create(client, "tag", {"title": "A"})
    create(client, "note", {"title": "X"})
    schema = {"type": "object", "properties": {"title": {"type": "string"}, "about": later}, "required": ["title"]}
    assert not replace(client, type_iri("note"), {"schema": schema}).faults
    return client


TEXT = {"type": "string"}
LINK = {"type": "string", "ref": {"targets": targets("tag"), "cardinality": "one", "parts": False, "on_delete": "refuse"}}
LINKS = {
    "a link in the version it conforms to and not in the latest": (LINK, TEXT, [iri("note", "x")]),
    "a link in the latest and not in the version it conforms to": (TEXT, LINK, []),
}


@pytest.mark.parametrize("case", sorted(LINKS))
def test_a_change_naming_no_version_carries_the_links_the_version_its_artifact_conforms_to_makes(root, case):
    earlier, later, reached = LINKS[case]
    client = _a_note_about_a_tag(root, earlier, later)
    changed = replace(client, iri("note", "x"), {"about": iri("tag", "a")})
    assert not changed.faults, changed.faults
    assert read(client, iri("note", "x")).type == version_iri("note", 1)
    assert [each.stub.id for each in refs(client, iri("tag", "a"), 1, inward=True).reached] == reached


def test_a_replacement_naming_a_later_version_carries_the_links_that_version_makes(root):
    client = _a_note_about_a_tag(root, TEXT, LINK)
    moved = replace(client, iri("note", "x"), {"about": iri("tag", "a")}, version=version_iri("note", 2))
    assert not moved.faults, moved.faults
    assert [each.stub.id for each in refs(client, iri("tag", "a"), 1, inward=True).reached] == [iri("note", "x")]
