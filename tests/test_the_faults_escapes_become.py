"""What the servicer's one boundary makes of an exception that escapes the domain, through kb.escapes."""
from pathlib import Path

import pytest

import held
from kb import escapes, port, store


def test_an_earlier_kbs_store_is_one_this_kb_can_neither_read_nor_move():
    fault = escapes.fault(store.EarlierKb(Path("/shop")))
    assert (fault.rule, fault.message) == (
        "unreadable", "the store at /shop was made by an earlier version of kb, which this kb cannot read or move",
    )
    assert "import" not in fault.message


def test_a_later_kbs_store_is_told_a_later_kb_is_needed():
    fault = escapes.fault(store.LaterKb(Path("/shop")))
    assert (fault.rule, fault.message.split(";")[0]) == (
        "unreadable", "the store at /shop was made by a later version of kb, which is needed to read it",
    )


def test_a_database_that_cannot_be_read_is_named():
    fault = escapes.fault(port.Unreadable("/shop/kb/store.sqlite3: file is not a database"))
    assert (fault.rule, fault.message) == (
        "unreadable", "the store's database cannot be read: /shop/kb/store.sqlite3: file is not a database",
    )


def test_a_marker_whose_form_only_equals_this_kbs_as_a_number_is_a_later_kbs(root):
    from calls import listing, start_a_store
    from kb import client as kb_client
    client = kb_client.connect(root)
    start_a_store(root)
    for written in ("store: true\n", "store: 1.0\n"):
        (root / "kb" / "store.yaml").write_text(written, encoding="utf-8")
        listed = listing(client, "schema")
        assert [fault.rule for fault in listed.faults] == ["unreadable"], written


@pytest.mark.parametrize("found", ["upward", "KB_ROOT"])
def test_a_store_made_before_contract_v2_is_refused_the_same_however_it_is_found(root, tmp_path, monkeypatch, found):
    from calls import listing, start_a_store
    from conftest import _kb
    from kb import client as kb_client
    start_a_store(root)
    held.made_before_contract_v2(root)
    before = held.bytes_held(root)
    outside = tmp_path / "outside"
    outside.mkdir()
    monkeypatch.chdir(root if found == "upward" else outside)
    env = {} if found == "upward" else {"KB_ROOT": str(root)}
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    refusal = f"the store at {root} was made by an earlier version of kb, which this kb cannot read or move"
    listed = listing(kb_client.connect(), "schema")
    assert [(fault.rule, fault.message) for fault in listed.faults] == [("unreadable", refusal)]
    checked = _kb("validate", cwd=Path.cwd(), env=env)
    assert (checked.returncode, checked.stdout) == (2, "")
    assert checked.stderr == f"kb validate: refused: unreadable: {refusal}\n"
    assert held.bytes_held(root) == before
