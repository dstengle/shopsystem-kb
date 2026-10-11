"""An import holds the store's write lock from before it reads the directory until it has landed, so what the store
holds is judged as it stands when the import lands: a client that changes the store while an import is under way waits
for the import, is refused as busy when the import holds the store longer than the store waits, and is never merged
with it. The client's change is made from inside the import's reading of the directory, so it falls in that window
every time. Through the operator's commands beside the contract, and the contract, over stores under the test's
tmp_path."""
from calls import (
    DECISION_TYPE, TYPE_OF_TYPES, WORK_ITEM_TYPE, create, define, iri, replace, request, start_a_store, type_iri,
)
import held
from kb import client as kb_client
from kb import offers, sqlite_store


def _started(root):
    root.mkdir()
    client = kb_client.connect(root)
    start_a_store(root)
    return client


def test_a_change_made_while_an_import_is_under_way_is_never_merged_with_it(tmp_path, monkeypatch):
    define(_started(tmp_path / "source"), WORK_ITEM_TYPE)
    monkeypatch.setenv("KB_ROOT", str(tmp_path / "source"))
    assert not kb_client.export(str(tmp_path / "for-import")).faults
    root = tmp_path / "store"
    client = _started(root)
    monkeypatch.setenv("KB_ROOT", str(root))
    monkeypatch.setattr(sqlite_store, "BUSY", held.WAIT)
    made = []
    reading = offers.offered

    def offered_while_a_client_changes_the_store(directory, *passed_over):
        made.append(request(
            client, "schema", DECISION_TYPE["title"], message="Define Decision",
            content={key: value for key, value in DECISION_TYPE.items() if key != "title"},
        ))
        return reading(directory, *passed_over)
    monkeypatch.setattr(offers, "offered", offered_while_a_client_changes_the_store)

    imported = kb_client.import_(str(tmp_path / "for-import"), "operator")

    assert list(imported.faults) == []
    assert [fault.rule for fault in made[0].faults] == ["busy"]
    assert held.names(root) == sorted([TYPE_OF_TYPES, type_iri("work-item")])


def test_a_change_to_an_artifact_an_import_passes_over_made_while_it_is_under_way_is_refused_and_the_file_passed_over(
    tmp_path, monkeypatch,
):
    """Over a store that already holds artifacts: had the client's change landed before the import compared its files
    with the store, the work item's file would differ from what the store holds and the import be refused."""
    root = tmp_path / "store"
    client = _started(root)
    define(client, WORK_ITEM_TYPE)
    create(client, "work-item", {"title": "Stands alone"})
    monkeypatch.setenv("KB_ROOT", str(root))
    assert not kb_client.export(str(tmp_path / "for-import")).faults
    before, history = held.holds(root), held.history(client)
    monkeypatch.setattr(sqlite_store, "BUSY", held.WAIT)
    made = []
    reading = offers.offered

    def offered_while_a_client_changes_the_store(directory, *passed_over):
        made.append(replace(client, iri("work-item", "stands-alone"), {"decisions": []}))
        return reading(directory, *passed_over)
    monkeypatch.setattr(offers, "offered", offered_while_a_client_changes_the_store)

    imported = kb_client.import_(str(tmp_path / "for-import"), "operator")

    assert (list(imported.faults), list(imported.errors)) == ([], [])
    assert [fault.rule for fault in made[0].faults] == ["busy"]
    assert (held.holds(root), held.history(client)) == (before, history)
