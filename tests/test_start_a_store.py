import hashlib
import subprocess
from pathlib import Path

import pytest
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


@pytest.fixture
def client(root):
    """A client over the store at root, for the steps that go on to use the store a scenario started."""
    return kb_client.connect(root)


@when("the client starts a store there, saying which role it is", target_fixture="started")
def _start_a_store(client, root):
    return client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))


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


def _everything_under(directory):
    """Every file below a directory, with its bytes, the store's git repository included."""
    return {path: path.read_bytes() for path in sorted(directory.rglob("*")) if path.is_file()}


@given("the client is working inside a store", target_fixture="working_in")
def _working_inside_a_store(tmp_path, monkeypatch):
    working_in = tmp_path / "shop"
    working_in.mkdir()
    kb_client.connect(working_in).Init(kb_pb2.InitRequest(root=str(working_in), actor=CLIENT))
    monkeypatch.chdir(working_in)
    monkeypatch.delenv("KB_ROOT", raising=False)
    return {"root": working_in, "held": _everything_under(working_in)}


@given("an empty directory elsewhere that sits inside no store", target_fixture="root")
def _empty_directory_elsewhere(tmp_path):
    root = tmp_path / "elsewhere"
    root.mkdir()
    return root


@when("the client starts a store in that empty directory, saying which role it is", target_fixture="started")
def _start_a_store_in_the_named_directory(root):
    return kb_client.connect().Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))


@then("the store is made in the directory the client named")
def _made_where_named(started, root):
    assert not started.faults, started.faults
    assert (root / "kb" / "store.yaml").is_file()
    assert (root / "kb" / "schema" / "schema.yaml").is_file()


@then("the store the client was working in is left as it was")
def _working_store_unchanged(working_in):
    assert _everything_under(working_in["root"]) == working_in["held"]


@given("the client has nothing at all to name as the directory to start a store in", target_fixture="here")
def _nothing_to_name(tmp_path, monkeypatch):
    """The client works in an empty directory, so a store made where it works, for want of a name, would show."""
    here = tmp_path / "here"
    here.mkdir()
    monkeypatch.chdir(here)
    monkeypatch.delenv("KB_ROOT", raising=False)
    return {"before": _everything_under(tmp_path)}


@when("the client starts a store naming nothing, saying which role it is", target_fixture="started")
def _start_a_store_naming_nothing():
    return kb_client.connect().Init(kb_pb2.InitRequest(root="", actor=CLIENT))


@then("starting the store is rejected because a store is started in a directory that was named and that exists")
def _rejected_as_named_nothing(started):
    assert [(fault.rule, fault.message) for fault in started.faults] == [
        ("root", "a store is started in a directory that was named and that exists; no directory was named"),
    ]


@then("no store is made anywhere")
def _no_store_anywhere(here, tmp_path):
    assert _everything_under(tmp_path) == here["before"]


@given("a place on the disk where no directory exists", target_fixture="root")
def _a_place_with_no_directory(tmp_path):
    return tmp_path / "nowhere" / "store"


@then("starting the store is rejected because a store is started in a directory that exists")
def _rejected_as_not_there(started, root):
    assert [(fault.rule, fault.message) for fault in started.faults] == [
        ("root", f"a store is started in a directory that exists; {str(root)!r} does not"),
    ]


@then("nothing is made at that place")
def _nothing_made_there(root):
    assert not root.parent.exists()


FILE_TEXT = b"notes the store must not write through\n"


@given("a place on the disk holding a file rather than a directory", target_fixture="root")
def _a_place_holding_a_file(tmp_path):
    root = tmp_path / "store"
    root.write_bytes(FILE_TEXT)
    return root


@then("starting the store is rejected because a store is started in a directory, and what was named is not one")
def _rejected_as_not_a_directory(started, root):
    assert [(fault.rule, fault.message) for fault in started.faults] == [
        ("root", f"a store is started in a directory, and {str(root)!r} is not one"),
    ]


@then("that file is left as it was")
def _file_left_as_it_was(root):
    assert root.read_bytes() == FILE_TEXT


UNRELATED = {"README.md": b"# The shop\n", "src/till.py": b"print('open')\n"}


@given("a directory holding files that have nothing to do with a store", target_fixture="root")
def _directory_holding_other_files(root):
    for name, data in UNRELATED.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_bytes(data)
    return root


@then("the store is made inside that directory, in a place of its own")
def _made_in_a_place_of_its_own(started, root):
    assert not started.faults, started.faults
    assert (root / "kb" / "store.yaml").is_file()
    assert sorted(path.name for path in root.iterdir()) == ["README.md", "kb", "src"]


@then("the files that were already there are left as they were, and none of them is the store's concern")
def _other_files_left_alone(client, root):
    for name, data in UNRELATED.items():
        assert (root / name).read_bytes() == data
    tracked = subprocess.run(
        ["git", "-C", str(root / "kb"), "ls-files"], capture_output=True, text=True, check=True,
    ).stdout.split()
    assert all(not name.startswith("..") for name in tracked), tracked
    checked = client.Validate(kb_pb2.ValidateRequest())
    assert (list(checked.faults), list(checked.violations), list(checked.stale)) == ([], [], [])


@then("starting the store is rejected because that directory already has a store inside it")
def _rejected_as_already_a_store(started, root):
    assert [(fault.rule, fault.message) for fault in started.faults] == [
        ("root", f"a store is never started over another; {str(root)!r} already has a store inside it"),
    ]


@then("starting the store is rejected because that directory is inside a store")
def _rejected_as_inside_a_store(started, root, before):
    assert [(fault.rule, fault.message) for fault in started.faults] == [
        ("root", f"stores do not nest; {str(root)!r} is inside the store at {str(before['store'])!r}"),
    ]
