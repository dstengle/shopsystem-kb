"""An IRI sits under another when the other's host and segments open its own, segment by whole segment, and more
follow; the type an IRI belongs to is the nearest held type it sits under (decision 9 of batch 32). `names.py` alone
reads the IRIs, `composition.py` asks the store which of them are types."""
import pytest

from calls import DECISION_TYPE, TYPE_OF_TYPES, create, define, iri, start_a_store, type_iri
from kb import client as kb_client, composition, names, store
from kb.draft import Draft
from kb.values import ArtifactId

DECISION = type_iri("decision")
MINOR = DECISION + "/minor"
SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]


@pytest.mark.parametrize("given", [DECISION + "/a", DECISION + "/minor/a", DECISION + "/a.b"])
def test_an_iri_sits_under_one_whose_segments_open_it(given):
    assert names.under(given, DECISION)


@pytest.mark.parametrize("given", [
    DECISION,
    DECISION + "s/a",
    DECISION + "-a/b",
    DECISION + ".a/b",
    "https://shop.example/kb",
    "https://shop.example/kb/note/a",
    "https://shop.example.org/kb/decision/a",
    "https://other.example/kb/decision/a",
])
def test_an_iri_does_not_sit_under_itself_nor_under_one_sharing_only_part_of_a_segment(given):
    assert not names.under(given, DECISION)


def test_the_iris_an_iri_sits_under_are_given_nearest_first():
    assert names.above(DECISION + "/minor/a") == (MINOR, DECISION, "https://shop.example/kb")


def test_an_iri_of_one_segment_sits_under_none():
    assert names.above("https://shop.example/kb") == ()


@pytest.fixture
def held(root):
    """A store holding the decision type and a decision, read as a set's draft reads it."""
    start_a_store(root)
    client = kb_client.connect(root)
    define(client, DECISION_TYPE)
    create(client, "decision", {"title": "Price reviews happen weekly", "sections": SECTIONS}, at=DECISION + "/a")
    with store.opened(root) as opened:
        yield client, Draft(opened)


def nearest(corpus, given):
    return composition.nearest_type(ArtifactId(given), corpus)


def test_the_type_an_iri_sits_under_is_the_held_type_whose_iri_opens_it(held):
    _, corpus = held
    assert nearest(corpus, iri("decision", "b")) == ArtifactId(DECISION)


def test_an_iri_at_a_types_own_iri_does_not_sit_under_that_type(held):
    _, corpus = held
    assert nearest(corpus, DECISION) is None


def test_an_iri_under_no_held_type_sits_under_none(held):
    _, corpus = held
    assert nearest(corpus, iri("note", "a")) is None


def test_an_artifact_that_is_not_a_type_is_not_one_an_iri_sits_under(held):
    _, corpus = held
    assert nearest(corpus, DECISION + "/a/b") == ArtifactId(DECISION)


def test_an_iri_under_the_type_that_describes_types_sits_under_it(held):
    _, corpus = held
    assert nearest(corpus, TYPE_OF_TYPES + "/a") == ArtifactId(TYPE_OF_TYPES)


def test_of_two_held_types_an_iri_sits_under_the_nearest(root):
    start_a_store(root)
    client = kb_client.connect(root)
    define(client, DECISION_TYPE)
    define(client, {**DECISION_TYPE, "title": "Minor decision"}, at=MINOR)
    with store.opened(root) as opened:
        corpus = Draft(opened)
        assert nearest(corpus, MINOR + "/a") == ArtifactId(MINOR)
        assert nearest(corpus, DECISION + "/a") == ArtifactId(DECISION)
        assert nearest(corpus, MINOR) == ArtifactId(DECISION)
