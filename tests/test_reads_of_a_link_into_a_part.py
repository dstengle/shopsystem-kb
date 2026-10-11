"""No held artifact is unreadable for a link it holds into a part of another artifact (`<IRI>#<place>`), whether the
store holds that artifact or not: at a glance the link's stub is the stub of the artifact the part is in, the IRI
alone when it is not held; read whole, following links or not, the link stays the reference as written, a part being
no artifact to fill in; Follow outward reaches the artifact the part is in and walks on from it only when it is
held, and Follow inward to it reaches the linking artifact. Through the contract."""
import pytest

from calls import DECISION_TYPE, NOTE_TYPE, create, define, iri, read, refs, start_a_store, type_iri
from kb import client as kb_client
from kb.content import loads
from kb.contract import kb_pb2

MONTHLY = iri("decision", "price-reviews-happen-monthly")
YEARLY = iri("decision", "price-reviews-happen-yearly")
NOTE = iri("note", "why-monthly")
SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]


@pytest.fixture
def client(root):
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, DECISION_TYPE)
    define(client, NOTE_TYPE)
    return client


@pytest.fixture
def held(client):
    """A decision holding an option, which supersedes another decision, and a note about that option: the reference
    the note holds."""
    create(client, "decision", {"title": "Price reviews happen yearly", "sections": SECTIONS})
    create(client, "decision", {
        "title": "Price reviews happen monthly", "supersedes": YEARLY, "sections": SECTIONS,
        "options": [{"title": "Go monthly"}],
    })
    option = loads(read(client, MONTHLY, whole=True).content)["options"][0]["id"]
    return _a_note_about(client, f"{MONTHLY}#options/{option}")


@pytest.fixture
def not_held(client):
    """A note about an option of a decision the store does not hold: the reference the note holds."""
    return _a_note_about(client, f"{MONTHLY}#options/go-monthly")


def _a_note_about(client, reference):
    answered(create(client, "note", {"title": "Why monthly", "about": reference}))
    return reference


def answered(response):
    assert not response.faults, response.faults
    return response


def outward(client, depth):
    followed = answered(refs(client, NOTE, depth))
    return [(reached.stub, [(hop.field, hop.id) for hop in reached.route]) for reached in followed.reached]


def test_at_a_glance_a_link_into_a_part_of_a_held_artifact_gives_the_stub_of_that_artifact(client, held):
    assert list(answered(read(client, NOTE)).references) == [kb_pb2.Stub(
        field="about", id=MONTHLY, type=type_iri("decision") + "@1", title="Price reviews happen monthly",
        fields=f"supersedes: {YEARLY}\n",
    )]


def test_at_a_glance_a_link_into_a_part_of_an_iri_not_held_gives_the_iri_alone(client, not_held):
    assert list(answered(read(client, NOTE)).references) == [kb_pb2.Stub(field="about", id=MONTHLY)]


@pytest.mark.parametrize("store", ["held", "not_held"])
@pytest.mark.parametrize("depth", [0, 1, 2])
def test_read_whole_a_link_into_a_part_stays_the_reference_written(client, request, store, depth):
    reference = request.getfixturevalue(store)
    assert loads(answered(read(client, NOTE, whole=True, depth=depth)).content)["about"] == reference


@pytest.mark.parametrize("depth", [1, 2])
def test_followed_outward_a_link_into_a_part_of_a_held_artifact_reaches_it_and_walks_on(client, held, depth):
    reached = outward(client, depth)
    assert [(stub.id, stub.title, route) for stub, route in reached] == [
        (MONTHLY, "Price reviews happen monthly", [("about", MONTHLY)]),
        (YEARLY, "Price reviews happen yearly", [("about", MONTHLY), ("supersedes", YEARLY)]),
    ][:depth]


@pytest.mark.parametrize("depth", [1, 2])
def test_followed_outward_a_link_into_a_part_of_an_iri_not_held_reaches_the_iri_alone(client, not_held, depth):
    assert outward(client, depth) == [(kb_pb2.Stub(field="about", id=MONTHLY), [("about", MONTHLY)])]


def test_followed_inward_to_the_artifact_the_part_is_in_the_linking_artifact_is_reached(client, held):
    followed = answered(refs(client, MONTHLY, 1, inward=True))
    assert [(reached.stub.field, reached.stub.id) for reached in followed.reached] == [("about", NOTE)]


def test_the_inbound_count_of_the_artifact_the_part_is_in_counts_the_link(client, held):
    inbound = answered(read(client, MONTHLY)).inbound
    assert [(each.kind, each.field, each.count) for each in inbound] == [(type_iri("note"), "about", 1)]
