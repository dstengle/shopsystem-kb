"""What `kb.export` gives of a store, through the module's public functions over the store opened: its files as a
sequence, the same the operator's export writes, byte for byte, and the position they reflect, the entry landed
last, whatever the moments the entries were stamped with (the plan's decision 3)."""
from datetime import datetime, timedelta, timezone

from calls import DECISION_TYPE, TAG_TYPE, change_type, create, define, journal, start_a_store
from kb import client as kb_client
from kb import export
from kb import store as stores

NOON = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)
SECTIONS = [{"title": "Purpose", "body": "Keep prices in step.\n"}, {"title": "Rationale", "body": "Costs move.\n"}]


class GoingBack:
    """A clock that reads an hour earlier each time it is read."""

    def __init__(self):
        self.at = NOON

    def __call__(self):
        self.at -= timedelta(hours=1)
        return self.at


def test_the_position_is_the_entry_landed_last_when_the_clock_goes_back(root):
    clock = GoingBack()
    start_a_store(root, clock)
    client = kb_client.connect(root, clock=clock)
    define(client, TAG_TYPE)
    create(client, "tag", {"title": "First"})
    last = create(client, "tag", {"title": "Landed last"})
    [landed] = journal(client, artifact=last.id).entries
    assert journal(client).entries[0].id == landed.id  # the earliest moment in the history is the last landed
    with stores.opened(root) as held:
        assert export.Position(landed.id) == list(export.taken(held))[-1]


def test_the_operators_export_writes_exactly_the_files_given_byte_for_byte(root, tmp_path, monkeypatch):
    start_a_store(root)
    client = kb_client.connect(root)
    define(client, DECISION_TYPE)
    define(client, TAG_TYPE)
    create(client, "decision", {"title": "Price reviews happen weekly", "sections": SECTIONS})
    create(client, "tag", {"title": "Kept"})
    assert not change_type(client, "tag", {**TAG_TYPE["schema"], "description": "A second version."}).faults
    monkeypatch.chdir(root)
    directory = tmp_path / "exported"
    assert kb_client.export(str(directory)).faults == []
    with stores.opened(root) as held:
        given = list(export.files(held))
    on_disk = {
        file.relative_to(directory).as_posix(): file.read_bytes() for file in directory.rglob("*") if file.is_file()
    }
    assert {file.place: file.text.encode("utf-8") for file in given} == on_disk
    assert sorted(file.place for file in given) == [
        "missingmass.io/kb/type@1.yaml", "shop.example/kb/decision/price-reviews-happen-weekly.yaml",
        "shop.example/kb/decision@1.yaml", "shop.example/kb/tag/kept.yaml", "shop.example/kb/tag@1.yaml",
        "shop.example/kb/tag@2.yaml",
    ]
