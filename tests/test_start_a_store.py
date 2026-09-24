from pathlib import Path

from pytest_bdd import given, scenarios, then, when

from calls import define, read
from kb import client as kb_client
from kb.contract import kb_pb2

scenarios("start-a-store.feature")


@given("an empty directory", target_fixture="root")
def _empty_directory(tmp_path):
    root = tmp_path / "store"
    root.mkdir()
    return root


@when("the client starts a store there", target_fixture="client")
def _start_a_store(root):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root)))
    return client


@then("the store holds the one type that describes what a type is")
def _holds_the_metaschema(client):
    schema = read(client, "schema/schema")
    assert schema.id == "schema/schema"
    assert schema.type == "schema"


@then("the store holds no other type and no content")
def _holds_nothing_else(root):
    store = root / "kb"
    files = sorted(p.relative_to(store) for p in store.rglob("*") if p.is_file() and ".git" not in p.parts)
    assert files == [Path("schema/schema.yaml"), Path("store.yaml")]


@then("the client can define its own types straight away")
def _can_define_a_type(client):
    defined = define(client, {
        "title": "Note",
        "version": 1,
        "schema": {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]},
    })
    assert defined.id == "schema/note"
    assert defined.revision == 1
