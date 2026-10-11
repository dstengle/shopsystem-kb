"""A test tagged to a slice the living plan holds as not green is expected to fail, and nothing else is.

Each test here runs pytest itself over a tiny tree of its own: a plan, a conftest wired to `slices` as this suite's is,
and one test module. What is asserted is what pytest reports for the run and whether the run succeeds."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parent

CONFTEST = """\
from pathlib import Path

import pytest

import slices


def pytest_configure(config):
    config.addinivalue_line("markers", "slice-165: a tag of the features, which the suite registers from them")
    slices.configure(config, Path(config.rootpath, "plan.md"), Path(config.rootpath, "listed.txt"))


def pytest_collection_modifyitems(config, items):
    slices.expect_failures(config, items)


@pytest.hookimpl(optionalhook=True, tryfirst=True)
def pytest_testnodedown(node, error):
    slices.stop_with(node)
"""

PLAN = """\
# a plan

Slices 0 to 165 are archived, all green.

## Slice 166: Built, and still listed
- Kind: enabling
- Check: `make test` -> green
- Status: green

## Slice 166.1: Under a built one
- Kind: capability
- Scenarios: one
- Status: planned

## Slice 171: Not begun
- Kind: capability
- Scenarios: one
- Status: planned: waits on slice 170

## Slice 172: Being built
- Kind: capability
- Scenarios: one
- Status: in progress

## Slice 173: Stopped
- Kind: capability
- Scenarios: one
- Status: blocked: green is not this slice's status

## Log
- 2026-10-11 slice 166 green.
"""

TAGGED = """\
import pytest


@getattr(pytest.mark, "slice-{slice}")
def test_tagged():
    assert {passes}, "the test's own failure"
"""


def _tree(tmp_path, slice, passes, plan=PLAN, listed=()):
    """A tree whose one test is tagged to that slice and passes or fails, under a plan (none when `plan` is None)
    and a list of the test ids that pass before their slice is built."""
    tree = tmp_path / "tree"
    tree.mkdir()
    (tree / "pytest.ini").write_text("[pytest]\n")
    (tree / "conftest.py").write_text(CONFTEST)
    (tree / "listed.txt").write_text("".join(["# tests that pass before their slice is built\n", *(f"{i}\n" for i in listed)]))
    (tree / "test_tagged.py").write_text(TAGGED.format(slice=slice, passes=passes))
    if plan is not None:
        (tree / "plan.md").write_text(plan)
    return tree


def _run(tree, *more, cache="no:cacheprovider"):
    """pytest run over the tree as a program of its own, its expected failures listed with their reasons, with any
    more arguments; without the cache of what failed last, unless `cache` names a plugin to keep it out instead."""
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-rxX", "-p", cache, *more],
        cwd=tree, env={**os.environ, "PYTHONPATH": str(TESTS)}, capture_output=True, text=True,
    )


def _summary(ran):
    """The last line pytest prints, without the time it took: its counts."""
    return ran.stdout.strip().splitlines()[-1].split(" in ")[0]


@pytest.mark.parametrize("slice", ["171", "172", "173"], ids=["planned", "in progress", "blocked"])
def test_a_failing_test_of_a_slice_the_plan_holds_as_not_green_is_expected_to_fail(tmp_path, slice):
    ran = _run(_tree(tmp_path, slice, passes=False))
    assert (ran.returncode, _summary(ran)) == (0, "1 xfailed"), ran.stdout + ran.stderr
    assert f"XFAIL test_tagged.py::test_tagged - slice {slice} not built" in ran.stdout


def test_a_passing_test_of_a_slice_not_built_is_unexpectedly_passing_and_the_run_succeeds(tmp_path):
    ran = _run(_tree(tmp_path, "171", passes=True))
    assert (ran.returncode, _summary(ran)) == (0, "1 xpassed"), ran.stdout + ran.stderr
    assert "XPASS test_tagged.py::test_tagged - slice 171 not built" in ran.stdout


def test_a_failing_test_of_a_slice_no_longer_in_the_plan_fails_the_run(tmp_path):
    ran = _run(_tree(tmp_path, "165", passes=False))
    assert (ran.returncode, _summary(ran)) == (1, "1 failed"), ran.stdout + ran.stderr
    assert "the test's own failure" in ran.stdout


def test_a_failing_test_of_a_slice_the_plan_holds_as_green_fails_the_run(tmp_path):
    ran = _run(_tree(tmp_path, "166", passes=False))
    assert (ran.returncode, _summary(ran)) == (1, "1 failed"), ran.stdout + ran.stderr


def test_a_dotted_slice_is_told_from_the_slice_it_is_numbered_under(tmp_path):
    ran = _run(_tree(tmp_path, "166.1", passes=False))
    assert (ran.returncode, _summary(ran)) == (0, "1 xfailed"), ran.stdout + ran.stderr
    assert "XFAIL test_tagged.py::test_tagged - slice 166.1 not built" in ran.stdout


def test_a_plan_that_is_not_there_stops_the_run_naming_the_file(tmp_path):
    tree = _tree(tmp_path, "171", passes=True, plan=None)
    ran = _run(tree)
    assert ran.returncode == 1, ran.stdout + ran.stderr
    assert str(tree / "plan.md") in ran.stderr
    assert "passed" not in ran.stdout and "xpassed" not in ran.stdout


def test_a_plan_that_cannot_be_read_stops_the_run_naming_the_file(tmp_path):
    tree = _tree(tmp_path, "171", passes=True, plan=None)
    (tree / "plan.md").mkdir()
    ran = _run(tree)
    assert ran.returncode == 1, ran.stdout + ran.stderr
    assert str(tree / "plan.md") in ran.stderr
    assert "passed" not in ran.stdout and "xpassed" not in ran.stdout


LISTED = "test_tagged.py::test_tagged"


def test_a_listed_failing_test_of_a_slice_not_built_runs_for_real_and_fails_the_run(tmp_path):
    ran = _run(_tree(tmp_path, "171", passes=False, listed=[LISTED]))
    assert (ran.returncode, _summary(ran)) == (1, "1 failed"), ran.stdout + ran.stderr
    assert "the test's own failure" in ran.stdout


def test_a_listed_passing_test_of_a_slice_not_built_is_a_plain_pass(tmp_path):
    ran = _run(_tree(tmp_path, "171", passes=True, listed=[LISTED]))
    assert (ran.returncode, _summary(ran)) == (0, "1 passed"), ran.stdout + ran.stderr


def test_a_listed_id_no_collected_test_has_fails_the_run_naming_it_and_the_file(tmp_path):
    tree = _tree(tmp_path, "171", passes=True, listed=[LISTED, "test_tagged.py::test_gone"])
    ran = _run(tree)
    assert ran.returncode == 1, ran.stdout + ran.stderr
    assert "test_tagged.py::test_gone" in ran.stdout + ran.stderr
    assert str(tree / "listed.txt") in ran.stdout + ran.stderr
    assert "passed" not in ran.stdout


def test_a_listed_id_in_a_file_that_is_not_there_fails_the_run_naming_it(tmp_path):
    tree = _tree(tmp_path, "171", passes=True, listed=[LISTED, "test_gone.py::test_tagged"])
    ran = _run(tree)
    assert ran.returncode == 1, ran.stdout + ran.stderr
    assert "test_gone.py::test_tagged" in ran.stdout + ran.stderr


def test_a_listed_test_whose_slice_the_plan_does_not_list_fails_the_run_naming_it(tmp_path):
    tree = _tree(tmp_path, "165", passes=True, listed=[LISTED])
    ran = _run(tree)
    assert ran.returncode == 1, ran.stdout + ran.stderr
    assert LISTED in ran.stdout + ran.stderr
    assert str(tree / "listed.txt") in ran.stdout + ran.stderr


def test_a_listed_test_whose_slice_the_plan_holds_as_green_fails_the_run_naming_it(tmp_path):
    ran = _run(_tree(tmp_path, "166", passes=True, listed=[LISTED]))
    assert ran.returncode == 1, ran.stdout + ran.stderr
    assert LISTED in ran.stdout + ran.stderr


def test_a_selection_that_leaves_a_listed_test_out_does_not_fail_the_run(tmp_path):
    tree = _tree(tmp_path, "171", passes=True, listed=[LISTED])
    ran = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-k", "nothing_is_named_this"],
        cwd=tree, env={**os.environ, "PYTHONPATH": str(TESTS)}, capture_output=True, text=True,
    )
    assert ran.returncode == 5, ran.stdout + ran.stderr
    assert "listed.txt" not in ran.stdout + ran.stderr


def _with_status(slice, status):
    """The plan with that slice's Status line written as given."""
    head, _, rest = PLAN.partition(f"## Slice {slice}:")
    before, _, after = rest.partition("- Status:")
    return f"{head}## Slice {slice}:{before}- Status: {status}\n{after.partition(chr(10))[2]}"


@pytest.mark.parametrize(
    "status", ["Green", "GREEN", "done", "`green`", "**green**", "", "green with fixes", "greenish: nearly"],
)
def test_a_status_the_plan_script_does_not_know_stops_the_run_naming_the_slice_and_the_status(tmp_path, status):
    ran = _run(_tree(tmp_path, "171", passes=False, plan=_with_status("171", status)))
    assert ran.returncode == 1, ran.stdout + ran.stderr
    assert f"slice 171 has the Status {status!r}" in ran.stderr
    assert "xfailed" not in ran.stdout and "passed" not in ran.stdout


def test_a_slice_with_no_status_stops_the_run_naming_the_slice(tmp_path):
    plan = PLAN.replace("- Status: planned: waits on slice 170\n", "")
    ran = _run(_tree(tmp_path, "171", passes=False, plan=plan))
    assert ran.returncode == 1, ran.stdout + ran.stderr
    assert "slice 171 has no Status" in ran.stderr
    assert "xfailed" not in ran.stdout


def test_only_the_word_before_the_colon_decides_a_status(tmp_path):
    ran = _run(_tree(tmp_path, "171", passes=False, plan=_with_status("171", "green: blocked no longer, not planned")))
    assert (ran.returncode, _summary(ran)) == (1, "1 failed"), ran.stdout + ran.stderr


def test_a_slice_numbered_as_deep_as_the_plan_script_allows_is_read(tmp_path):
    plan = PLAN.replace("## Slice 171: Not begun", "## Slice 166.1.1: Deeper\n- Kind: enabling\n- Check: one\n"
                        "- Status: planned\n\n## Slice 171: Not begun")
    ran = _run(_tree(tmp_path, "166.1.1", passes=False, plan=plan))
    assert (ran.returncode, _summary(ran)) == (0, "1 xfailed"), ran.stdout + ran.stderr
    assert "XFAIL test_tagged.py::test_tagged - slice 166.1.1 not built" in ran.stdout


@pytest.mark.parametrize("slice, listed, named", [
    ("171", [LISTED, "test_tagged.py::test_gone"], "test_tagged.py::test_gone (no collected test has it)"),
    ("166", [LISTED], f"{LISTED} (its slice is not one the plan lists as not built)"),
], ids=["an id no test has", "an id whose slice is built"])
def test_a_list_that_is_wrong_stops_a_run_in_parallel_with_the_same_message(tmp_path, slice, listed, named):
    tree = _tree(tmp_path, slice, passes=True, listed=listed)
    alone, ran = _run(tree), _run(tree, "-n", "2")
    refusal = f"refusing to run: {tree / 'listed.txt'!s} lists tests it should not: {named}"
    assert refusal in alone.stdout + alone.stderr
    assert ran.returncode == 1, ran.stdout + ran.stderr
    assert refusal in ran.stdout + ran.stderr
    assert "INTERNALERROR" not in ran.stdout + ran.stderr
    assert "passed" not in ran.stdout


def test_a_list_that_is_right_runs_in_parallel(tmp_path):
    ran = _run(_tree(tmp_path, "171", passes=True, listed=[LISTED]), "-n", "2")
    assert (ran.returncode, _summary(ran)) == (0, "1 passed"), ran.stdout + ran.stderr


OTHER = """

def test_other():
    import os
    assert not os.environ.get("OTHER_FAILS")
"""


def _tree_with_another_test(tmp_path):
    """A tree whose file holds a listed test, passing before its slice is built, and another test beside it."""
    tree = _tree(tmp_path, "171", passes=True, listed=[LISTED])
    with (tree / "test_tagged.py").open("a") as file:
        file.write(OTHER)
    return tree


def test_a_run_of_one_test_by_its_id_in_a_file_holding_a_listed_test_is_not_refused(tmp_path):
    ran = _run(_tree_with_another_test(tmp_path), "test_tagged.py::test_other")
    assert (ran.returncode, _summary(ran)) == (0, "1 passed"), ran.stdout + ran.stderr


def test_a_run_by_id_still_refuses_a_listed_test_it_collects_whose_slice_is_built(tmp_path):
    tree = _tree(tmp_path, "166", passes=True, listed=[LISTED])
    ran = _run(tree, LISTED)
    assert ran.returncode == 1, ran.stdout + ran.stderr
    assert f"{LISTED} (its slice is not one the plan lists as not built)" in ran.stdout + ran.stderr


def test_a_run_of_what_failed_last_in_a_file_holding_a_listed_test_is_not_refused(tmp_path, monkeypatch):
    tree = _tree_with_another_test(tmp_path)
    monkeypatch.setenv("OTHER_FAILS", "1")
    first = _run(tree, cache="no:nothing_by_this_name")
    assert (first.returncode, _summary(first)) == (1, "1 failed, 1 passed"), first.stdout + first.stderr
    ran = _run(tree, "--lf", cache="no:nothing_by_this_name")
    assert (ran.returncode, _summary(ran)) == (1, "1 failed"), ran.stdout + ran.stderr
    assert "refusing to run" not in ran.stdout + ran.stderr
