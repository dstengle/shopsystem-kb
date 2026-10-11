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

import slices


def pytest_configure(config):
    config.addinivalue_line("markers", "slice-165: a tag of the features, which the suite registers from them")
    slices.configure(config, Path(config.rootpath, "plan.md"))


def pytest_collection_modifyitems(config, items):
    slices.expect_failures(config, items)
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


def _tree(tmp_path, slice, passes, plan=PLAN):
    """A tree whose one test is tagged to that slice and passes or fails, under a plan (none when `plan` is None)."""
    tree = tmp_path / "tree"
    tree.mkdir()
    (tree / "pytest.ini").write_text("[pytest]\n")
    (tree / "conftest.py").write_text(CONFTEST)
    (tree / "test_tagged.py").write_text(TAGGED.format(slice=slice, passes=passes))
    if plan is not None:
        (tree / "plan.md").write_text(plan)
    return tree


def _run(tree):
    """pytest run over the tree as a program of its own, its expected failures listed with their reasons."""
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-rxX", "-p", "no:cacheprovider"],
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
