# kb Batch 12 Implementation Plan: slices 90.1 to 94.2, between the fifth and sixth architecture reviews

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Each task is one slice of `docs/superpowers/plans/2026-09-24-kb-slices.md`. Inside a capability task, follow `shopsystem-bdd:bdd-red-green` scenario by scenario; its stop conditions, hand-back and checkpoint apply, and they override any step here that conflicts with them. An enabling task (90.1, 94.1, 94.2) adds no scenario and changes no scenario's answer: its check is the suite's failing test ids unchanged, its structural target met, and a probe giving the answer the plan names.

**Goal:** The seven slices after slice 90, the fifth architecture review, up to slice 95, the sixth, leaving out slice 89.2, which is blocked awaiting approval:
- A place inside an artifact is written and read in one place (slice 90.1, enabling).
- The history answers every filter plainly, and says where a change landed (slice 91).
- Prose is kept as written or refused (slice 92).
- A snapshot asked for wrongly is refused (slice 93).
- A store's corner is never taken over, and a client readied early can start one (slice 94).
- Which type a kind names is asked of composition alone, by every reader (slice 94.1, enabling).
- What a title gives is worked out in one place (slice 94.2, enabling).

**Not in this plan:** slice 89.2, "The client follows the links out of one place inside an artifact". Its Given has a section carry a link, which the spec says a section never does; the slice plan's log holds the RE-FORMULATE entry, the proposed rewrite and the question. No task here touches that scenario, and it stays red (tagged `@slice-89.2`). Slice 95, the sixth architecture review, is run by `slicing-into-increments` once these land, as slice 90 was; it is not a task here.

**Architecture:** kb is the Python package `kb` in `/home/vscode/shopsystem-kb`. A protobuf contract (`kb.contract`) sits in front of `KbServicer` (`servicer.py`), whose every rpc runs inside one boundary that turns `values.Refused` into that rpc's faults. `requests.py`/`values.py` convert requests; `canonical.py` is the one YAML checker, dump and load; `settled.py` is what the store settles for every artifact; `write.py` drafts a set and only then writes; `edits.py` says what each operation does to the draft; `names.py` is the grammar of names and the minting of item names; `places.py` resolves a place inside an artifact; `validation.py` holds the composed schema and kb's own checks; `composition.py` reads a type through what it is built on and says which type a kind names; `definitions.py` checks a type as it is written; `check.py` is the check of the whole store; `links.py` is the one reading of links; `read.py` and `query.py` answer reads and questions; `store.py` is files, git and discovery, and `Store.load` returns an artifact or `Damaged`. `CLAUDE.md` is the rulebook. This plan implements each rule it touches once:
- **Names live in one place (rule 6), with the module map.** How a place inside an artifact is written and read back is `names.placed` and `names.steps`, asked by the conversion of a locator, by every refusal naming a place and by what a change records (Task 1), so slice 91 records a placed write's place the same way (Task 2). Which values a title may be written as to give a name is `names.title` (Task 7); a new artifact's name, or its title's faults and the name they are said of, is `values.named` alone (Task 7).
- **Which type a kind names is composition's (the map, rule 3's readers).** Every reader asks `composition.kind_schema`, which asks `composition.kind_type`; the store and the draft keep no lookup of their own (Task 6).
- **One canonical checker (rule 5), applied to bytes before writing.** Prose the store could not write back as its one block is refused where the store lays prose down, in `canonical.py`'s prose representer, so every write path refuses it through the fault `write.py` already makes of a text that cannot be written (Task 3).
- **Parse, don't validate (rule 2).** A snapshot's actor is converted with its role and piece of work required, in `values.py`, before the domain is called (Task 4).
- **Fail-closed boundary (rule 1).** No rpc gains a `try`. The crashes Task 6 makes unreachable are made so by one function every reader asks, never by a catch.

**Provenance:** Every code block here was assembled in a scratch clone of this repository (`/tmp/kb12`, cloned at `c47ef15`, run with this checkout's `.venv` and `PYTHONPATH=/tmp/kb12/src`) on 2026-09-26, and the tasks were applied in order, one commit each. The red and green results, the suite counts, the failing-id comparisons, the line counts, the probes and the Review Focus reproductions are what those runs gave. This repository was not touched except to write this plan and the slice plan's entries. The plan was then replayed from its text alone, in the foreground of the same session, in a second clone (`/tmp/kb12-replay`, from `c47ef15`, `PYTHONPATH=/tmp/kb12-replay/src`): every code block taken verbatim from this file by its place in its task, every replacement found exactly as many times as the step says, every command run as written. Every Expected held: the red runs and their messages, the suite counts (`13/183`, `9/187`, `7/189`, `4/192`, `1/195`, `1/195`, `1/195`), the failing-id diffs, the probes before and after, the greps and the line counts; the one failure left is slice 89.2's, with no diff under `features/`, and the replayed `src/` and `tests/` are the scratch run's. The replay found two faults in this text, both corrected here and re-run: Task 7's replacement in `requests.py` ended part-way through the `return Create(` line and matched nothing, and Task 5's run of the whole test module reads `2 failed, 11 passed`, not `13`. The scratch run's `write.py` line was wrapped under 120 columns in this text, which the replay's line count (`123`) reflects.

**Tech Stack:** Python 3.11, setuptools (src layout), protobuf + grpcio (generated code committed; no `.proto` change in this batch), python-jsonschema 4.26 with `referencing`, ruamel.yaml 0.19 (YAML 1.2), git via subprocess, pytest 9 + pytest-bdd 8.

**Spec:** `docs/superpowers/specs/2026-09-23-kb-design.md`, in particular:
- "Journal entry": `path` is among what every entry carries.
- "Canonical form": "Every prose body is a literal block scalar, however short."
- "Snapshot entries carry `op: snapshot` and a list of `{ artifact, revision, digest }`."
- "The client and the store": "A client is constructed without finding a store. Discovery runs on each call, so a client whose working directory has moved into a different store uses the store it now sits in. `Init` takes its root on the request and skips discovery."

The slice plan is `docs/superpowers/plans/2026-09-24-kb-slices.md`, and the feature files are in `features/`. Each capability slice's scenarios carry `@slice-<n>`, so `.venv/bin/python -m pytest -q -m slice-91` runs one slice. `CLAUDE.md` at the repository root is binding.

## Global Constraints

- Feature files are read-only for the implementer. Only `slicing-into-increments` edits a tag line, and only `formulating-features` edits a Given, When, or Then. Any diff under `features/` is a stop condition; this batch touches none.
- Code only what a scenario asserts (bdd-red-green). Where the scenarios are silent, the code is silent too, and the silence goes into the checkpoint entry as an open question. The decisions this plan makes are listed below, each tied to the scenario or slice that asks for it.
- **CLAUDE.md's rules are implemented once, never per row.** No rpc in `servicer.py` gains a `try`, a check, or a branch in this batch (`grep -c "try:" src/kb/servicer.py` stays `1`). No module but `names.py` joins or splits a locator's place; no module but `composition.py` says which type a kind names; no module but `canonical.py` decides how prose is written. No module catches a broad exception (`grep -nE "except (Exception|BaseException)|except:" src/kb/*.py` prints nothing).
- **Extend, never add beside.** Test helpers and shared test constants live in `tests/calls.py`; a step two feature files share word for word is one step definition in `tests/conftest.py`, never two. A test module never imports from `conftest.py`.
- **Size.** No module over 250 lines; `servicer.py` under 150. The line counts each task ends at are in its check. At the end of the batch the largest are `values.py` 241, `store.py` 209, `edits.py` 182, `canonical.py` 181 and `requests.py` 177. `values.py` is the one to watch: slice 95 weighs it first.
- Errors are a typed list of `{ artifact, path, rule, message }`. A response that carries faults is a refusal, and nothing was written.
- kb is exercised through its in-process transport (`kb.client.connect`).
- `make test` runs the suite in this checkout's virtualenv (`.venv/bin/python -m pytest -q`). While any scenario is red, make's own error line comes last, so the steps run pytest directly to see the summary. A worktree needs its own `.venv` first (`make dev`).
- The contract's version stays `0.1`, `pyproject.toml` stays `0.1.0`. Version and tag are the user's call.
- Work on `main` in `/home/vscode/shopsystem-kb`. shop-knowledge pins kb at `v0.1.0`; nothing here touches or runs its suite.
- Commits: `git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit`, the message ending with the Co-Authored-By line of the model that made the commit, e.g. `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- "Append at the end of the file" means after two blank lines, as the files' top-level definitions are spaced.
- The suite prints pytest-bdd `PytestRemovedIn10Warning`s. That is the baseline, not a fault. The summary lines quoted as Expected leave out the `, N warnings in Xs` that pytest adds.
- Baseline before Task 1: `.venv/bin/python -m pytest -q` → `13 failed, 183 passed`. After each task the suite reads, failed/passed: 1 `13/183`; 2 `9/187`; 3 `7/189`; 4 `4/192`; 5 `1/195`; 6 `1/195`; 7 `1/195`. The one failure left after Task 7 is slice 89.2's, and it never goes green here.
- Every task's first step saves the failing ids (`.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before`). An enabling task's check compares them after (`... | sort | diff /tmp/failing-before -` prints nothing); a capability task's check shows only its own scenarios leaving (`diff` prints only `<` lines, one per row of the slice).
- A probe is a Python script run with `.venv/bin/python` from the repository root, given in full in the task, that drives the in-process client over a store in a temporary directory. Save it under `/tmp`, run it before the change and after, and compare.

## Decisions this plan makes (the spec left them open or silent)

1. **The place a change records (slice 91).** A Write records the place its locator names, written as a locator's place is (`sections/rationale`), and a whole Write records none, as before; an Append records the item's place as it did. A Delete names no place, since a removal takes a whole artifact.
2. **A journal filter that names nothing (slice 91).** A set, or a role, nothing in the history was done under gives no entries and no fault; `since` that is not ISO 8601 is refused with rule `since`, as slice 54 already converts it. Both already held; the slice adds their steps.
3. **Prose that cannot be written as the store writes prose (slice 92).** A line of a prose body ending in a space is refused as the store lays the body down, with rule `content`, the fault `write.py` makes of any text it cannot write, said of the artifact, with the message "every piece of prose is written as a block, and this prose could not be written back as one; its line N ends in a space". It is refused on every write path (Create, Write, Append, Apply) since all of them dump through `canonical.dump`. ruamel.yaml could write such a line inside a block; the approved scenario refuses it, and the plan follows the scenario. A line ending in a tab, or a section's title ending in a space, is not prose the scenario names and is left as it is (Review Focus 2). An empty body is a literal block holding nothing and reads back empty; that already held.
4. **What a snapshot's actor must carry (slice 93).** A role and a piece of work, each refused with rule `actor` when missing, both faults together when both are, before the names are looked at: a snapshot refused for its actor does not also report a name the store lacks (Review Focus 3). The messages are the scenario's reasons: "every entry in the history names the role that made it" and "a snapshot records what a named piece of work read".
5. **The store's corner (slice 94).** A root whose `kb` holds a store is refused as before ("a store is never started over another"); a root whose `kb` is anything else, an empty folder, a file, or a link to nothing, is refused with rule `root`, "a store goes in a place of its own, and '<root>' already holds something in that place", and left as it was.
6. **A client readied where there was no store (slice 94).** Per "The client and the store", a readied client finds a store on each call from where it works; it does not adopt the root it started. The scenario's "can read and write in it straight away" moves the client's working directory into the directory it started the store in, and reads and defines a type there with the same client. Nothing in `client.py` changes.
7. **A kind with no type met in passing (slice 94.1).** A summary counting what points at an artifact, the links into one, a removal looking for what points at it, and a search whose hit is such an artifact are refused with the fault slice 82 gives a kind with no type, rule `kind`, where they raised `FileNotFoundError`. Whether they should pass it over as the check does is a question in the slice plan's log; the refusal is what every reader asking one function gives.

## Review Focus

Five inputs no task's scenarios exercise, most likely to bite first. Each was reproduced against the end state of the scratch run; none is a scenario, so each is a question for the spec in the checkpoint that meets it, never code.

1. **A Create, Write, Append, Delete or Apply with no role still breaks off.** Reproduction: the decision type; Create a decision under `kb_pb2.Actor()` (no role): `subprocess.CalledProcessError` at the commit, through the client. After Task 4 a snapshot with no role is refused plainly with rule `actor`, "every entry in the history names the role that made it", so the sibling answer now exists; whether every write takes it is the spec's (open since review 1).
2. **Prose ending a line in a tab is written; a line ending in a space is refused.** Reproduction: Create a decision whose purpose body is the literal block `Tabbed\t`: accepted, `decision/tabbed`. A person would expect trailing whitespace of either kind to be treated alike.
3. **A snapshot refused for its actor says nothing of the names.** Reproduction: Snapshot `decision/never` under an actor with a piece of work and no role: one fault, `('', 'actor')`; the name the store lacks is not reported beside it, where Create and Apply give every fault together.
4. **A placed Write whose prose ends a line in a space is refused with no place.** Reproduction: Write `decision/tabbed` at `sections/purpose` with the body `ends ` followed by a newline: refused `('decision/tabbed', '', 'content')`. The fault names the artifact but not the section, where a fault from the type names its place.
5. **A section titled with a trailing space is refused as missing.** Reproduction: Create a decision whose first section is titled `'Purpose '`: refused twice with `('sections', 'sections')`, once for Purpose and once for Rationale being out of place, where a person would expect to be told the title does not match. Not changed by this batch; slice 92's rule is about prose bodies only.

---

### Task 1: Slice 90.1, a place inside an artifact is written and read in one place

**Slice plan entry:** Slice 90.1, enabling. Check: the suite's summary and failing ids unchanged; `grep -nE '"/"\.join\(|\.split\("/"\)' src/kb/values.py src/kb/refusals.py src/kb/edits.py` → no lines (6 before); `grep -n '"schema", 1, 1' src/kb/write.py` → no lines (1 before); `refusals.py` has no run of three blank lines (1 before); `names.py` still imports `re` and `typing` alone (beside `kb.content`, which Task 7 removes); the probe unchanged.

**Files:**
- Modify: `src/kb/names.py` (new `placed`, `steps`)
- Modify: `src/kb/values.py` (`_located` reads a place with `names.steps`)
- Modify: `src/kb/refusals.py` (four refusals write a place with `names.placed`; the stray blank line goes)
- Modify: `src/kb/edits.py` (an Append records its item's place with `names.placed`)
- Modify: `src/kb/write.py` (the type of types is given `METASCHEMA_ID.kind.name`)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `values.Locator(id: ArtifactId, place: tuple[str, ...])`.
- Produces: `names.placed(steps) -> str` (the steps joined by `/`); `names.steps(text: str) -> tuple[str, ...]` (empty text gives `()`). Task 2 records a Write's place with `names.placed(operation.locator.place)`.

- [ ] **Step 1: Save the failing ids and the probe's answers**

Save this probe as `/tmp/probe-90-1.py`:

```python
"""Slice 90.1's probe: where a refusal says a place is, and the place an addition records."""
import pathlib, sys, tempfile

sys.path.insert(0, "tests")
from calls import CLIENT, DECISION_TYPE
from kb import client as kb_client, journal
from kb.content import dumps
from kb.contract import kb_pb2

root = pathlib.Path(tempfile.mkdtemp())
client = kb_client.connect(root)
client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
client.Create(kb_pb2.CreateRequest(type="schema", title="Decision", actor=CLIENT, message="m",
    content=dumps({"version": 1, "schema": DECISION_TYPE["schema"]})))
sections = [{"title": "Purpose", "body": "p"}, {"title": "Rationale", "body": "r"}]
client.Create(kb_pb2.CreateRequest(type="decision", title="D one", actor=CLIENT, message="m",
    content=dumps({"sections": sections, "options": [{"title": "O one"}]})))
at = lambda path: kb_pb2.Locator(id="decision/d-one", path=path)
show = lambda label, response: print(label, [(f.path, f.rule) for f in response.faults])
show("write options/nope", client.Write(kb_pb2.WriteRequest(locator=at("options/nope"), content=dumps({"title": "X"}), actor=CLIENT, message="m")))
show("append sections", client.Append(kb_pb2.AppendRequest(locator=at("sections"), content=dumps({"title": "X"}), actor=CLIENT, message="m")))
show("delete options/o-one", client.Delete(kb_pb2.DeleteRequest(locator=at("options/o-one"), actor=CLIENT, message="m")))
added = client.Append(kb_pb2.AppendRequest(locator=at("options"), content=dumps({"title": "O two"}), actor=CLIENT, message="m"))
print("append options", added.id, [entry["path"] for entry in journal.entries(root / "kb") if entry["op"] == "append"])
```

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
.venv/bin/python /tmp/probe-90-1.py | tee /tmp/probe-90-1-before.txt
grep -nE '"/"\.join\(|\.split\("/"\)' src/kb/values.py src/kb/refusals.py src/kb/edits.py
```

Expected: the probe prints

```
write options/nope [('options/nope', 'not-found')]
append sections [('sections', 'collection')]
delete options/o-one [('options/o-one', 'locator')]
append options o-two ['options/o-two']
```

and the grep six lines: one in `values.py`, four in `refusals.py`, one in `edits.py`.

- [ ] **Step 2: How a place is written and read, in names.py**

In `src/kb/names.py`, replace:

```python
def referred(ref: str) -> tuple[str, str] | None:
```

with:

```python
def placed(steps) -> str:
    """A place inside an artifact as it is written: its steps, each a collection, an item's or a section's name, or a
    field, joined by slashes."""
    return "/".join(steps)


def steps(text: str) -> tuple[str, ...]:
    """A written place read back as its steps, none for no place, none of them yet checked."""
    return tuple(text.split("/")) if text else ()


def referred(ref: str) -> tuple[str, str] | None:
```

- [ ] **Step 3: Every reader and writer of a place asks it**

In `src/kb/values.py`, replace:

```python
    place = tuple(path.split("/")) if path else ()
```

with:

```python
    place = names.steps(path)
```

In `src/kb/refusals.py`, replace:

```python
from kb.contract import kb_pb2
from kb.names import Misnamed
```

with:

```python
from kb import names
from kb.contract import kb_pb2
from kb.names import Misnamed
```

and replace each of the four lines (in `not_a_collection`, `nothing_at`, `settled_place` and `whole_only`):

```python
    place = "/".join(locator.place)
```

with:

```python
    place = names.placed(locator.place)
```

In the same file, replace the three blank lines between `unwritable` and `no_section`:

```python
    return kb_pb2.Fault(artifact=str(artifact_id), rule="content", message=problem)



def no_section(artifact_id: ArtifactId, title: str) -> kb_pb2.Fault:
```

with two:

```python
    return kb_pb2.Fault(artifact=str(artifact_id), rule="content", message=problem)


def no_section(artifact_id: ArtifactId, title: str) -> kb_pb2.Fault:
```

In `src/kb/edits.py`, replace:

```python
    return Change("append", locator.id, "/".join((*locator.place, item["id"])), item["id"])
```

with:

```python
    return Change("append", locator.id, names.placed((*locator.place, item["id"])), item["id"])
```

In `src/kb/write.py`, replace:

```python
    metaschema = settled.given(settled.content(METASCHEMA), str(METASCHEMA_ID), "schema", 1, 1, METASCHEMA["title"])
```

with:

```python
    metaschema = settled.given(
        settled.content(METASCHEMA), str(METASCHEMA_ID), METASCHEMA_ID.kind.name, 1, 1, METASCHEMA["title"],
    )
```

- [ ] **Step 4: Check**

```bash
.venv/bin/python -m pytest -q 2>&1 | tail -1
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before -
.venv/bin/python /tmp/probe-90-1.py | diff /tmp/probe-90-1-before.txt -
grep -nE '"/"\.join\(|\.split\("/"\)' src/kb/values.py src/kb/refusals.py src/kb/edits.py
grep -n '"schema", 1, 1' src/kb/write.py
.venv/bin/python -c "print(open('src/kb/refusals.py').read().count(chr(10)*4))"
wc -l src/kb/names.py src/kb/values.py src/kb/refusals.py src/kb/edits.py src/kb/write.py
```

Expected: `13 failed, 183 passed`; no diff; no diff; no lines; no lines; `0`; `127`, `226`, `119`, `182`, `123`.

- [ ] **Step 5: Checkpoint and commit**

Append the slice 90.1 checkpoint to the slice plan's log (what someone reading the code can now rely on, the check before and after, the probe, line counts, open questions: none) and set its Status to `green`.

```bash
git add src/kb docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 90.1: A place inside an artifact is written and read in one place

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Slice 91, the history answers every filter plainly, and says where a change landed

**Slice plan entry:** Slice 91, capability. Scenarios: kb / read-the-journal / Every way the history can be asked for is checked and answered plainly (three rows); kb / read-the-journal / A change aimed at one place records the place it changed.

**Files:**
- Modify: `tests/test_read_the_journal.py` (the `since` step takes a date only; five new steps)
- Modify: `src/kb/edits.py` (a Write records its locator's place)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `names.placed` (Task 1); `calls.journal(client, artifact="", role="", execution="", since="", batch="")`, `calls.write(client, artifact_id, content, message=..., actor=..., path="")`; the Background's `client`, `DECISION`, `AGENT`, and the step `the client reads the journal for that decision` (fixture `entries`).
- Produces: nothing later tasks use.

- [ ] **Step 1: Save the failing ids**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
.venv/bin/python -m pytest -q -m slice-91 2>&1 | tail -1
```

Expected: `4 failed, 192 deselected`: three `StepDefinitionNotFoundError`s and, on the `since` row, an `AssertionError: [rule: "since"` from the existing `since {day}` step, which matches the row's text and asserts no fault.

- [ ] **Step 2: Write the steps**

In `tests/test_read_the_journal.py`, replace:

```python
@when(parsers.parse("the client reads the journal since {day}"), target_fixture="narrowed")
```

with:

```python
@when(parsers.re(r"the client reads the journal since (?P<day>\d{4}-\d{2}-\d{2})"), target_fixture="narrowed")
```

Append at the end of the file:

```python
@when("the client reads the journal for a set of changes the history holds nothing under", target_fixture="asked")
def _for_an_unknown_set(client):
    return journal(client, batch="20260101T000000000000Z-1")


@when("the client reads the journal for a role nothing in the history was done under", target_fixture="asked")
def _for_an_unknown_role(client):
    return journal(client, role="auditor")


@when("the client reads the journal since something that cannot be read as a moment in time", target_fixture="asked")
def _since_what_is_no_time(client):
    return journal(client, since="last Tuesday")


@then("the client is given no entries and no fault")
def _nothing_and_no_fault(asked):
    assert (list(asked.entries), list(asked.faults)) == ([], [])


@then("the read is rejected because since names a moment in time")
def _rejected_since(asked):
    assert [(fault.rule, fault.path) for fault in asked.faults] == [("since", "")]
    assert "'last Tuesday'" in asked.faults[0].message
    assert list(asked.entries) == []


@given("a store where an agent replaced one section of a decision")
def _one_section_replaced(client):
    replaced = write(client, DECISION, {"title": "Rationale", "body": "Costs move every week.\n"},
                     message="Say it plainer", actor=AGENT, path="sections/rationale")
    assert not replaced.faults, replaced.faults


@then("the entry for that change names the place inside the decision that was changed")
def _names_the_place(entries):
    assert [(entry.op, entry.path, entry.message) for entry in entries][-1] == (
        "write", "sections/rationale", "Say it plainer",
    )
```

- [ ] **Step 3: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-91 --tb=line 2>&1 | grep -E "^E |passed|failed"
```

Expected: `1 failed, 3 passed, 192 deselected`, the failure `AssertionError: assert ('write', '',...y it plainer') == ('write', 'se...y it plainer')`. The three filter rows pass on their steps alone: a filter naming nothing already narrowed to nothing, and `since` has been converted since slice 54.

- [ ] **Step 4: A Write records the place it landed**

In `src/kb/edits.py`, replace:

```python
    return Change("write", _replace(draft, operation))
```

with:

```python
    return Change("write", _replace(draft, operation), names.placed(operation.locator.place))
```

- [ ] **Step 5: Run it green, and the neighbours**

```bash
.venv/bin/python -m pytest -q -m "slice-91 or slice-9 or slice-35" 2>&1 | tail -1
.venv/bin/python -m pytest -q 2>&1 | tail -1
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before -
wc -l src/kb/edits.py
```

Expected: `9 passed, 187 deselected` (slice 9's whole Write still records no place); `9 failed, 187 passed`; the diff prints only four `<` lines, the slice's rows; `182`.

- [ ] **Step 6: Checkpoint and commit**

Append the slice 91 checkpoint to the slice plan's log (someone can now, surprised by, the answer to its unknown, red and green, open questions) and set its Status to `green`.

```bash
git add src tests docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 91: The history answers every filter plainly, and says where a change landed

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Slice 92, prose is kept as written or refused

**Slice plan entry:** Slice 92, capability. Scenarios: kb / create-an-artifact / A section whose body is empty is kept as it is; kb / create-an-artifact / Prose the store could not write back in its one form is refused.

**Files:**
- Modify: `tests/test_create_an_artifact.py` (four new steps)
- Modify: `src/kb/canonical.py` (the prose representer refuses a line ending in a space)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: in `tests/test_create_an_artifact.py`, `SECTIONS`, `_raw(client, text)` (a Create of the decision titled "Price reviews happen weekly" from text as written), `create`, `read`, `everything_under`, `content`, `canonical`; the existing steps `the client is given the name the artifact keeps for life and its first version` (fixture `created`) and `nothing is written anywhere in the store` (fixture `attempt` with `before` and `after`). `write._serialised` turns a `canonical.NotCanonical` raised by `canonical.dump` into `refusals.unwritable(artifact_id, message)`, rule `content`.
- Produces: `canonical.dump` raises `NotCanonical` for a prose body with a line ending in a space.

- [ ] **Step 1: Save the failing ids**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
```

- [ ] **Step 2: Write the steps**

Append at the end of `tests/test_create_an_artifact.py`:

```python
@when(
    "the client creates a decision whose rationale carries a title and an empty body, saying which role and why",
    target_fixture="created",
)
def _create_with_an_empty_rationale(client):
    return create(client, "decision", {
        "title": "Price reviews happen weekly",
        "sections": [SECTIONS[0], {"title": "Rationale", "body": ""}],
    }, message="Say why later")


@then("the rationale reads back with an empty body")
def _rationale_reads_back_empty(root, client, created):
    rationale = read(client, created.id, section="Rationale")
    assert not rationale.faults, rationale.faults
    assert content.loads(rationale.content) == {"title": "Rationale", "body": ""}
    on_disk = canonical.load((root / "kb" / f"{created.id}.yaml").read_text())
    assert on_disk["sections"][1] == {"title": "Rationale", "body": ""}


@when(
    "the client creates a decision one of whose lines of prose ends in a space, saying which role and why",
    target_fixture="attempt",
)
def _create_with_a_line_ending_in_a_space(root, client):
    before = everything_under(root)
    text = (
        "sections:\n  - title: Purpose\n    body: |\n      Keep prices in step with costs.\n"
        "  - title: Rationale\n    body: |\n      Costs move weekly. \n      So we review weekly.\n"
    )
    response = _raw(client, text)
    return {"response": response, "before": before, "after": everything_under(root)}


@then(
    "the artifact is rejected because every piece of prose is written as a block, and this prose could not be "
    "written back as one"
)
def _rejected_as_prose_that_is_no_block(attempt):
    refused = attempt["response"]
    assert (refused.id, refused.revision) == ("", 0)
    assert [(fault.artifact, fault.rule) for fault in refused.faults] == [
        ("decision/price-reviews-happen-weekly", "content"),
    ]
    assert refused.faults[0].message.startswith(
        "every piece of prose is written as a block, and this prose could not be written back as one"
    )
```

The content with the trailing space is sent as text, since `content.dumps` is `canonical.dump` and would itself refuse it once Step 4 lands.

- [ ] **Step 3: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-92 --tb=line 2>&1 | grep -E "^E |passed|failed"
```

Expected: `1 failed, 1 passed, 194 deselected`, the failure `AssertionError: assert ('decision/pr...en-weekly', 1) == ('', 0)`: the prose was accepted. The empty body passes on its steps alone; it is written `body: |` and reads back empty.

- [ ] **Step 4: Refuse prose the store could not write as its one block**

In `src/kb/canonical.py`, replace:

```python
def _represent_prose(representer, value):
    return representer.represent_scalar("tag:yaml.org,2002:str", str(value), style="|")
```

with:

```python
def _represent_prose(representer, value):
    """Prose as a literal block. A line ending in a space is refused rather than written: the store writes every
    piece of prose one way."""
    for number, line in enumerate(value.split("\n"), start=1):
        if line.endswith(" "):
            raise NotCanonical(
                "every piece of prose is written as a block, and this prose could not be written back as one; "
                f"its line {number} ends in a space"
            )
    return representer.represent_scalar("tag:yaml.org,2002:str", str(value), style="|")
```

`NotCanonical` is defined further down the module; the representer runs only once the module is loaded, so the name resolves.

- [ ] **Step 5: Run it green**

```bash
.venv/bin/python -m pytest -q -m slice-92 2>&1 | tail -1
.venv/bin/python -m pytest -q 2>&1 | tail -1
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before -
wc -l src/kb/canonical.py
```

Expected: `2 passed, 194 deselected`; `7 failed, 189 passed`; the diff prints only the slice's two `<` lines; `181`.

- [ ] **Step 6: Checkpoint and commit**

Append the slice 92 checkpoint to the slice plan's log, with Review Focus 2 and 4 as questions for the spec if they reproduce, and set its Status to `green`.

```bash
git add src tests docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 92: Prose is kept as written or refused

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Slice 93, a snapshot asked for wrongly is refused

**Slice plan entry:** Slice 93, capability. Scenarios: kb / snapshot-what-a-piece-of-work-read / Every way a snapshot can be asked for wrongly is refused (three rows).

**Files:**
- Modify: `tests/test_snapshot_what_a_piece_of_work_read.py` (three new steps)
- Modify: `src/kb/values.py` (new `reader`)
- Modify: `src/kb/servicer.py` (Snapshot converts its actor with `values.reader`)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `calls.snapshot(client, execution, artifacts, message=..., role="agent")`, `calls.journal`; the Background's `client`, `DECISION`, `PROCESS`, `EXECUTION`; `values.signed(request, message) -> Signed`.
- Produces: `values.reader(request: kb_pb2.Actor, message: str) -> Signed`, raising `Refused` with a fault of rule `actor` for a missing role and one for a missing piece of work.

- [ ] **Step 1: Save the failing ids**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
```

- [ ] **Step 2: Write the steps**

In `tests/test_snapshot_what_a_piece_of_work_read.py`, replace:

```python
import hashlib

from pytest_bdd import given, scenarios, then, when
```

with:

```python
import hashlib
import re

from pytest_bdd import given, parsers, scenarios, then, when
```

Append at the end of the file:

```python
WRONGLY = {
    "the decision and the process without naming the piece of work": ("", [DECISION, PROCESS], "agent"),
    "the decision and an artifact the store holds nothing under": (EXECUTION, [DECISION, "decision/never-made"], "agent"),
    "the decision and the process without saying which role it is": (EXECUTION, [DECISION, PROCESS], ""),
}


@when(parsers.re(f"the client snapshots (?P<request>{'|'.join(map(re.escape, WRONGLY))})"), target_fixture="refused")
def _snapshot_wrongly(client, request):
    execution, artifacts, role = WRONGLY[request]
    return snapshot(client, execution, artifacts, message="Read before restocking", role=role)


REASONS = {
    "a snapshot records what a named piece of work read": [("", "", "actor")],
    "the store holds nothing by that name, and the name asked for is given back": [
        ("decision/never-made", "", "not-found"),
    ],
    "every entry in the history names the role that made it": [("", "", "actor")],
}


@then(parsers.parse("the snapshot is rejected because {reason}"))
def _snapshot_rejected(refused, reason):
    assert refused.entry == ""
    assert [(fault.artifact, fault.path, fault.rule) for fault in refused.faults] == REASONS[reason]
    if REASONS[reason][0][2] == "actor":
        assert refused.faults[0].message.startswith(reason)


@then("the journal holds no entry for it")
def _no_entry_for_it(client):
    assert [entry for entry in journal(client).entries if entry.op == "snapshot"] == []
```

The When is a regular expression over the rows' own words, so it never swallows slice 37's `the client snapshots the decision and the process for a piece of work`.

- [ ] **Step 3: Run it red**

```bash
.venv/bin/python -m pytest -q -m "slice-93 or slice-37" --tb=line 2>&1 | grep -E "^E |passed|failed" | cut -c1-160
```

Expected: `2 failed, 2 passed, 192 deselected`: the row without a piece of work fails `AssertionError: assert '<an entry id>' == ''` (the snapshot was recorded), and the row without a role raises `subprocess.CalledProcessError` from `git commit`. The row naming an artifact the store lacks passes on its steps alone (slice 37's `query.snapshotted` refuses it), as does slice 37.

- [ ] **Step 4: A snapshot's actor names a role and a piece of work**

In `src/kb/values.py`, replace:

```python
def starter(request: kb_pb2.Actor) -> Actor:
```

with:

```python
def reader(request: kb_pb2.Actor, message: str) -> Signed:
    """Who records what a piece of work read, who must name a role and the piece of work; both faults when both fail."""
    faults = []
    if not request.role:
        faults.append(kb_pb2.Fault(rule="actor", message="every entry in the history names the role that made it"))
    if not request.execution:
        faults.append(kb_pb2.Fault(rule="actor", message="a snapshot records what a named piece of work read"))
    if faults:
        raise Refused(faults)
    return signed(request, message)


def starter(request: kb_pb2.Actor) -> Actor:
```

In `src/kb/servicer.py`, replace:

```python
        named, signed = requests.snapshotted(request.artifacts), values.signed(request.actor, request.message)
```

with:

```python
        named, signed = requests.snapshotted(request.artifacts), values.reader(request.actor, request.message)
```

- [ ] **Step 5: Run it green**

```bash
.venv/bin/python -m pytest -q -m "slice-93 or slice-37" 2>&1 | tail -1
.venv/bin/python -m pytest -q 2>&1 | tail -1
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before -
grep -c "try:" src/kb/servicer.py
wc -l src/kb/values.py src/kb/servicer.py
```

Expected: `4 passed, 192 deselected`; `4 failed, 192 passed`; the diff prints only the slice's three `<` lines; `1`; `238` and `101`.

- [ ] **Step 6: Checkpoint and commit**

Append the slice 93 checkpoint to the slice plan's log, with Review Focus 1 and 3 as questions for the spec if they reproduce, and set its Status to `green`.

```bash
git add src tests docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 93: A snapshot asked for wrongly is refused

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Slice 94, a store's corner is never taken over, and a client readied early can start one

**Slice plan entry:** Slice 94, capability. Scenarios: kb / start-a-store / Starting a store where the store's own corner is already taken is refused (two rows); kb / start-a-store / A client readied where there was no store can still start one.

**Files:**
- Modify: `tests/test_start_a_store.py` (a `readied` fixture the existing When takes; five new steps)
- Modify: `src/kb/store.py` (`vacant` tells a store in the corner from anything else there)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: in `tests/test_start_a_store.py`, `FILE_TEXT`, `CLIENT`, `define`, `read`, `kb_client`, the `root` fixture (`tmp_path / "store"`, made), the existing steps `the client starts a store there, saying which role it is` (fixture `started`), `an empty directory elsewhere that sits inside no store` (fixture `root`) and `the store is made in the directory the client named`; `calls.DECISION_TYPE`; `store.MARKER` (`Path("kb") / "store.yaml"`).
- Produces: nothing later tasks use.

- [ ] **Step 1: Save the failing ids**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
```

- [ ] **Step 2: Write the steps**

In `tests/test_start_a_store.py`, replace:

```python
from calls import CLIENT, define, read
```

with:

```python
from calls import CLIENT, DECISION_TYPE, define, read
```

Replace:

```python
@when("the client starts a store in that empty directory, saying which role it is", target_fixture="started")
def _start_a_store_in_the_named_directory(root):
    return kb_client.connect().Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
```

with:

```python
@pytest.fixture
def readied():
    """The client that starts a store elsewhere, readied as the step starting it is taken, unless a step readied it
    before."""
    return kb_client.connect()


@when("the client starts a store in that empty directory, saying which role it is", target_fixture="started")
def _start_a_store_in_the_named_directory(readied, root):
    return readied.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
```

Append at the end of the file:

```python
CORNERS = {
    "an empty folder where a store would go": lambda corner: corner.mkdir(),
    "a file where a store would go": lambda corner: corner.write_bytes(FILE_TEXT),
}


def _held(directory):
    """Everything below a directory, folders as well as files, a file with its bytes."""
    return {path: path.read_bytes() if path.is_file() else None for path in sorted(directory.rglob("*"))}


@given(parsers.re(f"a directory holding (?P<what>{'|'.join(CORNERS)})"), target_fixture="before")
def _a_directory_holding(root, what):
    CORNERS[what](root / "kb")
    return _held(root)


@then("starting the store is rejected because that directory already holds the place a store goes")
def _rejected_as_the_place_taken(started, root):
    assert [(fault.rule, fault.message) for fault in started.faults] == [
        ("root", f"a store goes in a place of its own, and {str(root)!r} already holds something in that place"),
    ]


@then("what was there is left as it was")
def _left_as_it_was(root, before):
    assert _held(root) == before


@given(
    "the client was readied to call a store while working where there was none and nothing named one",
    target_fixture="readied",
)
def _readied_where_there_was_none(tmp_path, monkeypatch):
    nowhere = tmp_path / "nowhere"
    nowhere.mkdir()
    monkeypatch.chdir(nowhere)
    monkeypatch.delenv("KB_ROOT", raising=False)
    return kb_client.connect()


@then("the client can read and write in it straight away")
def _reads_and_writes_there(readied, root, monkeypatch):
    monkeypatch.chdir(root)
    assert read(readied, "schema/schema").id == "schema/schema"
    defined = define(readied, DECISION_TYPE)
    assert not defined.faults, defined.faults
    assert read(readied, "schema/decision").revision == 1
```

The two rows' names hold no character a regular expression reads specially, so they are joined as written. The last step moves the client's working directory into the new store, since a client finds its store on each call (Decision 6).

- [ ] **Step 3: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-94 --tb=line 2>&1 | grep -E "^E |passed|failed"
.venv/bin/python -m pytest -q tests/test_start_a_store.py 2>&1 | tail -1
```

Expected: `2 failed, 1 passed, 193 deselected`, each failure `assert [('root', 'a ...e inside it')] == [('root', 'a ... that place')]`: both corners are refused today, but as a store already there. The readied client's row passes on its steps alone. The second run gives `2 failed, 11 passed`: the two are this slice's rows, and the scenario sharing the When, "Where a store is started is settled by the directory named, not by where the client is working", still passes with the `readied` fixture.

- [ ] **Step 4: Anything but a store in the store's place is its own refusal**

In `src/kb/store.py`, replace:

```python
    """Refuse a root a store cannot be started in: one that is not there, is not a directory, has anything called kb
    inside it, or is inside a store."""
```

with:

```python
    """Refuse a root a store cannot be started in: one that is not there, is not a directory, has a store inside it or
    anything else in the place a store goes, or is inside a store."""
```

and replace:

```python
    if (root.path / "kb").exists():
        raise Refused([kb_pb2.Fault(
            rule="root", message=f"a store is never started over another; {root.named!r} already has a store inside it",
        )])
```

with:

```python
    if (root.path / MARKER).is_file():
        raise Refused([kb_pb2.Fault(
            rule="root", message=f"a store is never started over another; {root.named!r} already has a store inside it",
        )])
    if (root.path / MARKER.parent).exists() or (root.path / MARKER.parent).is_symlink():
        raise Refused([kb_pb2.Fault(
            rule="root",
            message=f"a store goes in a place of its own, and {root.named!r} already holds something in that place",
        )])
```

`is_symlink` catches a link to nothing, which `exists` does not, and which reached `mkdir` as `FileExistsError` (batch 6's minor).

- [ ] **Step 5: Run it green**

```bash
.venv/bin/python -m pytest -q -m slice-94 2>&1 | tail -1
.venv/bin/python -m pytest -q 2>&1 | tail -1
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before -
wc -l src/kb/store.py
```

Expected: `3 passed, 193 deselected`; `1 failed, 195 passed`; the diff prints only the slice's three `<` lines; `216`. The one failure left is slice 89.2's.

- [ ] **Step 6: Checkpoint and commit**

Append the slice 94 checkpoint to the slice plan's log and set its Status to `green`. Then append the batch line: slices 90.1 to 94 green, suite 1 failed, 195 passed, the one failure slice 89.2's; next: slice 94.1.

```bash
git add src tests docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 94: A store's corner is never taken over, and a client readied early can start one

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Slice 94.1, which type a kind names is asked of composition alone, by every reader

**Slice plan entry:** Slice 94.1, enabling. Check: the suite's summary and failing ids unchanged; `grep -n "def schema" src/kb/store.py` → no lines (2 before); `grep -nE "\.schema\(" src/kb/*.py` → no lines (10 before); the probe, every `FileNotFoundError` replaced by the `kind` fault and every other row unchanged.

**Files:**
- Modify: `src/kb/composition.py` (new `kind_schema`)
- Modify: `src/kb/store.py` (`Store.schema` and `Draft.schema` are gone, with the `values` import)
- Modify: `src/kb/read.py`, `src/kb/query.py`, `src/kb/edits.py` (every reader asks `composition.kind_schema`)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `composition.kind_type(kind, corpus) -> ArtifactId` (raises `Refused` with `refusals.no_type`); `corpus.artifact(artifact_id) -> dict` on `Store` and `Draft` (raises `Refused` for a damaged file).
- Produces: `composition.kind_schema(kind: values.Kind, corpus) -> dict`, the type artifact, its JSON Schema under `schema`.

- [ ] **Step 1: Save the failing ids and the probe's answers**

Save this probe as `/tmp/probe-94-1.py`:

```python
"""Slice 94.1's probe: every call over a store holding an artifact of a kind it has no type for."""
import pathlib, sys, tempfile

sys.path.insert(0, "tests")
from calls import CLIENT, DECISION_TYPE, WORK_ITEM_TYPE
from kb import client as kb_client
from kb.content import dumps
from kb.contract import kb_pb2

root = pathlib.Path(tempfile.mkdtemp())
client = kb_client.connect(root)
client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
for kind in (DECISION_TYPE, WORK_ITEM_TYPE):
    client.Create(kb_pb2.CreateRequest(type="schema", title=kind["title"], actor=CLIENT, message="m",
        content=dumps({"version": kind["version"], "schema": kind["schema"]})))
sections = [{"title": "Purpose", "body": "p"}, {"title": "Rationale", "body": "r"}]
client.Create(kb_pb2.CreateRequest(type="decision", title="D one", actor=CLIENT, message="m", content=dumps({"sections": sections})))
client.Create(kb_pb2.CreateRequest(type="work-item", title="W", actor=CLIENT, message="m", content=dumps({"decisions": ["decision/d-one"]})))
(root / "kb" / "invoice").mkdir()
(root / "kb" / "invoice" / "i-one.yaml").write_text(
    "id: invoice/i-one\ntype: invoice\nschema_version: 1\nrevision: 1\ntitle: I one\n")
at = lambda name: kb_pb2.Locator(id=name)
calls = {
    "read invoice/i-one": lambda: client.Read(kb_pb2.ReadRequest(locator=at("invoice/i-one"))),
    "read decision/d-one": lambda: client.Read(kb_pb2.ReadRequest(locator=at("decision/d-one"))),
    "whole decision/d-one": lambda: client.Read(kb_pb2.ReadRequest(locator=at("decision/d-one"), level=kb_pb2.ReadRequest.WHOLE)),
    "refs into decision/d-one": lambda: client.Refs(kb_pb2.RefsRequest(locator=at("decision/d-one"), depth=1, direction=kb_pb2.RefsRequest.IN)),
    "refs out of work-item/w": lambda: client.Refs(kb_pb2.RefsRequest(locator=at("work-item/w"), depth=1)),
    "delete work-item/w": lambda: client.Delete(kb_pb2.DeleteRequest(locator=at("work-item/w"), actor=CLIENT, message="m")),
    "search fields for one": lambda: client.Search(kb_pb2.SearchRequest(text="one", scope=kb_pb2.SearchRequest.FIELDS)),
    "list invoice": lambda: client.List(kb_pb2.ListRequest(type="invoice")),
    "validate": lambda: client.Validate(kb_pb2.ValidateRequest()),
}
for label, call in calls.items():
    try:
        response = call()
    except Exception as error:
        print(label, "-> raises", type(error).__name__)
        continue
    faults = [(fault.artifact, fault.rule, fault.message) for fault in response.faults]
    violations = [(fault.artifact, fault.rule) for fault in getattr(response, "violations", [])]
    print(label, "->", faults or "answered", violations or "")
print("work-item/w still there:", (root / "kb" / "work-item" / "w.yaml").is_file())
```

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
.venv/bin/python /tmp/probe-94-1.py
grep -nE "\.schema\(" src/kb/*.py | wc -l
```

Expected: the probe prints

```
read invoice/i-one -> raises FileNotFoundError
read decision/d-one -> raises FileNotFoundError
whole decision/d-one -> answered 
refs into decision/d-one -> raises FileNotFoundError
refs out of work-item/w -> answered 
delete work-item/w -> raises FileNotFoundError
search fields for one -> raises FileNotFoundError
list invoice -> [('', 'kind', "a kind must name a type the store holds; the store holds no type called 'invoice'")] 
validate -> answered [('invoice/i-one', 'kind')]
work-item/w still there: True
```

and the grep `10`.

- [ ] **Step 2: The one lookup of a kind's type, in composition.py**

In `src/kb/composition.py`, replace:

```python
def named_type(kind: values.Kind, corpus, artifact: str = "") -> values.ArtifactId | kb_pb2.Fault:
```

with:

```python
def kind_schema(kind: values.Kind, corpus) -> dict:
    """The type a kind names, as the corpus holds it, its JSON Schema under `schema`. Raises Refused when the corpus
    holds none, or when its file cannot be read."""
    return corpus.artifact(kind_type(kind, corpus))


def named_type(kind: values.Kind, corpus, artifact: str = "") -> values.ArtifactId | kb_pb2.Fault:
```

- [ ] **Step 3: The store and the draft keep no lookup of their own**

In `src/kb/store.py`, replace `from kb import canonical, refusals, settled, values` with `from kb import canonical, refusals, settled`. Delete from `Store`:

```python
    def schema(self, kind: Kind) -> dict:
        """The schema artifact of a kind; its JSON Schema is under `schema`. Raises Refused for a damaged file."""
        return self.artifact(values.type_of(kind))

```

(the method and the blank line after it, so `commit` follows `artifact`), and from `Draft`:

```python

    def schema(self, kind: Kind) -> dict:
        return self.artifact(values.type_of(kind))
```

(the blank line before it and the method, so `artifact` ends the class). In `Draft`'s docstring, replace `Read like the store: holds, load, schema, ids.` with `Read like the store: holds, load, artifact, ids.`

- [ ] **Step 4: Every reader asks composition.py**

In `src/kb/read.py` replace, one at a time:

```python
    schema = store.schema(target_id.kind)["schema"]
```
→
```python
    schema = composition.kind_schema(target_id.kind, store)["schema"]
```

```python
    schema = store.schema(locator.id.kind)["schema"]
```
→
```python
    schema = composition.kind_schema(locator.id.kind, store)["schema"]
```

```python
    carried = links.carried(found, store.schema(artifact_id.kind)["schema"], store)
```
→
```python
    carried = links.carried(found, composition.kind_schema(artifact_id.kind, store)["schema"], store)
```

```python
        schema = store.schema(values.kind(other["type"]))["schema"]
```
→
```python
        schema = composition.kind_schema(values.kind(other["type"]), store)["schema"]
```

In `src/kb/query.py` replace:

```python
    schema = store.schema(artifact_id.kind)["schema"]
```
→
```python
    schema = composition.kind_schema(artifact_id.kind, store)["schema"]
```

```python
        schema = store.schema(other_id.kind)["schema"]
```
→
```python
        schema = composition.kind_schema(other_id.kind, store)["schema"]
```

In `src/kb/edits.py` replace:

```python
    kind = creation.kind
    composition.kind_type(kind, draft)
```
→
```python
    kind = creation.kind
    type_id = composition.kind_type(kind, draft)
```

```python
    schema = draft.schema(kind)
```
→
```python
    schema = draft.artifact(type_id)
```

(a Create still asks which type its kind names before anything else, and loads that type only after its title and content faults, as before),

```python
    declared = composition.declared(draft.schema(locator.id.kind)["schema"], draft)
```
→
```python
    declared = composition.declared(composition.kind_schema(locator.id.kind, draft)["schema"], draft)
```

```python
        schema = draft.schema(other_id.kind)["schema"]
```
→
```python
        schema = composition.kind_schema(other_id.kind, draft)["schema"]
```

```python
    schema = draft.schema(artifact_id.kind)
```
→
```python
    schema = composition.kind_schema(artifact_id.kind, draft)
```

`read.py`, `query.py` and `edits.py` already import `composition`.

- [ ] **Step 5: Check**

```bash
.venv/bin/python -m pytest -q 2>&1 | tail -1
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before -
.venv/bin/python /tmp/probe-94-1.py
grep -n "def schema" src/kb/store.py
grep -nE "\.schema\(" src/kb/*.py
wc -l src/kb/store.py src/kb/composition.py src/kb/read.py src/kb/query.py src/kb/edits.py
```

Expected: `1 failed, 195 passed`; no diff; the probe prints

```
read invoice/i-one -> [('', 'kind', "a kind must name a type the store holds; the store holds no type called 'invoice'")] 
read decision/d-one -> [('', 'kind', "a kind must name a type the store holds; the store holds no type called 'invoice'")] 
whole decision/d-one -> answered 
refs into decision/d-one -> [('', 'kind', "a kind must name a type the store holds; the store holds no type called 'invoice'")] 
refs out of work-item/w -> answered 
delete work-item/w -> [('', 'kind', "a kind must name a type the store holds; the store holds no type called 'invoice'")] 
search fields for one -> [('', 'kind', "a kind must name a type the store holds; the store holds no type called 'invoice'")] 
list invoice -> [('', 'kind', "a kind must name a type the store holds; the store holds no type called 'invoice'")] 
validate -> answered [('invoice/i-one', 'kind')]
work-item/w still there: True
```

no lines; no lines; `209`, `89`, `120`, `137`, `182`.

- [ ] **Step 6: Checkpoint and commit**

Append the slice 94.1 checkpoint to the slice plan's log (what someone reading the code can now rely on, the check and the probe before and after, line counts; open questions: the slice plan's question of 2026-09-26 on a kind with no type met in passing still stands) and set its Status to `green`.

```bash
git add src/kb docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 94.1: Which type a kind names is asked of composition alone, by every reader

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Slice 94.2, what a title gives is worked out in one place

**Slice plan entry:** Slice 94.2, enabling. Check: the suite's summary and failing ids unchanged; `grep -n "def title" src/kb/content.py` → no lines (1 before); `grep -nE "^(import|from) " src/kb/names.py` → 2 lines (3 before); `grep -n "names\." src/kb/requests.py` → no lines (1 before); `grep -n "^from kb import" src/kb/requests.py` → `from kb import values`; `grep -n "names.slug" src/kb/values.py src/kb/requests.py` → 2 lines, both in `values.py` (5 before); the probe unchanged.

**Files:**
- Modify: `src/kb/names.py` (new `title`; the `kb.content` import goes; `items` asks `title`)
- Modify: `src/kb/content.py` (`title` goes)
- Modify: `src/kb/values.py` (`_titled` asks `names.title`; `named` gives the name, the name its faults are said of, and the faults)
- Modify: `src/kb/requests.py` (`_create` takes all three from `values.named`; the `names` import goes)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `names.slug`, `names.written`, `values._leaves_nothing`.
- Produces: `names.title(value) -> str | None`; `values.named(kind: Kind, title: str) -> tuple[ArtifactId | None, str, tuple]`. `content.text` stays, used by `query._holds` and by a step in `tests/test_create_an_artifact.py`.

- [ ] **Step 1: Save the failing ids and the probe's answers**

Save this probe as `/tmp/probe-94-2.py`:

```python
"""Slice 94.2's probe: the names titles give, to artifacts and to items."""
import pathlib, sys, tempfile

sys.path.insert(0, "tests")
from calls import CLIENT, DECISION_TYPE
from kb import client as kb_client
from kb.content import dumps
from kb.contract import kb_pb2

root = pathlib.Path(tempfile.mkdtemp())
client = kb_client.connect(root)
client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
flat = {"type": "object", "parts": {"steps": {"items": {}}}}
for title, schema in (("Decision", DECISION_TYPE["schema"]), ("Flat", flat)):
    client.Create(kb_pb2.CreateRequest(type="schema", title=title, actor=CLIENT, message="m",
        content=dumps({"version": 1, "schema": schema})))
sections = dumps({"sections": [{"title": "Purpose", "body": "p"}, {"title": "Rationale", "body": "r"}]})
for title in ("", "!!!", "D one", "D one"):
    created = client.Create(kb_pb2.CreateRequest(type="decision", title=title, actor=CLIENT, message="m", content=sections))
    print(repr(title), "->", created.id or [(f.artifact, f.path, f.rule, f.message) for f in created.faults])
print("flat/c ->", client.Create(kb_pb2.CreateRequest(type="flat", title="C", actor=CLIENT, message="m", content=dumps({"steps": []}))).id)
for item in ({"title": 12}, {"title": True}, {"title": [1]}, {"title": None}, {"title": "!!!"}):
    added = client.Append(kb_pb2.AppendRequest(locator=kb_pb2.Locator(id="flat/c", path="steps"), content=dumps(item), actor=CLIENT, message="m"))
    print(item, "->", added.id or [(f.path, f.rule) for f in added.faults])
```

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
.venv/bin/python /tmp/probe-94-2.py | tee /tmp/probe-94-2-before.txt
```

Expected:

```
'' -> [('decision/', 'title', 'title', 'an artifact cannot be created without a title')]
'!!!' -> [('decision/', 'title', 'title', "a title must leave something to make a name from; '!!!' leaves nothing")]
'D one' -> decision/d-one
'D one' -> decision/d-one-2
flat/c -> flat/c
{'title': 12} -> 12
{'title': True} -> true
{'title': [1]} -> 3
{'title': None} -> 4
{'title': '!!!'} -> [('title', 'title')]
```

- [ ] **Step 2: Which values a title may be written as, in names.py**

In `src/kb/names.py`, delete the import line and the blank line before it:

```python

from kb.content import title as title_of
```

so the imports are `import re` and `from typing import Callable, NamedTuple`. Replace:

```python
def slug(title: str) -> str:
```

with:

```python
def title(value) -> str | None:
    """A title as the text a name is made from: text as it is, and a number, true or false as YAML 1.2 writes it.
    None for anything a title is never written as: nothing, a list or a mapping."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int, float)):
        return str(value)
    return None


def slug(title: str) -> str:
```

and, in `items`, replace:

```python
                title = title_of(item.get("title"))
                item["id"] = numbered(slug(title) if title is not None else str(place), taken.__contains__)
```

with:

```python
                text = title(item.get("title"))
                item["id"] = numbered(slug(text) if text is not None else str(place), taken.__contains__)
```

In `src/kb/content.py`, delete `title` and the two blank lines after it:

```python
def title(value) -> str | None:
    """A title as text: text as it is, and a number, true or false as YAML 1.2 writes it. None for anything a title
    is never written as: nothing, a list or a mapping."""
    if isinstance(value, (str, bool, int, float)):
        return text(value)
    return None


```

- [ ] **Step 3: A new artifact's name, worked out once, in values.py**

In `src/kb/values.py`, replace `from kb.content import entries, loads, title as title_of` with `from kb.content import entries, loads`, and in `_titled` replace `    title = title_of(tree.get("title"))` with `    title = names.title(tree.get("title"))`. Replace:

```python
def named(kind: Kind, title: str) -> ArtifactId:
    """The name kb gives an artifact of this kind from its title. A title is required and must leave a name."""
    at = names.written(kind.name, names.slug(title))
    if not title:
        raise Refused([kb_pb2.Fault(artifact=at, path="title", rule="title",
                                    message="an artifact cannot be created without a title")])
    if not names.slug(title):
        raise Refused([kb_pb2.Fault(artifact=at, path="title", rule="title", message=_leaves_nothing(title))])
    return ArtifactId(kind, names.slug(title))
```

with:

```python
def named(kind: Kind, title: str) -> tuple[ArtifactId | None, str, tuple]:
    """The name kb gives an artifact of this kind from its title, and the name its faults are said of; None, with the
    title's faults, when it gives none. A title is required and must leave a name."""
    slug = names.slug(title)
    at = names.written(kind.name, slug)
    if not title:
        message = "an artifact cannot be created without a title"
    elif not slug:
        message = _leaves_nothing(title)
    else:
        return ArtifactId(kind, slug), at, ()
    return None, at, (kb_pb2.Fault(artifact=at, path="title", rule="title", message=message),)
```

In `src/kb/requests.py`, replace `from kb import names, values` with `from kb import values`, and replace:

```python
    kind = values.kind(creation.type)
    try:
        name, title_faults = values.named(kind, creation.title), ()
    except Refused as refused:
        name, title_faults = None, tuple(refused.faults)
    at = names.written(kind.name, names.slug(creation.title))
    return Create(kind, creation.title, name, at, title_faults, values.content(creation.content))
```

with:

```python
    kind = values.kind(creation.type)
    name, at, title_faults = values.named(kind, creation.title)
    return Create(kind, creation.title, name, at, title_faults, values.content(creation.content))
```

`Refused` is still imported by `requests.py`, for the conversions of a set and of the journal's filters.

- [ ] **Step 4: Check**

```bash
.venv/bin/python -m pytest -q 2>&1 | tail -1
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before -
.venv/bin/python /tmp/probe-94-2.py | diff /tmp/probe-94-2-before.txt -
grep -n "def title" src/kb/content.py
grep -nE "^(import|from) " src/kb/names.py
grep -n "names\." src/kb/requests.py
grep -n "^from kb import" src/kb/requests.py
grep -n "names.slug" src/kb/values.py src/kb/requests.py
wc -l src/kb/names.py src/kb/values.py src/kb/requests.py src/kb/content.py
```

Expected: `1 failed, 195 passed`; no diff; no diff; no lines; `4:import re` and `5:from typing import Callable, NamedTuple`; no lines; `7:from kb import values`; two lines, both in `values.py` (in `named` and `_titled`); `135`, `241`, `177`, `31`.

- [ ] **Step 5: Checkpoint and commit**

Append the slice 94.2 checkpoint to the slice plan's log (what someone reading the code can now rely on, the check and the probe before and after, line counts, open questions: none) and set its Status to `green`. Then append the batch line: slices 90.1 to 94.2 green; suite 1 failed, 195 passed, the one failure slice 89.2's; next: slice 89.2 if approved, otherwise slice 95, the sixth architecture review.

```bash
git add src/kb docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 94.2: What a title gives is worked out in one place

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```
