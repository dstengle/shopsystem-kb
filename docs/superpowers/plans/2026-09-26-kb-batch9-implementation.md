# kb Batch 9 Implementation Plan: slices 73.1, 74 and 75

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Each task is one slice of `docs/superpowers/plans/2026-09-24-kb-slices.md`. Inside a capability task, follow `shopsystem-bdd:bdd-red-green` scenario by scenario; its stop conditions, hand-back and checkpoint apply, and they override any step here that conflicts with them. An enabling task (73.1) adds no scenario and changes no behaviour: its check is the suite's failing test ids unchanged and its structural target met.

**Goal:** The three slices before slice 76, the third architecture review:
- The check of the whole store leaves `validation.py` for a module of its own, and the two wordings batch 8 left stale are brought up to date (slice 73.1, enabling).
- Every shape of damage to a stored file, an empty file and a file holding a list among them, is the one named finding when the store is checked (slice 74).
- Content that is not a set of named entries is refused as it converts, with the reason and the place, and content of the wrong shape inside is refused by the type (slice 75).

**Architecture:** kb is the Python package `kb` in `/home/vscode/shopsystem-kb`. A protobuf contract (`kb.contract`) sits in front of `KbServicer` (`servicer.py`), whose every rpc runs inside one boundary that turns `values.Refused` into that rpc's faults. `requests.py`/`values.py` convert requests; `content.py` reads content crossing the contract; `canonical.py` is the one YAML checker, dump and load; `write.py` drafts a set and only then writes; `edits.py` says what each operation does to the draft; `validation.py` holds the composed schema and kb's own checks; `store.py` is files and git, and `Store.load` returns an artifact or `Damaged`. `CLAUDE.md` is the rulebook. This plan implements each rule it touches once:
- **A new concern gets a new module.** The check of the whole store, the only part of `validation.py` that asks the store for anything, becomes `check.py`, with a row in CLAUDE.md's module map (Task 1).
- **Loading returns a value (rule 3) and one canonical checker (rule 5).** "A stored artifact, and a whole artifact's content, is a set of named entries" is one function, `canonical.entries(text)`, which reads as `canonical.load` does and raises `NotCanonical` for a list, a single value or nothing. `Store.load` reads through it, so every such file becomes `Damaged` where every other damaged file already does (Task 2); `values.content` reads a whole artifact's content through it, so such content is refused as it converts (Task 3). No caller checks the shape itself.
- **Parse, don't validate (rule 2).** Content of the right root shape but the wrong shape inside (sections as text, options as one value, an option as a bare value) reaches the type check, which slice 66 and slice 73 already made refuse it with the place; nothing is added for those rows.

**Provenance:** Every code block here was assembled in a scratch clone of this repository (`/tmp/kb9`, cloned at `303b659`, run with this checkout's `.venv` and `PYTHONPATH=/tmp/kb9/src`) on 2026-09-26, and the tasks were applied in order, one commit each. The red and green results, the suite counts, the failing-id comparisons, the line counts and the Review Focus reproductions are what those runs gave. The plan was then replayed from its own text on a fresh clone (`/tmp/kb9-replay`, at `303b659`) by an agent that had not seen the scratch run: every "replace" and "delete" text was found verbatim once, every red, green, suite count, failing-id diff and line count matched, every file compiled, no import was left unused, and the 40 failures left were exactly the later slices listed below. Its one note on the text (Task 3's feature-file diff compared from one commit too far back) is fixed here. This repository was not touched except to write this plan and log it in the slice plan.

**Tech Stack:** Python 3.11, setuptools (src layout), protobuf + grpcio (generated code committed; no `.proto` change in this batch), python-jsonschema 4.26 with `referencing`, ruamel.yaml 0.19 (YAML 1.2), git via subprocess, pytest 9 + pytest-bdd 8.

**Spec:** `docs/superpowers/specs/2026-09-23-kb-design.md`, in particular:
- "Canonical YAML": one serialization, YAML 1.2, checked on the way in and on the way out.
- "Validate": every violation reported with its artifact, place and rule, the stale listed beside them, and a file that cannot be read reported as a violation.
- "Write path", step 4: "Collect every error; if any, stop here."

The slice plan is `docs/superpowers/plans/2026-09-24-kb-slices.md`, and the feature files are in `features/`. Each capability slice's scenarios carry `@slice-<n>`, so `.venv/bin/python -m pytest -q -m slice-74` runs one slice. `CLAUDE.md` at the repository root is binding.

## Global Constraints

- Feature files are read-only for the implementer. Only `slicing-into-increments` edits a tag line, and only `formulating-features` edits a Given, When, or Then. Any diff under `features/` is a stop condition; this batch touches none.
- Code only what a scenario asserts (bdd-red-green). Where the scenarios are silent, the code is silent too, and the silence goes into the checkpoint entry as an open question. The decisions this plan makes are listed below, each tied to the scenario or slice that asks for it.
- **CLAUDE.md's rules are implemented once, never per row.** No rpc in `servicer.py` gains a `try`, a check, or a branch in this batch (`grep -c "try:" src/kb/servicer.py` stays `1`). No module but `canonical.py` decides that a document is a set of named entries; no reader of a stored file or of content tests the shape of what it loaded. No module catches a broad exception.
- **Extend, never add beside.** A new concern gets a new module (`check.py`), and it goes into CLAUDE.md's module map in the task that makes it. Test helpers live in `tests/calls.py`; a step two feature files share word for word is one step definition in `tests/conftest.py`, never two.
- **Size.** No module over 250 lines; `servicer.py` under 150. After Task 1, `validation.py` is 153 lines and `check.py` 33; after Task 2, `canonical.py` is 196; after Task 3, `values.py` is 216 and `content.py` 31.
- Errors are a typed list of `{ artifact, path, rule, message }`. A response that carries faults is a refusal, and nothing was written.
- kb is exercised through its in-process transport (`kb.client.connect`).
- `make test` runs the suite in this checkout's virtualenv (`.venv/bin/python -m pytest -q`). While any scenario is red, make's own error line comes last, so the steps run pytest directly to see the summary. A worktree needs its own `.venv` first (`make dev`).
- The contract's version stays `0.1`, `pyproject.toml` stays `0.1.0`. Version and tag are the user's call.
- Work on `main` in `/home/vscode/shopsystem-kb`. shop-knowledge pins kb at `v0.1.0`; nothing here touches or runs its suite.
- Commits: `git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit`, the message ending with the Co-Authored-By line of the model that made the commit, e.g. `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- "Append at the end of the file" means after two blank lines, as the files' top-level definitions are spaced.
- The suite prints pytest-bdd `PytestRemovedIn10Warning`s. That is the baseline, not a fault. The summary lines quoted as Expected leave out the `, N warnings in Xs` that pytest adds.
- Baseline before Task 1: `.venv/bin/python -m pytest -q` → `54 failed, 142 passed`. After Tasks 1 to 3 the suite reads `54/142`, `47/149` and `40/156` (failed/passed). Every failure left after Task 3 is tagged for slice 77 or later (77: 1, 78: 1, 79: 2, 80: 3, 81: 1, 82: 3, 84: 1, 85: 3, 86: 2, 87: 2, 88: 7, 89: 2, 91: 4, 92: 2, 93: 3, 94: 3), and none of those goes green early.
- An enabling task's first step saves the failing ids (`.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before`), and its check compares them after (`... | sort | diff /tmp/failing-before -` prints nothing).

## Decisions this plan makes (the spec left them open or silent)

1. **The store-wide check is `check.py` (slice 73.1).** `check.everything(store: Store) -> kb_pb2.ValidateResponse` is `validation.check` moved as it stands, with its helper `_with_type`; the servicer's `Validate` calls it. `validation.py` keeps `compose`, `registry`, `validate` and the checks, and no longer imports `canonical` or `kb.store`. The name `everything` reads as what it checks at the call site, `check.everything(self._store)`.
2. **The two stale wordings (slice 73.1, from the batch 8 review).** `validation.py`'s docstring still said JSON Schema runs "in one pass, then" kb's checks, which slice 73 changed to running beside them, and that a link lands "on an artifact", which slice 72 widened to a part inside one; it now also says that nothing in the module finds or opens a file. CLAUDE.md's `names.py` row still said "artifact and item ids" only; since slice 71.1 `names.py` also writes and reads an artifact's name, a link's place and a type's `kb:` reference, and the row says so.
3. **Shared check steps (slice 74).** The When `the client checks the store`, the Then `that file is reported as a violation, naming the file` and the And `the check comes back with its answer rather than breaking off` are word for word the same in check-the-store (slice 1.20) and a-file-the-store-cannot-read (slice 74). They move from `tests/test_check_the_store.py` to `tests/conftest.py`, unchanged. `everything else in the store is checked and reported alongside it` stays one definition per module, since each Background leaves different things beside the damaged file: in slice 74's, the process and the tag fit their types, so the one violation is the damaged decision and nothing is stale.
4. **One rule of a document's shape (slices 74 and 75).** `canonical.entries(text) -> dict` loads as `canonical.load` does, then raises `NotCanonical("content is a set of named entries; this is <a list | nothing at all | the single value 'x'>")` for anything that is not a mapping. A stored file is damaged by it (`Store.load`), and so is a whole artifact's content (`values.content` with `at_root`). Content aimed at a place inside an artifact is still read by `content.loads`, since a place may hold a list or a single value; an item added to a collection is still read that way too (Review Focus 1). The journal's entries are slice 79's and are not changed.
5. **The place named for content that makes no sense (slice 75).** For content that is not a set of named entries, the place is the content as a whole, `path` empty, as every root-level content fault already is; for content that cannot be read at all, the message names the line (`... at line 7`). For content of the wrong shape inside, the place is where JSON Schema found it: `sections`, `options`, `options/0`, rule `type`. A whole Write, and a create inside an Apply, convert through the same function, so they refuse the same content the same way; no scenario pins either.

## Review Focus

In this project, tests are scenarios, and the feature files are the human gate, so no unit tests are added. Instead, each line below goes into the owning task's checkpoint entry as a `QUESTION FOR THE SPEC`, with the reproduction given here. Each was reproduced in scratch after all three tasks.

1. **An item that is a bare value holding the letters "id" crashes an addition.** Reproduction: a decision `decision/d-one`; Append to `decision/d-one` at `options` the content `a valid idea\n`. It raises `TypeError: string indices must be integers, not 'str'` through the client, since `values.item` asks `"id" in` the tree, which for text is a substring test. `just words\n` is refused with `options/0 type`, as a person expects. Whether an item, like a whole artifact, must be a set of named entries as it converts is for the spec; slice 75's scenario is about Create. Task 3 logs it.
2. **A stored file whose bytes are not UTF-8 still breaks the check off.** Reproduction: write the bytes `ff fe 00 62 61 64` over a decision's file; Validate raises `UnicodeDecodeError` through the client. Slice 74's outline has no row for it; the question logged on 2026-09-26 (a row "in bytes that are not text at all") is still open. Task 2 logs that it is unchanged.
3. **A stored file that is a set of named entries but lacks what the store settles breaks the check off.** Reproduction: write `title: D one\n` over a decision's file; Validate raises `KeyError: 'schema_version'` from `check.everything`. A person expects a violation naming the file. Task 2 logs it.
4. **A stored artifact of the wrong shape inside breaks a search, though the check reports it.** Reproduction: a decision's file with `sections: oops` in place of its sections list; Validate reports `sections type`, but Search for `a` raises `TypeError: string indices must be integers, not 'str'`. Task 2 logs it.
5. **A type file that cannot be read is reported once for itself and once for every artifact of its kind.** Reproduction: two decisions; write `- a\n` over `kb/schema/decision.yaml`; Validate reports the same `schema/decision` `unreadable` fault three times. Slice 79 makes a type that cannot be read a named fault for a create; nothing says how often the check reports it. Task 2 logs it.

---

### Task 1: Slice 73.1, the check of the whole store is its own module

**Slice plan entry:** Slice 73.1, enabling. Unknown: none. Check: the suite's failing ids unchanged; `grep -nE "def check|store\.(ids|load)\(|Store\b|Damaged" src/kb/validation.py` → no lines (9 before); CLAUDE.md's module map has a row for the new module. This task also carries the two wordings batch 8 left stale: `validation.py`'s docstring and CLAUDE.md's `names.py` row.

**Files:**
- Create: `src/kb/check.py`
- Modify: `src/kb/validation.py` (docstring, imports, `check` and `_with_type` out)
- Modify: `src/kb/servicer.py` (`Validate` calls `check.everything`)
- Modify: `CLAUDE.md` (the `names.py` row; a row for `check.py`), `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `validation.validate(artifact_id: str, content: dict, schema: dict, corpus) -> list[kb_pb2.Fault]`; `store.Store`, `store.Damaged`; `values.type_of(kind) -> ArtifactId`; `canonical.IDENTITY`.
- Produces: `check.everything(store: Store) -> kb_pb2.ValidateResponse`, answering as `validation.check` did. `validation.check` no longer exists. Task 2 reads through `check.everything` unchanged.

- [ ] **Step 1: Save the failing ids and count**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
wc -l < /tmp/failing-before
grep -nE "def check|store\.(ids|load)\(|Store\b|Damaged" src/kb/validation.py | wc -l
```

Expected: `54`; `9`.

- [ ] **Step 2: `check.py`**

Create `src/kb/check.py`:

```python
"""The check of the whole store: every artifact against the current version of its type, the stale listed beside
the violations, and a file that cannot be read reported as the file it is, the check going on past it."""
from kb import canonical, validation, values
from kb.contract import kb_pb2
from kb.store import Damaged, Store


def everything(store: Store) -> kb_pb2.ValidateResponse:
    """Every artifact checked against the current version of its type, and listed as stale when it was last
    checked against an older one; a file that cannot be read is reported and the check goes on."""
    violations, stale = [], []
    for artifact_id in store.ids():
        loaded = _with_type(store, artifact_id)
        if isinstance(loaded, Damaged):
            violations.append(loaded.fault)
            continue
        artifact, schema = loaded
        if artifact["schema_version"] < schema["version"]:
            stale.append(kb_pb2.Stale(
                artifact=str(artifact_id), schema_version=artifact["schema_version"], current=schema["version"],
            ))
        content = {key: value for key, value in artifact.items() if key not in canonical.IDENTITY[:4]}
        violations += validation.validate(str(artifact_id), content, schema["schema"], store)
    return kb_pb2.ValidateResponse(violations=violations, stale=stale)


def _with_type(store: Store, artifact_id) -> tuple[dict, dict] | Damaged:
    """The artifact and its type as stored, or the damage of the first of them whose file cannot be read."""
    artifact = store.load(artifact_id)
    if isinstance(artifact, Damaged):
        return artifact
    schema = store.load(values.type_of(artifact_id.kind))
    return schema if isinstance(schema, Damaged) else (artifact, schema)
```

- [ ] **Step 3: `validation.py` checks what it is given**

In `src/kb/validation.py`, delete the two functions `check` and `_with_type`, from the line `def check(store: Store) -> kb_pb2.ValidateResponse:` up to, not including, the line `def _lands(target: str, ref: dict, corpus) -> bool:`, with the two blank lines after `_with_type`. What goes is exactly the body of Step 2's two functions, under the names `check` and `_with_type`, with `validate(` in place of `validation.validate(`.

Replace the imports

```python
from kb import canonical, links, values
from kb.composition import composition, declared, type_schema
from kb.contract import kb_pb2
from kb.store import Damaged, Store
```

with

```python
from kb import links, values
from kb.composition import composition, declared, type_schema
from kb.contract import kb_pb2
```

Replace the module docstring

```python
"""Schema validation: the type's JSON Schema composed with kb's own structural rules, checked in one pass, then
what the schema language cannot say, checked in code: required sections in their declared order, and links that
land on an artifact the corpus holds, of a kind the type allows. kb's keywords are read through kb.composition.
"""
```

with

```python
"""Schema validation: the type's JSON Schema composed with kb's own structural rules, and beside it what the schema
language cannot say, checked in code: required sections in their declared order, and links that land on an artifact
the corpus holds, or a part inside it, of a kind the type allows. Every fault comes back together; kb's rules pass
over a node JSON Schema found misshapen. kb's keywords are read through kb.composition. What is checked, and the
corpus it is checked against, are given; nothing here finds or opens a file.
"""
```

- [ ] **Step 4: The servicer calls it**

In `src/kb/servicer.py`, replace

```python
from kb import query, read, requests, validation, values, write
```

with

```python
from kb import check, query, read, requests, values, write
```

and replace

```python
        return validation.check(self._store)
```

with

```python
        return check.everything(self._store)
```

- [ ] **Step 5: The module map**

In `CLAUDE.md`, replace the row

```markdown
| `names.py` | minting, uniqueness, reuse and grammar of artifact and item ids | I/O |
```

with

```markdown
| `names.py` | the grammar of artifact and item names; how an artifact's name, a link's place inside one and a type's `kb:` reference are written and read; minting, uniqueness and reuse of item names | I/O |
```

and insert after the row beginning `` | `validation.py` | ``:

```markdown
| `check.py` | the check of the whole store: every artifact against the current version of its type, the stale listed beside the violations, a file that cannot be read reported and passed over | checks of its own, writes |
```

- [ ] **Step 6: The check**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before -
.venv/bin/python -m pytest -q 2>&1 | tail -1
grep -nE "def check|store\.(ids|load)\(|Store\b|Damaged" src/kb/validation.py
grep -rn "validation\.check" src/kb tests
grep -c "try:" src/kb/servicer.py
wc -l src/kb/validation.py src/kb/check.py src/kb/servicer.py
grep -c '`check.py`' CLAUDE.md
```

Expected: no diff; `54 failed, 142 passed`; no lines; no lines; `1`; `153`, `33` and `101`; `1`.

- [ ] **Step 7: Checkpoint and commit**

Append the slice 73.1 checkpoint to the slice plan's log (the check's results, before and after, and the two wordings brought up to date), and set slice 73.1's Status to `green`.

```bash
git add src/kb CLAUDE.md docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 73.1: The check of the whole store is its own module

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Slice 74, every shape of damage to a stored file is the one finding

**Slice plan entry:** Slice 74, capability. Unknown: does the one canonical check, applied to what the store loads, catch every shape of damage before anything reads the file as an artifact? Scenario:

- kb / a-file-the-store-cannot-read / Every shape of damage to a stored file is the one named finding (seven rows)

The answer to the unknown, found in scratch: for five of the seven shapes, yes, already: a mangled file, a second document, a tag, an alias and an entry named twice are each `NotCanonical`, which `Store.load` turns into `Damaged`, and those rows pass as soon as their steps exist. An empty file and a file holding a list are plain YAML, so `canonical.load` gives `None` and a list, and the check breaks off reading them as an artifact. The shape of a document becomes part of the one canonical reading.

**Files:**
- Modify: `tests/conftest.py` (three check steps moved in), `tests/test_check_the_store.py` (the same three moved out), `tests/test_a_file_the_store_cannot_read.py` (the damage Given, this feature's "everything else")
- Modify: `src/kb/canonical.py` (new `entries`, `_shape`), `src/kb/store.py` (`Store.load` reads through `entries`)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: Task 1's `check.everything(store)`.
- Produces: `canonical.entries(text: str) -> dict`, raising `canonical.NotCanonical` with the message `content is a set of named entries; this is a list` (or `this is nothing at all`, or `this is the single value 'x'`) for a document that is not a mapping. Task 3 reads a whole artifact's content through it. `Store.load` returns `Damaged` for such a file. In the tests, `conftest.py` defines the When `the client checks the store` (fixture `checked`) and the two Thens moved with it.

- [ ] **Step 1: The steps**

First save the failing ids, so Step 4 can say which went green:

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
wc -l < /tmp/failing-before
```

Expected: `54`.

The When and two of the three Thens are already defined, word for word, in `tests/test_check_the_store.py` for slice 1.20. A step definition in a test module serves that module only, so they move to `tests/conftest.py`, where both feature files find them.

In `tests/test_check_the_store.py`, delete

```python
@when("the client checks the store", target_fixture="checked")
def _check_the_store(client):
    return client.Validate(kb_pb2.ValidateRequest())


@then("that file is reported as a violation, naming the file")
def _reported_as_unreadable(checked):
    unreadable = [fault for fault in checked.violations if fault.rule == "unreadable"]
    assert [fault.artifact for fault in unreadable] == ["decision/price-reviews-happen-weekly"]
    assert "decision/price-reviews-happen-weekly.yaml cannot be read" in unreadable[0].message


```

and delete

```python


@then("the check comes back with its answer rather than breaking off")
def _answers(checked):
    assert isinstance(checked, kb_pb2.ValidateResponse)
    assert not checked.faults, checked.faults
```

and replace its first line

```python
from pytest_bdd import given, scenarios, then, when
```

with

```python
from pytest_bdd import given, scenarios, then
```

In `tests/conftest.py`, replace

```python
from pytest_bdd import given, then
```

with

```python
from pytest_bdd import given, then, when
```

and append at the end of the file:

```python
@when("the client checks the store", target_fixture="checked")
def _check_the_store(client):
    return client.Validate(kb_pb2.ValidateRequest())


@then("that file is reported as a violation, naming the file")
def _reported_as_unreadable(checked):
    unreadable = [fault for fault in checked.violations if fault.rule == "unreadable"]
    assert [fault.artifact for fault in unreadable] == ["decision/price-reviews-happen-weekly"]
    assert "decision/price-reviews-happen-weekly.yaml cannot be read" in unreadable[0].message


@then("the check comes back with its answer rather than breaking off")
def _answers(checked):
    assert isinstance(checked, kb_pb2.ValidateResponse)
    assert not checked.faults, checked.faults
```

In `tests/test_a_file_the_store_cannot_read.py`, append at the end of the file. The Given's pattern lists the seven damages exactly, so it never matches slice 63's Given `... left it in a shape the store cannot read`, which `conftest.py` defines.

```python
DAMAGE = {
    "in a shape that cannot be read at all": lambda held: "title: [a bracket opened by hand and never closed\n",
    "empty, with nothing in it": lambda held: "",
    "holding a list rather than a set of named entries": lambda held: "- title: Price reviews happen weekly\n- revision: 1\n",
    "holding a second document after the first": lambda held: held + "---\n" + held,
    "telling a reader how to build one of its values": lambda held: held + "reviewed: !!str Monday\n",
    "pointing back at a value written elsewhere in it": lambda held: held + "reviewed: &day Monday\ndecided: *day\n",
    "naming the same entry twice": lambda held: held + "title: Price reviews happen monthly\n",
}


@given(parsers.re(f"someone edited the decision's file by hand and left it (?P<damage>{'|'.join(map(re.escape, DAMAGE))})"))
def _decision_file_damaged_by_hand(root, damage):
    """The Background's decision left damaged in one way, the rest of what it wrote left as it was."""
    decision = root / "kb" / f"{DECISION}.yaml"
    decision.write_text(DAMAGE[damage](decision.read_text()))


@then("everything else in the store is checked and reported alongside it")
def _the_rest_checked_alongside(checked):
    assert [(fault.artifact, fault.path, fault.rule) for fault in checked.violations] == [(DECISION, "", "unreadable")]
    assert list(checked.stale) == []
```

- [ ] **Step 2: Run it red**

```bash
.venv/bin/python -m pytest -q -m "slice-74 or slice-1.20 or slice-43 or slice-63" -rf 2>&1 | grep -E "^E  +TypeError|^FAILED"
.venv/bin/python -m pytest -q -m "slice-74 or slice-1.20 or slice-43 or slice-63" 2>&1 | tail -1
```

Expected: `E           TypeError: 'NoneType' object is not subscriptable` and `E           TypeError: list indices must be integers or slices, not str`, and the two failures `...[empty, with nothing in it]` and `...[holding a list rather than a set of named entries]`; `2 failed, 17 passed, 177 deselected`. The other five rows pass on their steps alone, and slices 1.20, 43 and 63 still pass through the moved steps.

- [ ] **Step 3: A document's shape is part of the one canonical reading**

In `src/kb/canonical.py`, replace

```python
def _unreadable(error: YAMLError) -> str:
```

with

```python
def entries(text: str) -> dict:
    """Plain YAML 1.2 that is a set of named entries, as an artifact always is: read as `load` reads it. Text that is
    anything else, a list, a single value or nothing, raises NotCanonical saying what it is."""
    loaded = load(text)
    if not isinstance(loaded, dict):
        raise NotCanonical(f"content is a set of named entries; this is {_shape(loaded)}")
    return loaded


def _shape(value) -> str:
    if value is None:
        return "nothing at all"
    if isinstance(value, list):
        return "a list"
    return f"the single value {value!r}"


def _unreadable(error: YAMLError) -> str:
```

In `src/kb/store.py`, in `Store.load`, replace

```python
            return canonical.load(path.read_text(encoding="utf-8"))
```

with

```python
            return canonical.entries(path.read_text(encoding="utf-8"))
```

`Store.load` already turns `NotCanonical` into `Damaged` naming the file, and every reader already handles `Damaged`, so nothing else changes: the check reports the file and goes on, and every other call refuses it with the file named, as slice 63 made them.

- [ ] **Step 4: Run it green**

```bash
.venv/bin/python -m pytest -q -m slice-74 2>&1 | tail -1
.venv/bin/python -m pytest -q 2>&1 | tail -1
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before - | grep -c "^<"
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before - | grep -c "^>"
wc -l src/kb/canonical.py src/kb/store.py
```

Expected: `7 passed, 189 deselected`; `47 failed, 149 passed`; `7` (slice 74's rows, gone from the failures); `0` (nothing newly failing); `196` and `197`.

- [ ] **Step 5: Checkpoint and commit**

Append the slice 74 checkpoint, with the answer to its unknown (five shapes were caught already; an empty file and a list are now caught by `canonical.entries`, read by `Store.load`), and Review Focus 2, 3, 4 and 5 as `QUESTION FOR THE SPEC` lines with their reproductions (2 as "still open, unchanged by this slice"). Set slice 74's Status to `green`.

```bash
git add src/kb tests docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 74: Every shape of damage to a stored file is the one finding

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Slice 75, content the store cannot make sense of is refused

**Slice plan entry:** Slice 75, capability. Unknown: can content that is not a set of named entries be refused as it converts, with the place named, before anything checks it against a type? Needs slice 66's collections in the composed schema (its rows on options). Scenario:

- kb / create-an-artifact / Content the store cannot make sense of is refused (seven rows)

The answer to the unknown, found in scratch: yes, by reading a whole artifact's content through Task 2's `canonical.entries`. Four rows pass as soon as their steps exist: content that cannot be read was already refused as it converts, and the three rows of the wrong shape inside are refused by the type at their place (slices 66 and 73). Content that is a list or a single value breaks off in `edits._create` at `{"title": ..., **content}`, and content with nothing in it reads as `{}` and is refused for its missing sections rather than as content that is not a set of named entries.

**Files:**
- Modify: `tests/test_create_an_artifact.py` (`import re`; the When, the Then and the And, appended)
- Modify: `src/kb/content.py` (new `entries`), `src/kb/values.py` (`content` reads a whole artifact's content through it)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: Task 2's `canonical.entries(text) -> dict`. In the test module: `_raw(client, text)`, which sends a Create of a decision titled `Price reviews happen weekly` with the text as written; `everything_under(root)`; and the existing Then `nothing is written anywhere in the store`, which compares `attempt["after"]` with `attempt["before"]`.
- Produces: `content.entries(text: str) -> dict`, raising `canonical.NotCanonical`. `values.content(text, at_root=True)` gives `Content(None, (("", "content", "content is a set of named entries; this is ..."),))` for such text; with `at_root=False` it reads as before. In the test module, the fixture `attempt` of this When is a dict with `response`, `before`, `after` and `place`.

- [ ] **Step 1: The steps**

In `tests/test_create_an_artifact.py`, replace the first line

```python
from pytest_bdd import given, parsers, scenarios, then, when
```

with

```python
import re

from pytest_bdd import given, parsers, scenarios, then, when
```

and append at the end of the file. The When's pattern lists the seven contents exactly, so it never matches the existing Whens `the client creates a decision from that content, ...` and `... from content holding two documents one after the other, ...`.

```python
WHOLE = "sections:\n  - title: Purpose\n    body: Why.\n  - title: Rationale\n    body: Because.\n"
SENSELESS = {
    "content that cannot be read as written at all": (WHOLE + "options: [Keep weekly\n", ""),
    "content that is a list rather than a set of named entries": ("- Purpose\n- Rationale\n", ""),
    "content that is a single bare value": ("Keep prices in step with costs.\n", ""),
    "content with nothing in it at all": ("", ""),
    "content whose sections are one line of text rather than sections":
        ("sections: Keep prices in step with costs.\n", "sections"),
    "content whose options are a single value rather than a collection": (WHOLE + "options: Keep weekly\n", "options"),
    "content one of whose options is a bare value": (WHOLE + "options:\n  - Keep weekly\n", "options/0"),
}


@when(
    parsers.re(f"the client creates a decision from (?P<senseless>{'|'.join(map(re.escape, SENSELESS))}), "
               "saying which role and why"),
    target_fixture="attempt",
)
def _create_from_senseless_content(root, client, senseless):
    before = everything_under(root)
    text, place = SENSELESS[senseless]
    response = _raw(client, text)
    return {"response": response, "before": before, "after": everything_under(root), "place": place}


REASONS = {
    "content cannot be read as written": ("content", "it is not YAML that can be read"),
    "content is a set of named entries": ("content", "content is a set of named entries"),
    "the content does not fit the type": ("type", "is not of type"),
}


@then(parsers.re(
    f"the artifact is rejected because (?P<reason>{'|'.join(map(re.escape, REASONS))}), "
    "and the place it went wrong is named"
))
def _rejected_for_senseless_content(attempt, reason):
    refused, (rule, words) = attempt["response"], REASONS[reason]
    assert (refused.id, refused.revision) == ("", 0)
    assert [(fault.path, fault.rule) for fault in refused.faults] == [(attempt["place"], rule)]
    assert words in refused.faults[0].message


@then("the call comes back with its answer rather than breaking off")
def _the_call_answers(attempt):
    assert isinstance(attempt["response"], kb_pb2.CreateResponse)
    assert attempt["response"].faults
```

The place of content that is not a set of named entries is the content as a whole, `path` empty; for content that cannot be read at all, the message names the line (`... at line 7`) as it did before this slice.

- [ ] **Step 2: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-75 -rf 2>&1 | grep -E "^E  +(TypeError|AssertionError)|^FAILED"
.venv/bin/python -m pytest -q -m slice-75 2>&1 | tail -1
```

Expected: `E       TypeError: 'list' object is not a mapping`, `E       TypeError: 'str' object is not a mapping` and `E       AssertionError: assert [('sections',..., 'sections')] == [('', 'content')]`, for the rows `content that is a list ...`, `content that is a single bare value` and `content with nothing in it at all`; `3 failed, 4 passed, 189 deselected`.

- [ ] **Step 3: A whole artifact's content is a set of named entries as it converts**

In `src/kb/content.py`, replace

```python
def text(value) -> str:
```

with

```python
def entries(text: str) -> dict:
    """A whole artifact's content: a set of named entries, read plainly. Raises canonical.NotCanonical for text that
    is anything else, nothing at all included."""
    return canonical.entries(text)


def text(value) -> str:
```

In `src/kb/values.py`, replace

```python
from kb.content import loads
```

with

```python
from kb.content import entries, loads
```

and, in `content`, replace

```python
        tree = loads(text)
```

with

```python
        tree = entries(text) if at_root else loads(text)
```

`content` already turns `NotCanonical` into a problem at the fault's place with rule `content`, and `edits._create` refuses a Create carrying one before it looks at the type. Content aimed at a place, and an item, are still read by `loads`, since a place may hold a list or a single value.

- [ ] **Step 4: Run it green**

```bash
.venv/bin/python -m pytest -q -m slice-75 2>&1 | tail -1
.venv/bin/python -m pytest -q 2>&1 | tail -1
wc -l src/kb/values.py src/kb/content.py
```

Expected: `7 passed, 189 deselected`; `40 failed, 156 passed`; `216` and `31`.

- [ ] **Step 5: The batch's failures are all later slices'**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sed 's/\[.*//' | sort | uniq -c
.venv/bin/python -m pytest -q -m "slice-74 or slice-75" 2>&1 | tail -1
git diff --stat HEAD~2 -- features
```

Expected: 40 failures across the test functions of slices 77 to 82, 84 to 89 and 91 to 94 (counts as in Global Constraints), and none of slices 74 or 75; `14 passed, 182 deselected`; no output (no feature file touched since the batch began; Tasks 1 and 2 are the two commits before this one).

- [ ] **Step 6: Checkpoint and commit**

Append the slice 75 checkpoint, with the answer to its unknown, and Review Focus 1 as a `QUESTION FOR THE SPEC` line with its reproduction. Set slice 75's Status to `green`. Then append a log line that slices 73.1, 74 and 75 are green, the suite `40 failed, 156 passed`, every failure tagged 77 or later, and `Next: slice 76, the third architecture review.`

```bash
git add src/kb tests docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 75: Content the store cannot make sense of is refused

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```
