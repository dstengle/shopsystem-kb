"""Pins what kb publishes to a client through the contract alone (adrs/0018): `kb.content`'s `loads`, `dumps`,
`text` and `NotCanonical`; that `NotCanonical` has `path`; `kb.client.connect`, and its `clock` keyword, defaulting to
None; `kb.contract.kb_pb2`'s being importable, as package `kb.v1`; the changes `Create`, `Replace`, `Add` and `Remove`,
each taking one `Signature` and answering its result or a refusal, and the small values naming kinds `kind` and places
`place`; that each item an `AddMany` adds names the artifact it went to; and the set of kb's own rule names against
the spec's list. It does not pin the wording of any fault."""
import inspect
import re
from pathlib import Path

import pytest

from calls import DECISION_TYPE, add_many, added, create, define, request
from kb import client as kb_client, rules
from kb import content as kb_content
from kb.content import NotCanonical, dumps, loads, text
from kb.contract import kb_pb2

CLIENT = kb_pb2.Actor(role="client")

SPEC = Path(__file__).resolve().parent.parent / "spec" / "index.md"

TYPED = {
    "title": "Typed",
    "version": 1,
    "schema": {
        "type": "object",
        "properties": {"title": {"type": "string"}, "detail": {"type": "string"}},
        "required": ["title", "detail"],
    },
}


def test_kb_content_publishes_only_what_the_contract_names():
    assert sorted(kb_content.__all__) == ["NotCanonical", "dumps", "loads", "text"]
    assert not hasattr(kb_content, "entries")


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


def test_connects_clock_is_a_keyword_defaulting_to_none():
    clock = inspect.signature(kb_client.connect).parameters["clock"]
    assert clock.kind is inspect.Parameter.KEYWORD_ONLY
    assert clock.default is None


def test_the_rule_names_kb_gives_are_exactly_the_spec_lists():
    sentence = re.search(r"kb's own rule names:\s*(.*?)\.", SPEC.read_text(encoding="utf-8"), re.DOTALL)
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


CHANGES = {
    "Create": ("CreateRequest", {"kind", "title", "content", "signature"}, "Created", {"id", "revision"}),
    "Replace": ("ReplaceRequest", {"locator", "content", "signature", "revision"}, "Replaced", {"id", "revision"}),
    "Add": ("AddRequest", {"locator", "content", "signature", "revision"}, "Added", {"artifact", "id", "revision"}),
    "Remove": ("RemoveRequest", {"locator", "signature", "revision"}, "Removed", {"id", "revision"}),
}


def _fields(name):
    return set(kb_pb2.DESCRIPTOR.message_types_by_name[name].fields_by_name)


def test_the_contract_is_version_one():
    assert kb_pb2.DESCRIPTOR.package == "kb.v1"


@pytest.mark.parametrize("rpc", sorted(CHANGES))
def test_each_change_takes_one_signature_and_answers_its_result_or_a_refusal(rpc):
    asked, carries, result, gives = CHANGES[rpc]
    method = kb_pb2.DESCRIPTOR.services_by_name["Kb"].methods_by_name[rpc]
    assert (method.input_type.name, method.output_type.name) == (asked, f"{rpc}Response")
    assert _fields(asked) == carries
    assert _fields(result) == gives
    outcome = method.output_type.oneofs_by_name["outcome"]
    assert [(field.name, field.message_type.name) for field in outcome.fields] == [("result", result), ("refusal", "Refusal")]
    assert _fields(f"{rpc}Response") == {"result", "refusal"}


def test_the_small_values_name_kinds_and_places_in_the_specs_words():
    assert _fields("Signature") == {"role", "execution", "message"}
    assert _fields("Refusal") == {"faults"}
    assert _fields("Locator") == {"id", "place"}
    assert _fields("Fault") == {"artifact", "place", "rule", "message"}
    assert _fields("Stub") == {"field", "id", "kind", "title", "fields"}
    assert _fields("InboundCount") == {"kind", "field", "count"}
    assert "place" in _fields("Entry") and "path" not in _fields("Entry")


def test_the_v0_changes_are_gone():
    methods = kb_pb2.DESCRIPTOR.services_by_name["Kb"].methods_by_name
    assert not {"Write", "Append", "Delete"} & set(methods)
    assert not {"WriteRequest", "AppendRequest", "DeleteRequest"} & set(kb_pb2.DESCRIPTOR.message_types_by_name)
    for rpc, (asked, _, _, _) in CHANGES.items():
        assert "actor" not in _fields(asked)


def test_each_item_an_add_many_adds_names_the_artifact_it_went_to(tmp_path):
    root = tmp_path / "store"
    root.mkdir()
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, DECISION_TYPE)
    for title in ("Weekly", "Daily"):
        sections = [{"title": "Purpose", "body": "Why.\n"}, {"title": "Rationale", "body": "Because.\n"}]
        create(client, "decision", {"title": title, "sections": sections})
    landed = add_many(client, [
        added("decision/weekly", "options", {"title": "Go monthly"}),
        added("decision/daily", "options", {"title": "Go hourly"}),
    ])
    assert [(each.artifact, each.id, each.revision) for each in landed.results] == [
        ("decision/weekly", "go-monthly", 2), ("decision/daily", "go-hourly", 2),
    ]
