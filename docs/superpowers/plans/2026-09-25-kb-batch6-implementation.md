# kb Batch 6 Implementation Plan: slices 43, 45, 46 and 51

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Each task is one slice of `docs/superpowers/plans/2026-09-24-kb-slices.md`. Inside a task, follow `shopsystem-bdd:bdd-red-green` scenario by scenario. Its stop conditions, hand-back, and checkpoint apply, and they override any step here that conflicts with them.

**Goal:** The last four slices of the kb plan:
- A client checking a store is told of every violation, of nothing when the store is sound, of an artifact behind its type as stale, and of one both behind and broken both ways.
- A client can start a store in a directory that holds other things, and is refused starting one over another store or inside one.
- An operator can set up and check a store from a shell with kb's own `kb` command, which offers nothing else.
- A client can read the journal for one set, by the name Apply gave it.

**Architecture:** kb is the Python package `kb` in `/home/vscode/shopsystem-kb`. A protobuf contract (`kb.contract`) sits in front of `KbServicer`, which works over a `Store`. The store is one canonical YAML file per artifact under `<root>/kb/`, and that directory is itself a git repository. `kb.values` holds the boundary conversions, `kb.discovery` finds a store the way git finds a repository, and `kb.client.connect()` gives the in-process client. This plan:
- adds no code for slice 43: `Validate` already reports violations and stale artifacts (slices 1.20 and 42's work), so the task is its step definitions;
- has `values.root`, which converts Init's root, refuse a directory with `kb/` inside it and a directory inside a store (slice 45);
- adds `kb.cli`, the console command `kb` with `init` and `validate`, each one call on the in-process client (slice 46);
- gives `JournalRequest` a `batch` filter (slice 51).

**Provenance:** Every code block here was assembled in a scratch clone of this repository (`/tmp/batch6/kb`, cloned at `b16908f`) on 2026-09-25, with its own `.venv` from `make dev`, and the tasks were applied in order. The red and green results, the suite counts, and the Review Focus reproductions below are what those runs gave. The plan was then replayed from its own text and code blocks on a fresh clone (`/tmp/batch6-replay`, at `b16908f`, its own `.venv`) by an agent that had not seen the scratch run. Every red and green, and the mutation check, matched; the replay's `src/` and `tests/` were identical to the scratch run's; and all five Review Focus items reproduced. Its three notes on the text (a red command that hid its summary line, Review Focus 2's second write, the blank lines before an appended block) are fixed here. This repository was not touched except to log the batch 5 findings and to write this plan.

**Tech Stack:** Python 3.11, setuptools (src layout), protobuf + grpcio + grpcio-tools (generated code is committed; `make contract` regenerates it), python-jsonschema 4.26 with `referencing`, ruamel.yaml 0.19 (YAML 1.2), git via subprocess, argparse, pytest 9 + pytest-bdd 8.

**Spec:** `docs/superpowers/specs/2026-09-23-kb-design.md`, in particular:
- "Schema validation": "An artifact whose `schema_version` is behind its schema is reported as stale on load, never failed";
- "Write path", step 2: "An artifact behind that version which still fits is reported stale; one that does not is reported stale and in violation. Nothing fails";
- "The contract": the `Init` row ("Refused when `kb/` already exists under the root, or when the root is inside a store"), the `Validate` row, and the `Journal` row ("filters: artifact, actor, execution, batch, since");
- "Serialization", Layout: "Nothing else in `<root>` is the store's concern";
- "Finding the store": "A client or the admin CLI finds the store the way git finds a repository";
- "Admin CLI": "`kb init <root>`, `kb validate`, and later `kb serve`. No user-facing operations; those belong to clients."

The slice plan is `docs/superpowers/plans/2026-09-24-kb-slices.md`, slices 43, 45, 46 and 51, and the feature files are in `features/`. Each slice's scenarios carry `@slice-<n>`, so `.venv/bin/python -m pytest -q -m slice-43` runs one slice.

## Global Constraints

- Feature files are read-only for the implementer. Only `slicing-into-increments` edits a tag line, and only `formulating-features` edits a Given, When, or Then. Any other diff under `features/` is a stop condition.
- Code only what a scenario asserts (bdd-red-green). Where the scenarios are silent, the code is silent too, and the silence goes into the checkpoint entry as an open question. The decisions this plan makes are listed below, each tied to the spec line or scenario that asks for it.
- The batch 5 review's findings (a Delete in a set reading the removed artifact after earlier operations were saved; Delete ignoring links inside items; Append giving an empty or not-plain item name; a name reusable after a removal) are questions for the spec with no scenario. None is coded here.
- **Extend, never add beside.**
  - Init's root is converted by `values.root`; the new refusals go there, beside the three it has, with the same rule `root`.
  - The store above a directory is found by `discovery.find_above`, which `values.root` now uses too. The CLI finds its store through `client.connect()` with no root, so the discovery refusals come from `discovery.locate` unchanged.
  - Journal filters live in `KbServicer.Journal`'s one comprehension.
  - Test helpers live in `tests/calls.py`, and a Given or Then two feature files share lives in `tests/conftest.py`, rather than being copied.
- Errors are a typed list of `{ artifact, path, rule, message }`. A response that carries faults is a refusal, and nothing was written.
- kb is exercised through its in-process transport. The CLI's scenarios run the installed `kb` command as a subprocess, since the command is what the operator runs.
- Each checkout has its own virtualenv. `make test` runs the suite (`.venv/bin/python -m pytest -q`). `make contract` regenerates `kb_pb2.py`, `kb_pb2.pyi` and `kb_pb2_grpc.py` from `kb.proto`, and every regenerated file is committed with the `.proto`. After Task 3 adds the console script, `.venv/bin/pip install -q -e '.[dev]'` must run once so that `.venv/bin/kb` exists.
- The contract's version stays `0.1` in the `.proto` header and in `CONTRACT_VERSION`, and `pyproject.toml` stays `0.1.0`. Bumping the version and tagging are the user's call and are not part of this plan (see "After slice 51").
- Work on `main` in `/home/vscode/shopsystem-kb`. A worktree needs its own `.venv` first (`make dev`).
- shop-knowledge pins kb at `v0.1.0`. Nothing here touches or runs its suite.
- Commits: `git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit`, the message ending with the Co-Authored-By line of the model that made the commit, e.g. `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- "Append at the end of the file" means after two blank lines, as the files' top-level definitions are spaced.
- The suite prints pytest-bdd `PytestRemovedIn10Warning`s. That is the baseline, not a fault. The summary lines quoted as Expected leave out the `, N warnings in Xs` that pytest adds.
- Baseline before Task 1: `make test` → `19 failed, 99 passed`. After Tasks 1 to 4 the suite reads `15/103`, `12/106`, `1/117` and `0/118` (failed/passed).

## Decisions this plan makes (the spec left them open or silent)

1. **Check (slice 43).** No code. The steps make an artifact fall behind its type with a Write of the type at its next version (`calls.next_version`), and, for "no longer fits", the next version requires a third section, `Review`. The two faults of "Every violation is reported" are made by hand in the stored files, since the store refuses to write either: a decision left with its `Purpose` alone (rule `sections`, path `sections`) and a work item pointing at `decision/prices-are-reviewed-monthly`, which the store lacks (rule `ref`, path `decisions/0`). The slice plan's open question from slices 42 and 43 ("is an artifact behind its type checked against the current type at all?") is answered by the fourth scenario: it is, and it is reported both ways.
2. **Init refusals (slice 45).** `values.root` refuses, after its three existing checks and in this order, with rule `root`:
   - a directory with anything called `kb` inside it: `a store is never started over another; '<root>' already has a store inside it`. The spec says "when `kb/` already exists", so a `kb` that is not a store is refused the same way (Review Focus 3);
   - a directory with a store above it, found by `discovery.find_above` from the resolved directory's parent: `stores do not nest; '<root>' is inside the store at '<store root>'`. A directory inside another store's `kb/` is inside that store.
   - `<root>` is the text the request gave; the store root is the resolved path found.
3. **Shared steps (slices 45 and 46).** The Givens "a directory that already has a store inside it, with content in that store" and "a directory that sits inside a store", and the Thens "the store that is there holds what it held before" and "the store it sits inside holds what it held before", are word for word the same in `start-a-store` and `look-after-a-store`. They go in `tests/conftest.py`, with a `before` fixture the Given fills with the store's root and every file below it. "Inside a store" is the directory `notes/drafts` below the store's root.
4. **The command line (slice 46).** `src/kb/cli.py`, installed as the console script `kb = "kb.cli:main"` in `pyproject.toml`, with argparse subcommands `init <root>` and `validate` and nothing else.
   - `kb init <root>` takes the role from `KB_ACTOR`. Unset or empty, it is refused by the CLI itself, before any call, with rule `actor`: `a store can only be started under a role, named through KB_ACTOR`. Otherwise it is one `Init` with the root as given.
   - `kb validate` is one `Validate` on `client.connect()` with no root, so the store is found from the working directory or `KB_ROOT`, and every discovery refusal is `discovery.locate`'s own.
   - A refusal prints `kb <command>: refused: <rule>: <message>` to stderr, one line per fault, and exits 2 (argparse's exit for a usage error, `invalid choice: 'create'` among them, is 2 as well).
   - `kb validate` prints each violation as `violation\t<artifact>\t<path>\t<rule>\t<message>`, then each stale artifact as `stale\t<artifact>\tchecked against version <n> of its type, which is at <m>`, on stdout. It exits 1 when there is a violation and 0 otherwise, a stale artifact alone included. A sound store prints nothing.
   - `kb init` prints nothing on success.
   - The scenarios run `.venv/bin/kb` (found beside `sys.executable`) as a subprocess, with `KB_ROOT` and `KB_ACTOR` taken out of its environment unless a step sets them.
5. **The set in the history (slice 51).** `JournalRequest` gains `string batch = 5`. An entry is kept when its `batch` equals the one given; it is compared, never used as a path, so it is not converted, as `role` and `execution` are not. A batch naming no set answers no entries and no fault (Review Focus 5).

## Review Focus

In this project, tests are scenarios, and the feature files are the human gate, so no unit tests are added. Instead, each line below goes into the owning task's checkpoint entry as a `QUESTION FOR THE SPEC`, with the reproduction given here. Each was reproduced in scratch after all four tasks.

1. **`kb validate` over a store holding a kind with no type exits 1, the code for "violations found".** Reproduction: after Task 3, `KB_ACTOR=op kb init c`, then put `c/kb/note/n.yaml` holding `id: note/n`, `type: note`, `schema_version: 1`, `revision: 1`, `title: N`, and run `kb validate` in `c`. It prints a `FileNotFoundError` traceback for `kb/schema/note.yaml` and exits 1, so a script reading the exit code takes a crash for a report. The raise is batch 2's open question (Validate on a stray kind directory); the exit code is new. Task 3 logs it.
2. **A type written back without raising its version.** Reproduction: after Task 1, with the decision type at version 1 and a decision that fits it, write `schema/decision` at version 1 requiring a third section. It is accepted; `Validate` reports the decision as a violation and not as stale. Then write it back at version 0 with its first schema, the two sections alone: that is accepted too, and the decision, now ahead of its type, is reported as neither. The spec says a schema's version "increments when it changes"; nothing checks it. Task 1 logs it.
3. **A `kb` inside the root that is not a store.** Reproduction: after Task 2, `kb init d1` where `d1/kb` is an empty directory, or `kb init d2` where `d2/kb` is a file, is refused with "already has a store inside it", though there is none. The spec's words are "when `kb/` already exists"; the message says more than it knows. Task 2 logs it.
4. **`KB_ROOT` set but empty, from the shell.** Reproduction: after Task 3, `KB_ROOT= kb validate` outside any store is refused with `KB_ROOT names a directory that holds no store: .`. This is slice 61's open question (is an empty `KB_ROOT` unset?), now one an operator meets. Task 3 logs it.
5. **A batch naming no set.** Reproduction: after Task 4, `journal(client, batch="nothing")` answers no entries and no fault, where a name that is not plain is refused on the `artifact` filter. Task 4 logs it.

---

### Task 1: Slice 43, a check reports every violation, nothing when sound, stale when behind, and both when behind and broken

**Slice plan entry:** Slice 43, capability. Unknown: none. Scenarios:

1. kb / check-the-store / A store with nothing wrong reports nothing
2. kb / check-the-store / Every violation is reported
3. kb / check-the-store / An artifact behind its type is reported as stale
4. kb / check-the-store / An artifact behind its type that no longer fits it is reported both ways

All four go green on their step definitions alone, on the `Validate` that slice 1.20 built. Each is red first for want of a step. No production code changes.

**Files:**
- Modify: `tests/calls.py` (new `next_version`, just above `everything_under`)
- Modify: `tests/test_check_the_store.py` (imports; ten steps and a helper appended)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `test_check_the_store.py`'s When `the client checks the store` (fixture `checked`, a `ValidateResponse`) and `SECTIONS`. `calls.write`, `calls.define`, `calls.create`, `calls.DECISION_TYPE`, `calls.WORK_ITEM_TYPE`, `canonical.load`, `canonical.dump`, the `root` fixture.
- Produces: `calls.next_version(client, kind: str, type_content: dict, sections: list[str] | None = None) -> WriteResponse`, which Task 3 uses.

- [ ] **Step 1: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-43 2>&1 | grep -E "^E |passed|failed" | tail -5
```

Expected: `4 failed`, each a `StepDefinitionNotFoundError` for its Given.

- [ ] **Step 2: The helper**

In `tests/calls.py`, just above `def everything_under(directory):`, add:

```python
def next_version(client, kind, type_content, sections=None):
    """Write the type of a kind back at its next version, the sections it requires replaced when sections are given,
    so what the store holds of that kind falls behind it. Returns the Write's response."""
    schema = copy.deepcopy(type_content["schema"])
    if sections is not None:
        schema["sections"] = [{"title": title} for title in sections]
    return write(client, f"schema/{kind}", {"version": type_content["version"] + 1, "schema": schema},
                 message=f"Revise {type_content['title']}")


```

- [ ] **Step 3: The steps**

In `tests/test_check_the_store.py`, replace the line

```python
from calls import CLIENT, DECISION_TYPE, create, define
```

with

```python
from calls import CLIENT, DECISION_TYPE, WORK_ITEM_TYPE, create, define, next_version
```

and append at the end of the file:

```python
WEEKLY = "decision/price-reviews-happen-weekly"


def _store_with_a_decision(root):
    """A client over a new store holding the decision type and one decision that fits it."""
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, DECISION_TYPE)
    create(client, "decision", {"title": "Price reviews happen weekly", "sections": SECTIONS})
    return client


@given("a store where everything fits its type", target_fixture="client")
def _store_where_everything_fits(root):
    client = _store_with_a_decision(root)
    define(client, WORK_ITEM_TYPE)
    create(client, "work-item", {"title": "Move the review to Mondays", "decisions": [WEEKLY]})
    return client


@given(
    "a store where one artifact is missing a section its type requires and another points at something the store "
    "does not hold",
    target_fixture="client",
)
def _store_with_two_faults(root):
    """Both faults are made by hand behind the store's back, since the store refuses to write either."""
    client = _store_with_a_decision(root)
    define(client, WORK_ITEM_TYPE)
    create(client, "work-item", {"title": "Move the review to Mondays", "decisions": [WEEKLY]})
    decision = root / "kb" / "decision" / "price-reviews-happen-weekly.yaml"
    held = canonical.load(decision.read_text())
    held["sections"] = held["sections"][:1]
    decision.write_text(canonical.dump(held))
    work_item = root / "kb" / "work-item" / "move-the-review-to-mondays.yaml"
    held = canonical.load(work_item.read_text())
    held["decisions"] = ["decision/prices-are-reviewed-monthly"]
    work_item.write_text(canonical.dump(held))
    return client


@then("both are reported, each naming the artifact, the place in it and the rule broken")
def _both_reported(checked):
    assert not checked.faults, checked.faults
    assert [(fault.artifact, fault.path, fault.rule) for fault in checked.violations] == [
        (WEEKLY, "sections", "sections"),
        ("work-item/move-the-review-to-mondays", "decisions/0", "ref"),
    ]


@then("the client is told of no violation")
def _no_violation(checked):
    assert not checked.faults, checked.faults
    assert list(checked.violations) == []
    assert list(checked.stale) == []


@given(
    "a store where a decision was last checked against an older version of the decision type",
    target_fixture="client",
)
def _store_with_a_decision_behind_its_type(root):
    client = _store_with_a_decision(root)
    next_version(client, "decision", DECISION_TYPE)
    return client


@given(
    "a store where a decision was last checked against an older version of the decision type, and no longer fits "
    "the current version",
    target_fixture="client",
)
def _store_with_a_decision_behind_its_type_that_no_longer_fits(root):
    client = _store_with_a_decision(root)
    next_version(client, "decision", DECISION_TYPE, sections=["Purpose", "Rationale", "Review"])
    return client


@then("that decision is listed as behind its type")
def _listed_as_stale(checked):
    assert [(entry.artifact, entry.schema_version, entry.current) for entry in checked.stale] == [(WEEKLY, 1, 2)]


@then("it is not reported as a violation")
def _not_a_violation(checked):
    assert list(checked.violations) == []


@then("it is also reported as a violation, naming the artifact, the place in it and the rule broken")
def _also_a_violation(checked):
    assert [(fault.artifact, fault.path, fault.rule, fault.message) for fault in checked.violations] == [
        (WEEKLY, "sections", "sections",
         "the sections the type requires must all be present, in order; 'Review' is missing"),
    ]


@then("the check itself does not fail")
def _the_check_does_not_fail(checked):
    assert isinstance(checked, kb_pb2.ValidateResponse)
    assert not checked.faults, checked.faults
```

- [ ] **Step 4: Run it green, and the suite**

```bash
.venv/bin/python -m pytest -q -m slice-43 2>&1 | tail -1
make test 2>&1 | grep -E "passed|failed" | tail -1
```

Expected: `4 passed, 114 deselected`; `15 failed, 103 passed`.

A step that passes at once still has to be able to fail. Before committing, change `(WEEKLY, 1, 2)` in `_listed_as_stale` to `(WEEKLY, 1, 3)`, run the slice, see scenarios 3 and 4 fail on that assertion, and put it back.

- [ ] **Step 5: Commit**

```bash
git add tests/calls.py tests/test_check_the_store.py && git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 43: a check reports every violation, nothing when sound, stale when behind, and both

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 6: Checkpoint**

In `docs/superpowers/plans/2026-09-24-kb-slices.md`, set slice 43's Status to `green`. Append at the very end of the Log, and check with `tail` that it is last:

```
- <date> slice 43 green. Someone can now: check a store and be told of every violation, each with its artifact, place and rule; be told of none when everything fits; see a decision behind its type listed as stale and not as a violation; and see one behind its type that no longer fits it listed both ways, the check still answering.
  Surprised by: <nothing, or what>. All four went green on their step definitions alone, on the Validate slice 1.20 built, red first for want of a step.
  Open questions:
  - QUESTION FOR THE SPEC: a type written back at the same version, or a lower one, is accepted. Its artifacts then violate without being stale, or sit ahead of their type and are reported as neither. The spec says a schema's version increments when it changes; nothing checks it. (Review Focus 2)
  - The question logged for slices 42 and 43 in the plan's first cut (is an artifact behind its type checked against the current type?) is answered by "reported both ways": it is.
  Next: slice 45.
```

Commit the plan: `Slice 43 green`.

---

### Task 2: Slice 45, a store sits beside other things, and is not started twice or inside another

**Slice plan entry:** Slice 45, capability. Unknown: none. Scenarios:

1. kb / start-a-store / A directory holding other things can still be given a store
2. kb / start-a-store / Starting a store in a directory that already has one inside it is refused
3. kb / start-a-store / Starting a store inside a store is refused

Scenario 1 goes green on its step definitions alone: the store has lived in `<root>/kb/` since slice 1. Scenarios 2 and 3 need code. Today scenario 2's Init raises `FileExistsError` through the client, and scenario 3's starts a second store inside the first.

**Files:**
- Modify: `tests/conftest.py` (imports; the `before` fixture, two Givens and a Then shared with Task 3)
- Modify: `tests/test_start_a_store.py` (five steps appended)
- Modify: `src/kb/values.py` (`root`: two refusals; imports `discovery`)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `test_start_a_store.py`'s When `the client starts a store there, saying which role it is` (fixture `started`, an `InitResponse`) and its `client` fixture. `discovery.find_above(Path) -> Path | None`. `calls.everything_under`, `calls.define`, `calls.create`, `calls.DECISION_TYPE`.
- Produces:
  - `conftest.before`, a dict fixture the two Givens fill with `store` (the store's root, a `Path`) and `held` (`everything_under` of it).
  - The Givens `a directory that already has a store inside it, with content in that store` and `a directory that sits inside a store`, each with `target_fixture="root"`, and the Thens `the store that is there holds what it held before` and `the store it sits inside holds what it held before`, all in `conftest.py`, which Task 3's scenarios use.
  - `values.root` refusing, with rule `root`, `a store is never started over another; '<root>' already has a store inside it` and `stores do not nest; '<root>' is inside the store at '<store root>'`, which Task 3's CLI prints.

- [ ] **Step 1: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-45 2>&1 | grep -E "^E |passed|failed" | tail -4
```

Expected: `3 failed`, each a `StepDefinitionNotFoundError` for its Given.

- [ ] **Step 2: The shared steps**

In `tests/conftest.py`, replace

```python
from pytest_bdd import given

from calls import CLIENT
```

with

```python
from pytest_bdd import given, then

from calls import CLIENT, DECISION_TYPE, create, define, everything_under
```

and append at the end of the file:

```python
@pytest.fixture
def before():
    """What a store held before a scenario's When, filled in by the Given that made it: the store's root, and every
    file below it with its bytes."""
    return {}


def _store_with_content(root):
    """A store started in root, holding the decision type and a decision."""
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, DECISION_TYPE)
    create(client, "decision", {
        "title": "Price reviews happen weekly",
        "sections": [
            {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
            {"title": "Rationale", "body": "Costs move weekly.\n"},
        ],
    })


@given("a directory that already has a store inside it, with content in that store", target_fixture="root")
def _directory_with_a_store_inside(root, before):
    _store_with_content(root)
    before.update(store=root, held=everything_under(root))
    return root


@given("a directory that sits inside a store", target_fixture="root")
def _directory_inside_a_store(root, before):
    _store_with_content(root)
    inside = root / "notes" / "drafts"
    inside.mkdir(parents=True)
    before.update(store=root, held=everything_under(root))
    return inside


@then("the store that is there holds what it held before")
@then("the store it sits inside holds what it held before")
def _store_holds_what_it_held(before):
    assert everything_under(before["store"]) == before["held"]
```

- [ ] **Step 3: The slice's own steps**

Append at the end of `tests/test_start_a_store.py`:

```python
UNRELATED = {"README.md": b"# The shop\n", "src/till.py": b"print('open')\n"}


@given("a directory holding files that have nothing to do with a store", target_fixture="root")
def _directory_holding_other_files(root):
    for name, data in UNRELATED.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_bytes(data)
    return root


@then("the store is made inside that directory, in a place of its own")
def _made_in_a_place_of_its_own(started, root):
    assert not started.faults, started.faults
    assert (root / "kb" / "store.yaml").is_file()
    assert sorted(path.name for path in root.iterdir()) == ["README.md", "kb", "src"]


@then("the files that were already there are left as they were, and none of them is the store's concern")
def _other_files_left_alone(client, root):
    for name, data in UNRELATED.items():
        assert (root / name).read_bytes() == data
    tracked = subprocess.run(
        ["git", "-C", str(root / "kb"), "ls-files"], capture_output=True, text=True, check=True,
    ).stdout.split()
    assert all(not name.startswith("..") for name in tracked), tracked
    checked = client.Validate(kb_pb2.ValidateRequest())
    assert (list(checked.faults), list(checked.violations), list(checked.stale)) == ([], [], [])


@then("starting the store is rejected because that directory already has a store inside it")
def _rejected_as_already_a_store(started, root):
    assert [(fault.rule, fault.message) for fault in started.faults] == [
        ("root", f"a store is never started over another; {str(root)!r} already has a store inside it"),
    ]


@then("starting the store is rejected because that directory is inside a store")
def _rejected_as_inside_a_store(started, root, before):
    assert [(fault.rule, fault.message) for fault in started.faults] == [
        ("root", f"stores do not nest; {str(root)!r} is inside the store at {str(before['store'])!r}"),
    ]
```

- [ ] **Step 4: Run it red for want of the refusals**

```bash
.venv/bin/python -m pytest -q -m slice-45 2>&1 | grep -E "^E  |passed|failed" | grep -E "Error|assert \[\] ==|passed|failed"
```

Expected: `2 failed, 1 passed, 115 deselected` on the last line. Scenario 2 fails with `FileExistsError: [Errno 17] File exists: '.../store/kb'`; scenario 3 with `assert [] == [('root', "stores do not nest; ...")]`.

- [ ] **Step 5: The refusals**

In `src/kb/values.py`, change the import `from kb import canonical` to

```python
from kb import canonical, discovery
```

(`kb.discovery` imports only `kb.contract`, so there is no cycle.) Then replace the whole of `def root(text: str) -> Path:` with:

```python
def root(text: str) -> Path:
    """The directory a store is started in, as the request names it; relative names stay relative. It must be a
    directory that is there, with nothing called kb/ inside it, and inside no store."""
    if not text:
        raise Refused([kb_pb2.Fault(
            rule="root",
            message="a store is started in a directory that was named and that exists; no directory was named",
        )])
    named = Path(text)
    if not named.exists():
        raise Refused([kb_pb2.Fault(
            rule="root", message=f"a store is started in a directory that exists; {text!r} does not",
        )])
    if not named.is_dir():
        raise Refused([kb_pb2.Fault(
            rule="root", message=f"a store is started in a directory, and {text!r} is not one",
        )])
    if (named / "kb").exists():
        raise Refused([kb_pb2.Fault(
            rule="root", message=f"a store is never started over another; {text!r} already has a store inside it",
        )])
    above = discovery.find_above(named.resolve().parent)
    if above is not None:
        raise Refused([kb_pb2.Fault(
            rule="root", message=f"stores do not nest; {text!r} is inside the store at {str(above)!r}",
        )])
    return named
```

- [ ] **Step 6: Run it green, and the suite**

```bash
.venv/bin/python -m pytest -q -m slice-45 2>&1 | tail -1
make test 2>&1 | grep -E "passed|failed" | tail -1
```

Expected: `3 passed, 115 deselected`; `12 failed, 106 passed`. Slice 1.16's scenario, which starts a store elsewhere while working inside one, stays green: the directory it names sits inside no store.

- [ ] **Step 7: Commit**

```bash
git add src/kb/values.py tests/conftest.py tests/test_start_a_store.py && git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 45: a store sits beside other things, and is not started twice or inside another

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 8: Checkpoint**

In `docs/superpowers/plans/2026-09-24-kb-slices.md`, set slice 45's Status to `green`. Append at the very end of the Log, and check with `tail` that it is last:

```
- <date> slice 45 green. Someone can now: start a store in a directory holding a project's files, the store in kb/ and none of the files its concern; and be refused starting one where a store already is, or inside one, the store there holding what it held.
  Surprised by: <nothing, or what>. "A directory holding other things" went green on its step definitions alone, red first for want of a step.
  Open questions:
  - QUESTION FOR THE SPEC: anything called kb inside the root, an empty directory or a file, is refused as "already has a store inside it", though no store is there. The spec says "when kb/ already exists"; should the message say only that? (Review Focus 3)
  - The shared Givens and Thens of slices 45 and 46 are in tests/conftest.py.
  Next: slice 46.
```

Commit the plan: `Slice 45 green`.

---

### Task 3: Slice 46, the operator looks after a store

**Slice plan entry:** Slice 46, capability. Unknown: none. Needs: kb's own console entry point (every scenario). Scenarios:

1. kb / look-after-a-store / The operator sets up a store
2. kb / look-after-a-store / Setting up a store where the directory already has one inside it is refused
3. kb / look-after-a-store / Setting up a store inside a store is refused
4. kb / look-after-a-store / The operator checks the whole store
5. kb / look-after-a-store / The command line does nothing to content
6. kb / look-after-a-store / Setting up a store without naming which role is refused
7. kb / look-after-a-store / The operator checks the store from a folder inside it
8. kb / look-after-a-store / The operator names the store instead of standing in it
9. kb / look-after-a-store / Running the command line where no store can be found is refused
10. kb / look-after-a-store / Naming a store that is not there is refused
11. kb / look-after-a-store / Standing in one store while naming another is refused

All eleven need the `kb` command. Once it exists, each goes green at once: the refusals are Task 2's and `discovery.locate`'s, and the check is `Validate`'s.

**Files:**
- Create: `src/kb/cli.py`
- Modify: `pyproject.toml` (`[project.scripts]`)
- Modify: `tests/test_look_after_a_store.py` (imports; steps and helpers appended)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: Task 1's `calls.next_version`. Task 2's `conftest.before`, its two Givens and two Thens, and its `values.root` refusals. `client.connect()`, `discovery.locate`'s refusal messages, `InitRequest`, `ValidateRequest`, the `root` fixture, and the Given `a store` in `conftest.py`.
- Produces: `kb.cli.main(argv: list[str] | None = None) -> int`, and the `kb` console script that calls it. Nothing later uses it.

- [ ] **Step 1: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-46 2>&1 | grep -E "^E |passed|failed" | tail -12
```

Expected: `11 failed, 107 deselected`, each a `StepDefinitionNotFoundError`. Eight fail for their Given; "The command line does nothing to content" for its When, `the operator asks what the command line offers`; and the two whose Given Task 2 put in `conftest.py` for their When, `the operator runs kb init against that directory, saying which role they are`.

- [ ] **Step 2: The steps**

In `tests/test_look_after_a_store.py`, replace the imports at the top of the file,

```python
import re

from pytest_bdd import given, scenarios, then, when

from calls import CLIENT, DECISION_TYPE, create, define
from kb import client as kb_client
from kb.contract import kb_pb2
```

with

```python
import os
import re
import subprocess
import sys
from pathlib import Path

from pytest_bdd import given, scenarios, then, when

from calls import CLIENT, DECISION_TYPE, create, define, next_version
from kb import canonical, client as kb_client
from kb.contract import kb_pb2
```

and append at the end of the file:

```python
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
```

- [ ] **Step 3: Run it red for want of the command**

```bash
.venv/bin/python -m pytest -q -m slice-46 2>&1 | grep -E "^E  |passed|failed" | sort | uniq -c | tail -3
```

Expected: `11 failed`, each with `FileNotFoundError: [Errno 2] No such file or directory: '.../.venv/bin/kb'`.

- [ ] **Step 4: The command**

In `pyproject.toml`, just above `[project.optional-dependencies]`, add:

```toml
[project.scripts]
kb = "kb.cli:main"

```

Create `src/kb/cli.py`:

```python
"""kb's own command line, for the operator: set a store up, and check one. Nothing else; every change to content goes
through a client.

Each command is one call on the in-process client. A refusal is printed to stderr and exits 2; a check that finds a
violation exits 1.
"""
import argparse
import os
import sys

from kb import client as kb_client
from kb.contract import kb_pb2

REFUSED, VIOLATED = 2, 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="kb", description="Look after a kb store.")
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="set up a store in a directory")
    init.add_argument("root", help="the directory the store is made inside, as its kb/ subdirectory")
    commands.add_parser("validate", help="check the store found here, or the one KB_ROOT names")
    args = parser.parse_args(argv)
    if args.command == "init":
        return _init(args.root)
    return _validate()


def _init(root: str) -> int:
    """Start a store under the role KB_ACTOR names."""
    role = os.environ.get("KB_ACTOR", "")
    if not role:
        return _refused("init", [kb_pb2.Fault(
            rule="actor", message="a store can only be started under a role, named through KB_ACTOR",
        )])
    started = kb_client.connect().Init(kb_pb2.InitRequest(root=root, actor=kb_pb2.Actor(role=role)))
    if started.faults:
        return _refused("init", started.faults)
    return 0


def _validate() -> int:
    """Check the store this directory finds: every violation, then every artifact behind its type, one to a line."""
    checked = kb_client.connect().Validate(kb_pb2.ValidateRequest())
    if checked.faults:
        return _refused("validate", checked.faults)
    for fault in checked.violations:
        print("\t".join(("violation", fault.artifact, fault.path, fault.rule, fault.message)))
    for stale in checked.stale:
        print(f"stale\t{stale.artifact}\tchecked against version {stale.schema_version} of its type, "
              f"which is at {stale.current}")
    return VIOLATED if checked.violations else 0


def _refused(command: str, faults) -> int:
    for fault in faults:
        print(f"kb {command}: refused: {fault.rule}: {fault.message}", file=sys.stderr)
    return REFUSED
```

Install it into the checkout's virtualenv, so that `.venv/bin/kb` exists:

```bash
.venv/bin/pip install -q -e '.[dev]' && ls .venv/bin/kb
```

Expected: `.venv/bin/kb`.

- [ ] **Step 5: Run it green, and the suite**

```bash
.venv/bin/python -m pytest -q -m slice-46 2>&1 | tail -1
make test 2>&1 | grep -E "passed|failed" | tail -1
```

Expected: `11 passed, 107 deselected`; `1 failed, 117 passed`.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml src/kb/cli.py tests/test_look_after_a_store.py && git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 46: the operator looks after a store

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 7: Checkpoint**

In `docs/superpowers/plans/2026-09-24-kb-slices.md`, set slice 46's Status to `green`. Append at the very end of the Log, and check with `tail` that it is last:

```
- <date> slice 46 green. Someone can now: run kb init to set up a store in a directory, under the role KB_ACTOR names, and be refused without one, over a store, or inside one; run kb validate from anywhere inside a store, or with KB_ROOT naming one, and be told every violation and every artifact behind its type, one to a line; be refused where no store is found, KB_ROOT names none, or it names a store other than the one they stand in; and find kb offers init and validate and nothing else.
  Surprised by: <nothing, or what>.
  Open questions:
  - QUESTION FOR THE SPEC: kb validate over a store holding a kind with no type prints a FileNotFoundError traceback and exits 1, the code it gives for violations found, so a script takes a crash for a report. (Review Focus 1; the raise is batch 2's open question.)
  - QUESTION FOR THE SPEC: KB_ROOT set but empty is refused from the shell as naming ".", slice 61's open question, now one an operator meets. (Review Focus 4)
  - The command's output and exit codes are this plan's: faults to stderr as "kb <command>: refused: <rule>: <message>", exit 2; violations then stale artifacts to stdout, one tab-separated line each, exit 1 when there is a violation and 0 otherwise. No scenario pins either beyond what the steps read.
  Next: slice 51.
```

Commit the plan: `Slice 46 green`.

---

### Task 4: Slice 51, the set's name finds the set in the history

**Slice plan entry:** Slice 51, capability. Unknown: none. Scenario:

1. kb / make-several-changes-in-one-go / The name given for a set finds the set in the history

**Files:**
- Modify: `src/kb/contract/kb.proto` (`JournalRequest`: `batch`), then `make contract`
- Modify: `src/kb/servicer.py` (`Journal`: the batch filter)
- Modify: `tests/calls.py` (`journal` takes `batch`)
- Modify: `tests/test_make_several_changes_in_one_go.py` (import; one step appended)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: the feature's Background, `a store holding a decision type and a work item` (fixture `client`), and its When (fixture `applied`, an `ApplyResponse`), with `DECISION` and `WORK_ITEM`. `calls.journal`.
- Produces: `kb_pb2.JournalRequest(batch=...)`, and `calls.journal(client, artifact="", role="", execution="", since="", batch="")`.

- [ ] **Step 1: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-51 2>&1 | grep -E "^E |passed|failed" | tail -2
```

Expected: `1 failed`, a `StepDefinitionNotFoundError` for its Then.

- [ ] **Step 2: The step**

In `tests/calls.py`, replace `journal`'s signature, docstring and loop header,

```python
def journal(client, artifact="", role="", execution="", since=""):
    """The journal's entries, narrowed to those about one artifact, made by one role, for one piece of work, or at or
    after a time, by whichever are given."""
    request = kb_pb2.JournalRequest(artifact=artifact)
    for name, value in (("role", role), ("execution", execution), ("since", since)):
```

with

```python
def journal(client, artifact="", role="", execution="", since="", batch=""):
    """The journal's entries, narrowed to those about one artifact, made by one role, for one piece of work, at or
    after a time, or landed in one set, by whichever are given."""
    request = kb_pb2.JournalRequest(artifact=artifact)
    for name, value in (("role", role), ("execution", execution), ("since", since), ("batch", batch)):
```

In `tests/test_make_several_changes_in_one_go.py`, replace

```python
from calls import CLIENT, DECISION_TYPE, WORK_ITEM_TYPE, apply, create, creation, define, read, replacement
```

with

```python
from calls import (
    CLIENT, DECISION_TYPE, WORK_ITEM_TYPE, apply, create, creation, define, journal, read, replacement,
)
```

and append at the end of the file:

```python
@then("the changes the history shows under the name the client was given for the set are exactly those two")
def _the_set_in_the_history(client, applied):
    assert not applied.faults, applied.faults
    shown = journal(client, batch=applied.batch)
    assert not shown.faults, shown.faults
    assert [(entry.op, entry.artifact, entry.revision, entry.batch) for entry in shown.entries] == [
        ("create", DECISION, 1, applied.batch), ("write", WORK_ITEM, 2, applied.batch),
    ]
```

- [ ] **Step 3: Run it red for want of the filter**

```bash
.venv/bin/python -m pytest -q -m slice-51 2>&1 | grep -E "^E  |passed|failed" | head -2
```

Expected: `1 failed`, with `AttributeError: Protocol message JournalRequest has no "batch" field.`

- [ ] **Step 4: The filter**

In `src/kb/contract/kb.proto`, replace `JournalRequest` and the comment above it with:

```proto
// Narrows the journal to the entries about one artifact, made under one
// role, for one piece of work, at or after a time (ISO 8601, a date alone
// meaning its midnight, UTC unless it says otherwise), or landed in one
// set, named by the batch Apply gave, by each one given; with none, every
// entry.
message JournalRequest {
  string artifact = 1;
  string role = 2;
  string execution = 3;
  string since = 4;
  string batch = 5;
}
```

Run `make contract`. `git status --short src/kb/contract` should list `kb.proto`, `kb_pb2.py` and `kb_pb2.pyi`.

In `src/kb/servicer.py`, in `Journal`, replace the docstring with

```python
        """The journal's entries, oldest first, narrowed by each of artifact, role, piece of work, time and set given."""
```

and add the last condition of the comprehension, so that its end reads:

```python
            and (since is None or datetime.fromisoformat(entry["at"]) >= since)
            and (not request.batch or entry["batch"] == request.batch)
        ])
```

- [ ] **Step 5: Run it green, and the suite**

```bash
.venv/bin/python -m pytest -q -m slice-51 2>&1 | tail -1
make test 2>&1 | grep -E "passed|failed" | tail -1
```

Expected: `1 passed, 117 deselected`; `118 passed`.

- [ ] **Step 6: Commit**

```bash
git add src/kb/contract/ src/kb/servicer.py tests/calls.py tests/test_make_several_changes_in_one_go.py && git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 51: the set's name finds the set in the history

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 7: Checkpoint**

In `docs/superpowers/plans/2026-09-24-kb-slices.md`, set slice 51's Status to `green`. Append at the very end of the Log, and check with `tail` that it is last:

```
- <date> slice 51 green. Someone can now: make two changes in one go and read, under the name given for the set, exactly those two in the history.
  Surprised by: <nothing, or what>.
  Open questions:
  - QUESTION FOR THE SPEC: a batch naming no set answers no entries and no fault; it is compared and never converted, as role and execution are. (Review Focus 5)
  - The question logged at the first cut (does the journal take the set's name as a filter, or does the client keep the entries that name it?) is answered: the journal takes it, as the spec's Journal row lists.
  Next: the whole-batch review.
```

Commit the plan: `Slice 51 green`.

---

## After slice 51

Not a slice. Every slice in the kb plan is then green. Run the whole-batch review over the commits of Tasks 1 to 4, using `superpowers:requesting-code-review` with this plan and the spec as the brief. Every finding goes to `slicing-into-increments`, which places it by its unknown. No finding is coded here.

The contract grows again in this batch (a Journal filter), kb gains a console command, and batches 3 to 5's additions are still unreleased. The version stays `0.1.0`. Whether to bump it and tag a release is the user's call, as the 0.1 tag was, and the review should say whether anything in this batch or the batch 5 findings stands in the way.
