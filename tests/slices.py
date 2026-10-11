"""Which tests wait on a slice the living plan has not built, and their marking as expected failures.

A test carries the marker `slice-<n>`: a scenario from its feature's `@slice-<n>` tag, a plain test from `waits_on`.
While the plan lists slice n with a Status whose first word is not `green`, the test is expected to fail: it still
runs, a failure is reported as xfailed with the reason "slice <n> not built", and a pass as xpassed. A slice the plan
no longer lists is archived, so built: its tests run for real. The plan is read once in each pytest process, and a
plan that cannot be read stops the run: without it nothing says which failures are regressions.

A test that passes although its slice is not built stays out of this: its id is a line of a checked-in list, and it
runs as an ordinary test, so a regression in it fails the run. The list is kept honest at collection: an id no
collected test has, or whose slice the plan does not list as not built, stops the run naming the id and the file."""
import re
from pathlib import Path

import pytest

PLAN = "docs/superpowers/plans/2026-09-24-kb-slices.md"
PASSING = "passing_before_their_slice.txt"

_UNBUILT = pytest.StashKey[frozenset]()
_LISTED = pytest.StashKey[tuple]()
_SLICE = re.compile(r"^## Slice (\d+(?:\.\d+)?):.*\n(?:(?!## ).*\n)*?- Status: *([a-z ]+)", re.MULTILINE)
_MARKER = re.compile(r"slice-(\d+(?:\.\d+)?)")


def waits_on(number):
    """The marker of a plain test that waits on that slice, as a scenario's tag gives it."""
    return getattr(pytest.mark, f"slice-{number}")


def statuses(text):
    """Each slice a plan's text lists, with the word its Status begins with."""
    return {number: status.strip() for number, status in _SLICE.findall(text)}


def _read(path, what):
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        pytest.exit(
            f"refusing to run: {what} {path!s} cannot be read ({error}); "
            f"which slices are not built, and so which tests are expected to fail, is read from them",
            returncode=1,
        )


def _ids(text):
    """The test ids a list holds: one a line, a line starting with # a comment."""
    return tuple(line for line in map(str.strip, text.splitlines()) if line and not line.startswith("#"))


def configure(config, plan, passing=None):
    """Read the plan at that path, keep its slices that are not green, and register each one's marker.

    `passing` is the path of the list of ids that pass before their slice is built, if the suite keeps one."""
    held = statuses(_read(plan, "the living plan"))
    config.stash[_LISTED] = (passing, _ids(_read(passing, "the list of tests passing before their slice")) if passing else ())
    config.stash[_UNBUILT] = frozenset(number for number, status in held.items() if status != "green")
    for number in held:
        config.addinivalue_line("markers", f"slice-{number}: test waiting on that slice of the plan")


def expect_failures(config, items):
    """Mark each collected test of a slice not built as an expected failure that still runs."""
    unbuilt = config.stash[_UNBUILT]
    path, listed = config.stash[_LISTED]
    _keep_honest(config, items, path, listed)
    for item in items:
        if item.nodeid in listed:
            continue
        for number in _waited_on(item) & unbuilt:
            item.add_marker(pytest.mark.xfail(reason=f"slice {number} not built", run=True, strict=False))


def _waited_on(item):
    """The slices a test's markers name."""
    return {match.group(1) for match in map(_MARKER.fullmatch, (mark.name for mark in item.iter_markers())) if match}


def _keep_honest(config, items, path, listed):
    """Stop the run naming each listed id that no collected test has, or whose slice is built.

    `items` is every test collected, before any selection by -k or -m. An id in a file that was not collected (a
    run of other files) cannot be told from here, unless that file is not there at all."""
    unbuilt = config.stash[_UNBUILT]
    held = {item.nodeid: item for item in items}
    collected = {item.nodeid.split("::")[0] for item in items}
    wrong = []
    for nodeid in listed:
        file = nodeid.split("::")[0]
        if nodeid in held:
            if not _waited_on(held[nodeid]) & unbuilt:
                wrong.append(f"{nodeid} (its slice is not one the plan lists as not built)")
        elif file in collected or not Path(config.rootpath, file).exists():
            wrong.append(f"{nodeid} (no collected test has it)")
    if wrong:
        pytest.exit(f"refusing to run: {path!s} lists tests it should not: " + "; ".join(wrong), returncode=1)
