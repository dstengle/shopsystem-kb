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
