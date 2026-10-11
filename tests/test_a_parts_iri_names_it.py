"""A part is named by its artifact's IRI, `#` and its place (decision 4 of batch 38): a read, and a change that names a
part, may give that IRI as the locator's name, and it means what the locator's name and place mean (Review Focus 5).
A locator giving both a part's IRI and a place is refused: a part is named one way or the other."""
import pytest

from calls import DECISION_TYPE, answer, define, iri, refs, request, signature, start_a_store
from kb import client as kb_client
from kb.content import dumps, loads
from kb.contract import kb_pb2

DECISION = iri("decision", "weekly-reviews")
SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]
OPTIONS = [{"id": "keep-weekly", "title": "Keep weekly", "body": "As now.\n"}, {"title": "Go monthly"}]
LEVELS = [
    {"summary": kb_pb2.ReadRequest.Summary()}, {"whole": kb_pb2.ReadRequest.Whole()},
    {"whole": kb_pb2.ReadRequest.Whole(depth=1)}, {"section": kb_pb2.ReadRequest.Section(title="Purpose")},
]
PLACES = ["options/keep-weekly", "options/keep-weekly/body", "options/go-monthly", "sections/purpose", "options"]


@pytest.fixture
def client(root):
    start_a_store(root)
    client = kb_client.connect(root)
    define(client, DECISION_TYPE)
    created = request(client, "decision", "Weekly reviews", {"sections": SECTIONS, "options": OPTIONS}, at=DECISION)
    assert not created.faults, created.faults
    return client


def _by_iri(place):
    return kb_pb2.Locator(id=f"{DECISION}#{place}")


def _by_place(place):
    return kb_pb2.Locator(id=DECISION, place=place)


def _options(client):
    read = answer(client.Read(kb_pb2.ReadRequest(locator=kb_pb2.Locator(id=DECISION), whole=kb_pb2.ReadRequest.Whole())))
    return loads(read.content)["options"]


@pytest.mark.parametrize("place", PLACES)
@pytest.mark.parametrize("level", LEVELS, ids=["summary", "whole", "whole following links", "section"])
def test_a_read_by_a_parts_iri_gives_what_the_read_by_its_place_gives(client, place, level):
    by_iri = client.Read(kb_pb2.ReadRequest(locator=_by_iri(place), **level))
    assert by_iri == client.Read(kb_pb2.ReadRequest(locator=_by_place(place), **level))


def test_a_read_by_a_parts_iri_is_answered_with_the_part_alone_beside_its_artifacts_name(client):
    read = answer(client.Read(kb_pb2.ReadRequest(locator=_by_iri("options/keep-weekly"), whole=kb_pb2.ReadRequest.Whole())))
    assert read.id == DECISION
    assert loads(read.content) == OPTIONS[0]


@pytest.mark.parametrize("place", ["options/no-such-option", "options/keep-weekly/steps/none", "no-such/place"])
def test_a_parts_iri_naming_nothing_is_refused_as_the_place_naming_nothing_is(client, place):
    by_iri = client.Read(kb_pb2.ReadRequest(locator=_by_iri(place), whole=kb_pb2.ReadRequest.Whole()))
    assert by_iri == client.Read(kb_pb2.ReadRequest(locator=_by_place(place), whole=kb_pb2.ReadRequest.Whole()))
    assert [fault.rule for fault in by_iri.refusal.faults] == ["not-found"]


@pytest.mark.parametrize("name", [
    f"{DECISION}#Options/Keep Weekly", f"{DECISION}#", f"{DECISION}#options#keep-weekly", "decision#options/keep-weekly",
])
def test_a_name_that_is_neither_an_artifacts_iri_nor_a_parts_is_refused_whole_as_a_name(client, name):
    refused = client.Read(kb_pb2.ReadRequest(locator=kb_pb2.Locator(id=name))).refusal
    assert [(fault.artifact, fault.place, fault.rule) for fault in refused.faults] == [(name, "", "locator")]
    assert "a name is an IRI of kb's grammar" in refused.faults[0].message


def test_a_part_is_replaced_by_its_iri(client):
    changed = answer(client.Replace(kb_pb2.ReplaceRequest(
        locator=_by_iri("options/keep-weekly"), content=dumps({"title": "Keep weekly", "body": "Every Monday.\n"}),
        signature=signature("Say when"),
    )))
    assert not changed.faults, changed.faults
    assert _options(client)[0] == {"id": "keep-weekly", "title": "Keep weekly", "body": "Every Monday.\n"}


def test_an_item_is_added_to_the_collection_a_parts_iri_names(client):
    added = answer(client.Add(kb_pb2.AddRequest(
        locator=_by_iri("options"), content=dumps({"title": "Go fortnightly"}), signature=signature("Add one"),
    )))
    assert not added.faults, added.faults
    assert [option["id"] for option in _options(client)] == ["keep-weekly", "go-monthly", "go-fortnightly"]


def test_a_removal_by_a_parts_iri_is_refused_as_the_removal_of_its_place_is(client):
    by_iri = client.Remove(kb_pb2.RemoveRequest(locator=_by_iri("options/keep-weekly"), signature=signature("Drop it")))
    by_place = client.Remove(kb_pb2.RemoveRequest(locator=_by_place("options/keep-weekly"), signature=signature("Drop it")))
    assert by_iri == by_place
    assert by_iri.WhichOneof("outcome") == "refusal"


def test_a_locator_giving_a_parts_iri_and_a_place_is_refused_whether_or_not_they_agree(client):
    for place in ("options/keep-weekly", "options/go-monthly"):
        asked = kb_pb2.Locator(id=f"{DECISION}#options/keep-weekly", place=place)
        refused = client.Read(kb_pb2.ReadRequest(locator=asked)).refusal
        assert [(fault.artifact, fault.place, fault.rule) for fault in refused.faults] == [
            (f"{DECISION}#options/keep-weekly", place, "locator"),
        ]
        assert refused.faults[0].message.startswith(
            "a part is named by its artifact's IRI, # and its place, or by the IRI with the place beside it, never both"
        )


def test_the_links_of_an_artifact_are_followed_from_a_parts_iri_as_from_its_place(client):
    assert refs(client, f"{DECISION}#options/keep-weekly", 1) == refs(client, DECISION, 1, place="options/keep-weekly")
