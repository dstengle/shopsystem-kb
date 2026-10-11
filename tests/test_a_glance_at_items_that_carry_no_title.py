"""A read at a glance gives a stub of each part with the title the part has, empty when it carries none, whether the
artifact or a part of it is read. Through the contract."""
import pytest

from calls import answer, create, define, iri, start_a_store
from kb import client as kb_client
from kb.content import loads
from kb.contract import kb_pb2

CHECKS = iri("list", "tidy")
LIST_TYPE = {
    "title": "List",
    "version": 1,
    "schema": {
        "type": "object",
        "properties": {"title": {"type": "string"}},
        "required": ["title"],
        "parts": {"checks": {"items": {
            "type": "object", "properties": {"says": {"type": "string"}},
            "parts": {"notes": {"items": {"type": "object", "properties": {"says": {"type": "string"}}}}},
        }}},
    },
}


@pytest.fixture
def client(root):
    start_a_store(root)
    client = kb_client.connect(root)
    define(client, LIST_TYPE)
    create(client, "list", {"title": "Tidy", "checks": [{"id": "a", "says": "x", "notes": [{"id": "n", "says": "y"}]}]})
    return client


def _glance(client, locator):
    return answer(client.Read(kb_pb2.ReadRequest(locator=locator, summary=kb_pb2.ReadRequest.Summary())))


def test_an_artifact_whose_items_carry_no_title_is_read_at_a_glance_with_an_empty_title_for_each(client):
    given = _glance(client, kb_pb2.Locator(id=CHECKS))
    assert [(part.collection, part.id, part.title) for part in given.parts] == [("checks", "a", "")]


def test_a_part_whose_items_carry_no_title_is_read_at_a_glance_with_an_empty_title_for_each(client):
    given = _glance(client, kb_pb2.Locator(id=f"{CHECKS}#checks/a"))
    assert loads(given.content) == {"id": "a"}
    assert [(part.collection, part.id, part.title) for part in given.parts] == [("notes", "n", "")]
