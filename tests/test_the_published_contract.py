"""Pins what kb publishes to a client through the contract alone (adrs/0018): `kb.content`'s `loads`, `dumps`,
`text` and `NotCanonical`; that `NotCanonical` has `path`; `kb.client.connect`, and its `clock` keyword, defaulting to
None; `kb.contract.kb_pb2`'s being importable, as package `kb.v1`; the changes `Create`, `Replace`, `Add` and `Remove`,
each taking one `Signature` and answering its result or a refusal, and the small values naming kinds `kind` and places
`place`; the reads `Read`, `List`, `Follow`, `Search` and `History`, the signed `Snapshot` and the `Check`, each
answering its result or a refusal; that no rpc starts a store, `kb.init` does, raising `kb.NotStarted` with its
faults; that each item an `AddMany` adds names the artifact it went to; and the set of kb's own rule names against
the spec's list. It does not pin the wording of any fault."""
import inspect
import re
from pathlib import Path

import pytest

import kb
from calls import DECISION_TYPE, add_many, added, create, define, request
from kb import client as kb_client, rules
from kb import content as kb_content
from kb.content import NotCanonical, dumps, loads, text
from kb.contract import kb_pb2

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
    assert kb.init(root, "client") is None
    response = kb_client.connect(root).Check(kb_pb2.CheckRequest())
    assert isinstance(response, kb_pb2.CheckResponse)
    assert response.WhichOneof("outcome") == "result"


def test_kb_init_takes_a_root_and_a_role_and_the_clock_connect_takes():
    parameters = inspect.signature(kb.init).parameters
    assert list(parameters) == ["root", "role", "execution", "clock"]
    assert parameters["execution"].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters["execution"].default == ""
    assert parameters["clock"].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters["clock"].default is None


def test_kb_init_refuses_by_raising_not_started_with_the_faults(tmp_path):
    with pytest.raises(kb.NotStarted) as refused:
        kb.init(tmp_path / "nowhere", "client")
    assert [fault.rule for fault in refused.value.faults] == ["root"]
    assert issubclass(kb.NotStarted, Exception)


def test_no_rpc_starts_a_store_and_no_request_names_an_actor():
    methods = kb_pb2.DESCRIPTOR.services_by_name["Kb"].methods_by_name
    assert "Init" not in methods
    messages = kb_pb2.DESCRIPTOR.message_types_by_name
    assert not {"InitRequest", "InitResponse"} & set(messages)
    for method in methods.values():
        assert "actor" not in method.input_type.fields_by_name


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
    kb.init(root, "client")
    client = kb_client.connect(root)
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


READS = {
    "Read": ("ReadRequest", {"locator", "summary", "whole", "section"}, "Artifact", {
        "id", "kind", "schema_version", "revision", "title", "content", "references", "parts", "inbound",
    }),
    "List": ("ListRequest", {"kind", "fields", "form"}, "Listed", {"stubs", "ids"}),
    "Follow": ("FollowRequest", {"locator", "depth", "direction", "via", "kind"}, "Followed", {"reached"}),
    "Search": ("SearchRequest", {"text", "kind", "scope"}, "Found", {"matches"}),
    "History": ("HistoryRequest", {"artifact", "role", "execution", "since", "batch"}, "Entries", {"entries"}),
    "Snapshot": ("SnapshotRequest", {"signature", "artifacts"}, "Recorded", {"entry"}),
    "Check": ("CheckRequest", set(), "Checked", {"violations", "stale"}),
}


@pytest.mark.parametrize("rpc", sorted(READS))
def test_each_read_the_snapshot_and_the_check_answer_their_result_or_a_refusal(rpc):
    asked, carries, result, gives = READS[rpc]
    method = kb_pb2.DESCRIPTOR.services_by_name["Kb"].methods_by_name[rpc]
    assert (method.input_type.name, method.output_type.name) == (asked, f"{rpc}Response")
    assert _fields(asked) == carries
    assert _fields(result) == gives
    outcome = method.output_type.oneofs_by_name["outcome"]
    assert [(field.name, field.message_type.name) for field in outcome.fields] == [("result", result), ("refusal", "Refusal")]
    assert _fields(f"{rpc}Response") == {"result", "refusal"}


def test_a_read_asks_for_one_level():
    read = kb_pb2.DESCRIPTOR.message_types_by_name["ReadRequest"]
    level = read.oneofs_by_name["level"]
    assert [(field.name, field.message_type.name) for field in level.fields] == [
        ("summary", "Summary"), ("whole", "Whole"), ("section", "Section"),
    ]
    assert set(read.nested_types_by_name["Summary"].fields_by_name) == set()
    assert set(read.nested_types_by_name["Whole"].fields_by_name) == {"depth"}
    assert set(read.nested_types_by_name["Section"].fields_by_name) == {"title"}


def test_the_v0_reads_are_gone():
    methods = kb_pb2.DESCRIPTOR.services_by_name["Kb"].methods_by_name
    assert not {"Refs", "Journal", "Validate"} & set(methods)
    assert _fields("Entry") >= {"actor"} and _fields("Actor") == {"role", "execution"}


def test_the_v0_changes_are_gone():
    methods = kb_pb2.DESCRIPTOR.services_by_name["Kb"].methods_by_name
    assert not {"Write", "Append", "Delete"} & set(methods)
    assert not {"WriteRequest", "AppendRequest", "DeleteRequest"} & set(kb_pb2.DESCRIPTOR.message_types_by_name)
    for rpc, (asked, _, _, _) in CHANGES.items():
        assert "actor" not in _fields(asked)


def test_each_item_an_add_many_adds_names_the_artifact_it_went_to(tmp_path):
    root = tmp_path / "store"
    root.mkdir()
    kb.init(root, "client")
    client = kb_client.connect(root)
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


def _field_type(message, field):
    return kb_pb2.DESCRIPTOR.message_types_by_name[message].fields_by_name[field].message_type.name


@pytest.mark.parametrize("message", ["CreateRequest", "ReplaceRequest", "AddRequest", "RemoveRequest",
                                     "CreateManyRequest", "ReplaceManyRequest", "AddManyRequest",
                                     "RemoveManyRequest", "SnapshotRequest"])
def test_every_change_and_the_snapshot_carry_their_signature_as_a_signature(message):
    assert _field_type(message, "signature") == "Signature"


@pytest.mark.parametrize("message", ["ReadRequest", "FollowRequest", "ReplaceRequest", "AddRequest",
                                     "RemoveRequest", "ReplaceItem", "AddItem", "RemoveItem"])
def test_every_request_naming_an_artifact_or_a_place_does_so_with_a_locator(message):
    assert _field_type(message, "locator") == "Locator"


def test_a_part_is_stubbed_by_its_collection_id_and_title():
    assert _fields("PartStub") == {"collection", "id", "title"}
    assert _field_type("Artifact", "parts") == "PartStub"


@pytest.mark.parametrize("message", ["ReplaceItem", "AddItem", "RemoveItem", "ReplaceRequest", "AddRequest",
                                     "RemoveRequest"])
def test_a_change_may_say_the_revision_it_read_as_a_whole_number(message):
    field = kb_pb2.DESCRIPTOR.message_types_by_name[message].fields_by_name["revision"]
    assert field.type == field.TYPE_INT32


@pytest.mark.parametrize("root", [5, None, b"bytes", ["a"]])
def test_a_root_that_is_neither_text_nor_a_path_is_refused_as_not_started(root, tmp_path, monkeypatch):
    here = tmp_path / "here"
    here.mkdir()
    monkeypatch.chdir(here)
    with pytest.raises(kb.NotStarted) as refused:
        kb.init(root, "client")
    assert [fault.rule for fault in refused.value.faults] == ["root"]
    assert list(here.iterdir()) == []
