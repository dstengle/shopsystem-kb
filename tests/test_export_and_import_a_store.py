"""Export and import a store, bound scenario by scenario as each slice comes in. The exported files are the operator's
output, read here as files; the store behind them is read through `held`."""
import re
from pathlib import Path

from pytest_bdd import given, parsers, scenario, then, when
from ruamel.yaml import YAML

from calls import CLIENT, DECISION_TYPE, WORK_ITEM_TYPE, create, define
from conftest import _kb
import held
from kb import client as kb_client
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
