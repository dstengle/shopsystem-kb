"""A directory holding a type's version files offers each, named by its own version's IRI, so none overwrites another
and each is found."""
from kb import canonical, names, offers, roots

TYPE = "https://example.test/kb/type/note"


def _version(number):
    return {"id": TYPE, "type": f"{names.TYPES}@1", "revision": number, "title": "Note", "version": number}


def _written(base, number):
    file = base.joinpath(*names.place(TYPE, number))
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(canonical.dump(_version(number)))


def test_two_version_files_of_one_type_are_offered_each_by_its_own_version(tmp_path):
    _written(tmp_path, 1)
    _written(tmp_path, 2)

    found = offers.offered(roots.directory(str(tmp_path)))

    assert [str(each.name) for each in found] == [names.versioned(TYPE, 1), names.versioned(TYPE, 2)]
    assert [each.artifact["version"] for each in found] == [1, 2]
    assert [str(each.id) for each in found] == [TYPE, TYPE]
