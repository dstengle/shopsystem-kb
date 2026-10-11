"""A link as kb hands it to the port (`links.handed`): one whose target the corpus does not hold carries the held type
that target's IRI sits under, which the adapter checks again as it lands the link (decision 2 of batch 35); one whose
target is held carries the type that target sits under too, for a target removed before the link lands (decision 10);
the link to an artifact's own type carries none."""
import copy

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
def test_a_link_carries_the_held_type_its_target_sits_under_held_or_not(corpus, target, under):
    of_its_type, supersedes = handed(corpus, target)
    assert (supersedes.target, supersedes.under) == (ArtifactId(target), under)
    assert (of_its_type.implicit, of_its_type.under) == (True, None)


def test_a_link_says_it_waits_only_when_it_is_among_those_the_store_held_waiting_for_its_artifact(corpus):
    """decision/a-link-that-waits-keeps-waiting: the mark is the store's own account of the artifact, the field,
    what holds it, the IRI and the part alike, and how many like it stand before it (`port_values.told`)."""
    target = iri("decision", "nothing-here")
    artifact = {**corpus.artifact(HELD), "supersedes": target}
    typed = composition.conformed(artifact, corpus)
    named = ArtifactId(iri("decision", "b"))
    marks = lambda waited: [each.waits for each in links.handed(named, artifact, corpus, typed, waited)]
    assert marks(frozenset()) == [False, False]
    assert marks(frozenset({("supersedes", "", ArtifactId(target), "", 0)})) == [False, True]
    assert marks(frozenset({("supersedes", "", ArtifactId(target), "options/a", 0)})) == [False, False]
    assert marks(frozenset({("supersedes", "options/a", ArtifactId(target), "", 0)})) == [False, False]
    assert marks(frozenset({("supersedes", "", ArtifactId(target), "", 1)})) == [False, False]
    assert marks(frozenset({("", "", ArtifactId(type_iri("decision")), "", 0)})) == [False, False]


def test_a_link_says_what_holds_it_the_artifact_or_the_item_by_name_or_with_no_name_by_where_it_stands(root):
    """Decision 14 of batch 35: an item is told by its name, wherever it stands; one with no name, which only a file
    imported can hold, by where it stands, and so is what it holds."""
    start_a_store(root)
    client = kb_client.connect(root)
    linking = copy.deepcopy(DECISION_TYPE)
    linking["schema"]["parts"]["options"]["items"]["properties"]["replaces"] = {
        "type": "array", "items": {"type": "string"}, "ref": linking["schema"]["properties"]["supersedes"]["ref"],
    }
    define(client, linking)
    options = [{"id": "first", "title": "First"}, {"id": "second", "title": "Second", "replaces": [str(HELD), str(HELD)]},
               {"title": "Unnamed", "replaces": [str(HELD)]}, {"id": 4, "title": "Numbered", "replaces": [str(HELD)]}]
    artifact = {"id": iri("decision", "b"), "type": type_iri("decision") + "@1", "supersedes": str(HELD), "options": options}
    with store.opened(root) as opened:
        draft = Draft(opened)
        carried = links.carried(artifact, composition.conformed(artifact, draft)["schema"], draft)
        handed = links.handed(ArtifactId(iri("decision", "b")), artifact, draft, composition.conformed(artifact, draft))
    assert [(each.place, each.holder) for each in carried] == [
        ("supersedes", ""), ("options/1/replaces/0", "options/second"), ("options/1/replaces/1", "options/second"),
        ("options/2/replaces/0", "options/2"), ("options/3/replaces/0", "options/3"),
    ]
    assert [(each.place, each.holder) for each in handed[1:]] == [(each.place, each.holder) for each in carried]
    assert links.told(carried) == [
        ("supersedes", "", HELD, "", 0), ("replaces", "options/second", HELD, "", 0),
        ("replaces", "options/second", HELD, "", 1), ("replaces", "options/2", HELD, "", 0),
        ("replaces", "options/3", HELD, "", 0),
    ]
