"""No held artifact is unreadable for a link it holds to an IRI the store does not hold (decision 7 of batch 35):
every read level, a Follow each way and a list answer, the IRI not held coming back as the IRI alone, marked as not
held, with no kind, title or fields, never filled in and never walked on from, and a whole read giving the link
beside its content as landing on nothing held. Through the contract."""
import pytest

from calls import TAG_TYPE, create, define, iri, listing, read, refs, start_a_store, tagged_decision_type, type_iri
from kb import client as kb_client
from kb.content import loads
from kb.contract import kb_pb2

NOT_HELD = iri("decision", "price-reviews-happen-monthly")
TAG = iri("tag", "pricing")
WEEKLY = iri("decision", "price-reviews-happen-weekly")
DAILY = iri("decision", "price-reviews-happen-daily")
SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]
BARE = kb_pb2.Stub(field="supersedes", id=NOT_HELD, not_held=True)


@pytest.fixture
def client(root):
    """A store holding a tag, a decision tagged with it that supersedes a decision the store does not hold, and a
    decision that supersedes that one."""
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, TAG_TYPE)
    define(client, tagged_decision_type())
    create(client, "tag", {"title": "Pricing"})
    create(client, "decision", {
        "title": "Price reviews happen weekly", "supersedes": NOT_HELD, "tags": [TAG], "sections": SECTIONS,
    })
    create(client, "decision", {"title": "Price reviews happen daily", "supersedes": WEEKLY, "sections": SECTIONS})
    return client


def answered(response):
    assert not response.faults, response.faults
    return response


def test_at_a_glance_the_link_comes_back_as_the_iri_alone_beside_the_stub_of_what_is_held(client):
    shown = answered(read(client, WEEKLY))
    assert list(shown.references) == [
        BARE, kb_pb2.Stub(field="tags", id=TAG, type=type_iri("tag") + "@1", title="Pricing", fields="{}\n"),
    ]
    assert loads(shown.content) == {"supersedes": NOT_HELD}


def test_a_section_of_the_artifact_reads(client):
    assert loads(answered(read(client, WEEKLY, section="Rationale")).content) == SECTIONS[1]


def test_read_whole_the_link_is_the_iri_it_names(client):
    assert loads(answered(read(client, WEEKLY, whole=True)).content)["supersedes"] == NOT_HELD


@pytest.mark.parametrize("depth", [1, 2])
def test_read_whole_following_links_the_link_is_never_filled_in(client, depth):
    content = loads(answered(read(client, WEEKLY, whole=True, depth=depth)).content)
    assert content["supersedes"] == NOT_HELD
    assert [tag["id"] for tag in content["tags"]] == [TAG]


def test_read_whole_two_steps_from_an_artifact_that_reaches_it_the_link_is_never_filled_in(client):
    content = loads(answered(read(client, DAILY, whole=True, depth=2)).content)
    assert (content["supersedes"]["id"], content["supersedes"]["supersedes"]) == (WEEKLY, NOT_HELD)


@pytest.mark.parametrize("depth", [1, 2])
def test_followed_outward_the_iri_is_reached_as_the_iri_alone_and_not_walked_on_from(client, depth):
    followed = answered(refs(client, WEEKLY, depth))
    assert [(reached.stub.id, [hop.id for hop in reached.route]) for reached in followed.reached] == [
        (NOT_HELD, [NOT_HELD]), (TAG, [TAG]),
    ]
    assert followed.reached[0].stub == BARE


def test_followed_outward_two_steps_from_an_artifact_that_reaches_it(client):
    followed = answered(refs(client, DAILY, 2))
    assert [(reached.stub.id, [hop.id for hop in reached.route]) for reached in followed.reached] == [
        (WEEKLY, [WEEKLY]), (NOT_HELD, [WEEKLY, NOT_HELD]), (TAG, [WEEKLY, TAG]),
    ]
    assert followed.reached[1].stub == BARE


def test_followed_outward_to_one_kind_the_iri_has_no_kind_to_be_reached_by(client):
    assert [reached.stub.id for reached in answered(refs(client, WEEKLY, 1, type_name="tag")).reached] == [TAG]
    assert [reached.stub.id for reached in answered(refs(client, WEEKLY, 1, type_name="decision")).reached] == []


def test_followed_inward_to_a_held_artifact_it_also_links_the_artifact_is_reached(client):
    followed = answered(refs(client, TAG, 2, inward=True))
    assert [(reached.stub.id, reached.stub.title) for reached in followed.reached] == [
        (WEEKLY, "Price reviews happen weekly"), (DAILY, "Price reviews happen daily"),
    ]


def test_a_list_of_its_kind_gives_it_with_the_link_as_the_iri_it_names(client):
    listed = answered(listing(client, "decision"))
    assert [(stub.id, loads(stub.fields)) for stub in listed.stubs] == [
        (DAILY, {"supersedes": WEEKLY}), (WEEKLY, {"supersedes": NOT_HELD}),
    ]
    assert list(answered(listing(client, "decision", ids_only=True)).ids) == [DAILY, WEEKLY]


@pytest.mark.parametrize("depth", [0, 1, 2])
def test_read_whole_the_link_is_marked_as_landing_on_nothing_held_and_the_link_that_lands_is_not(client, depth):
    assert list(answered(read(client, WEEKLY, whole=True, depth=depth)).placeholders) == [
        kb_pb2.Placeholder(id=NOT_HELD, links=[kb_pb2.Linking(artifact=WEEKLY, field="supersedes", place="supersedes")]),
    ]


def test_at_a_glance_and_by_section_nothing_is_given_beside_the_stubs(client):
    assert not answered(read(client, WEEKLY)).placeholders
    assert not answered(read(client, WEEKLY, section="Rationale")).placeholders
