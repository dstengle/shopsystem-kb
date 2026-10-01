"""Export and import a store, bound scenario by scenario as each slice comes in. The exported files are the operator's
output, read here as files; the store behind them is read through `held`."""
import re
from pathlib import Path

import pytest

from pytest_bdd import given, parsers, scenario, then, when
from ruamel.yaml import YAML

from calls import CLIENT, DECISION_TYPE, WORK_ITEM_TYPE, create, define
from conftest import _kb
import held
from kb import canonical, client as kb_client
from kb.contract import kb_pb2

FEATURE = "export-and-import-a-store.feature"
IDENTITY = ["id", "type", "schema_version", "revision", "title"]


@scenario(FEATURE, "The operator exports the store to a directory that is empty or does not exist")
def test_the_operator_exports_the_store():
    pass


@scenario(FEATURE, "The operator opens an exported artifact's file")
def test_the_operator_opens_an_exported_file():
    pass


@scenario(FEATURE, "Two stores given the same content by the same client are exported")
def test_two_stores_given_the_same_content_are_exported():
    pass


@scenario(FEATURE, "Exporting to a directory that holds anything is refused")
def test_exporting_to_a_directory_that_holds_anything_is_refused():
    pass


@scenario(FEATURE, "The operator checks a directory for import and each error is reported by file and reason")
def test_each_error_is_reported_by_file_and_reason():
    pass


@scenario(FEATURE, "The operator checks a directory for import that holds a file with an error, and files link to it")
def test_files_linking_to_a_broken_file_would_be_skipped():
    pass


@scenario(FEATURE, "The operator checks a directory for import that holds no error")
def test_a_clean_directory_is_said_to_be_clean():
    pass


@scenario(FEATURE, "A directory checked for import holds an error")
def test_a_directory_holding_an_error_fails_the_check():
    pass


@scenario(FEATURE, "The operator checks a directory for import and the store is left as it was")
def test_checking_leaves_the_store_as_it_was():
    pass


@scenario(FEATURE, "The operator checks a directory for import whose type that describes types differs from the store's")
def test_a_differing_type_of_types_is_an_error():
    pass


def _started(root):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    return client


def _loaded(text):
    """A file as a YAML 1.2 reader other than kb's reads it, its entries in the order written."""
    return YAML(typ="safe", pure=True).load(text)


@given("a store holding a type for decisions, a type for work items, two decisions and a work item")
def _store_with_decisions_and_a_work_item(root):
    client = _started(root)
    define(client, DECISION_TYPE)
    define(client, WORK_ITEM_TYPE)
    for title in ("Price reviews happen weekly", "Prices are reviewed monthly"):
        create(client, "decision", {"title": title, "sections": [
            {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
            {"title": "Rationale", "body": "Costs move weekly.\n"},
        ]})
    create(client, "work-item", {"title": "Move the review to Mondays", "decisions": ["decision/price-reviews-happen-weekly"]})


@given(parsers.parse("a directory for the export that {state}"), target_fixture="target")
def _directory_for_the_export(tmp_path, state):
    target = tmp_path / "exported"
    if state == "is empty":
        target.mkdir()
    return target


@when("the operator exports the store to that directory", target_fixture="ran")
def _kb_export(root, target):
    return _kb("export", str(target), cwd=root)


def _files(target):
    return sorted(str(path.relative_to(target)) for path in Path(target).rglob("*") if path.is_file())


@then("the directory holds one file for each artifact in the store, under a folder named for its kind")
def _one_file_for_each_artifact(ran, root, target):
    assert (ran.returncode, ran.stdout, ran.stderr) == (0, "", "")
    assert _files(target) == sorted(f"{name}.yaml" for name in held.names(root))
    assert {path.parent.name for path in Path(target).rglob("*.yaml")} == {"schema", "decision", "work-item"}


@then("the types' files are under the folder for types")
def _types_under_the_folder_for_types(target):
    assert sorted(path.name for path in (Path(target) / "schema").iterdir()) == [
        "decision.yaml", "schema.yaml", "work-item.yaml",
    ]


@then("each file gives the artifact's identity first, its name, kind, type version, revision and title, and then its content")
def _identity_first(root, target):
    for name in held.names(root):
        written = _loaded((Path(target) / f"{name}.yaml").read_text(encoding="utf-8"))
        assert list(written)[:len(IDENTITY)] == IDENTITY, name
        assert written == held.artifact(root, name)


@then("every file shows the store as it stood at one moment")
def _as_the_store_stood(root, target):
    for name in held.names(root):
        assert (Path(target) / f"{name}.yaml").read_text(encoding="utf-8") == held.text(root, name), name


LONG = (
    "Costs move weekly, so a monthly review leaves prices behind them for up to three weeks at a time, and every "
    "supplier we buy from changes its list on a Monday.\n"
)
LONG_TITLE = "Review on the first working day of each month, after the suppliers have sent their new price lists"


@given(
    "a store holding a decision whose purpose is one short line and which carries a list of options, exported to a "
    "directory",
    target_fixture="target",
)
def _decision_with_options_exported(root, tmp_path):
    client = _started(root)
    define(client, DECISION_TYPE)
    create(client, "decision", {
        "title": "Price reviews happen weekly",
        "sections": [{"title": "Purpose", "body": "Keep prices.\n"}, {"title": "Rationale", "body": LONG}],
        "options": [
            {"title": "Weekly", "body": "Review every Monday.\n"},
            {"title": LONG_TITLE, "body": "Review on the first.\n"},
        ],
    })
    target = tmp_path / "exported"
    ran = _kb("export", str(target), cwd=root)
    assert (ran.returncode, ran.stderr) == (0, ""), ran.stderr
    return target


@when("the operator opens the decision's exported file", target_fixture="opened")
def _open_the_decision(target):
    return (Path(target) / "decision" / "price-reviews-happen-weekly.yaml").read_text(encoding="utf-8")


def _bodies(value):
    """Every piece of prose in a file as read: each value under a `body` key, at any depth."""
    if isinstance(value, dict):
        return [found for key, item in value.items()
                for found in ([item] if key == "body" else _bodies(item))]
    if isinstance(value, list):
        return [found for item in value for found in _bodies(item)]
    return []


@then("every piece of prose stands as a block of its own, however short it is")
def _prose_as_blocks(opened):
    bodies = _bodies(_loaded(opened))
    assert "Keep prices.\n" in bodies and len(bodies) == 4
    assert len(re.findall(r"^ *(?:- )?body: \|\n", opened, re.MULTILINE)) == len(bodies)


@then("each list is written beneath the name it belongs to, indented under it")
def _lists_under_their_names(opened):
    lines = opened.splitlines()
    for key in ("sections", "options"):
        below = lines[lines.index(f"{key}:") + 1]
        assert below.startswith("  - "), (key, below)


@then("no line of prose has been broken to fit a width")
def _no_line_broken(opened):
    assert f"    {LONG.rstrip()}\n" in opened
    assert f"    title: {LONG_TITLE}\n" in opened


@then("nothing in the file tells a reader how to build a value")
def _no_tags(opened):
    assert not re.search(r"(^|[\s\[{,])!", opened)


@given(
    "two stores each given the same decision by the same client, and each exported to a directory of its own",
    target_fixture="targets",
)
def _two_stores_exported(tmp_path):
    targets = []
    for each in ("first", "second"):
        root = tmp_path / each
        root.mkdir()
        client = _started(root)
        define(client, DECISION_TYPE)
        create(client, "decision", {
            "title": "Price reviews happen weekly",
            "sections": [
                {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
                {"title": "Rationale", "body": "Costs move weekly.\n"},
            ],
            "options": [{"title": "Weekly", "body": "Review every Monday.\n"}],
        })
        target = tmp_path / f"{each}-exported"
        ran = _kb("export", str(target), cwd=root)
        assert (ran.returncode, ran.stderr) == (0, ""), ran.stderr
        targets.append(target)
    return targets


@when("the operator compares the two exported decision files", target_fixture="compared")
def _compare_the_decision_files(targets):
    return [(target / "decision" / "price-reviews-happen-weekly.yaml").read_bytes() for target in targets]


@then("the two files are the same, byte for byte")
def _same_bytes(compared):
    first, second = compared
    assert first.startswith(b"id: decision/price-reviews-happen-weekly\n")
    assert first == second


@given("a store holding a decision")
def _store_holding_a_decision(root):
    client = _started(root)
    define(client, DECISION_TYPE)
    create(client, "decision", {"title": "Price reviews happen weekly", "sections": [
        {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
        {"title": "Rationale", "body": "Costs move weekly.\n"},
    ]})


@given("a directory that already holds a file", target_fixture="target")
def _directory_holding_a_file(tmp_path, before):
    target = tmp_path / "exported"
    (target / "decision").mkdir(parents=True)
    (target / "decision" / "price-reviews-happen-weekly.yaml").write_text("notes the export must not write over\n")
    before.update(target=held.everything_in(target))
    return target


@then("the export is rejected because export never overwrites")
def _rejected_as_never_overwriting(ran, target):
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr == f"kb export: refused: root: an export never overwrites; {str(target)!r} already holds something\n"


@then("what the directory holds is left as it was")
def _directory_as_it_was(target, before):
    assert held.everything_in(target) == before["target"]


# The operator's check of a directory for import. Each directory is a real export of a store of its own, then broken
# in the one way a step names; the files are the operator's input, written and read here as files.

WEEKLY = "decision/price-reviews-happen-weekly"
MONTHLY = "decision/prices-are-reviewed-monthly"
MONDAYS = "work-item/move-the-review-to-mondays"


def _for_import(tmp_path, fill=None):
    """A directory for import: the export of a store holding the types for decisions and work items, two decisions and
    a work item linking to the first; or holding what `fill` gives a started store."""
    source = tmp_path / "source"
    source.mkdir()
    if fill is None:
        _store_with_decisions_and_a_work_item(source)
    else:
        fill(_started(source))
    target = tmp_path / "for-import"
    ran = _kb("export", str(target), cwd=source)
    assert (ran.returncode, ran.stderr) == (0, ""), ran.stderr
    return target


def _file(name):
    """The file the export layout gives an artifact's name."""
    return f"{name}.yaml"


def _read(target, name):
    return canonical.entries((Path(target) / _file(name)).read_text(encoding="utf-8"))


def _put(target, artifact):
    """An artifact written as an export writes it, in canonical form, at its place in the layout."""
    path = Path(target) / _file(artifact["id"])
    path.parent.mkdir(exist_ok=True)
    path.write_text(canonical.dump(artifact), encoding="utf-8")


def _artifact(name, title, **content):
    kind = name.partition("/")[0]
    return {"id": name, "type": kind, "schema_version": 1, "revision": 1, "title": title, **content}


def _unreadable(target):
    for name in (WEEKLY, MONTHLY):
        (Path(target) / _file(name)).write_text(f"id: {name}\ntitle: [never closed\n", encoding="utf-8")
    return {_file(WEEKLY): "unreadable", _file(MONTHLY): "unreadable"}


def _not_canonical(target):
    """One file with a comment in it; the other with its title ahead of its name."""
    weekly = Path(target) / _file(WEEKLY)
    weekly.write_text("# reviewed by hand\n" + weekly.read_text(encoding="utf-8"), encoding="utf-8")
    monthly = Path(target) / _file(MONTHLY)
    lines = monthly.read_text(encoding="utf-8").splitlines(keepends=True)
    titled = [line for line in lines if line.startswith("title: ")]
    monthly.write_text("".join(titled + [line for line in lines if line not in titled]), encoding="utf-8")
    return {_file(WEEKLY): "content", _file(MONTHLY): "content"}


def _no_type_for_the_kind(target):
    for name in ("memo/first-memo", "memo/second-memo"):
        _put(target, _artifact(name, name.partition("/")[2].replace("-", " ").capitalize()))
    return {"memo/first-memo.yaml": "kind", "memo/second-memo.yaml": "kind"}


def _not_fitting(target):
    """One decision without the section its type requires second; the other pointing at a number."""
    weekly = _read(target, WEEKLY)
    weekly["sections"] = weekly["sections"][:1]
    _put(target, weekly)
    monthly = _read(target, MONTHLY)
    _put(target, {**{key: monthly[key] for key in IDENTITY}, "supersedes": 5, "sections": monthly["sections"]})
    return {_file(WEEKLY): "sections", _file(MONTHLY): "type"}


def _linking_to_nothing(target):
    mondays = _read(target, MONDAYS)
    _put(target, {**mondays, "decisions": [WEEKLY, "decision/nothing-by-this-name"]})
    _put(target, _artifact("work-item/review-on-fridays", "Review on Fridays", decisions=["decision/nor-this"]))
    return {_file(MONDAYS): "ref", "work-item/review-on-fridays.yaml": "ref"}


FAULTS = {
    "cannot be read as YAML 1.2": _unreadable,
    "is not in canonical form": _not_canonical,
    "claims a kind neither the directory nor the store holds a type for": _no_type_for_the_kind,
    "has content that does not fit its type": _not_fitting,
    "carries a link that lands on nothing in the directory or the store": _linking_to_nothing,
}


@given(
    parsers.parse("a directory for import holding well-formed files and two files that each {fault}"),
    target_fixture="target",
)
def _for_import_with_two_faults(tmp_path, fault, broken):
    target = _for_import(tmp_path)
    broken.update(FAULTS[fault](target))
    return target


@pytest.fixture
def broken():
    """The files a Given broke, each with the rule it breaks."""
    return {}


@when("the operator checks the directory for import", target_fixture="ran")
def _kb_import_check(root, target):
    return _kb("import", str(target), "--check", cwd=root)


def _report(ran):
    """The check's report, one line at a time, each split into its fields."""
    return [line.split("\t") for line in ran.stdout.splitlines()]


@then(parsers.parse("each of the two files is reported as an error, naming the file, with the reason that {reason}"))
def _each_reported_with_its_reason(ran, broken):
    errors = {(line[1], line[2]) for line in _report(ran) if line[0] == "error"}
    assert ran.stderr == ""
    for file, rule in broken.items():
        assert (file, rule) in errors, (file, rule, ran.stdout)


def _the_two_types(client):
    define(client, DECISION_TYPE)
    define(client, WORK_ITEM_TYPE)


def _decision(name, **fields):
    """A decision that fits its type, carrying the fields given."""
    return _artifact(name, name.partition("/")[2].replace("-", " ").capitalize(), **fields, sections=[
        {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
        {"title": "Rationale", "body": "Costs move weekly.\n"},
    ])


def _a_file_with_an_error(target):
    """A decision missing the section its type requires second."""
    broken = _decision("decision/broken")
    broken["sections"] = broken["sections"][:1]
    _put(target, broken)
    return "decision/broken"


def _a_broken_decision_type(target):
    """The type for decisions with a version that is not a number, which the type that describes types refuses."""
    _put(target, {**_read(target, "schema/decision"), "version": "one"})
    return "schema/decision"


def _linking_directly(target, broken):
    _put(target, _decision("decision/linking", supersedes=broken))
    return {"linking": "decision/linking"}


def _linking_through_a_second(target, broken):
    _put(target, _decision("decision/second", supersedes=broken))
    _put(target, _artifact("work-item/first", "First", decisions=["decision/second"]))
    return {"second": "decision/second", "first": "work-item/first"}


def _a_decision_of_the_broken_type(target, broken):
    _put(target, _decision("decision/of-the-type"))
    return {"decision": "decision/of-the-type"}


def _a_work_item_to_a_decision_of_the_broken_type(target, broken):
    _put(target, _decision("decision/of-the-type"))
    _put(target, _artifact("work-item/to-the-decision", "To the decision", decisions=["decision/of-the-type"]))
    return {"decision": "decision/of-the-type", "work item": "work-item/to-the-decision"}


BROKEN = {
    "a file with an error": _a_file_with_an_error,
    "a type for decisions whose content does not fit the type that describes types": _a_broken_decision_type,
}
LINKING = {
    "a file that links to the broken file directly": _linking_directly,
    "a file that links to a second file, which links to the broken file": _linking_through_a_second,
    "a decision, whose link to its own type leads to the broken file": _a_decision_of_the_broken_type,
    "a work item that links to a decision, whose link to its own type leads to the broken file":
        _a_work_item_to_a_decision_of_the_broken_type,
}


@given(
    parsers.re(
        r"a directory for import holding (?P<broken>a file with an error|a type for decisions whose content does not "
        r"fit the type that describes types), and (?P<linking>.+)"
    ),
    target_fixture="target",
)
def _for_import_with_a_broken_file_and_links_to_it(tmp_path, broken, linking, files):
    target = _for_import(tmp_path, _the_two_types)
    files["broken"] = BROKEN[broken](target)
    files.update(LINKING[linking](target, files["broken"]))
    return target


@pytest.fixture
def files():
    """The names of the files a Given put in a directory, by the part each plays."""
    return {}


SKIPPED = {
    "the file that links to it is": [("linking", "broken")],
    "the second file and the first file are": [("second", "broken"), ("first", "second", "broken")],
    "the decision is": [("decision", "broken")],
    "the decision and the work item are": [("decision", "broken"), ("work item", "decision", "broken")],
}


@then(parsers.parse(
    "{skipped} reported as a file that would be skipped, each with the chain of links that leads from it to the "
    "broken file"
))
def _reported_as_skipped(ran, files, skipped):
    reported = {(line[1], line[2]) for line in _report(ran) if line[0] == "skipped"}
    expected = {
        (_file(files[chain[0]]), " -> ".join(_file(files[part]) for part in chain)) for chain in SKIPPED[skipped]
    }
    assert reported == expected, ran.stdout


@given(
    "a directory for import in which every file is well formed, fits its type and links only to what is there",
    target_fixture="target",
)
def _for_import_clean(tmp_path):
    return _for_import(tmp_path)


@given("a directory for import holding one file whose content does not fit its type", target_fixture="target")
def _for_import_with_one_unfit_file(tmp_path):
    target = _for_import(tmp_path)
    weekly = _read(target, WEEKLY)
    weekly["sections"] = weekly["sections"][:1]
    _put(target, weekly)
    return target


@then("the check reports success")
def _check_reports_success(ran, target):
    assert (ran.returncode, ran.stderr) == (0, "")
    assert _report(ran) == [["clean", f"{target} checks clean for import"]]


@then("the check reports failure")
def _check_reports_failure(ran):
    assert (ran.returncode, ran.stderr) == (1, "")
    assert "clean" not in [line[0] for line in _report(ran)], ran.stdout


@given("a directory for import", target_fixture="target")
def _a_directory_for_import(tmp_path, root, before):
    target = _for_import(tmp_path)
    before.update(held=held.holds(root))
    return target


@then("the store holds what it held before")
def _store_as_before(ran, root, before):
    assert ran.returncode in (0, 1), ran.stderr
    assert held.holds(root) == before["held"]


@given("a freshly started store")
def _a_freshly_started_store(root):
    _started(root)


@given(
    "a directory for import holding a copy of the type that describes types that differs from the store's",
    target_fixture="target",
)
def _for_import_with_a_differing_type_of_types(tmp_path):
    """A clean export whose copy of the type that describes types has a field of its own added."""
    target = _for_import(tmp_path)
    copy = _read(target, "schema/schema")
    copy["schema"]["properties"]["owner"] = {"type": "string"}
    _put(target, copy)
    return target


@then("the file holding that copy is reported as an error, naming the file")
def _the_copy_is_an_error(ran):
    assert ran.returncode == 1, ran.stderr
    assert [line[1] for line in _report(ran) if line[0] == "error"] == ["schema/schema.yaml"], ran.stdout
