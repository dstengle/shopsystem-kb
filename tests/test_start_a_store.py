import hashlib
import subprocess
from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when

from calls import CLIENT, define, read
from kb import canonical, client as kb_client
from kb.contract import kb_pb2

scenarios("start-a-store.feature")


@given("an empty directory", target_fixture="root")
def _empty_directory(tmp_path):
    root = tmp_path / "store"
    root.mkdir()
    return root


@when("the client starts a store there, saying which role it is", target_fixture="client")
def _start_a_store(root):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
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
    assert [f for f in files if f.parts[0] != "journal"] == [Path("schema/schema.yaml"), Path("store.yaml")]


@then("the client can define its own types straight away")
def _can_define_a_type(client):
    defined = define(client, {
        "title": "Note",
        "version": 1,
        "schema": {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]},
    })
    assert defined.id == "schema/note"
    assert defined.revision == 1


@then(
    parsers.parse('the store\'s history holds one entry, under that role, with the message "{message}"'),
    target_fixture="entry",
)
def _one_entry_under_the_role(root, message):
    entries = sorted((root / "kb" / "journal").rglob("*.yaml"))
    assert len(entries) == 1, entries
    entry = canonical.load(entries[0].read_text())
    assert (entry["actor"]["role"], entry["message"]) == ("client", message)
    log = subprocess.run(
        ["git", "-C", str(root / "kb"), "log", "--format=%an%x09%s"], capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    assert log == [f"client\t{message}"]
    return entry


@then(
    "that entry is the writing of the one type that describes what a type is, at its first version, "
    "with a fingerprint of what was written"
)
def _the_entry_is_the_metaschema_write(root, entry):
    assert (entry["op"], entry["artifact"], entry["path"], entry["revision"]) == ("create", "schema/schema", "", 1)
    assert entry["digest"] == hashlib.sha256((root / "kb" / "schema" / "schema.yaml").read_bytes()).hexdigest()


@when("the client starts a store there without saying which role it is", target_fixture="refused")
def _start_a_store_without_a_role(root):
    return kb_client.connect(root).Init(kb_pb2.InitRequest(root=str(root)))


@then("starting the store is rejected because a store can only be started under a role")
def _rejected_without_a_role(refused):
    assert [(fault.rule, fault.message) for fault in refused.faults] == [
        ("actor", "a store can only be started under a role"),
    ]


@then("that directory holds no store")
def _no_store_there(root):
    assert not (root / "kb").exists()
    assert list(root.iterdir()) == []
