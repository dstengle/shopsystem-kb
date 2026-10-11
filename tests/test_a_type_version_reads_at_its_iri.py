"""A type's version reads at the version's IRI, `<type IRI>@<n>`: the content, the revision and the title it was made
with, under that IRI (decision 5 of batch 33). While a type stands at one version, that version is what a read at the
type's IRI gives too."""
from calls import DECISION_TYPE, define, read, start_a_store, type_iri, version_iri
from kb import client as kb_client


def test_a_read_at_a_versions_iri_gives_the_version_the_type_stands_at(root):
    start_a_store(root)
    client = kb_client.connect(root)
    define(client, DECISION_TYPE)
    standing = read(client, type_iri("decision"), whole=True)
    version = read(client, version_iri("decision", 1), whole=True)
    assert not version.refused
    assert (version.id, version.title, version.revision) == (version_iri("decision", 1), standing.title, standing.revision)
    assert version.content == standing.content


def test_a_read_at_the_iri_of_a_version_no_type_holds_is_not_found(root):
    start_a_store(root)
    client = kb_client.connect(root)
    define(client, DECISION_TYPE)
    for asked in (version_iri("decision", 2), version_iri("missing", 1)):
        refused = read(client, asked)
        assert [(fault.artifact, fault.rule) for fault in refused.faults] == [(asked, "not-found")]
