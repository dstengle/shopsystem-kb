# kb Batch 13 Implementation Plan: slice 95.1, after the sixth architecture review

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Each task is one slice of `docs/superpowers/plans/2026-09-24-kb-slices.md`. The one task here is an enabling slice: it adds no scenario and changes no scenario's answer; its check is the suite's failing test ids unchanged, its structural target met, and a probe giving the answer the plan names.

**Goal:** The one slice slice 95, the sixth architecture review, cut:
- Where a link sits is read where links are read (slice 95.1, enabling).

**Not in this plan:** slice 89.2, "The client follows the links out of one place inside an artifact". Its Given has a section carry a link, which the spec says a section never does; the slice plan's log holds the RE-FORMULATE entry and the question. No task here touches that scenario, and it stays red (tagged `@slice-89.2`). Every other gap review 6 found closes only by changing what some call answers, and is a QUESTION FOR THE SPEC in the slice plan's log, never a task here (see Review Focus).

**Architecture:** kb is the Python package `kb` in `/home/vscode/shopsystem-kb`. A protobuf contract (`kb.contract`) sits in front of `KbServicer` (`servicer.py`), whose every rpc runs inside one boundary that turns `values.Refused` into that rpc's faults. `links.py` is, by `CLAUDE.md`'s module map, "the one reading of links: every link an artifact carries, wherever it sits"; it finds each link with `links.carried`, which gives a `Link(field, place, target, ref)`, the place written as `names.placed` writes one (`decisions/0`, `steps/0/uses`). `read.py` answers reads; its whole read at a depth fills in the links in the artifact's own fields and leaves a link inside an item a name, a choice slice 87.1 kept in `read.py` on purpose. Today `read._own` learns whether a link sits in an own field by taking apart the place `links.py` wrote (`partition("/")`, `isdigit()`): a second reading of a link's place outside `links.py`. This plan implements the map once:
- **links.py is the one reading of links (the module map).** A `Link` says whether it sits in one of the artifact's own fields, alone or in a list, rather than in a field of an item, as `links._links_in` finds it (the place it is found at is the artifact's root when `at` is empty). `read._resolved` asks `link.own`; `read._own` goes. Which links a whole read fills in stays said in `read.py`.
- **Fail-closed boundary (rule 1).** No rpc gains a `try`; nothing here catches anything.

**Provenance:** Every code block here was assembled in a scratch clone of this repository (`/tmp/kb13`, cloned at `487e48a`, run with this checkout's `.venv` and `PYTHONPATH=/tmp/kb13/src`) on 2026-09-26, and the task applied in one commit. The suite counts, the failing-id comparison, the probe before and after, the grep and the line counts are what that run gave. This repository was not touched except to write this plan and the slice plan's entries. The plan was then replayed from its text alone, in the foreground of the same session, in a second clone (see the end of this file).

**Tech Stack:** Python 3.11, setuptools (src layout), protobuf + grpcio (generated code committed; no `.proto` change in this batch), python-jsonschema 4.26 with `referencing`, ruamel.yaml 0.19 (YAML 1.2), git via subprocess, pytest 9 + pytest-bdd 8.

**Spec:** `docs/superpowers/specs/2026-09-23-kb-design.md`. No sentence of it changes meaning here; the slice is structural. The slice plan is `docs/superpowers/plans/2026-09-24-kb-slices.md` (slice 95.1 and review 6's log entry), and the feature files are in `features/`. `CLAUDE.md` at the repository root is binding.

## Global Constraints

- Feature files are read-only for the implementer. Any diff under `features/` is a stop condition; this batch touches none.
- An enabling slice changes no behaviour: no call answers differently afterwards, no scenario is added, no step definition changes.
- **CLAUDE.md's rules are implemented once.** No rpc in `servicer.py` gains a `try` (`grep -c "try:" src/kb/servicer.py` stays `1`). No module but `links.py` reads a link's place to say where the link sits. No module catches a broad exception (`grep -nE "except (Exception|BaseException)|except:" src/kb/*.py` prints nothing).
- **Size.** No module over 250 lines; `servicer.py` under 150. After the task `read.py` is 114 lines and `links.py` 54. `values.py` stays 241 and is not touched.
- Tests use the contract or a module's public functions, never private helpers. This task changes no test.
- `make test` runs the suite in this checkout's virtualenv (`.venv/bin/python -m pytest -q`). While any scenario is red, make's own error line comes last, so the steps run pytest directly to see the summary. A worktree needs its own `.venv` first (`make dev`).
- The contract's version stays `0.1`, `pyproject.toml` stays `0.1.0`.
- Work on `main` in `/home/vscode/shopsystem-kb`.
- Commits: `git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit`, the message ending with the Co-Authored-By line of the model that made the commit, e.g. `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- The suite prints pytest-bdd `PytestRemovedIn10Warning`s. That is the baseline, not a fault. The summary lines quoted as Expected leave out the `, N warnings in Xs` that pytest adds.
- Baseline before Task 1: `.venv/bin/python -m pytest -q` → `1 failed, 195 passed`, the one failure slice 89.2's (`tests/test_follow_the_links.py::test_the_client_follows_the_links_out_of_one_place_inside_an_artifact`). After Task 1: `1 failed, 195 passed`, the same id.
- A probe is a Python script run with `.venv/bin/python` from the repository root, given in full in the task, that drives the in-process client over a store in a temporary directory. Save it under `/tmp`, run it before the change and after, and compare.

## Decisions this plan makes

1. **How a link says where it sits.** A fifth field on `links.Link`, `own: bool`, true for a link in one of the artifact's own fields (alone, or an entry of a list), false for a link in a field of an item at any depth. It is set where the link is found, from whether the node being read is the artifact itself. Every `Link` is built in `links.py` alone (`grep -rn "Link(" src/kb/` shows only `links.py`), and no reader unpacks a `Link` by position, so the new field reaches no other module but `read.py`, which asks it.

## Review Focus

Five inputs no task's scenarios exercise, most likely to bite first. Each was reproduced against `487e48a` by review 6, is logged as a QUESTION FOR THE SPEC in the slice plan's log, and is never code in this plan.

1. **A write under no role or no message leaves its change on disk.** Reproduction: the decision and work-item types, `work-item/w` with `decisions: [decision/d-one]`; Write `work-item/w` with `decisions: []` under `kb_pb2.Actor(role="")`: `subprocess.CalledProcessError` through the client, and `git -C kb status --porcelain` shows `M  work-item/w.yaml` and a journal entry added, uncommitted; a Read then answers revision 2. The same with a role and the message `""`, and a Snapshot with the message `""` leaves its entry.
2. **Stored prose with a line ending in a space breaks reads.** Reproduction: `decision/d-one` with its Rationale body `b` changed to `b ` by hand in `kb/decision/d-one.yaml`: a whole Read, a section Read of Rationale, and a whole Read at depth 1 of a work item linking to it raise `canonical.NotCanonical`; a Write to its Purpose is refused with rule `content` and no place.
3. **A file whose name is not a name is listed.** Reproduction: copy `kb/decision/d-one.yaml` to `kb/decision/Bad Name.yaml`; List the decisions as names: `['decision/Bad Name', 'decision/d-one']`, and a Read of `decision/Bad Name` is refused with rule `locator`.
4. **Prose ending a line in a tab is written.** Reproduction: Create a decision titled `Tabbed` whose Purpose body is `a\t\n`: accepted, where a line ending in a space is refused (slice 92).
5. **A history entry without its id breaks the journal off.** Reproduction: write `op: create\n` over the newest file under `kb/journal/`; Journal raises `KeyError: 'id'` through the client (batch 10's question, re-run by review 6).

---

### Task 1: Slice 95.1, where a link sits is read where links are read

**Slice plan entry:** Slice 95.1, enabling. Check: the suite's summary and failing ids unchanged; `grep -nE 'partition|isdigit' src/kb/read.py` → no lines (2 before); which links a whole read fills in is still said in `read.py`; `read.py` and `links.py` under 250 lines; the probe unchanged: the work item's decision filled in, the process step's link still a name, the link into a part refused with rule `locator`.

**Files:**
- Modify: `src/kb/links.py` (`Link` gains `own`; `_links_in` sets it)
- Modify: `src/kb/read.py` (`_resolved` asks `link.own`; `_own` goes)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `links.carried(artifact, schema, corpus) -> list[Link]`, unchanged in signature.
- Produces: `links.Link(field: str, place: str, target: str, ref: dict, own: bool)`. `own` is true for a link in one of the artifact's own fields, alone or in a list, and false for a link in a field of an item at any depth.

- [ ] **Step 1: Save the failing ids and the probe's answers**

Save this probe as `/tmp/probe-95-1.py`:

```python
"""Slice 95.1's probe: which links a whole read at depth 1 fills in, by where they sit."""
import copy, pathlib, sys, tempfile

sys.path.insert(0, "tests")
from calls import CLIENT, DECISION_TYPE, PROCESS_TYPE, WORK_ITEM_TYPE, create, define, read
from kb import client as kb_client
from kb.content import loads
from kb.contract import kb_pb2

root = pathlib.Path(tempfile.mkdtemp())
client = kb_client.connect(root)
client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
process_type = copy.deepcopy(PROCESS_TYPE)
process_type["schema"]["parts"]["steps"]["items"]["properties"]["uses"]["ref"]["targets"] = ["decision"]
work_item_type = copy.deepcopy(WORK_ITEM_TYPE)
work_item_type["schema"]["properties"]["decisions"]["ref"].update(targets=["decision", "process"], parts=True)
for type_content in (DECISION_TYPE, process_type, work_item_type):
    define(client, type_content)
create(client, "decision", {"title": "D one", "sections": [{"title": "Purpose", "body": "a\n"}, {"title": "Rationale", "body": "b\n"}]})
create(client, "process", {"title": "Open the shop", "steps": [{"title": "Count the till", "uses": "decision/d-one"}]})
create(client, "work-item", {"title": "W", "decisions": ["decision/d-one"]})
create(client, "work-item", {"title": "V", "decisions": ["process/open-the-shop#steps/count-the-till"]})
whole = read(client, "work-item/w", whole=True, depth=1)
print("work-item/w decisions ->", [value["id"] if isinstance(value, dict) else value for value in loads(whole.content)["decisions"]],
      [type(value).__name__ for value in loads(whole.content)["decisions"]])
process = read(client, "process/open-the-shop", whole=True, depth=1)
print("process step uses ->", repr(loads(process.content)["steps"][0]["uses"]))
refused = read(client, "work-item/v", whole=True, depth=1)
print("work-item/v ->", [(fault.artifact, fault.path, fault.rule) for fault in refused.faults])
```

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
.venv/bin/python /tmp/probe-95-1.py | tee /tmp/probe-95-1-before.txt
grep -nE 'partition|isdigit' src/kb/read.py
```

Expected: `/tmp/failing-before` holds the one line `FAILED tests/test_follow_the_links.py::test_the_client_follows_the_links_out_of_one_place_inside_an_artifact`; the probe prints:

```
work-item/w decisions -> ['decision/d-one'] ['dict']
process step uses -> 'decision/d-one'
work-item/v -> [('process/open-the-shop#steps/count-the-till', '', 'locator')]
```

and the grep prints two lines, `93:` (`head, _, rest = link.place.partition("/")`) and `94:` (`return head == link.field and (not rest or rest.isdigit())`).

- [ ] **Step 2: A link says where it sits, in links.py**

In `src/kb/links.py`, replace:

```python
class Link(NamedTuple):
    """One link an artifact carries: the field that holds it, the place of that field in the artifact, the name it
    points at, and the field's `ref`, which says what it may land on."""
    field: str
    place: str
    target: str
    ref: dict
```

with:

```python
class Link(NamedTuple):
    """One link an artifact carries: the field that holds it, the place of that field in the artifact, the name it
    points at, the field's `ref`, which says what it may land on, and whether the field is one of the artifact's own,
    holding the link alone or in a list, rather than a field of one of its items."""
    field: str
    place: str
    target: str
    ref: dict
    own: bool
```

and, in `_links_in`, replace:

```python
            found += [Link(field, f"{at}{field}/{index}", target, ref) for index, target in enumerate(value)]
        elif value is not None:
            found.append(Link(field, f"{at}{field}", value, ref))
```

with:

```python
            found += [Link(field, f"{at}{field}/{index}", target, ref, not at) for index, target in enumerate(value)]
        elif value is not None:
            found.append(Link(field, f"{at}{field}", value, ref, not at))
```

`at` is empty exactly when the node being read is the artifact itself; an item's links are found with `at` ending in `<collection>/<index>/`.

- [ ] **Step 3: A whole read asks the link, in read.py**

In `src/kb/read.py`, in `_resolved`, replace:

```python
    for field in {link.field for link in carried if _own(link)}:
```

with:

```python
    for field in {link.field for link in carried if link.own}:
```

and delete `_own` with the two blank lines after it:

```python
def _own(link: links.Link) -> bool:
    """Whether a link sits in one of the artifact's own fields, alone or in a list, rather than inside an item."""
    head, _, rest = link.place.partition("/")
    return head == link.field and (not rest or rest.isdigit())


```

`read.py` still imports `links`, for `links.carried` and `links.points_at`.

- [ ] **Step 4: Check**

```bash
.venv/bin/python -m pytest -q 2>&1 | tail -1
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before -
.venv/bin/python /tmp/probe-95-1.py | diff /tmp/probe-95-1-before.txt -
grep -nE 'partition|isdigit' src/kb/read.py
grep -rn "Link(" src/kb/
grep -c "try:" src/kb/servicer.py
git status --porcelain features/
wc -l src/kb/read.py src/kb/links.py
```

Expected: `1 failed, 195 passed`; no diff; no diff; no lines; three lines, all in `src/kb/links.py` (the class and the two constructions); `1`; nothing; `114` and `54`.

- [ ] **Step 5: Checkpoint and commit**

Append the slice 95.1 checkpoint to the slice plan's log, in the shape of slice 94.2's: slice 95.1 green (enabling, no scenario); what someone reading the code can now rely on (`links.Link.own` says whether a link sits in one of the artifact's own fields, set where `links.py` finds it; `read.py` no longer takes a link's place apart, and still says which links a whole read fills in); surprised by; the check before and after (failing ids unchanged, the suite `1 failed, 195 passed` before and after, the grep two lines before and none after, the probe unchanged, the line counts); open questions: none. Set slice 95.1's Status to `green`. Then append the batch line: slice 95.1 green; suite 1 failed, 195 passed, the one failure slice 89.2's; the plan is complete apart from slice 89.2, blocked awaiting approval, and the questions for the spec logged by review 6.

```bash
git add src/kb docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 95.1: Where a link sits is read where links are read

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Replay

Replayed from this file's text alone, in the foreground of the session that wrote it, in a second clone (`/tmp/kb13-replay`, from `487e48a`, `PYTHONPATH=/tmp/kb13-replay/src`, this checkout's `.venv`): the probe and the step commands taken verbatim from Task 1's code blocks by their place in it, each replacement found exactly once, every command run as written. Every Expected held: the failing id saved before, the probe's three lines before, the grep's two lines before; after Steps 2 and 3, `1 failed, 195 passed`, no diff of the failing ids, no diff of the probe, no lines from the grep, the three `Link(` lines all in `links.py`, `1` `try:` in `servicer.py`, nothing under `features/`, and `114` and `54` lines. The replayed `src/` is identical to the scratch run's (`diff -r`, no output). The replay found no fault in this text.
