"""Which tests wait on a slice the living plan has not built, and their marking as expected failures.

A test carries the marker `slice-<n>`: a scenario from its feature's `@slice-<n>` tag, a plain test from `waits_on`.
While the plan lists slice n with a Status other than `green`, the test is expected to fail: it still runs, a failure
is reported as xfailed with the reason "slice <n> not built", and a pass as xpassed. A slice the plan no longer lists
is archived, so built: its tests run for real. A Status is read as the plan script reads it: the text before its first
colon, which is `planned`, `in progress`, `green` or `blocked`. The plan is read once in each pytest process, and a
plan that cannot be read, or that gives a slice any other Status, stops the run naming the slice and the Status:
without it nothing says which failures are regressions.

A test that passes although its slice is not built stays out of this: its id is a line of a checked-in list, and it
runs as an ordinary test, so a regression in it fails the run. The list is kept honest at collection: an id no
collected test has, or whose slice the plan does not list as not built, stops the run naming the id and the file,
in a run in parallel (pytest-xdist) as in any other: there the workers collect, and the first to stop hands its
refusal to the controller, which stops the run with it (`stop_with`, from the suite's `pytest_testnodedown`)."""
import re
from pathlib import Path

import pytest

PLAN = "docs/superpowers/plans/2026-09-24-kb-slices.md"
PASSING = "passing_before_their_slice.txt"

_REFUSAL = "slices_refusal"
_UNBUILT = pytest.StashKey[frozenset]()
_LISTED = pytest.StashKey[tuple]()
_KNOWN = ("planned", "in progress", "green", "blocked")
_BLOCK = re.compile(r"^## (?=(.*))", re.MULTILINE)
_SLICE = re.compile(r"Slice (\d+(?:\.\d+)*): .+")
_STATUS = "- Status:"
_MARKER = re.compile(r"slice-(\d+(?:\.\d+)*)")


def waits_on(number):
    """The marker of a plain test that waits on that slice, as a scenario's tag gives it."""
    return getattr(pytest.mark, f"slice-{number}")


def statuses(text):
    """Each slice a plan's text lists, with its Status as the plan script finds it: what the first `- Status:` line
    of the slice's block holds; None for a block with no such line."""
    held = {}
    for heading, block in _blocks(text):
        match = _SLICE.fullmatch(heading)
        if match:
            line = next((line for line in block if line.startswith(_STATUS)), None)
            held[match.group(1)] = None if line is None else line[len(_STATUS):].strip()
    return held


def _blocks(text):
    """Each `## ` block of a plan's text: its heading, and its lines."""
    parts = _BLOCK.split(text)[1:]
    return [(heading.rstrip(), body.splitlines()) for heading, body in zip(parts[::2], parts[1::2])]


def _word(status):
    """The word that decides a Status, as the plan script takes it: the text before its first colon."""
    return status.split(":")[0]


def _known(held, plan):
    """Each slice's deciding word, or the run stopped naming each slice whose Status has none the plan script knows."""
    wrong = [f"slice {number} has no Status" if status is None else f"slice {number} has the Status {status!r}"
             for number, status in held.items() if status is None or _word(status) not in _KNOWN]
    if wrong:
        pytest.exit(
            f"refusing to run: in the living plan {plan!s}, {'; '.join(wrong)}; a Status is "
            f"{', '.join(_KNOWN[:-1])} or {_KNOWN[-1]}, with a note only after a colon, and anything else would be "
            f"read as a slice not built, its tests expected to fail",
            returncode=1,
        )
    return {number: _word(status) for number, status in held.items()}


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
    held = _known(statuses(_read(plan, "the living plan")), plan)
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
    run of other files), or collected in part (`_in_part`), cannot be told from here, unless that file is not there
    at all."""
    unbuilt = config.stash[_UNBUILT]
    held = {item.nodeid: item for item in items}
    collected = {item.nodeid.split("::")[0] for item in items} - _in_part(config, items)
    wrong = []
    for nodeid in listed:
        file = nodeid.split("::")[0]
        if nodeid in held:
            if not _waited_on(held[nodeid]) & unbuilt:
                wrong.append(f"{nodeid} (its slice is not one the plan lists as not built)")
        elif file in collected or not Path(config.rootpath, file).exists():
            wrong.append(f"{nodeid} (no collected test has it)")
    if wrong:
        _stop(config, f"refusing to run: {path!s} lists tests it should not: " + "; ".join(wrong))


def _in_part(config, items):
    """The files this run collected only some tests of: each a `file::test` argument names a test inside, and, when
    the run is of what failed last (`--lf`), every one, since that leaves a file's passing tests uncollected."""
    if config.getoption("lf", False):
        return {item.nodeid.split("::")[0] for item in items}
    named = (Path(config.invocation_params.dir, arg.split("::")[0]) for arg in config.args if "::" in arg)
    return {_under(config.rootpath, file) for file in named}


def _under(root, file):
    """A file as a test id names it: its path below the root, with forward slashes; as given when outside it."""
    try:
        return file.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(file)


def _stop(config, refusal):
    """Stop the run with that refusal. A worker of a run in parallel (pytest-xdist) collects in the controller's
    place and cannot stop the run itself, so it hands the refusal to the controller as it stops (`stop_with`)."""
    if hasattr(config, "workerinput"):
        config.workeroutput[_REFUSAL] = refusal
    pytest.exit(refusal, returncode=1)


def stop_with(node):
    """On the controller of a run in parallel, as a worker goes down: stop the run with the refusal it stopped for."""
    refusal = getattr(node, "workeroutput", {}).get(_REFUSAL)
    if refusal:
        pytest.exit(refusal, returncode=1)
