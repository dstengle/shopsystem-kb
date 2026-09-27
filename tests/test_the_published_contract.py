"""Pins what kb publishes to a client through the contract alone (adrs/0018): `kb.content`'s `loads`, `dumps`,
`text` and `NotCanonical`; that `NotCanonical` has `path`; `kb.client.connect`; `kb.contract.kb_pb2`'s being
importable; and the set of kb's own rule names against the spec's list. It does not pin the wording of any fault."""
import re
from pathlib import Path

import pytest

from calls import define, request
from kb import client as kb_client, rules
from kb.content import NotCanonical, dumps, loads, text
from kb.contract import kb_pb2

CLIENT = kb_pb2.Actor(role="client")

SPEC = Path(__file__).resolve().parent.parent / "docs" / "superpowers" / "specs" / "2026-09-23-kb-design.md"

TYPED = {
    "title": "Typed",
    "version": 1,
    "schema": {
        "type": "object",
        "properties": {"title": {"type": "string"}, "detail": {"type": "string"}},
        "required": ["title", "detail"],
    },
}


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


def test_the_rule_names_kb_gives_are_exactly_the_spec_lists():
    sentence = re.search(r"kb's own rule names are:\s*(.*?)\.", SPEC.read_text(encoding="utf-8"), re.DOTALL)
    assert set(re.findall(r"`([a-z_-]+)`", sentence.group(1))) == set(rules.ALL)


def test_a_json_schema_keyword_passes_through_as_a_rule_outside_the_pinned_set(tmp_path):
    root = tmp_path / "store"
    root.mkdir()
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, TYPED)
    response = request(client, "typed", "Missing detail", {})
    assert [fault.rule for fault in response.faults] == ["required"]
    assert response.faults[0].rule not in rules.ALL
