"""An artifact's IRI holds neither a part's place nor a type's version: a create giving one that carries `#` or `@` is
refused with `locator` when the request is converted, and nothing is written (Review Focus 1 of batch 32)."""
import pytest

from calls import DECISION_TYPE, define, iri, request, start_a_store
import held
from kb import client as kb_client, values

SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]
NOT_AN_ARTIFACTS = [iri("decision", "a") + "#steps/x", iri("decision", "a") + "@2"]


@pytest.mark.parametrize("given", NOT_AN_ARTIFACTS)
def test_an_iri_carrying_a_place_or_a_version_does_not_convert_as_an_artifacts(given):
    with pytest.raises(values.Refused) as refused:
        values.artifact_id(given)
    assert [(fault.artifact, fault.rule) for fault in refused.value.faults] == [(given, "locator")]


@pytest.mark.parametrize("given", NOT_AN_ARTIFACTS)
def test_a_create_at_an_iri_carrying_a_place_or_a_version_is_refused_and_writes_nothing(root, given):
    start_a_store(root)
    client = kb_client.connect(root)
    define(client, DECISION_TYPE)
    before = held.holds(root)
    refused = request(client, "decision", "Price reviews happen weekly", {"sections": SECTIONS}, at=given)
    assert [(fault.artifact, fault.rule) for fault in refused.faults] == [(given, "locator")]
    assert held.holds(root) == before
