"""Every rpc of contract v1 and every operator command that needs a store is refused with rule `unreadable`, writing
nothing, whether the store's database is damaged or its marker is a later kb's. The scenarios of
answer-a-damaged-file.feature pin each reason once, with one call; this table pins that no call goes round the
boundary. A call added to the service without a row fails `test_every_rpc_has_a_row`."""
import pytest

import held
from calls import DECISION_TYPE, PROCESS_TYPE, TAG_TYPE, added, create, create_many, created, define, journal
from calls import listing, read, refs, remove, remove_many, removed, replace, replace_many, replaced, request
from calls import search, snapshot, start_a_store, add, add_many, check
from conftest import OPERATOR, _kb
from kb import client as kb_client
from kb.contract import kb_pb2

DECISION = "decision/price-reviews-happen-weekly"
PROCESS = "process/open-the-shop"
SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]
NEW = {"sections": SECTIONS}

RPCS = {
    "Create": lambda c: request(c, "decision", "Close early on Sundays", NEW),
    "Read": lambda c: read(c, DECISION),
    "Check": lambda c: check(c),
    "Replace": lambda c: replace(c, DECISION, NEW),
    "History": lambda c: journal(c),
    "Search": lambda c: search(c, "weekly"),
    "Follow": lambda c: refs(c, DECISION, 1),
    "List": lambda c: listing(c, "decision"),
    "Snapshot": lambda c: snapshot(c, "restock-2026-10-01", [DECISION, PROCESS]),
    "Add": lambda c: add(c, DECISION, "options", {"title": "Go monthly"}),
    "Remove": lambda c: remove(c, DECISION),
    "BatchCreate": lambda c: create_many(c, [created("decision", "Close early on Sundays", NEW)]),
    "BatchReplace": lambda c: replace_many(c, [replaced(DECISION, NEW)]),
    "BatchAdd": lambda c: add_many(c, [added(DECISION, "options", {"title": "Go monthly"})]),
    "BatchRemove": lambda c: remove_many(c, [removed(DECISION)]),
}

COMMANDS = {
    "validate": lambda exported: (["validate"], {}),
    "export": lambda exported: (["export", str(exported.parent / "empty")], {}),
    "import --check": lambda exported: (["import", str(exported), "--check"], {}),
    "import": lambda exported: (["import", str(exported)], {"KB_ACTOR": OPERATOR}),
}

DAMAGES = {"damaged database": held.damage_the_database, "a later kb's marker": held.made_by_a_later_kb}


def test_every_rpc_has_a_row():
    methods = {method.name for method in kb_pb2.DESCRIPTOR.services_by_name["Kb"].methods}
    assert set(RPCS) == methods


@pytest.fixture
def exported(tmp_path):
    """A directory a second, healthy store holding the decision type and a decision was exported to."""
    other = tmp_path / "other"
    other.mkdir()
    client = kb_client.connect(other)
    start_a_store(other)
    define(client, DECISION_TYPE)
    create(client, "decision", {"title": "Prices are reviewed monthly", "sections": SECTIONS})
    exported = tmp_path / "exported"
    ran = _kb("export", str(exported), cwd=other)
    assert (ran.returncode, ran.stderr) == (0, ""), ran.stderr
    (tmp_path / "empty").mkdir()
    return exported


@pytest.fixture
def client(root):
    client = kb_client.connect(root)
    start_a_store(root)
    for type_content in (DECISION_TYPE, PROCESS_TYPE, TAG_TYPE):
        define(client, type_content)
    create(client, "decision", {"title": "Price reviews happen weekly", "sections": SECTIONS})
    create(client, "process", {"title": "Open the shop", "steps": [{"title": "Unlock"}]})
    return client


@pytest.mark.parametrize("damage", DAMAGES)
@pytest.mark.parametrize("rpc", RPCS)
def test_an_rpc_is_refused_as_unreadable_writing_nothing(root, client, rpc, damage):
    DAMAGES[damage](root)
    before = held.bytes_held(root)
    [fault] = RPCS[rpc](client).faults
    assert fault.rule == "unreadable"
    assert held.bytes_held(root) == before


@pytest.mark.parametrize("damage", DAMAGES)
@pytest.mark.parametrize("command", COMMANDS)
def test_a_command_is_refused_as_unreadable_writing_nothing(root, client, exported, command, damage):
    DAMAGES[damage](root)
    before = held.bytes_held(root)
    argv, env = COMMANDS[command](exported)
    ran = _kb(*argv, cwd=root, env=env)
    assert ran.returncode == 2, ran.stderr
    [line] = ran.stderr.splitlines()
    assert line.split(": ", 3)[2] == "unreadable", line
    assert held.bytes_held(root) == before
    assert held.holds_nothing(exported.parent / "empty")
