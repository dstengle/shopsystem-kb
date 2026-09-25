import os
import re
import subprocess
import sys
from pathlib import Path

from pytest_bdd import given, scenarios, then, when

from calls import CLIENT, DECISION_TYPE, create, define, next_version
from kb import canonical, client as kb_client
from kb.contract import kb_pb2

scenarios("look-after-a-store.feature")

LONG_LINE = (
    "Costs move weekly, and a review that runs once a month lags them by three weeks on average, "
    "which is long enough to lose money on every shelf in the shop."
)


@given(
    "a store holding a decision whose purpose is one short line and which carries a list of options",
    target_fixture="decision_file",
)
def _store_with_a_short_decision(root):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, DECISION_TYPE)
    created = create(client, "decision", {
        "title": "Price reviews happen weekly",
        "sections": [
            {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
            {"title": "Rationale", "body": LONG_LINE + "\n"},
        ],
        "options": [
            {"title": "Keep weekly", "body": "Review every Monday."},
            {"title": "Go monthly", "body": "Review on the first of the month."},
        ],
    })
    return root / "kb" / f"{created.id}.yaml"


@when("the operator opens the decision's file", target_fixture="text")
def _open_the_file(decision_file):
    return decision_file.read_text()


@then("every piece of prose stands as a block of its own, however short it is")
def _prose_as_blocks(text):
    bodies = re.findall(r"^\s*body: (.*)$", text, re.M)
    assert len(bodies) == 4, text
    assert all(marker in ("|", "|-") for marker in bodies), text


@then("each list is written beneath the name it belongs to, indented under it")
def _lists_indented(text):
    assert re.search(r"^sections:\n  - title: Purpose$", text, re.M), text
    assert re.search(r"^options:\n  - id: keep-weekly$", text, re.M), text


@then("no line of prose has been broken to fit a width")
def _no_folding(text):
    assert ("\n      " + LONG_LINE + "\n") in text, text


@then("nothing in the file tells a reader how to build a value")
def _no_tags(text):
    assert not re.search(r"\s!\S", text), text


SAME_DECISION = {
    "title": "Price reviews happen weekly",
    "sections": [
        {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
        {"title": "Rationale", "body": "Costs move weekly.\n"},
    ],
    "options": [{"title": "Keep weekly", "body": "Review every Monday."}],
}


@given("two stores each given the same decision by the same client", target_fixture="files")
def _two_stores_with_the_same_decision(tmp_path):
    files = []
    for name in ("one", "two"):
        root = tmp_path / name
        root.mkdir()
        client = kb_client.connect(root)
        client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
        define(client, DECISION_TYPE)
        created = create(client, "decision", SAME_DECISION)
        files.append(root / "kb" / f"{created.id}.yaml")
    return files


@when("the operator compares the two decision files", target_fixture="comparison")
def _compare_the_files(files):
    return [path.read_bytes() for path in files]


@then("the two files are the same, byte for byte")
def _the_same_bytes(comparison):
    assert comparison[0] == comparison[1]
    assert len(comparison[0]) > 0


KB = Path(sys.executable).with_name("kb")
OPERATOR = "operator"


def _kb(*args, cwd, env=None):
    """kb's own console command, run as the operator runs it: in a directory, with KB_ROOT and KB_ACTOR set only when
    a step sets them."""
    clean = {key: value for key, value in os.environ.items() if key not in ("KB_ROOT", "KB_ACTOR")}
    return subprocess.run([str(KB), *args], cwd=cwd, env={**clean, **(env or {})}, capture_output=True, text=True)


@given("a directory that has no store inside it", target_fixture="root")
@given("a directory that has no store inside it, and nothing names which role the operator is", target_fixture="root")
def _directory_with_no_store(root):
    return root


@when("the operator runs kb init against that directory, saying which role they are", target_fixture="ran")
def _kb_init_with_a_role(root, tmp_path):
    return _kb("init", str(root), cwd=tmp_path, env={"KB_ACTOR": OPERATOR})


@when("the operator runs kb init against that directory", target_fixture="ran")
def _kb_init_without_a_role(root, tmp_path):
    return _kb("init", str(root), cwd=tmp_path)


@then("there is a store inside that directory, in a place of its own")
def _a_store_inside(ran, root):
    assert (ran.returncode, ran.stderr) == (0, "")
    assert (root / "kb" / "store.yaml").is_file()
    assert [path.name for path in root.iterdir()] == ["kb"]


@then("a client can begin defining its own types in it straight away")
def _client_defines_a_type(root):
    defined = define(kb_client.connect(root), DECISION_TYPE)
    assert (defined.id, defined.revision) == ("schema/decision", 1)


@then("setting the store up is rejected because the role must be named through KB_ACTOR")
def _rejected_without_kb_actor(ran):
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr == "kb init: refused: actor: a store can only be started under a role, named through KB_ACTOR\n"


@then("that directory still has no store inside it")
def _still_no_store(root):
    assert list(root.iterdir()) == []


@then("setting the store up is rejected because that directory already has a store inside it")
def _init_rejected_as_already_a_store(ran, root):
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr == (
        f"kb init: refused: root: a store is never started over another; {str(root)!r} already has a store inside it\n"
    )


@then("setting the store up is rejected because that directory is inside a store")
def _init_rejected_as_inside_a_store(ran, root, before):
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr == (
        f"kb init: refused: root: stores do not nest; {str(root)!r} is inside the store at {str(before['store'])!r}\n"
    )


def _store_needing_attention(root):
    """A store a client filled: two decisions behind the decision type, and one of them, edited by hand, missing the
    body of its purpose."""
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, DECISION_TYPE)
    for title in ("Price reviews happen weekly", "Prices are reviewed monthly"):
        create(client, "decision", {"title": title, "sections": [
            {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
            {"title": "Rationale", "body": "Costs move weekly.\n"},
        ]})
    next_version(client, "decision", DECISION_TYPE)
    monthly = root / "kb" / "decision" / "prices-are-reviewed-monthly.yaml"
    held = canonical.load(monthly.read_text())
    del held["sections"][0]["body"]
    monthly.write_text(canonical.dump(held))
    return root


REPORT = (
    "violation\tdecision/prices-are-reviewed-monthly\tsections/0\trequired\t'body' is a required property\n"
    "stale\tdecision/price-reviews-happen-weekly\tchecked against version 1 of its type, which is at 2\n"
    "stale\tdecision/prices-are-reviewed-monthly\tchecked against version 1 of its type, which is at 2\n"
)


@given("a store whose content the operator did not write", target_fixture="where")
def _store_the_operator_did_not_write(root):
    return {"cwd": _store_needing_attention(root), "env": {}}


@when("the operator runs kb validate in that store", target_fixture="ran")
@when("the operator runs kb validate there", target_fixture="ran")
def _kb_validate(where):
    return _kb("validate", cwd=where["cwd"], env=where["env"])


@then("the operator is told of everything in the store that does not fit its type, and where")
def _told_of_every_violation(ran):
    assert (ran.returncode, ran.stderr) == (1, "")
    assert [line for line in ran.stdout.splitlines() if line.startswith("violation")] == REPORT.splitlines()[:1]


@then("of everything that is behind the type it was last checked against")
def _told_of_everything_stale(ran):
    assert ran.stdout == REPORT


@when("the operator asks what the command line offers", target_fixture="ran")
def _kb_help(root):
    return _kb("--help", cwd=root)


@then("it offers setting a store up and checking one")
def _offers_init_and_validate(ran):
    assert (ran.returncode, ran.stderr) == (0, "")
    assert re.search(r"^ +init +set up a store in a directory$", ran.stdout, re.M), ran.stdout
    assert re.search(r"^ +validate +check the store", ran.stdout, re.M), ran.stdout


@then("nothing that changes what the store holds")
def _offers_nothing_else(ran, root):
    assert set(re.findall(r"\{(.*)\}", ran.stdout)) == {"init,validate"}, ran.stdout
    refused = _kb("create", "decision", cwd=root)
    assert refused.returncode == 2
    assert "invalid choice: 'create'" in refused.stderr


@given("a store, with the operator working in a folder deep inside the directory it sits in", target_fixture="where")
def _working_deep_inside(root):
    deep = _store_needing_attention(root) / "notes" / "2026" / "september"
    deep.mkdir(parents=True)
    return {"cwd": deep, "env": {}}


@then("the store found above where they are working is the one checked")
@then("the store KB_ROOT names is the one checked")
def _that_store_checked(ran):
    assert (ran.returncode, ran.stdout, ran.stderr) == (1, REPORT, "")


@given("a store, with the operator working outside any store and KB_ROOT naming that one", target_fixture="where")
def _outside_with_kb_root(root, tmp_path):
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    return {"cwd": outside, "env": {"KB_ROOT": str(_store_needing_attention(root))}}


@given("the operator is working outside any store and nothing names one", target_fixture="where")
def _outside_with_nothing_named(tmp_path):
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    return {"cwd": outside, "env": {}}


@then("the check is rejected because no store was found, neither above where they are working nor named outright")
def _rejected_as_no_store(ran, where):
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr == f"kb validate: refused: store: no store was found, neither above {where['cwd']} nor named outright\n"


@given(
    "the operator is working outside any store, with KB_ROOT naming a directory that holds no store",
    target_fixture="where",
)
def _outside_with_kb_root_naming_no_store(tmp_path):
    outside, empty = tmp_path / "elsewhere", tmp_path / "empty"
    outside.mkdir()
    empty.mkdir()
    return {"cwd": outside, "env": {"KB_ROOT": str(empty)}}


@then("the check is rejected because KB_ROOT names a directory that holds no store")
def _rejected_as_kb_root_names_no_store(ran, where):
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr == (
        f"kb validate: refused: store: KB_ROOT names a directory that holds no store: {where['env']['KB_ROOT']}\n"
    )


@given("the operator is working inside a store, with KB_ROOT naming a different store", target_fixture="where")
def _inside_one_naming_another(root, tmp_path):
    other = tmp_path / "other"
    other.mkdir()
    kb_client.connect(other).Init(kb_pb2.InitRequest(root=str(other), actor=CLIENT))
    return {"cwd": _store_needing_attention(root), "env": {"KB_ROOT": str(other)}}


@then(
    "the check is rejected because KB_ROOT names a store other than the one they are standing in, and neither of the "
    "two is guessed at"
)
def _rejected_as_two_stores(ran, where):
    assert (ran.returncode, ran.stdout) == (2, "")
    assert ran.stderr == (
        f"kb validate: refused: store: KB_ROOT names a store other than the one {where['cwd']} is working in: "
        f"KB_ROOT is {where['env']['KB_ROOT']}, the working directory is inside {where['cwd']}; neither is guessed at\n"
    )
