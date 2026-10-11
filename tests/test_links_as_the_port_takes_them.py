"""A link as kb hands it to the port (`links.handed`): one whose target the corpus does not hold carries the held type
that target's IRI sits under, which the adapter checks again as it lands the link (decision 2 of batch 35); one whose
target is held carries the type that target sits under too, for a target removed before the link lands (decision 10);
the link to an artifact's own type carries none."""
import pytest

from calls import DECISION_TYPE, create, define, iri, start_a_store, type_iri
from kb import client as kb_client, composition, links, store
from kb.draft import Draft
from kb.values import ArtifactId

DECISION = ArtifactId(type_iri("decision"))
HELD = ArtifactId(iri("decision", "a"))
SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]


@pytest.fixture
def corpus(root):
    """A store holding the decision type, whose `supersedes` links to a decision, and one decision, as a draft reads
    it."""
    start_a_store(root)
    client = kb_client.connect(root)
    define(client, DECISION_TYPE)
    create(client, "decision", {"title": "Price reviews happen weekly", "sections": SECTIONS}, at=str(HELD))
    with store.opened(root) as opened:
        yield Draft(opened)


def handed(corpus, supersedes):
    """The links of a decision superseding the IRI given, as the port takes them: the implicit one, then its own."""
    artifact = {**corpus.artifact(HELD), "supersedes": supersedes}
    return links.handed(ArtifactId(iri("decision", "b")), artifact, corpus, composition.conformed(artifact, corpus))


@pytest.mark.parametrize("target, under", [
    (iri("decision", "nothing-here"), DECISION),
    (iri("decision", "minor/nothing-here"), DECISION),
    (iri("note", "nothing-here"), None),
    (str(HELD), DECISION),
], ids=["not held, under a held type", "not held, deeper under it", "not held, under no held type", "held"])
def test_a_link_carries_the_held_type_a_target_not_held_sits_under(corpus, target, under):
    of_its_type, supersedes = handed(corpus, target)
    assert (supersedes.target, supersedes.under) == (ArtifactId(target), under)
    assert (of_its_type.implicit, of_its_type.under) == (True, None)
