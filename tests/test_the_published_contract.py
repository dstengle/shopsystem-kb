"""Pins what kb publishes to a client through the contract alone (adrs/0018): `kb.content`'s `loads`, `dumps`,
`text` and `NotCanonical`; that `NotCanonical` has `path`; `kb.client.connect`; and `kb.contract.kb_pb2`'s being
importable. It does not pin the wording of any fault."""
import pytest

from kb import client as kb_client
from kb.content import NotCanonical, dumps, loads, text
from kb.contract import kb_pb2

CLIENT = kb_pb2.Actor(role="client")


def test_content_round_trips_and_refuses_what_it_cannot_keep():
    written = dumps({"title": "Weekly review"})
    assert loads(written) == {"title": "Weekly review"}
    assert text(True) == "true"
    assert text(12) == "12"

    with pytest.raises(NotCanonical) as excinfo:
        loads("a: 1\na: 2\n")
    assert excinfo.value.path == "a"

    with pytest.raises(NotCanonical):
        dumps({"body": "a line with a trailing space \nits last line"})


def test_the_in_process_client_and_contract_are_reachable(tmp_path):
    root = tmp_path / "store"
    root.mkdir()
    client = kb_client.connect(root)
    response = client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    assert isinstance(response, kb_pb2.InitResponse)
    assert not response.faults
