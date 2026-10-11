"""Which tests wait on a slice the living plan has not built, and their marking as expected failures.

A test carries the marker `slice-<n>`: a scenario from its feature's `@slice-<n>` tag, a plain test from `waits_on`.
While the plan lists slice n with a Status whose first word is not `green`, the test is expected to fail: it still
runs, a failure is reported as xfailed with the reason "slice <n> not built", and a pass as xpassed. A slice the plan
no longer lists is archived, so built: its tests run for real. The plan is read once in each pytest process, and a
plan that cannot be read stops the run: without it nothing says which failures are regressions."""
import re

import pytest

PLAN = "docs/superpowers/plans/2026-09-24-kb-slices.md"

_UNBUILT = pytest.StashKey[frozenset]()
_SLICE = re.compile(r"^## Slice (\d+(?:\.\d+)?):.*\n(?:(?!## ).*\n)*?- Status: *([a-z ]+)", re.MULTILINE)
_MARKER = re.compile(r"slice-(\d+(?:\.\d+)?)")


def waits_on(number):
    """The marker of a plain test that waits on that slice, as a scenario's tag gives it."""
    return getattr(pytest.mark, f"slice-{number}")


def statuses(text):
    """Each slice a plan's text lists, with the word its Status begins with."""
    return {number: status.strip() for number, status in _SLICE.findall(text)}


def _read(plan):
    try:
        return plan.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        pytest.exit(
            f"refusing to run: the living plan {plan!s} cannot be read ({error}); "
            f"which slices are not built, and so which tests are expected to fail, is read from it",
            returncode=1,
        )


def configure(config, plan):
    """Read the plan at that path, keep its slices that are not green, and register each one's marker."""
    held = statuses(_read(plan))
    config.stash[_UNBUILT] = frozenset(number for number, status in held.items() if status != "green")
    for number in held:
        config.addinivalue_line("markers", f"slice-{number}: test waiting on that slice of the plan")


def expect_failures(config, items):
    """Mark each collected test of a slice not built as an expected failure that still runs."""
    unbuilt = config.stash[_UNBUILT]
    for item in items:
        for number in _waited_on(item) & unbuilt:
            item.add_marker(pytest.mark.xfail(reason=f"slice {number} not built", run=True, strict=False))


def _waited_on(item):
    """The slices a test's markers name."""
    return {match.group(1) for match in map(_MARKER.fullmatch, (mark.name for mark in item.iter_markers())) if match}
