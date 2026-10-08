"""A seed directory read for a seeded start: the place the start made is passed over wherever it lies below the seed,
and nothing else of the root, nor any other place of that name, is."""
from kb import offers, store, values


def _written(base, *places):
    for place in places:
        file = base / place
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text("title: x\n")


def _read(seed, passed_over):
    return [each.file for each in offers.offered(values.directory(str(seed)), passed_over)]


def test_a_root_two_levels_down_has_only_the_place_it_made_passed_over(tmp_path):
    root = tmp_path / "a" / "b"
    _written(tmp_path, "decision/one.yaml")
    _written(root, f"{store.STAGING}/kb/kb.db", f"{store.STAGING}/kb/marker.yaml")

    assert _read(tmp_path, root / store.STAGING) == ["decision/one.yaml"]


def test_the_other_files_of_the_root_are_read_as_part_of_the_seed(tmp_path):
    root = tmp_path / "r"
    _written(tmp_path, "decision/one.yaml")
    _written(root, "notes.txt", f"{store.STAGING}/kb/kb.db")

    assert _read(tmp_path, root / store.STAGING) == ["decision/one.yaml", "r/notes.txt"]


def test_a_place_of_that_name_that_is_not_the_one_made_is_read_as_any_other(tmp_path):
    _written(tmp_path, f"r/{store.STAGING}/one.yaml", f"s/{store.STAGING}/two.yaml")

    assert _read(tmp_path, tmp_path / "r" / store.STAGING) == [f"s/{store.STAGING}/two.yaml"]
