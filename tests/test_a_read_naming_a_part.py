"""A read that names a part, by a locator's place or by the part's IRI, gives that part and nothing else of its
artifact, at the level asked (fix round 1 of slice 179): whole, the part as its artifact holds it, its own links
followed as an artifact's own are and those landing on nothing held marked; at a glance, its name and title with a
stub of each thing a link in it points at and of each of its own parts; a section, refused, a part holding none.
What travels beside the content says which artifact the part is of. Through the contract."""
import copy

import pytest

from calls import DECISION_TYPE, answer, create, define, iri, read, start_a_store, targets, version_iri
from kb import client as kb_client
from kb.content import loads
from kb.contract import kb_pb2

YEARLY, MONTHLY, WEEKLY = (iri("decision", name) for name in ("yearly", "monthly", "weekly"))
GONE, LOST, AWAY = (iri("decision", name) for name in ("gone", "lost", "away"))
SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]
STEP = {"id": "ask", "title": "Ask the shop", "after": LOST}
KEPT = {
    "id": "keep", "title": "Keep weekly", "body": "As now.\n", "replaces": MONTHLY, "sees": [YEARLY, GONE],
    "steps": [STEP, {"id": "tell", "title": "Tell the shop"}],
}
OTHER = {"id": "drop", "title": "Drop them", "replaces": AWAY}


def _link(cardinality):
    return {"targets": targets("decision"), "cardinality": cardinality, "parts": False, "on_delete": "refuse"}


def _the_type():
    """The decision type with options that link to decisions, alone and in a list, and carry steps that link too."""
    made = copy.deepcopy(DECISION_TYPE)
    made["schema"]["parts"]["options"]["items"]["properties"].update(
        replaces={"type": "string", "ref": _link("one")},
        sees={"type": "array", "items": {"type": "string"}, "ref": _link("many")},
    )
    made["schema"]["parts"]["options"]["items"]["parts"] = {"steps": {"items": {
        "type": "object", "properties": {"title": {"type": "string"}, "after": {"type": "string", "ref": _link("one")}},
    }}}
    return made


@pytest.fixture
def client(root):
    """A store holding the weekly decision, which supersedes a decision not held and whose option `keep` points at
    two held decisions, one of them pointing on, and at one not held, as one of its steps does."""
    start_a_store(root)
    client = kb_client.connect(root)
    define(client, _the_type())
    for made in (
        {"title": "Yearly", "sections": SECTIONS},
        {"title": "Monthly", "sections": SECTIONS, "supersedes": YEARLY, "options": [{"title": "Wait", "replaces": AWAY}]},
        {"title": "Weekly", "sections": SECTIONS, "supersedes": GONE, "options": [KEPT, OTHER]},
    ):
        assert not create(client, "decision", made).faults
    return client


def _read(client, locator, **level):
    return answer(client.Read(kb_pb2.ReadRequest(locator=locator, **(level or {"summary": kb_pb2.ReadRequest.Summary()}))))


def _keep():
    return kb_pb2.Locator(id=WEEKLY, place="options/keep")


def _waiting(given):
    return [(each.id, [(link.artifact, link.field, link.place) for link in each.links]) for each in given.placeholders]


def _beside(given):
    return (given.id, given.type, given.revision, given.title)


def test_a_part_read_whole_is_the_part_alone_as_its_artifact_holds_it(client):
    given = _read(client, _keep(), whole=kb_pb2.ReadRequest.Whole())
    assert loads(given.content) == KEPT
    assert not given.references and not given.parts and not given.inbound


def test_what_travels_beside_a_part_says_which_artifact_it_is_of(client):
    whole = read(client, WEEKLY, whole=True)
    assert _beside(whole) == (WEEKLY, version_iri("decision"), 1, "Weekly")
    for level in ({}, {"whole": kb_pb2.ReadRequest.Whole()}):
        assert _beside(_read(client, _keep(), **level)) == _beside(whole)


def test_a_part_read_whole_marks_its_own_links_that_land_on_nothing_held_and_no_other_of_its_artifact(client):
    given = _read(client, _keep(), whole=kb_pb2.ReadRequest.Whole())
    assert _waiting(given) == [
        (GONE, [(WEEKLY, "sees", "options/0/sees/1")]), (LOST, [(WEEKLY, "after", "options/0/steps/0/after")]),
    ]


def test_a_part_read_whole_following_links_has_the_links_in_its_own_fields_filled_in(client):
    given = _read(client, _keep(), whole=kb_pb2.ReadRequest.Whole(depth=1))
    filled = loads(given.content)
    monthly = loads(read(client, MONTHLY, whole=True).content)
    assert filled["replaces"] == {
        "id": MONTHLY, "type": version_iri("decision"), "revision": 1, "title": "Monthly", **monthly,
    }
    assert filled["replaces"]["supersedes"] == YEARLY
    assert [each if isinstance(each, str) else each["id"] for each in filled["sees"]] == [YEARLY, GONE]
    assert filled["steps"] == KEPT["steps"]
    assert {key: filled[key] for key in ("id", "title", "body")} == {key: KEPT[key] for key in ("id", "title", "body")}
    assert _waiting(given) == [
        (AWAY, [(MONTHLY, "replaces", "options/0/replaces")]),
        (GONE, [(WEEKLY, "sees", "options/0/sees/1")]), (LOST, [(WEEKLY, "after", "options/0/steps/0/after")]),
    ]


def test_a_part_read_whole_following_links_two_steps_fills_in_what_its_targets_point_at(client):
    filled = loads(_read(client, _keep(), whole=kb_pb2.ReadRequest.Whole(depth=2)).content)
    assert filled["replaces"]["supersedes"]["id"] == YEARLY


def test_a_part_at_a_glance_is_its_name_and_title_with_stubs_of_what_it_points_at_and_of_its_own_parts(client):
    given = _read(client, _keep())
    assert loads(given.content) == {"id": "keep", "title": "Keep weekly"}
    assert [(stub.field, stub.id, stub.not_held) for stub in given.references] == [
        ("replaces", MONTHLY, False), ("sees", YEARLY, False), ("sees", GONE, True), ("after", LOST, True),
    ]
    assert [(part.collection, part.id, part.title) for part in given.parts] == [
        ("steps", "ask", "Ask the shop"), ("steps", "tell", "Tell the shop"),
    ]
    assert not given.inbound
    assert _waiting(given) == [
        (GONE, [(WEEKLY, "sees", "options/0/sees/1")]), (LOST, [(WEEKLY, "after", "options/0/steps/0/after")]),
    ]


def test_a_part_inside_a_part_is_read_alone(client):
    step = kb_pb2.Locator(id=f"{WEEKLY}#options/keep/steps/ask")
    assert loads(_read(client, step, whole=kb_pb2.ReadRequest.Whole()).content) == STEP
    glance = _read(client, step)
    assert loads(glance.content) == {"id": "ask", "title": "Ask the shop"}
    assert [(stub.field, stub.id, stub.not_held) for stub in glance.references] == [("after", LOST, True)]
    assert not glance.parts


@pytest.mark.parametrize("title", ["Purpose", "Steps"])
def test_a_section_of_a_part_is_refused_saying_the_part_holds_no_section_of_that_title(client, title):
    refused = client.Read(kb_pb2.ReadRequest(locator=_keep(), section=kb_pb2.ReadRequest.Section(title=title)))
    assert not refused.HasField("result")
    assert [(fault.artifact, fault.place, fault.rule, fault.message) for fault in refused.refusal.faults] == [
        (WEEKLY, "options/keep", "not-found", f"'{WEEKLY}#options/keep' holds no section titled {title!r}"),
    ]


def test_a_section_the_artifact_lacks_is_refused_naming_the_artifact(client):
    lacking = client.Read(kb_pb2.ReadRequest(
        locator=kb_pb2.Locator(id=WEEKLY), section=kb_pb2.ReadRequest.Section(title="Steps"),
    ))
    assert [(fault.artifact, fault.place, fault.rule, fault.message) for fault in lacking.refusal.faults] == [
        (WEEKLY, "sections", "not-found", f"'{WEEKLY}' holds no section titled 'Steps'"),
    ]


@pytest.mark.parametrize("level", [
    {"summary": kb_pb2.ReadRequest.Summary()}, {"whole": kb_pb2.ReadRequest.Whole()},
    {"whole": kb_pb2.ReadRequest.Whole(depth=2)}, {"section": kb_pb2.ReadRequest.Section(title="Purpose")},
], ids=["summary", "whole", "whole following links", "section"])
def test_a_part_is_read_alike_by_its_iri_and_by_its_place(client, level):
    by_iri = client.Read(kb_pb2.ReadRequest(locator=kb_pb2.Locator(id=f"{WEEKLY}#options/keep"), **level))
    assert by_iri == client.Read(kb_pb2.ReadRequest(locator=_keep(), **level))


def test_a_part_the_artifact_lacks_is_refused(client):
    refused = client.Read(kb_pb2.ReadRequest(
        locator=kb_pb2.Locator(id=WEEKLY, place="options/none"), whole=kb_pb2.ReadRequest.Whole(),
    ))
    assert [(fault.artifact, fault.place, fault.rule) for fault in refused.refusal.faults] == [
        (WEEKLY, "options/none", "not-found"),
    ]


def test_an_artifact_read_with_no_place_is_given_whole_as_before(client):
    given = read(client, WEEKLY, whole=True)
    assert loads(given.content) == {"supersedes": GONE, "sections": SECTIONS, "options": [KEPT, OTHER]}
    assert _waiting(given) == [
        (AWAY, [(WEEKLY, "replaces", "options/1/replaces")]),
        (GONE, [(WEEKLY, "supersedes", "supersedes"), (WEEKLY, "sees", "options/0/sees/1")]),
        (LOST, [(WEEKLY, "after", "options/0/steps/0/after")]),
    ]
