"""The type of types resolves its 2020-12 metaschema through a registry of kb's own, never through what the validator
bundles or fetches: with the library's own specifications emptied and the network unreachable, a store starts and a
type is defined, and the registry holds every 2020-12 resource the type of types names."""
import socket

import pytest
from referencing import Registry

from calls import DECISION_TYPE, define, start_a_store
from kb import client as kb_client
from kb import validation

DIALECT = "https://json-schema.org/draft/2020-12/"
RESOURCES = [DIALECT + "schema"] + [
    DIALECT + "meta/" + name
    for name in ("applicator", "content", "core", "format-annotation", "format-assertion", "meta-data", "unevaluated",
                 "validation")
]


@pytest.fixture
def library_retrieval_off(monkeypatch):
    def unreachable(*args, **kwargs):
        raise OSError("the network is unreachable")
    monkeypatch.setattr("jsonschema.validators.SPECIFICATIONS", Registry())
    monkeypatch.setattr(socket.socket, "connect", unreachable)


@pytest.mark.parametrize("uri", RESOURCES)
def test_kbs_registry_holds_every_2020_12_resource(uri):
    resolved = validation.registry({}).get_or_retrieve(uri)
    assert resolved.value.contents["$id"] == uri


def test_a_store_starts_and_a_type_is_defined_with_the_library_retrieval_off(root, library_retrieval_off):
    connected = kb_client.connect(root)
    start_a_store(root)
    response = define(connected, DECISION_TYPE)
    assert not response.faults
