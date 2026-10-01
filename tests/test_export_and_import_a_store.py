"""Export and import a store, bound scenario by scenario as each slice comes in. The exported files are the operator's
output, read here as files; the store behind them is read through `held`."""
import re
from pathlib import Path

import pytest

from pytest_bdd import given, parsers, scenario, then, when
from ruamel.yaml import YAML

from calls import CLIENT, DECISION_TYPE, WORK_ITEM_TYPE, create, define, journal, next_version, write
from conftest import OPERATOR, _kb
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
def _a_freshly_started_store(root, before):
    _started(root)
    before.update({"started": held.holds(root), "type of types": held.text(root, "schema/schema")})


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


# The operator's import of a directory into a freshly started store. Each directory is, as for the check, a real
# export of a store of its own, broken where a step says; the store imported into is read through `held` and its
# history through the contract.

@scenario(
    FEATURE,
    "The operator imports a directory that checks clean into a freshly started store, saying which role they are",
)
def test_a_clean_directory_lands_as_one_signed_set():
    pass


def _exported_names(target):
    """The name of every artifact a directory for import holds but the type that describes types, sorted."""
    files = [path.relative_to(target) for path in Path(target).glob("*/*.yaml")]
    return sorted(
        str(file.with_suffix("")) for file in files
        if file != Path("schema/schema.yaml") and file.parts[0] not in ("journal", ".git")
    )


def _decision_at_revision_three(client):
    """The type for decisions moved on to version 2, then a decision written against it and changed twice."""
    define(client, DECISION_TYPE)
    next_version(client, "decision", DECISION_TYPE)
    content = {"title": "Price reviews happen weekly", "sections": [
        {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
        {"title": "Rationale", "body": "Costs move weekly.\n"},
    ]}
    create(client, "decision", content)
    for body in ("Costs move every week.\n", "Costs move weekly, and so do we.\n"):
        content["sections"][1]["body"] = body
        assert not write(client, WEEKLY, {key: value for key, value in content.items() if key != "title"}).faults


@given(
    "a directory for import that checks clean, holding a type for decisions and a decision at revision 3 written "
    "against version 2 of the decision type",
    target_fixture="target",
)
def _for_import_with_a_decision_at_revision_three(tmp_path):
    target = _for_import(tmp_path, _decision_at_revision_three)
    weekly = _read(target, WEEKLY)
    assert (weekly["revision"], weekly["schema_version"]) == (3, 2), weekly
    return target


@when("the operator imports the directory, saying which role they are", target_fixture="ran")
def _kb_import(root, target):
    return _kb("import", str(target), cwd=root, env={"KB_ACTOR": OPERATOR})


def _imported(root):
    """The entries an import left in the store's history: every entry after its starting one."""
    entries = held.history(kb_client.connect(root))
    assert entries[0].message == "initialise store", entries[0]
    return entries[1:]


@then("everything in the directory lands as one set, signed by that role, with a message naming the directory")
def _lands_as_one_signed_set(ran, root, target):
    assert (ran.returncode, ran.stderr) == (0, "")
    assert held.names(root) == sorted([*_exported_names(target), "schema/schema"])
    entries = _imported(root)
    assert sorted(entry.artifact for entry in entries) == _exported_names(target)
    assert {(entry.batch, entry.actor.role, entry.message) for entry in entries} == {
        (entries[0].batch, OPERATOR, f"import {target}"),
    }


def _identity(artifact):
    return {key: artifact[key] for key in IDENTITY}


@then(
    "the decision lands under the same name and title, at revision 3, written against version 2 of the decision type"
)
def _the_decision_lands_as_it_was(root, target):
    landed = held.artifact(root, WEEKLY)
    assert _identity(landed) == {**_identity(_read(target, WEEKLY)), "revision": 3, "schema_version": 2}
    assert held.text(root, WEEKLY) == (Path(target) / _file(WEEKLY)).read_text(encoding="utf-8")


@then(
    "the type for decisions lands under the same name and title, at the revision and type version the directory gives "
    "it"
)
def _the_type_lands_as_it_was(root, target):
    assert held.text(root, "schema/decision") == (Path(target) / "schema/decision.yaml").read_text(encoding="utf-8")
    assert held.artifact(root, "schema/decision")["revision"] == 2


@scenario(
    FEATURE,
    "The operator imports a directory that checks clean, and the history shows each type landing before its artifacts",
)
def test_each_type_lands_before_its_artifacts():
    pass


@given(
    "a directory for import that checks clean, holding a type for decisions, a type for work items, two decisions and "
    "a work item",
    target_fixture="target",
)
def _for_import_with_two_types(tmp_path):
    return _for_import(tmp_path)


@then(
    "the store's history holds its starting entry followed by one import entry for each of the five artifacts, and "
    "nothing else"
)
def _one_import_entry_each(ran, root):
    assert (ran.returncode, ran.stderr) == (0, "")
    entries = _imported(root)
    assert sorted(entry.artifact for entry in entries) == sorted(
        ["schema/decision", "schema/work-item", WEEKLY, MONTHLY, MONDAYS],
    )
    assert {entry.op for entry in entries} == {"import"}


@then("in the history each type's import entry comes before the import entries of the artifacts of its kind")
def _types_first(root):
    landed = [entry.artifact for entry in _imported(root)]
    for kind in ("decision", "work-item"):
        of_kind = [index for index, name in enumerate(landed) if name.startswith(f"{kind}/")]
        assert of_kind and landed.index(f"schema/{kind}") < min(of_kind), landed


@scenario(FEATURE, "Importing a directory that holds an error is refused")
def test_importing_a_directory_holding_an_error_is_refused():
    pass


@then("the import is rejected because the check found errors")
def _rejected_as_the_check_found_errors(ran):
    assert ran.returncode == 2
    assert ran.stderr == (
        "kb import: refused: content: the check found 1 error(s) in the directory, and nothing was written\n"
    )


@then("the operator is shown the check's report")
def _shown_the_report(ran, root, target):
    assert ["error", _file(WEEKLY), "sections"] in [line[:3] for line in _report(ran)], ran.stdout
    assert ran.stdout == _kb("import", str(target), "--check", cwd=root).stdout


@then("nothing is written")
def _nothing_written(root, before):
    assert held.holds(root) == before["started"]


@scenario(FEATURE, "The operator imports with errors skipped")
def test_importing_with_errors_skipped():
    pass


STANDALONE = "work-item/stands-alone"


def _with_an_error_and_one_linking(target):
    _a_file_with_an_error(target)
    _linking_directly(target, "decision/broken")
    return {"decision/broken": "error", "decision/linking": "decision/linking -> decision/broken"}


def _with_an_error_and_two_linking(target):
    left_out = _with_an_error_and_one_linking(target)
    _put(target, _decision("decision/onward", supersedes="decision/linking"))
    return {**left_out, "decision/onward": "decision/onward -> decision/linking -> decision/broken"}


def _with_a_broken_type_and_a_decision(target):
    _a_broken_decision_type(target)
    _put(target, _decision("decision/of-the-type"))
    return {"schema/decision": "error", "decision/of-the-type": "decision/of-the-type -> schema/decision"}


TOGETHER_WITH = {
    "a type for decisions, a decision with an error and a decision that links to it": _with_an_error_and_one_linking,
    "a type for decisions, a decision with an error, a decision that links to it, and a decision that links to that "
    "one": _with_an_error_and_two_linking,
    "a type for decisions whose content does not fit the type that describes types, and a decision":
        _with_a_broken_type_and_a_decision,
}


@given(
    parsers.parse(
        "a directory for import holding a type for work items and a work item that leads to no broken file, together "
        "with {broken}"
    ),
    target_fixture="target",
)
def _for_import_with_errors_to_skip(tmp_path, broken, files):
    target = _for_import(tmp_path, _the_two_types)
    _put(target, _artifact(STANDALONE, "Stands alone"))
    files.update(TOGETHER_WITH[broken](target))
    return target


@when("the operator imports the directory with errors skipped, saying which role they are", target_fixture="ran")
def _kb_import_skipping_errors(root, target):
    return _kb("import", str(target), "--skip-errors", cwd=root, env={"KB_ACTOR": OPERATOR})


@then("the type for work items and the work item land")
def _the_work_item_lands(ran, root, target):
    assert (ran.returncode, ran.stderr) == (0, "")
    for name in ("schema/work-item", STANDALONE):
        assert held.text(root, name) == (Path(target) / _file(name)).read_text(encoding="utf-8")


LEFT_OUT = {
    "the decision with an error and the decision that links to it": ["decision/broken", "decision/linking"],
    "the three decisions": ["decision/broken", "decision/linking", "decision/onward"],
    "the type for decisions and the decision": ["schema/decision", "decision/of-the-type"],
}


@then(parsers.parse("{left_out} do not land"))
def _left_out(root, target, files, left_out):
    assert sorted(LEFT_OUT[left_out]) == sorted(files)
    landing = sorted(set(_exported_names(target)) - set(files))
    assert held.names(root) == sorted([*landing, "schema/schema"])
    assert sorted(entry.artifact for entry in _imported(root)) == landing


@then("the operator is told what was skipped and why")
def _told_what_was_skipped(ran, files):
    told = {
        line[1]: "error" if line[0] == "error" else line[2] for line in _report(ran) if line[0] in ("error", "skipped")
    }
    assert told == {
        _file(name): " -> ".join(_file(part) for part in why.split(" -> ")) if why != "error" else why
        for name, why in files.items()
    }, ran.stdout


@scenario(FEATURE, "Importing into a store that holds an artifact besides the type that describes types is refused")
def test_importing_into_a_store_that_is_not_fresh_is_refused():
    pass


@given("a store that has been given a type for decisions since it was started")
def _store_given_a_type(root, before):
    define(_started(root), DECISION_TYPE)
    before.update(started=held.holds(root))


@given("a directory for import that checks clean", target_fixture="target")
def _for_import_that_checks_clean(tmp_path):
    return _for_import(tmp_path, lambda client: define(client, WORK_ITEM_TYPE))


@then("the import is rejected because import goes only into a freshly started store")
def _rejected_as_not_fresh(ran, root, before):
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr == (
        "kb import: refused: store: import goes only into a freshly started store; this one holds 1 artifact(s) "
        "besides the type that describes types\n"
    )
    assert held.holds(root) == before["started"]


@scenario(FEATURE, "The operator imports the kb directory of an existing store")
def test_importing_the_kb_directory_of_an_existing_store():
    pass


PASSED_OVER = {
    ".git/HEAD": b"ref: refs/heads/main\n",
    ".git/objects/ab/cdef": b"\x78\x9c\x00\x01",
    "journal/20260924T120000000000Z-1.yaml": b"id: 20260924T120000000000Z-1\nop: create\n",
    "store.yaml": b"contract: '0.1'\n",
    "store.sqlite3": b"SQLite format 3\x00\x10\x00",
    "store.sqlite3-wal": b"\x37\x7f\x06\x82",
    "store.sqlite3-shm": b"\x00\x00",
}


@given(
    "the kb directory of an existing store, holding its types and artifacts, which check clean, together with its "
    "history and its store marker",
    target_fixture="target",
)
def _the_kb_directory_of_a_store(tmp_path):
    """An export laid out as a store's kb directory is: the files of its types and artifacts, beside them the history
    an old store kept in git and in `journal/`, and the marker and database files a store keeps."""
    target = _for_import(tmp_path)
    for file, data in PASSED_OVER.items():
        (target / file).parent.mkdir(parents=True, exist_ok=True)
        (target / file).write_bytes(data)
    return target


@when("the operator imports that kb directory, saying which role they are", target_fixture="ran")
def _kb_import_the_kb_directory(root, target):
    return _kb_import(root, target)


@then("its types and artifacts land as they would from an export")
def _land_as_from_an_export(ran, root, target):
    assert (ran.returncode, ran.stdout, ran.stderr) == (0, "", "")
    names = _exported_names(target)
    assert held.names(root) == sorted([*names, "schema/schema"])
    for name in names:
        assert held.text(root, name) == (Path(target) / _file(name)).read_text(encoding="utf-8"), name


@then("its history and its store marker are passed over, neither landing in the store")
def _history_and_marker_passed_over(root, target, before):
    assert sorted(entry.artifact for entry in _imported(root)) == _exported_names(target)
    assert not any(name.startswith(("journal/", ".git/", "store")) for name in held.names(root))
    assert held.holds(root)["marker"] == before["started"]["marker"]


@scenario(FEATURE, "Importing when nothing names the operator's role is refused")
def test_importing_without_a_role_is_refused():
    pass


@given("a freshly started store, and nothing names which role the operator is")
def _a_freshly_started_store_and_no_role(root, before):
    _a_freshly_started_store(root, before)


@when("the operator imports the directory", target_fixture="ran")
def _kb_import_without_a_role(root, target):
    return _kb("import", str(target), cwd=root)


@then("the import is rejected because the role must be named through KB_ACTOR")
def _rejected_without_kb_actor(ran):
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr == "kb import: refused: actor: an import lands only under a role, named through KB_ACTOR\n"


@scenario(FEATURE, "kb export and kb import find the store as kb validate does, with the same refusals")
def test_export_and_import_find_the_store_as_validate_does():
    pass


@given(
    "a freshly started store, with the operator working in a folder deep inside the directory it sits in",
    target_fixture="where",
)
def _fresh_and_working_deep_inside(root):
    _started(root)
    deep = root / "notes" / "2026" / "september"
    deep.mkdir(parents=True)
    return {"cwd": deep, "env": {}}


@given(
    "a freshly started store, with the operator working outside any store and KB_ROOT naming that one",
    target_fixture="where",
)
def _fresh_and_named_from_outside(root, tmp_path):
    _started(root)
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    return {"cwd": outside, "env": {"KB_ROOT": str(root)}}


@when("the operator runs kb export to an empty directory there", target_fixture="ran")
def _kb_export_there(where, tmp_path):
    target = tmp_path / "exported"
    target.mkdir()
    where["target"] = target
    return _kb("export", str(target), cwd=where["cwd"], env=where["env"])


@when(
    "the operator runs kb import of a directory that checks clean, saying which role they are there",
    target_fixture="ran",
)
def _kb_import_there(where, tmp_path):
    where["target"] = _for_import(tmp_path)
    return _kb("import", str(where["target"]), cwd=where["cwd"], env={**where["env"], "KB_ACTOR": OPERATOR})


@then("the store found above where they are working is the one exported")
@then("the store KB_ROOT names is the one exported")
def _that_store_exported(ran, root, where):
    assert (ran.returncode, ran.stdout, ran.stderr) == (0, "", "")
    assert _files(where["target"]) == sorted(f"{name}.yaml" for name in held.names(root))


@then("the store found above where they are working is the one imported into")
@then("the store KB_ROOT names is the one imported into")
def _that_store_imported_into(ran, root, where):
    assert (ran.returncode, ran.stdout, ran.stderr) == (0, "", "")
    assert held.names(root) == sorted([*_exported_names(where["target"]), "schema/schema"])


@then(parsers.parse(
    "the {command} is rejected because no store was found, neither above where they are working nor named outright"
))
def _rejected_as_no_store(ran, where, command):
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr == (
        f"kb {command}: refused: store: no store was found, neither above {where['cwd']} nor named outright\n"
    )


@then(parsers.parse("the {command} is rejected because KB_ROOT names a directory that holds no store"))
def _rejected_as_kb_root_names_no_store(ran, where, command):
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr == (
        f"kb {command}: refused: store: KB_ROOT names a directory that holds no store: {where['env']['KB_ROOT']}\n"
    )


@then(parsers.parse(
    "the {command} is rejected because KB_ROOT names a store other than the one they are standing in, and neither of "
    "the two is guessed at"
))
def _rejected_as_two_stores(ran, where, command):
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr == (
        f"kb {command}: refused: store: KB_ROOT names a store other than the one {where['cwd']} is working in: "
        f"KB_ROOT is {where['env']['KB_ROOT']}, the working directory is inside {where['cwd']}; neither is guessed at\n"
    )


@scenario(FEATURE, "Importing with errors skipped when nothing would land is refused")
def test_importing_with_errors_skipped_when_nothing_would_land_is_refused():
    pass


@given("a directory for import in which every file has an error", target_fixture="target")
def _for_import_all_broken(tmp_path):
    """The export of a store holding the types for decisions and work items, the decisions and the work item, each
    file then broken: the type for decisions given a version that is not a number, the type for work items, the
    decisions and the work item made unreadable, and the copy of the type that describes types given a field of its
    own."""
    target = _for_import(tmp_path)
    _a_broken_decision_type(target)
    for name in ("schema/work-item", WEEKLY, MONTHLY, MONDAYS):
        (Path(target) / _file(name)).write_text(f"id: {name}\ntitle: [never closed\n", encoding="utf-8")
    copy = _read(target, "schema/schema")
    copy["schema"]["properties"]["owner"] = {"type": "string"}
    _put(target, copy)
    return target


@then("the import is rejected because nothing would land")
def _rejected_as_nothing_would_land(ran):
    assert ran.returncode == 2
    assert {line[1] for line in _report(ran) if line[0] == "error"} == {
        _file(name) for name in ("schema/schema", "schema/decision", "schema/work-item", WEEKLY, MONTHLY, MONDAYS)
    }, ran.stdout
    assert ran.stderr == (
        "kb import: refused: operations: nothing in the directory would land, and nothing was written\n"
    )


@scenario(FEATURE, "The operator imports a directory whose type that describes types matches the store's")
def test_a_matching_type_of_types_is_passed_over():
    pass


@given(
    "a directory for import that checks clean, holding a copy of the type that describes types that matches the "
    "store's",
    target_fixture="target",
)
def _for_import_with_a_matching_type_of_types(tmp_path, root):
    target = _for_import(tmp_path, lambda client: define(client, DECISION_TYPE))
    assert (Path(target) / "schema/schema.yaml").read_text(encoding="utf-8") == held.text(root, "schema/schema")
    return target


@then("the directory's copy of the type that describes types is passed over")
def _the_copy_is_passed_over(ran, root):
    assert (ran.returncode, ran.stdout, ran.stderr) == (0, "", "")
    assert [entry.artifact for entry in _imported(root)] == ["schema/decision"]


@then("the store's type that describes types is kept as it was")
def _the_type_of_types_kept(root, before):
    assert held.text(root, "schema/schema") == before["type of types"]
    entries = journal(kb_client.connect(root), artifact="schema/schema").entries
    assert [(entry.op, entry.message) for entry in entries] == [("create", "initialise store")]


def test_an_artifact_written_before_its_type_reordered_its_fields_exports_in_the_order_its_type_now_declares(
    tmp_path, monkeypatch,
):
    def typed(order, version):
        fields = {name: {"type": "string"} for name in ["title", *order]}
        return {"version": version, "schema": {"type": "object", "properties": fields, "required": ["title"]}}

    source, target, exported = (tmp_path / each for each in ("source", "target", "exported"))
    for root in (source, target):
        root.mkdir()
        kb_client.connect(root).Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    client = kb_client.connect(source)
    define(client, {"title": "Note", **typed(["a", "b"], 1)})
    create(client, "note", {"title": "X", "b": "second", "a": "first"})
    write(client, "schema/note", typed(["b", "a"], 2))
    assert list(client.Validate(kb_pb2.ValidateRequest()).violations) == []
    monkeypatch.setenv("KB_ROOT", str(source))
    assert kb_client.export(str(exported)).faults == []
    text = (exported / "note" / "x.yaml").read_text(encoding="utf-8")
    assert list(_loaded(text)) == [*IDENTITY, "b", "a"]
    assert (_loaded(text)["schema_version"], _loaded(text)["revision"]) == (1, 1)
    monkeypatch.setenv("KB_ROOT", str(target))
    checked = kb_client.import_check(str(exported))
    assert (checked.faults, list(checked.errors), list(checked.skipped)) == ([], [], [])
    assert kb_client.import_(str(exported), OPERATOR).faults == []
    assert held.artifact(target, "note/x")["b"] == "second"


@scenario(
    FEATURE,
    'Exporting to something that is a file, not a directory, is refused',
)
def test_exporting_to_something_that_is_a_file_not_a_directory_is_refused():
    pass


@scenario(
    FEATURE,
    'Checking for import something that is not a directory is refused',
)
def test_checking_for_import_something_that_is_not_a_directory_is_refused():
    pass


@scenario(
    FEATURE,
    'Importing from something that is not a directory is refused',
)
def test_importing_from_something_that_is_not_a_directory_is_refused():
    pass


@scenario(
    FEATURE,
    'An import that waits longer than the store waits for another change is refused as busy',
)
def test_an_import_that_waits_longer_than_the_store_waits_for_another_change_is():
    pass


@scenario(
    FEATURE,
    'The operator exports the store while another change is being written',
)
def test_the_operator_exports_the_store_while_another_change_is_being_written():
    pass
