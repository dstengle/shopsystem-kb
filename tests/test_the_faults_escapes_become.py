"""What the servicer's one boundary makes of an exception that escapes the domain, through kb.escapes."""
from pathlib import Path

from kb import escapes, port, store


def test_an_earlier_kbs_store_is_told_to_import_the_directory_holding_its_files():
    fault = escapes.fault(store.EarlierKb(Path("/shop")))
    assert fault.rule == "unreadable"
    assert fault.message.endswith("start a new store and import the old one's files, from /shop/kb")


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
