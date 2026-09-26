# kb Batch 10 Implementation Plan: slices 77 to 82, and the refactors among them

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Each task is one slice of `docs/superpowers/plans/2026-09-24-kb-slices.md`. Inside a capability task, follow `shopsystem-bdd:bdd-red-green` scenario by scenario; its stop conditions, hand-back and checkpoint apply, and they override any step here that conflicts with them. An enabling task (77.1, 78.1, 78.2, 79.1, 79.2) adds no scenario and changes no scenario's answer: its check is the suite's failing test ids unchanged, its structural target met, and, where it makes a crash unreachable, a probe giving the answer the plan names.

**Goal:** The eleven slices between slice 76, the third architecture review, and slice 83, the fourth:
- A collection inside an item can be added to (slice 77).
- Where a link lands is asked of the one resolution of a place (slice 77.1, enabling).
- A field written as a bare date is the text written (slice 78).
- Where a file lies is the store's alone (slice 78.1, enabling).
- Loading gives an artifact or the damage, whatever the bytes (slice 78.2, enabling).
- A type, or an entry of the history, that cannot be read is refused, naming the file (slice 79).
- A damaged type met through another type's reference is the damaged file's fault (slice 79.1, enabling).
- An item is taken apart only once it is known to be a set of named entries (slice 79.2, enabling).
- An item's title becomes its name by the rule an artifact's does (slice 80).
- A check reports an artifact whose kind has no type (slice 81).
- A kind with no type is refused wherever it is asked by (slice 82).

**Architecture:** kb is the Python package `kb` in `/home/vscode/shopsystem-kb`. A protobuf contract (`kb.contract`) sits in front of `KbServicer` (`servicer.py`), whose every rpc runs inside one boundary that turns `values.Refused` into that rpc's faults. `requests.py`/`values.py` convert requests; `canonical.py` is the one YAML checker, dump and load; `write.py` drafts a set and only then writes; `edits.py` says what each operation does to the draft; `places.py` resolves a place inside an artifact; `validation.py` holds the composed schema and kb's own checks; `composition.py` reads a type through what it is built on; `check.py` is the check of the whole store; `store.py` is files and git, and `Store.load` returns an artifact or `Damaged`; `journal.py` owns the history's files. `CLAUDE.md` is the rulebook. This plan implements each rule it touches once:
- **Loading returns a value (rule 3).** `canonical.decoded(bytes)` is the one place a stored file's bytes become text, raising `NotCanonical` for bytes that are not UTF-8; `Store.load` reads through it and `canonical.entries`, then holds what it loaded to carrying what the store settles for every artifact, so every shape of damage is `Damaged` before any reader sees it (Task 5). The history's files are loaded the same way by `journal.entries`, which gives `Damaged` in place of the entries, and `store.readable` stays the one place damage becomes a refusal (Task 6). A refusal raised while the JSON Schema library retrieves a type comes out of `validation.validate` as itself (Task 7).
- **Parse, don't validate (rule 2).** An item as a request carries it is asked what it carries only once it is known to be a mapping (Task 8), and its title is made text there, by `content.text`, the one conversion a title that is not text goes through (Task 9).
- **Names live in one place (rule 6), with the module map.** Resolving a place is `places.py`'s: a link's place is asked of it (Task 2). Where files lie is `store.py`'s (Task 4). Which type a kind names, and the refusal when there is none, is one function, `composition.kind_type`, read by Create and by every question that takes a kind (Task 11).
- **A new concern gets a new module; nothing beside.** No module is added. CLAUDE.md's rows for `places.py` and `check.py` grow with what they now own (Tasks 2 and 10).

**Provenance:** Every code block here was assembled in a scratch clone of this repository (`/tmp/kb10`, cloned at `172b006`, run with this checkout's `.venv` and `PYTHONPATH=/tmp/kb10/src`) on 2026-09-26, and the tasks were applied in order, one commit each. The red and green results, the suite counts, the failing-id comparisons, the line counts, the probes and the Review Focus reproductions are what those runs gave. The plan was then replayed from its own text on a fresh clone (`/tmp/kb10-replay`, at `172b006`, run the same way), one commit per task: a fresh agent took Tasks 1 to 6, and after it was interrupted partway through Task 7 its working tree was reset to Task 6's commit and Tasks 7 to 11 were replayed from the text. Every "replace" text was found verbatim once, every probe, red, green, suite count, failing-id diff and line count matched, no import was left unused, no feature file changed, and the 29 failures left were exactly the later slices listed below; the replay's `src/`, `tests/` and `CLAUDE.md` were identical to the scratch run's. Tasks 7 to 11 needed no change to the text; the checks of slices 78.2 and 79.2 in the slice plan were amended while this plan was written (a `schema_version` written `one`, and one decoding of bytes, for 78.2; an item `12`, and `{id: x, title: T}` still refused at `id`, for 79.2), and the replay confirmed both. This repository was not touched except to write this plan and log it in the slice plan.

**Tech Stack:** Python 3.11, setuptools (src layout), protobuf + grpcio (generated code committed; no `.proto` change in this batch), python-jsonschema 4.26 with `referencing`, ruamel.yaml 0.19 (YAML 1.2), git via subprocess, pytest 9 + pytest-bdd 8.

**Spec:** `docs/superpowers/specs/2026-09-23-kb-design.md`, in particular:
- "Canonical YAML": one serialization, YAML 1.2, checked on the way in and on the way out.
- "Validate": every violation reported with its artifact, place and rule, the stale listed beside them, and a file that cannot be read reported as a violation.
- "Append": an item added to a collection named by its place, the item's name minted by the store.

The slice plan is `docs/superpowers/plans/2026-09-24-kb-slices.md`, and the feature files are in `features/`. Each capability slice's scenarios carry `@slice-<n>`, so `.venv/bin/python -m pytest -q -m slice-77` runs one slice. `CLAUDE.md` at the repository root is binding.

## Global Constraints

- Feature files are read-only for the implementer. Only `slicing-into-increments` edits a tag line, and only `formulating-features` edits a Given, When, or Then. Any diff under `features/` is a stop condition; this batch touches none.
- Code only what a scenario asserts (bdd-red-green). Where the scenarios are silent, the code is silent too, and the silence goes into the checkpoint entry as an open question. The decisions this plan makes are listed below, each tied to the scenario or slice that asks for it.
- **CLAUDE.md's rules are implemented once, never per row.** No rpc in `servicer.py` gains a `try`, a check, or a branch in this batch (`grep -c "try:" src/kb/servicer.py` stays `1`). No module but `canonical.py` decodes a stored file's bytes; no module but `store.py` says where a file lies (the journal's own files aside); no module but `places.py` walks a place; no module but `composition.py` decides whether a kind names a type. No module catches a broad exception (`grep -nE "except (Exception|BaseException)|except:" src/kb/*.py` prints nothing).
- **Extend, never add beside.** Test helpers and shared test constants live in `tests/calls.py`; a step two feature files share word for word is one step definition in `tests/conftest.py`, never two. A test module never imports from `conftest.py`.
- **Size.** No module over 250 lines; `servicer.py` under 150. The line counts each task ends at are in its check. At the end of the batch the largest are `values.py` 226, `store.py` 222 and `canonical.py` 213; slice 83 weighs them.
- Errors are a typed list of `{ artifact, path, rule, message }`. A response that carries faults is a refusal, and nothing was written.
- kb is exercised through its in-process transport (`kb.client.connect`).
- `make test` runs the suite in this checkout's virtualenv (`.venv/bin/python -m pytest -q`). While any scenario is red, make's own error line comes last, so the steps run pytest directly to see the summary. A worktree needs its own `.venv` first (`make dev`).
- The contract's version stays `0.1`, `pyproject.toml` stays `0.1.0`. Version and tag are the user's call.
- Work on `main` in `/home/vscode/shopsystem-kb`. shop-knowledge pins kb at `v0.1.0`; nothing here touches or runs its suite.
- Commits: `git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit`, the message ending with the Co-Authored-By line of the model that made the commit, e.g. `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- "Append at the end of the file" means after two blank lines, as the files' top-level definitions are spaced.
- The suite prints pytest-bdd `PytestRemovedIn10Warning`s. That is the baseline, not a fault. The summary lines quoted as Expected leave out the `, N warnings in Xs` that pytest adds.
- Baseline before Task 1: `.venv/bin/python -m pytest -q` → `40 failed, 156 passed`. After each task the suite reads, failed/passed: 1 `39/157`; 2 `39/157`; 3 `38/158`; 4 `38/158`; 5 `38/158`; 6 `36/160`; 7 `36/160`; 8 `36/160`; 9 `33/163`; 10 `32/164`; 11 `29/167`. Every failure left after Task 11 is tagged for slice 84 or later (84: 1, 85: 3, 86: 2, 87: 2, 88: 7, 89: 2, 91: 4, 92: 2, 93: 3, 94: 3), and none of those goes green early.
- Every task's first step saves the failing ids (`.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before`). An enabling task's check compares them after (`... | sort | diff /tmp/failing-before -` prints nothing); a capability task's check shows only its own scenarios leaving (`diff` prints only `<` lines, one per row of the slice).
- A probe is a Python script run with `.venv/bin/python`, given in full in the task, that drives the in-process client over a store in a temporary directory. Save it under `/tmp`, run it before the change and after, and compare.

## Decisions this plan makes (the spec left them open or silent)

1. **A collection inside an item (slice 77).** A place `steps/unlock-the-door/checks` names the collection `checks` of the step `unlock-the-door`; an addition may land in any collection the type declares where the place's last step stands, read through the item type of each collection the place passes through. Items are named at every depth, by the one rule `names.items` already applies to an artifact's own collections, whenever a create or a change names items; so the checks a Write gives a step are named as the step's own are. The entry's place, and the path of the new item, is the whole place with the item's name after it (`steps/unlock-the-door/checks/door-stays-open`), which for a collection of the artifact's own is what it was (`steps/count-the-float`).
2. **Where a link lands (slice 77.1).** `places.holds_part(content, place)` is true for pairs of a collection and the id of an item in it, at any depth, never a collection called `sections` and never a place ending in a field. That is what `validation._holds_part` answered; a link into a section stays refused (the question logged on 2026-09-26).
3. **A bare date (slice 78).** The one YAML reader constructs a value its resolver tags as a timestamp as the string it was written as. The dumper is unchanged, so text that looks like a date is still written quoted and every file's bytes, and every fingerprint, stay as they were.
4. **Where files lie (slice 78.1).** `Store.path` makes an artifact's path itself, and `Store.start` gives back where it wrote the marker, which `write.start` commits. `values.path` is gone.
5. **What loading holds a stored file to (slice 78.2).** Text in UTF-8 (`canonical.decoded`), canonical, a set of named entries, and carrying what the store settles for every artifact: `id`, `type` and `title` as text, `schema_version` and `revision` as whole numbers (`store.SETTLED`). Any other file is `Damaged` with the `unreadable` fault naming it, its message saying `it is not text written in UTF-8`, or `it does not carry what the store settles for every artifact: <the keys, in that order>`. A type's own keys beyond these (`schema`, `version`) are not held here (Review Focus 5).
6. **A history entry that cannot be read (slice 79).** `journal.entries` reads every entry's file as `Store.load` reads an artifact's, and gives the `Damaged` of the first file, in path order, that cannot be read, in place of the entries; `query.entries` reads it through `store.readable`. The fault names no artifact (`artifact` empty) and its message names the entry's file from the store's directory (`the stored file journal/2026/09/26/<id>.yaml cannot be read: ...`). `refusals.unreadable` therefore takes the name as text. A damaged type met by a create was already refused with its file named since slice 63; that row passes as soon as its steps exist.
7. **A damaged type met through a reference (slice 79.1).** `validation.validate` catches only `referencing.exceptions.Unresolvable`, and re-raises the `Refused` found among its causes; an `Unresolvable` no refusal caused is raised as it was.
8. **An item's shape (slice 79.2).** `values.item` asks whether an item carries a name only when the item is a mapping; any other item goes to its type, which refuses it at its place with rule `type`, as it already refused `just words`.
9. **An item's title (slice 80).** In an addition, an item's title that is a number or a yes-or-no is made text by `content.text` (`12` is `"12"`, `true` is `"true"`), and a title that leaves nothing to make a name from is refused at `title` with rule `title` and the message an artifact's gets, `a title must leave something to make a name from; '!!!' leaves nothing`. A title that is nothing, a list or a mapping is left for the type. Only an addition converts an item's title: no scenario asks for an item inside a Create or a Write (Review Focus 2).
10. **A kind with no type (slices 81 and 82).** `refusals.no_type(kind_name, artifact="")` is the one fault, rule `kind`. The check reports it for an artifact whose kind has no type, naming the artifact, and goes on. `composition.kind_type(kind, corpus)` gives the type's name or raises it, and Create, List, Search with a type, and Refs with a type all ask it before anything else, so a question by such a kind is refused before the name it starts from is looked up.

## Review Focus

In this project, tests are scenarios, and the feature files are the human gate, so no unit tests are added. Instead, each line below goes into the owning task's checkpoint entry as a `QUESTION FOR THE SPEC`, with the reproduction given here. Each was reproduced in scratch after all eleven tasks.

1. **The names on the items inside an item are taken on trust.** Reproduction: a process type whose steps carry a collection `checks` of items requiring a title; a process `process/p` with one step `S` holding one check `A`; Write `process/p` with `steps: [{id: s, title: S, checks: [{id: x, title: A}, {id: x, title: B}]}]`. It is accepted, and both checks are stored as `x`. `names.handed_back` reads the artifact's own collections only, so a name handed back inside an item is never checked, where one on a step is refused as `repeated` or `unknown`. Task 1 logs it.
2. **An item inside a Create or a Write is named by no rule for its title.** Reproduction: create a process `Q` whose steps are two items titled `!!!`; it is accepted, and the steps are named `""` and `-2`. Slice 80 converts an item's title only in an addition, as its scenario asks. Task 9 logs it.
3. **The check of the whole store breaks off at a type met through a reference that cannot be read.** Reproduction: types `schema/tool` (with `$defs.binding`), `schema/tool-use` whose field `b` refers to it, and a tag type; a `tool-use` `U` and a tag `T`; write `title: [` over `kb/schema/tool.yaml`; Validate answers with the one fault `schema/tool` `unreadable` among its faults, and no violations: the tag and the tool use go unchecked. Before slice 79.1 it raised through the client. A person expects the check to report the file and go on, as it does for a file met directly. Task 7 logs it.
4. **A history entry that is a set of named entries but lacks its id breaks the journal off.** Reproduction: write `op: create\n` over the newest file under `kb/journal/`; Journal raises `KeyError: 'id'` through the client, since the entries are sorted by their ids. Slice 79 holds an entry to being canonical and a set of named entries, as its scenario asks; what an entry must carry has no scenario. Task 6 logs it.
5. **A type file that lacks its schema breaks a create off.** Reproduction: define the tag type; delete `schema` from `kb/schema/tag.yaml` and write it back canonically; create a tag `T`: it raises `KeyError: 'schema'` through the client. Validate reports `schema/tag` `required`, as a person expects. Loading holds every file to what the store settles for every artifact, not to what a type must also carry. Task 5 logs it.

---

### Task 1: Slice 77, a collection inside an item can be added to

**Slice plan entry:** Slice 77, capability. Unknown: can a place name a collection inside an item, for an addition to land in? Scenario:

- kb / add-an-item-to-a-collection / The client adds an item to a collection inside an item

The answer to the unknown, found in scratch: yes. `places.resolve` already walks `steps/unlock-the-door/checks` to the step, holding the key `checks`; what refused it was the addition's own test that the place's holder is the artifact itself. Two things are new: which collections a type declares where a place stands, read through each item type on the way; and naming the items inside items, which nothing did, so an item added there had no name to give back.

**Files:**
- Modify: `tests/test_add_an_item_to_a_collection.py` (the scenario's steps)
- Modify: `src/kb/edits.py` (`_append`, new `_collections_at`, new `_named`; `_create` and `_revise` name through `_named`)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `places.resolve(content, locator) -> Spot(holder, key, collection)`; `composition.declared(schema, corpus) -> {"properties", "parts", "summary"}`; `names.items(declared, content, keep_named)`.
- Produces: an Append's `Change.path` is `"/".join((*locator.place, item_id))`. `edits._named(draft, declared, node, keep_named)` names items at every depth; `edits._collections_at(draft, locator) -> dict` (both private).

- [ ] **Step 1: Save the failing ids, and write the steps**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
wc -l < /tmp/failing-before
```

Expected: `40`.

Append at the end of `tests/test_add_an_item_to_a_collection.py`:

```python
@given("the steps of the process each carry a collection of checks of their own", target_fixture="before")
def _steps_carry_checks(client):
    checked = copy.deepcopy(PROCESS_TYPE["schema"])
    checked["parts"]["steps"]["items"]["parts"] = {
        "checks": {"items": {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]}},
    }
    assert not write(client, "schema/process", {"version": 2, "schema": checked}, message="Steps carry checks").faults
    steps = [{**STEPS[0], "checks": [{"title": "Key turns"}]}, {**STEPS[1], "checks": [{"title": "Every bulb lit"}]}]
    assert not write(client, PROCESS, {"steps": steps}, message="Give each step its checks").faults
    return loads(read(client, PROCESS, whole=True).content)


@when("the client adds a check to the first step of the process, saying which role and why", target_fixture="added")
def _add_a_check_to_the_first_step(client):
    return _added(client, {"title": "Door stays open"}, collection="steps/unlock-the-door/checks", message="Prop the door")


@then("the client is given the new check's name and the artifact's new version")
def _given_the_checks_name_and_version(client, added):
    assert (added["response"].id, added["response"].revision) == ("door-stays-open", 3)
    entry = journal(client, PROCESS).entries[-1]
    assert (entry.op, entry.path, entry.revision) == ("append", "steps/unlock-the-door/checks/door-stays-open", 3)


@then("the rest of the process is unchanged")
def _rest_unchanged(client, before):
    after = loads(read(client, PROCESS, whole=True).content)
    added = after["steps"][0]["checks"].pop()
    assert added == {"title": "Door stays open", "id": "door-stays-open"}
    assert after == before
```

The version is 3: the Background's create is 1 and the Given's write is 2; writing the type does not move the process on.

- [ ] **Step 2: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-77 2>&1 | grep -E "^E  |passed|failed" | head -3
```

Expected: `1 failed`, the When's `_added` failing on the fault `path: "steps/unlock-the-door/checks"`, `rule: "collection"`, `... is not one`.

- [ ] **Step 3: An addition lands in the collection the type declares where the place stands**

In `src/kb/edits.py`, replace:

```python
    spot = places.resolve(content, locator)
    collections = composition.declared(draft.schema(locator.id.kind)["schema"], draft)["parts"]
    if spot.holder is not content or spot.key not in collections:
        raise Refused([refusals.not_a_collection(locator)])
    item = addition.item.tree
    content.setdefault(spot.key, []).append(item)
    _revise(draft, locator.id, current, content)
    return Change("append", locator.id, f"{spot.key}/{item['id']}", item["id"])
```

with:

```python
    spot = places.resolve(content, locator)
    if spot.key not in _collections_at(draft, locator):
        raise Refused([refusals.not_a_collection(locator)])
    item = addition.item.tree
    spot.holder.setdefault(spot.key, []).append(item)
    _revise(draft, locator.id, current, content)
    return Change("append", locator.id, "/".join((*locator.place, item["id"])), item["id"])


def _collections_at(draft: Draft, locator: values.Locator) -> dict:
    """The collections the type declares where the locator's last step stands: the artifact's own, or those of the
    item type of each collection the place passes through on the way."""
    declared = composition.declared(draft.schema(locator.id.kind)["schema"], draft)
    for collection in locator.place[:-1:2]:
        part = declared["parts"].get(collection)
        if part is None:
            return {}
        declared = composition.declared(part.get("items", {}), draft)
    return declared["parts"]
```

A place into a section, or into a field, finds no collection there and is refused as before; a place naming an item (an even number of steps) ends at an index, which no collection is called.

- [ ] **Step 4: Items are named at every depth**

In `src/kb/edits.py`, in `_create`, replace `    names.items(declared, content, keep_named=False)` with `    _named(draft, declared, content, keep_named=False)`; in `_revise`, replace `    names.items(declared, content, keep_named=True)` with `    _named(draft, declared, content, keep_named=True)`. Then insert, just above `def _fits(`:

```python
def _named(draft: Draft, declared: dict, node: dict, keep_named: bool) -> None:
    """Every item of every collection the node holds given its name, and the items of the collections inside each
    item in turn, at every depth."""
    names.items(declared, node, keep_named)
    for collection, part in declared["parts"].items():
        inner = composition.declared(part.get("items", {}), draft)
        for item in node.get(collection, []):
            _named(draft, inner, item, keep_named)


```

It runs after the content fits its type, so every item it meets is a mapping.

- [ ] **Step 5: Run it green**

```bash
.venv/bin/python -m pytest -q -m slice-77 2>&1 | tail -1
.venv/bin/python -m pytest -q 2>&1 | tail -1
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before -
wc -l src/kb/edits.py
```

Expected: `1 passed, 195 deselected`; `39 failed, 157 passed`; one line, `< FAILED tests/test_add_an_item_to_a_collection.py::test_the_client_adds_an_item_to_a_collection_inside_an_item`; `193`.

- [ ] **Step 6: Checkpoint and commit**

Append the slice 77 checkpoint to the slice plan's log, with the answer to its unknown (the place already resolved; the collections declared where it stands are read through each item type on the way, and items are named at every depth), and Review Focus 1 as a `QUESTION FOR THE SPEC` line with its reproduction. Set slice 77's Status to `green`.

```bash
git add src/kb tests docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 77: A collection inside an item can be added to

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Slice 77.1, where a link lands is asked of the one resolution of a place

**Slice plan entry:** Slice 77.1, enabling. Unknown: can where a link lands be asked of the one resolution of a place while a link still lands only on an item named by its id? Check: the suite's failing ids unchanged; `grep -nE "_holds_part|item\.get\(\"id\"\) ==" src/kb/validation.py` → no lines (3 before); the probe below gives what it gave before.

The answer, found in scratch: yes. The walk inside `places.resolve` becomes `_walk`, which answers `None` where `resolve` refused; `resolve` refuses on it, and `holds_part` narrows it to what a link may land on.

**Files:**
- Modify: `src/kb/places.py` (`resolve` split; new `holds_part`, `_walk`)
- Modify: `src/kb/validation.py` (`_holds_part` gone; `_lands` asks `places`)
- Modify: `CLAUDE.md` (the `places.py` row), `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: Task 1's `places.resolve`.
- Produces: `places.holds_part(content: dict, place: tuple) -> bool`. `places.resolve(content, locator) -> Spot` answers as before.

- [ ] **Step 1: Save the failing ids, and run the probe before**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
grep -nE "_holds_part|item\.get\(\"id\"\) ==" src/kb/validation.py | wc -l
```

Expected: `3`.

Save as `/tmp/probe-77-1.py`:

```python
import sys, tempfile
from pathlib import Path
sys.path.insert(0, "tests")
from calls import CLIENT, DECISION_TYPE, define, request
from kb import client as kb_client
from kb.contract import kb_pb2

root = Path(tempfile.mkdtemp())
client = kb_client.connect(root)
client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
define(client, DECISION_TYPE)
define(client, {"title": "Note", "version": 1, "schema": {"type": "object", "properties": {
    "about": {"type": "string", "ref": {"targets": ["decision"], "parts": True, "on_delete": "refuse"}},
}}})
request(client, "decision", "D one", {
    "sections": [{"title": "Purpose", "body": "p\n"}, {"title": "Rationale", "body": "r\n"}],
    "options": [{"title": "Weekly"}],
})
for n, target in enumerate([
    "decision/d-one#options/x", "decision/d-one#sections/purpose", "decision/d-one#id/x", "decision/d-one#options",
    "decision/d-one#options/weekly/title", "decision/d-one#options/weekly",
]):
    response = request(client, "note", f"N {n}", {"about": target})
    print(target, "->", [(fault.path, fault.rule) for fault in response.faults] or "accepted")
```

```bash
.venv/bin/python /tmp/probe-77-1.py 2>/dev/null | tee /tmp/probe-77-1-before
```

Expected: the first five `-> [('about', 'ref')]`, the last `-> accepted`.

- [ ] **Step 2: One walk of a place**

In `src/kb/places.py`, replace the whole of `resolve`:

```python
def resolve(content: dict, locator: Locator) -> Spot:
    """Where the locator's place, which is not empty, stands in an artifact's content. Raises Refused for a place that
    begins at what only the store settles, or that names nothing the content holds."""
    steps = list(locator.place)
    if steps[0] in canonical.IDENTITY:
        raise Refused([refusals.settled_place(locator)])
    holder = content
    while len(steps) > 1:
        collection, name = steps.pop(0), steps.pop(0)
        items = holder.get(collection)
        index = _index(collection, items, name)
        if index is None:
            raise Refused([refusals.nothing_at(locator)])
        if not steps:
            return Spot(items, index, collection)
        holder = items[index]
    return Spot(holder, steps[0])
```

with:

```python
def resolve(content: dict, locator: Locator) -> Spot:
    """Where the locator's place, which is not empty, stands in an artifact's content. Raises Refused for a place that
    begins at what only the store settles, or that names nothing the content holds."""
    if locator.place[0] in canonical.IDENTITY:
        raise Refused([refusals.settled_place(locator)])
    spot = _walk(content, locator.place)
    if spot is None:
        raise Refused([refusals.nothing_at(locator)])
    return spot


def holds_part(content: dict, place: tuple) -> bool:
    """Whether a place names a part the content holds: an item of a collection, named by its id, at any depth; never
    a section, and never a field of an item. What a link inside an artifact may land on."""
    return not len(place) % 2 and "sections" not in place[::2] and _walk(content, place) is not None


def _walk(content: dict, place: tuple) -> Spot | None:
    """Where a place stands in the content, step by step, or None when a step names nothing there."""
    steps = list(place)
    holder = content
    while len(steps) > 1:
        collection, name = steps.pop(0), steps.pop(0)
        items = holder.get(collection)
        index = _index(collection, items, name)
        if index is None:
            return None
        if not steps:
            return Spot(items, index, collection)
        holder = items[index]
    return Spot(holder, steps[0])
```

A place beginning at `id` finds a text where a collection would be, so `_walk` answers `None` and no link lands there, as before.

- [ ] **Step 3: The check asks it**

In `src/kb/validation.py`, replace `from kb import links, values` with `from kb import links, places, values`; in `_lands`, replace `    return not link.place or _holds_part(corpus.artifact(link.id), link.place)` with `    return not link.place or places.holds_part(corpus.artifact(link.id), link.place)`; and delete the function `_holds_part`, from the line `def _holds_part(node: dict, place: tuple) -> bool:` up to, not including, the line `def _sections(`, keeping two blank lines between `_lands` and `_sections`.

- [ ] **Step 4: The module map**

In `CLAUDE.md`, replace the row

```markdown
| `places.py` | resolving a place inside an artifact to where its node stands, or the refusal saying why nothing does | I/O, what an operation does there |
```

with:

```markdown
| `places.py` | resolving a place inside an artifact to where its node stands, or the refusal saying why nothing does; whether a link's place names a part | I/O, what an operation does there |
```

- [ ] **Step 5: The check**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before -
.venv/bin/python -m pytest -q 2>&1 | tail -1
.venv/bin/python /tmp/probe-77-1.py 2>/dev/null | diff /tmp/probe-77-1-before -
grep -nE "_holds_part|item\.get\(\"id\"\) ==" src/kb/validation.py
wc -l src/kb/validation.py src/kb/places.py
```

Expected: no diff; `39 failed, 157 passed`; no diff; no lines; `139` and `65`.

- [ ] **Step 6: Checkpoint and commit**

Append the slice 77.1 checkpoint (the check's results, before and after, and the answer to its unknown). Set slice 77.1's Status to `green`.

```bash
git add src/kb CLAUDE.md docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 77.1: Where a link lands is asked of the one resolution of a place

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Slice 78, a bare date is the text written

**Slice plan entry:** Slice 78, capability. Unknown: can the one reader take a bare date as text without changing how any other value is read? Scenario:

- kb / create-an-artifact / A field written as a bare date is the text that was written

The answer, found in scratch: yes. ruamel.yaml's safe loader, even at YAML 1.2, resolves `2026-09-24` to a timestamp and constructs a `datetime.date`. A constructor of kb's own builds that tag as the string written; the resolver and the dumper are untouched, so a string that looks like a date is still written quoted.

**Files:**
- Modify: `tests/test_create_an_artifact.py` (the scenario's steps)
- Modify: `src/kb/canonical.py` (new `_Constructor`, used by `_yaml`)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: nothing new.
- Produces: `canonical.load` and everything reading through it give text for a value written as a date or a time. `canonical.dump` is unchanged.

- [ ] **Step 1: Save the failing ids, and write the steps**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
```

The decision type has no field of its own declared as text, but its options' `body` is one. The content is sent as text, since `content.dumps` would quote the date. Append at the end of `tests/test_create_an_artifact.py`:

```python
@when('the client creates a decision carrying a field written "2026-09-24", saying which role and why', target_fixture="created")
def _create_with_a_bare_date(client):
    text = content.dumps({"sections": SECTIONS}) + "options:\n  - title: Revisit\n    body: 2026-09-24\n"
    return client.Create(kb_pb2.CreateRequest(
        type="decision", title="Review prices again", content=text, actor=CLIENT, message="Say when to revisit",
    ))


@then("that field reads back as the text that was written, not as a date")
def _field_is_text_not_a_date(root, client, created):
    assert not created.faults, created.faults
    assert content.loads(read(client, created.id, whole=True).content)["options"][0]["body"] == "2026-09-24"
    on_disk = canonical.load((root / "kb" / f"{created.id}.yaml").read_text())
    assert on_disk["options"][0]["body"] == "2026-09-24"
```

- [ ] **Step 2: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-78 2>&1 | grep -E "^E  |passed|failed" | head -5
```

Expected: `1 failed`, on the fault `path: "options/0/body"`, `rule: "type"`, `message: "datetime.date(2026, 9, 24) is not of type 'string'"`.

- [ ] **Step 3: The one reader reads a date as the text written**

In `src/kb/canonical.py`, replace `from ruamel.yaml import YAML, events, nodes, tokens` with:

```python
from ruamel.yaml import YAML, events, nodes, tokens
from ruamel.yaml.constructor import SafeConstructor
```

insert just above `def _yaml() -> YAML:`:

```python
class _Constructor(SafeConstructor):
    """A value is read as written: one that looks like a date or a time is the text it was written as."""


_Constructor.add_constructor("tag:yaml.org,2002:timestamp", SafeConstructor.construct_yaml_str)


```

and in `_yaml`, replace `    yaml.Representer = _Representer` with:

```python
    yaml.Representer = _Representer
    yaml.Constructor = _Constructor
```

- [ ] **Step 4: Run it green**

```bash
.venv/bin/python -m pytest -q -m "slice-78 or slice-1.5" 2>&1 | tail -1
.venv/bin/python -m pytest -q 2>&1 | tail -1
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before -
.venv/bin/python -c "from kb import canonical; print(canonical.load('d: 2026-09-24\nt: 2026-09-24T09:00:00Z\n'), repr(canonical.dump({'d': '2026-09-24'})))"
wc -l src/kb/canonical.py
```

Expected: `2 passed, 194 deselected`; `38 failed, 158 passed`; one line, `< FAILED tests/test_create_an_artifact.py::test_a_field_written_as_a_bare_date_is_the_text_that_was_written`; `{'d': '2026-09-24', 't': '2026-09-24T09:00:00Z'} "d: '2026-09-24'\n"`; `205`.

- [ ] **Step 5: Checkpoint and commit**

Append the slice 78 checkpoint, with the answer to its unknown (the loader's timestamp tag built as text; the dumper untouched, so no stored byte changes). Set slice 78's Status to `green`.

```bash
git add src/kb tests docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 78: A bare date is the text written

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Slice 78.1, where a file lies is the store's alone

**Slice plan entry:** Slice 78.1, enabling. Unknown: none. Check: the suite's failing ids unchanged; `grep -nE '\.yaml|glob\(' src/kb/*.py | grep -v "^src/kb/store.py\|^src/kb/journal.py\|^src/kb/canonical.py\|^src/kb/contract"` → no lines (2 before, in `values.py` and `write.py`).

**Files:**
- Modify: `src/kb/values.py` (docstring; `path` gone), `src/kb/store.py` (`Store.path`, `Store.start`), `src/kb/write.py` (`start`)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `store.MARKER` (`Path("kb") / "store.yaml"`).
- Produces: `Store.path(artifact_id) -> Path`, made in `store.py`; `Store.start() -> Path`, where the marker was written. `values.path` no longer exists.

- [ ] **Step 1: Save the failing ids**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
grep -nE '\.yaml|glob\(' src/kb/*.py | grep -v "^src/kb/store.py\|^src/kb/journal.py\|^src/kb/canonical.py\|^src/kb/contract"
```

Expected: two lines, `src/kb/write.py:50` and `src/kb/values.py:209`.

- [ ] **Step 2: The path leaves `values.py`**

In `src/kb/values.py`, replace the module docstring's second paragraph:

```python
Storage takes only these values, never a string that came from a request, and `path` is the one place a file
path is made from a name.
```

with:

```python
Storage takes only these values, never a string that came from a request.
```

and delete the function `path`, from the line `def path(store_dir: Path, artifact_id: ArtifactId) -> Path:` up to, not including, `def _not_a_plain_name(`, keeping two blank lines between `root` and `_not_a_plain_name`. `Path` is still imported: `Root` uses it.

- [ ] **Step 3: The store makes its own paths, and says where its marker is**

In `src/kb/store.py`, replace:

```python
    def path(self, artifact_id: ArtifactId) -> Path:
        return values.path(self.dir, artifact_id)

    def start(self) -> None:
        """Make the store directory, its git repository, and its marker file."""
        self.dir.mkdir(parents=True)
        _git("init", "-q", "-b", "main", str(self.dir))
        (self.dir / "store.yaml").write_text(canonical.dump({"contract": CONTRACT_VERSION}), encoding="utf-8")
```

with:

```python
    def path(self, artifact_id: ArtifactId) -> Path:
        """The one place a file path is made from a name: <store>/<kind>/<name>.yaml."""
        if not isinstance(artifact_id, ArtifactId):
            raise TypeError(f"a path is made only from a checked name, not {artifact_id!r}")
        return self.dir / artifact_id.kind.name / f"{artifact_id.slug}.yaml"

    def start(self) -> Path:
        """Make the store directory, its git repository, and its marker file; where the marker is."""
        self.dir.mkdir(parents=True)
        _git("init", "-q", "-b", "main", str(self.dir))
        marker = self.root / MARKER
        marker.write_text(canonical.dump({"contract": CONTRACT_VERSION}), encoding="utf-8")
        return marker
```

In `src/kb/write.py`, in `start`, replace `    store.start()` with `    marker = store.start()`, and `    store.commit([store.dir / "store.yaml", path, entry], signed)` with `    store.commit([marker, path, entry], signed)`.

- [ ] **Step 4: The check**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before -
.venv/bin/python -m pytest -q 2>&1 | tail -1
grep -nE '\.yaml|glob\(' src/kb/*.py | grep -v "^src/kb/store.py\|^src/kb/journal.py\|^src/kb/canonical.py\|^src/kb/contract"
grep -rn "values.path" src/kb tests
wc -l src/kb/values.py src/kb/store.py src/kb/write.py
```

Expected: no diff; `38 failed, 158 passed`; no lines; no lines; `208`, `202` and `121`.

- [ ] **Step 5: Checkpoint and commit**

Append the slice 78.1 checkpoint (the check's results, before and after). Set slice 78.1's Status to `green`.

```bash
git add src/kb docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 78.1: Where a file lies is the store's alone

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Slice 78.2, loading gives an artifact or the damage, whatever the bytes

**Slice plan entry:** Slice 78.2, enabling. Unknown: can loading hold every stored file to being an artifact, with the fault other damage already gives, without the draft's own artifacts meeting that check? Check: the suite's failing ids unchanged; the probe below, where every line raised through the client at `9cb5f33`, answers with the one `unreadable` fault naming the file, from Validate as a violation and from Read as a refusal.

The answer, found in scratch: yes. `Draft.load` gives the draft's own artifacts without calling `Store.load`, and those are always whole, since `edits` builds them with every identity key; so only what is read from disk meets the check.

**Files:**
- Modify: `src/kb/canonical.py` (new `decoded`), `src/kb/store.py` (`Store.load`; new `SETTLED`, `_unsettled`)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: Task 4's `Store.path`; `canonical.entries(text) -> dict`; `refusals.unreadable(artifact_id, file, problem)`.
- Produces: `canonical.decoded(data: bytes) -> str`, raising `canonical.NotCanonical("it is not text written in UTF-8")`. `Store.load` never raises for what a file holds; it gives `Damaged` for bytes that are not UTF-8 and for a set of named entries lacking what `store.SETTLED` names. Task 6 reads the history through `canonical.decoded` too.

- [ ] **Step 1: Save the failing ids, and run the probe before**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
```

Save as `/tmp/probe-78-2.py`:

```python
import sys, tempfile
from pathlib import Path
sys.path.insert(0, "tests")
from calls import CLIENT, DECISION_TYPE, define, read, request
from kb import client as kb_client
from kb.contract import kb_pb2

SECTIONS = [{"title": "Purpose", "body": "p\n"}, {"title": "Rationale", "body": "r\n"}]


def run(label, call):
    try:
        response = call()
        found = list(response.faults) + list(getattr(response, "violations", []))
        print(label, "->", [(fault.artifact, fault.path, fault.rule, fault.message) for fault in found] or "answered")
    except Exception as error:
        print(label, "-> RAISES", type(error).__name__, str(error)[:60])


for damage in (
    b"title: D one\n",
    bytes.fromhex("fffe00626164"),
    b"id: decision/d-one\ntype: decision\nschema_version: one\nrevision: 1\ntitle: D one\n",
):
    root = Path(tempfile.mkdtemp())
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, DECISION_TYPE)
    request(client, "decision", "D one", {"sections": SECTIONS})
    (root / "kb" / "decision" / "d-one.yaml").write_bytes(damage)
    print(damage[:14])
    run("  Validate", lambda: client.Validate(kb_pb2.ValidateRequest()))
    run("  Read", lambda: read(client, "decision/d-one"))
```

```bash
.venv/bin/python /tmp/probe-78-2.py 2>/dev/null
```

Expected, each a crash through the client: `KeyError 'schema_version'` and `KeyError 'id'`; `UnicodeDecodeError` twice; `TypeError '<' not supported ...` and `TypeError 'str' object cannot be interpreted as an integer`.

- [ ] **Step 2: Bytes become text in one place**

In `src/kb/canonical.py`, insert just above `def entries(text: str) -> dict:`:

```python
def decoded(data: bytes) -> str:
    """A stored file's bytes as the text they are written as, UTF-8. Bytes that are not raise NotCanonical."""
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        raise NotCanonical("it is not text written in UTF-8") from None


```

- [ ] **Step 3: Loading holds a file to being an artifact**

In `src/kb/store.py`, replace the whole of `Store.load`:

```python
    def load(self, artifact_id: ArtifactId) -> dict | Damaged:
        """The artifact as stored, or, when its file cannot be read, the fault naming the file. Never raises for what
        a file holds."""
        path = self.path(artifact_id)
        try:
            return canonical.entries(path.read_text(encoding="utf-8"))
        except canonical.NotCanonical as error:
            return Damaged(refusals.unreadable(artifact_id, path.relative_to(self.dir), str(error)))
```

with:

```python
    def load(self, artifact_id: ArtifactId) -> dict | Damaged:
        """The artifact as stored, or, when its file cannot be read as one, the fault naming the file. Never raises
        for what a file holds."""
        path = self.path(artifact_id)
        try:
            loaded = canonical.entries(canonical.decoded(path.read_bytes()))
        except canonical.NotCanonical as error:
            problem = str(error)
        else:
            problem = _unsettled(loaded)
        if problem:
            return Damaged(refusals.unreadable(artifact_id, path.relative_to(self.dir), problem))
        return loaded
```

and insert just above `class Draft:`:

```python
SETTLED = {"id": str, "type": str, "schema_version": int, "revision": int, "title": str}


def _unsettled(loaded: dict) -> str:
    """What a stored artifact lacks of what the store settles for every artifact, said as the problem with its file;
    empty when it lacks nothing."""
    lacking = [
        key for key, kind in SETTLED.items()
        if not isinstance(loaded.get(key), kind) or isinstance(loaded.get(key), bool)
    ]
    if not lacking:
        return ""
    return f"it does not carry what the store settles for every artifact: {', '.join(lacking)}"


```

`bool` is refused beside `int` because `true` is an `int` to Python.

- [ ] **Step 4: The check**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before -
.venv/bin/python -m pytest -q 2>&1 | tail -1
.venv/bin/python /tmp/probe-78-2.py 2>/dev/null
grep -n "UnicodeDecodeError" src/kb/*.py
grep -nE "except (Exception|BaseException)|except:" src/kb/*.py
wc -l src/kb/canonical.py src/kb/store.py
```

Expected: no diff; `38 failed, 158 passed`; for each file, Validate and Read both give the one fault `('decision/d-one', '', 'unreadable', 'the stored file decision/d-one.yaml cannot be read: ...')`, the problem being `it does not carry what the store settles for every artifact: id, type, schema_version, revision`, then `it is not text written in UTF-8`, then `it does not carry what the store settles for every artifact: schema_version`; one line, in `canonical.py`; no lines; `213` and `222`.

- [ ] **Step 5: Checkpoint and commit**

Append the slice 78.2 checkpoint (the check's results, before and after, and the answer to its unknown), and Review Focus 5 as a `QUESTION FOR THE SPEC` line with its reproduction. Say in the checkpoint that the question logged on 2026-09-26 about bytes that are not UTF-8 is answered by CLAUDE.md's rule 3 (slice 76's log), the row it asked for still welcome. Set slice 78.2's Status to `green`.

```bash
git add src/kb docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 78.2: Loading gives an artifact or the damage, whatever the bytes

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Slice 79, a type or an entry of the history that cannot be read is refused

**Slice plan entry:** Slice 79, capability. Unknown: can the history's files be loaded as a value the way slice 63 loads the store's? Scenarios:

- kb / a-file-the-store-cannot-read / Creating an artifact of a kind whose type cannot be read is refused
- kb / a-file-the-store-cannot-read / An entry of the history that cannot be read is refused in the same way

The answer, found in scratch: yes. `journal.entries` reads each file through `canonical.decoded` and `canonical.entries`, as `Store.load` does, and gives `Damaged` for the first that cannot be read; `query.entries` reads it through `store.readable`, the one place damage becomes a refusal. The create row passes as soon as its steps exist: a create reads its kind's type through `Draft.schema`, which refuses a damaged file since slice 63.

**Files:**
- Modify: `tests/calls.py` (`MANGLED` moves here), `tests/conftest.py` (imports it), `tests/test_a_file_the_store_cannot_read.py` (two calls, two Givens, two Thens)
- Modify: `src/kb/refusals.py` (`unreadable` takes a name), `src/kb/store.py` (`load` passes one; `readable`'s docstring), `src/kb/journal.py` (`entries`), `src/kb/query.py` (`entries`)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: Task 5's `canonical.decoded`; `store.Damaged`, `store.readable`.
- Produces: `refusals.unreadable(named: str, file, problem: str) -> kb_pb2.Fault`; `journal.entries(store_dir: Path) -> list[dict] | Damaged`. In the tests, `calls.MANGLED`.

- [ ] **Step 1: Save the failing ids, and write the steps**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
```

The mangled text two modules now write moves to `tests/calls.py`. In `tests/calls.py`, replace `CLIENT = kb_pb2.Actor(role="client")` with:

```python
CLIENT = kb_pb2.Actor(role="client")

MANGLED = "title: [a bracket opened by hand and never closed\n"
```

In `tests/conftest.py`, delete the line `MANGLED = "title: [a bracket opened by hand and never closed\n"` with the two blank lines after it, and replace `from calls import CLIENT, DECISION_TYPE, create, define, everything_under` with `from calls import CLIENT, DECISION_TYPE, MANGLED, create, define, everything_under`.

In `tests/test_a_file_the_store_cannot_read.py`, replace the import:

```python
from calls import (
    CLIENT, DECISION_TYPE, PROCESS_TYPE, TAG_TYPE, append, create, define, everything_under, listing, refs, remove,
    search, write,
)
```

with:

```python
from calls import (
    CLIENT, DECISION_TYPE, MANGLED, PROCESS_TYPE, TAG_TYPE, append, create, define, everything_under, journal,
    listing, refs, remove, request, search, write,
)
```

The two Whens are calls like slice 63's, so they join its table. Replace:

```python
    "follows the links out of the decision":
        lambda client: refs(client, DECISION, 1),
}
```

with:

```python
    "follows the links out of the decision":
        lambda client: refs(client, DECISION, 1),
    "creates a decision with a title and both required sections, saying which role and why":
        lambda client: request(client, "decision", "Close early on Sundays", {"sections": SECTIONS}),
    "reads the journal":
        lambda client: journal(client),
}
```

Append at the end of the file:

```python
@given("someone edited the decision type's file by hand and left it in a shape the store cannot read")
def _decision_type_mangled_by_hand(root):
    (root / "kb" / "schema" / "decision.yaml").write_text(MANGLED)


@given(
    "someone edited one of the store's history entries by hand and left it in a shape the store cannot read",
    target_fixture="entry",
)
def _history_entry_mangled_by_hand(root):
    """The newest entry of the Background's history left unreadable; where it is, from the store's own directory."""
    entry = sorted((root / "kb" / "journal").rglob("*.yaml"))[-1]
    entry.write_text(MANGLED)
    return entry.relative_to(root / "kb")


@then("the create is rejected because that file cannot be read, and the file is named")
def _create_rejected_as_unreadable(answered):
    assert [(fault.artifact, fault.rule) for fault in answered.faults] == [("schema/decision", "unreadable")]
    assert "schema/decision.yaml cannot be read" in answered.faults[0].message
    assert (answered.id, answered.revision) == ("", 0)


@then("the read is rejected because that file cannot be read, and the file is named")
def _read_rejected_as_unreadable(answered, entry):
    assert [(fault.artifact, fault.rule) for fault in answered.faults] == [("", "unreadable")]
    assert f"{entry} cannot be read" in answered.faults[0].message
    assert list(answered.entries) == []
```

- [ ] **Step 2: Run it red**

```bash
.venv/bin/python -m pytest -q -m "slice-79 or slice-63 or slice-74" 2>&1 | grep -E "^E  |passed|failed" | head -3
```

Expected: `1 failed, 15 passed`, the journal row failing with `kb.canonical.NotCanonical: it is not YAML that can be read: ...`. The create row passes as soon as its steps exist.

- [ ] **Step 3: The history is loaded as a value**

In `src/kb/refusals.py`, replace:

```python
def unreadable(artifact_id: ArtifactId, file, problem: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(artifact_id), rule="unreadable", message=f"the stored file {file} cannot be read: {problem}",
    )
```

with:

```python
def unreadable(named: str, file, problem: str) -> kb_pb2.Fault:
    """A stored file that cannot be read: an artifact's, named, or an entry of the history, which names none."""
    return kb_pb2.Fault(
        artifact=named, rule="unreadable", message=f"the stored file {file} cannot be read: {problem}",
    )
```

In `src/kb/store.py`, in `Store.load`, replace `            return Damaged(refusals.unreadable(artifact_id, path.relative_to(self.dir), problem))` with `            return Damaged(refusals.unreadable(str(artifact_id), path.relative_to(self.dir), problem))`; and replace:

```python
def readable(loaded: dict | Damaged) -> dict:
    """The artifact loaded; a file that cannot be read refuses the call with the fault naming it. The one place a
    damaged file becomes a refusal."""
```

with:

```python
def readable(loaded):
    """What was loaded, an artifact or the journal's entries; a file that cannot be read refuses the call with the
    fault naming it. The one place a damaged file becomes a refusal."""
```

In `src/kb/journal.py`, replace `from kb import canonical` and `from kb.values import Signed` (two lines) with:

```python
from kb import canonical, refusals
from kb.store import Damaged
from kb.values import Signed
```

and replace:

```python
def entries(store_dir: Path) -> list[dict]:
    """Every entry in the journal, oldest first: by the time in its id, then by its place in its set."""
    found = [canonical.load(path.read_text(encoding="utf-8")) for path in (store_dir / "journal").rglob("*.yaml")]
    return sorted(found, key=_order)
```

with:

```python
def entries(store_dir: Path) -> list[dict] | Damaged:
    """Every entry in the journal, oldest first: by the time in its id, then by its place in its set. When an entry's
    file cannot be read, the fault naming the first such file in place of them all. Never raises for what a file
    holds."""
    found = []
    for path in sorted((store_dir / "journal").rglob("*.yaml")):
        try:
            found.append(canonical.entries(canonical.decoded(path.read_bytes())))
        except canonical.NotCanonical as error:
            return Damaged(refusals.unreadable("", path.relative_to(store_dir), str(error)))
    return sorted(found, key=_order)
```

`store.py` imports neither `journal` nor `write`, so `journal.py` importing `store` makes no cycle.

In `src/kb/query.py`, replace `from kb.store import Store` with `from kb.store import Store, readable`, and in `entries` replace `        _entry(entry) for entry in journal.entries(store.dir)` with `        _entry(entry) for entry in readable(journal.entries(store.dir))`.

- [ ] **Step 4: Run it green**

```bash
.venv/bin/python -m pytest -q -m "slice-79 or slice-63 or slice-74" 2>&1 | tail -1
.venv/bin/python -m pytest -q 2>&1 | tail -1
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before -
grep -rn "MANGLED = " tests
wc -l src/kb/journal.py src/kb/query.py src/kb/refusals.py src/kb/store.py
```

Expected: `16 passed, 180 deselected`; `36 failed, 160 passed`; two lines, `< ... test_an_entry_of_the_history_that_cannot_be_read_is_refused_in_the_same_way` and `< ... test_creating_an_artifact_of_a_kind_whose_type_cannot_be_read_is_refused`; one line, in `tests/calls.py`; `87`, `130`, `110` and `222`.

- [ ] **Step 5: Checkpoint and commit**

Append the slice 79 checkpoint, with the answer to its unknown (the history's files read as the store's are, giving `Damaged`; the create row passed on its steps alone), and Review Focus 4 as a `QUESTION FOR THE SPEC` line with its reproduction. Set slice 79's Status to `green`.

```bash
git add src/kb tests docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 79: A type or an entry of the history that cannot be read is refused

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Slice 79.1, a damaged type met through another type's reference is the damaged file's fault

**Slice plan entry:** Slice 79.1, enabling. Unknown: can a refusal raised while the JSON Schema library retrieves a type come out of it as itself, catching nothing broader than the library's own wrapping? Check: the suite's failing ids unchanged; the probe below answers with the one fault `schema/tool` `unreadable`, nothing written (it raised `_WrappedReferencingError` at `9cb5f33`); no module catches a broad exception.

The answer, found in scratch: yes. jsonschema raises its `_WrappedReferencingError`, a subclass of `referencing.exceptions.Unresolvable`, whose `__cause__` chain runs `Unresolvable`, `Unretrievable`, then the `Refused` that `composition.type_schema` raised through `store.readable`.

**Files:**
- Modify: `src/kb/validation.py` (`validate` reads JSON Schema's errors through new `_errors`; new `_refusal_behind`)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `validation.registry(corpus)`; `values.Refused`.
- Produces: `validation.validate` raises the `Refused` a type gave while being retrieved; its signature and answers are otherwise unchanged.

- [ ] **Step 1: Save the failing ids, and run the probe before**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
```

Save as `/tmp/probe-79-1.py`:

```python
import sys, tempfile
from pathlib import Path
sys.path.insert(0, "tests")
from calls import CLIENT, define, everything_under, request
from kb import client as kb_client
from kb.contract import kb_pb2

root = Path(tempfile.mkdtemp())
client = kb_client.connect(root)
client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
define(client, {"title": "Tool", "version": 1, "schema": {"type": "object", "$defs": {"binding": {"type": "object"}}}})
define(client, {"title": "Tool use", "version": 1, "schema": {
    "type": "object", "properties": {"b": {"$ref": "kb:schema/tool#/$defs/binding"}},
}})
(root / "kb" / "schema" / "tool.yaml").write_text("title: [\n")
before = everything_under(root)
try:
    response = request(client, "tool-use", "U", {"b": {}})
    print([(fault.artifact, fault.path, fault.rule) for fault in response.faults],
          "unchanged" if everything_under(root) == before else "WRITTEN")
except Exception as error:
    print("RAISES", type(error).__name__, str(error)[:80])
```

```bash
.venv/bin/python /tmp/probe-79-1.py 2>/dev/null
```

Expected: `RAISES _WrappedReferencingError Unresolvable: kb:schema/tool#/$defs/binding`.

- [ ] **Step 2: The refusal behind the library's failure**

In `src/kb/validation.py`, replace `from referencing import Registry` with:

```python
from referencing import Registry
from referencing.exceptions import Unresolvable
```

in `validate`, replace `    errors = list(Draft202012Validator(compose(schema, corpus), registry=registry(corpus)).iter_errors(content))` with `    errors = _errors(content, compose(schema, corpus), corpus)`; and insert just above `def _place(error) -> str:`:

```python
def _errors(content: dict, composed: dict, corpus) -> list:
    """JSON Schema's every error. A type met through a reference whose file cannot be read refuses the check with the
    fault naming that file, as meeting it directly does, rather than as the library's own failure to resolve it."""
    try:
        return list(Draft202012Validator(composed, registry=registry(corpus)).iter_errors(content))
    except Unresolvable as unresolvable:
        refusal = _refusal_behind(unresolvable)
        if refusal is None:
            raise
        raise refusal from None


def _refusal_behind(error: Exception) -> values.Refused | None:
    """The refusal a type gave while it was being retrieved, found among what caused the error; None when no refusal
    caused it."""
    cause = error.__cause__
    while cause is not None and not isinstance(cause, values.Refused):
        cause = cause.__cause__
    return cause


```

- [ ] **Step 3: The check**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before -
.venv/bin/python -m pytest -q 2>&1 | tail -1
.venv/bin/python /tmp/probe-79-1.py 2>/dev/null
grep -nE "except (Exception|BaseException)|except:" src/kb/*.py
wc -l src/kb/validation.py
```

Expected: no diff; `36 failed, 160 passed`; `[('schema/tool', '', 'unreadable')] unchanged`; no lines; `161`.

- [ ] **Step 4: Checkpoint and commit**

Append the slice 79.1 checkpoint (the check's results, before and after, and the answer to its unknown), and Review Focus 3 as a `QUESTION FOR THE SPEC` line with its reproduction. Say that batch 7's question on a damaged type met through a `$ref` is answered by rule 3 (slice 76's log). Set slice 79.1's Status to `green`.

```bash
git add src/kb docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 79.1: A damaged type met through another type's reference is the damaged file's fault

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 8: Slice 79.2, an item is taken apart only once it is known to be a set of named entries

**Slice plan entry:** Slice 79.2, enabling. Unknown: none. Check: the suite's failing ids unchanged; the probe below, where three items raised `TypeError` at `9cb5f33`, refuses each at `options/0` with rule `type`, as `just words` already was, nothing written; an item's name is asked of it only once it is known to be a mapping.

**Files:**
- Modify: `src/kb/values.py` (`item`)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `values.content(text, at_root=False) -> Content`.
- Produces: `values.item(text) -> Content`, answering as before for a mapping, and for anything else the read value with no problem, for its type to refuse. Task 9 extends it.

- [ ] **Step 1: Save the failing ids, and run the probe before**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
```

Save as `/tmp/probe-79-2.py`:

```python
import sys, tempfile
from pathlib import Path
sys.path.insert(0, "tests")
from calls import CLIENT, DECISION_TYPE, define, everything_under, request
from kb import client as kb_client
from kb.contract import kb_pb2

root = Path(tempfile.mkdtemp())
client = kb_client.connect(root)
client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
define(client, DECISION_TYPE)
request(client, "decision", "D one", {"sections": [{"title": "Purpose", "body": "p\n"}, {"title": "Rationale", "body": "r\n"}]})
for text in ("a valid idea\n", "- id\n", "just words\n", "12\n", "{id: x, title: T}\n"):
    before = everything_under(root)
    try:
        response = client.Append(kb_pb2.AppendRequest(
            locator=kb_pb2.Locator(id="decision/d-one", path="options"), content=text, actor=CLIENT, message="m",
        ))
        print(repr(text), "->", [(fault.path, fault.rule) for fault in response.faults],
              "unchanged" if everything_under(root) == before else "WRITTEN")
    except Exception as error:
        print(repr(text), "-> RAISES", type(error).__name__, str(error)[:60])
```

```bash
.venv/bin/python /tmp/probe-79-2.py 2>/dev/null
```

Expected: `'a valid idea\n' -> RAISES TypeError ...`, `'- id\n' -> RAISES TypeError ...`, `'just words\n' -> [('options/0', 'type')] unchanged`, `'12\n' -> RAISES TypeError ...`, `'{id: x, title: T}\n' -> [('id', 'identity')] unchanged`.

- [ ] **Step 2: Only a mapping is asked what it carries**

In `src/kb/values.py`, replace:

```python
def item(text: str) -> Content:
    """An item read plainly, never carrying its own name, which kb gives."""
    read = content(text, at_root=False)
    if read.problems or "id" not in read.tree:
        return read
```

with:

```python
def item(text: str) -> Content:
    """An item read plainly, never carrying its own name, which kb gives. Only a set of named entries can carry a
    name; an item of any other shape is left for its type to refuse."""
    read = content(text, at_root=False)
    if read.problems or not isinstance(read.tree, dict) or "id" not in read.tree:
        return read
```

- [ ] **Step 3: The check**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before -
.venv/bin/python -m pytest -q 2>&1 | tail -1
.venv/bin/python /tmp/probe-79-2.py 2>/dev/null
wc -l src/kb/values.py
```

Expected: no diff; `36 failed, 160 passed`; the first four `-> [('options/0', 'type')] unchanged`, the last `-> [('id', 'identity')] unchanged`; `209`.

- [ ] **Step 4: Checkpoint and commit**

Append the slice 79.2 checkpoint (the check's results, before and after). Say that batch 9's Review Focus 1 (an item holding the letters "id") is answered by rule 2 (slice 76's log), and that whether an item must be a set of named entries as it converts, with a fault of its own, is still the spec's. Set slice 79.2's Status to `green`.

```bash
git add src/kb docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 79.2: An item is taken apart only once it is known to be a set of named entries

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 9: Slice 80, an item's title becomes its name by the rule an artifact's does

**Slice plan entry:** Slice 80, capability. Unknown: can an item's title pass through the one conversion that makes an artifact's title text, where the item's title sits inside content rather than in a field of the request? Scenario:

- kb / add-an-item-to-a-collection / An item's title becomes its name by the same rules as an artifact's title (three rows)

The answer, found in scratch: yes. An artifact's title that is not text is made text by `content.text` before it crosses the contract, and refused by `values.named` when it leaves no name. An item's title sits in the item's content, so `values.item` makes it text by the same `content.text`, and refuses it with the message `values.named` gives, now one function, `_leaves_nothing`.

**Files:**
- Modify: `tests/test_add_an_item_to_a_collection.py` (the titled When answers faults and all; a When for a title that is not text; two Thens)
- Modify: `src/kb/values.py` (`named` and new `_leaves_nothing`; `item` and new `_titled`)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: Task 8's `values.item`; `content.text(value) -> str`; `names.slug`.
- Produces: `values.item(text)` gives an item whose title, when a number or a yes-or-no, is text, and refuses one that leaves no name with the problem `("title", "title", "a title must leave something to make a name from; '!!!' leaves nothing")`.

- [ ] **Step 1: Save the failing ids, and write the steps**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
```

The row `"!!!"` reads with the When slice 39 defined, which asserts the addition was accepted. It now gives the response, faults and all; slice 39's Then already checks the name it was given.

In `tests/test_add_an_item_to_a_collection.py`, replace `import copy` (the first line) with:

```python
import copy
import re
```

and replace:

```python
@when(parsers.parse('the client adds a step titled "{title}" to the process, saying which role and why'), target_fixture="added")
def _add_a_titled_step(client, title):
    return _added(client, {"title": title})
```

with:

```python
@when(parsers.parse('the client adds a step titled "{title}" to the process, saying which role and why'), target_fixture="added")
def _add_a_titled_step(client, title):
    return {"response": append(client, PROCESS, "steps", {"title": title}), "sent": {"title": title}}


TITLES = {"the number 12 rather than text": 12, "the yes-or-no true rather than text": True}


@when(
    parsers.re(f"the client adds a step titled (?P<title>{'|'.join(map(re.escape, TITLES))}) to the process, "
               "saying which role and why"),
    target_fixture="added",
)
def _add_a_step_titled_other_than_text(client, title):
    return _added(client, {"title": TITLES[title]})
```

Append at the end of the file:

```python
@then("the item is rejected because a title must leave something to make a name from")
def _rejected_for_an_empty_name(client, added):
    response = added["response"]
    assert [(fault.artifact, fault.path, fault.rule) for fault in response.faults] == [(PROCESS, "title", "title")]
    assert "leave something to make a name from" in response.faults[0].message
    assert [step["id"] for step in _steps(client)] == ["unlock-the-door", "turn-on-the-lights"]


@then(parsers.parse('the name the client is given for the new item is made from the text "{text}"'))
def _named_from_the_text(client, added, text):
    assert added["response"].id == text
    assert _steps(client)[-1] == {"id": text, "title": text}
```

- [ ] **Step 2: Run it red**

```bash
.venv/bin/python -m pytest -q -m "slice-80 or slice-39" 2>&1 | grep -E "^E  |passed|failed" | head -8
```

Expected: `3 failed, 8 passed`: the `"!!!"` row on `assert [] == [('process/op...le', 'title')]`, and the two others on the fault `path: "steps/2/title"`, `rule: "type"`, `12 is not of type 'string'` (and `True is not of type 'string'`).

- [ ] **Step 3: One rule makes a title a name**

In `src/kb/values.py`, replace `from kb.content import entries, loads` with `from kb.content import entries, loads, text as text_of` (the function `item` has a parameter called `text`). In `named`, replace:

```python
    if not names.slug(title):
        raise Refused([kb_pb2.Fault(artifact=at, path="title", rule="title",
                                    message=f"a title must leave something to make a name from; {title!r} leaves nothing")])
    return ArtifactId(kind, names.slug(title))
```

with:

```python
    if not names.slug(title):
        raise Refused([kb_pb2.Fault(artifact=at, path="title", rule="title", message=_leaves_nothing(title))])
    return ArtifactId(kind, names.slug(title))


def _leaves_nothing(title: str) -> str:
    return f"a title must leave something to make a name from; {title!r} leaves nothing"
```

Replace the whole of `item` (as Task 8 left it):

```python
def item(text: str) -> Content:
    """An item read plainly, never carrying its own name, which kb gives. Only a set of named entries can carry a
    name; an item of any other shape is left for its type to refuse."""
    read = content(text, at_root=False)
    if read.problems or not isinstance(read.tree, dict) or "id" not in read.tree:
        return read
    return Content(read.tree, (("id", "identity",
        f"content holds only what the type declares; an item's id is settled by the store, and the content carried id: {read.tree['id']!r}"),))
```

with:

```python
def item(text: str) -> Content:
    """An item read plainly, never carrying its own name, which kb gives, and with its title, which its name is made
    from, as text. Only a set of named entries can carry a name or a title; an item of any other shape is left for
    its type to refuse."""
    read = content(text, at_root=False)
    if read.problems or not isinstance(read.tree, dict):
        return read
    if "id" in read.tree:
        return Content(read.tree, (("id", "identity",
            f"content holds only what the type declares; an item's id is settled by the store, and the content carried id: {read.tree['id']!r}"),))
    return _titled(read.tree)


def _titled(tree: dict) -> Content:
    """An item whose title, when it has one, is text whatever it was written as, as an artifact's is, and leaves a
    name to be made from it."""
    if "title" not in tree or not isinstance(tree["title"], (str, int, float)):
        return Content(tree)
    title = text_of(tree["title"])
    if not names.slug(title):
        return Content(tree, (("title", "title", _leaves_nothing(title)),))
    return Content({**tree, "title": title})
```

- [ ] **Step 4: Run it green**

```bash
.venv/bin/python -m pytest -q -m "slice-80 or slice-39" 2>&1 | tail -1
.venv/bin/python -m pytest -q 2>&1 | tail -1
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before -
.venv/bin/python /tmp/probe-79-2.py 2>/dev/null
wc -l src/kb/values.py
```

Expected: `11 passed, 185 deselected`; `33 failed, 163 passed`; three lines, each `< ... test_an_items_title_becomes_its_name_by_the_same_rules_as_an_artifacts_title[...]`; Task 8's answers unchanged; `226`.

- [ ] **Step 5: Checkpoint and commit**

Append the slice 80 checkpoint, with the answer to its unknown (an item's title made text by `content.text` as it converts, and refused by the rule an artifact's is), and Review Focus 2 as a `QUESTION FOR THE SPEC` line with its reproduction. Set slice 80's Status to `green`.

```bash
git add src/kb tests docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 80: An item's title becomes its name by the rule an artifact's does

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 10: Slice 81, a check reports an artifact whose kind has no type

**Slice plan entry:** Slice 81, capability. Unknown: can a missing type be a finding of the whole-store check the way an unreadable file is, with the artifact and the kind named? Scenario:

- kb / check-the-store / An artifact of a kind the store holds no type for is reported as a violation

The answer, found in scratch: yes. The check's own reading of an artifact with its type gives back the finding that stands in for checking it, a fault, where it gave `Damaged`: the damage's fault, or `refusals.no_type` naming the artifact when the store holds no type for its kind.

**Files:**
- Modify: `tests/test_check_the_store.py` (slice 1.20's Given says what it expects reported; the new Given and Then; "everything else" reads what the Given expects)
- Modify: `src/kb/refusals.py` (`no_type` names an artifact), `src/kb/check.py` (`everything`, `_with_type`)
- Modify: `CLAUDE.md` (the `check.py` row), `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `store.Store.holds`, `store.Damaged`; `values.type_of(kind)`.
- Produces: `refusals.no_type(kind_name: str, artifact: str = "") -> kb_pb2.Fault`, rule `kind`; `check.everything(store)` reports an artifact of a kind with no type as that fault and goes on. Task 11 raises `no_type` with no artifact.

- [ ] **Step 1: Save the failing ids, and write the steps**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
```

`everything else in the store is checked and reported alongside it` is one step in this module, shared with slice 1.20, and each Given leaves different things beside the finding, so each Given says what it expects in the `before` fixture from `conftest.py`. In `tests/test_check_the_store.py`, replace, from `def _store_with_a_file_mangled_by_hand(root):` to the end of `_the_rest_checked_alongside` (the decorator above the first stays):

```python
def _store_with_a_file_mangled_by_hand(root):
    """Two decisions edited by hand: one left unreadable, one left readable but without the body of its purpose."""
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, DECISION_TYPE)
    create(client, "decision", {"title": "Price reviews happen weekly", "sections": SECTIONS})
    create(client, "decision", {"title": "Prices are reviewed monthly", "sections": SECTIONS})
    (root / "kb" / "decision" / "price-reviews-happen-weekly.yaml").write_text(MANGLED)
    monthly = root / "kb" / "decision" / "prices-are-reviewed-monthly.yaml"
    held = canonical.load(monthly.read_text())
    del held["sections"][0]["body"]
    monthly.write_text(canonical.dump(held))
    return client


@then("everything else in the store is checked and reported alongside it")
def _the_rest_checked_alongside(checked):
    assert [(fault.artifact, fault.path, fault.rule) for fault in checked.violations] == [
        ("decision/price-reviews-happen-weekly", "", "unreadable"),
        ("decision/prices-are-reviewed-monthly", "sections/0", "required"),
    ]
```

with:

```python
def _store_with_a_file_mangled_by_hand(root, before):
    """Two decisions edited by hand: one left unreadable, one left readable but without the body of its purpose."""
    client = _store_with_a_decision_without_its_purpose(root)
    (root / "kb" / "decision" / "price-reviews-happen-weekly.yaml").write_text(MANGLED)
    before.update(reported=[
        ("decision/price-reviews-happen-weekly", "", "unreadable"),
        ("decision/prices-are-reviewed-monthly", "sections/0", "required"),
    ])
    return client


@given("a store holding an artifact of a kind the store holds no type for", target_fixture="client")
def _store_with_an_artifact_of_no_type(root, before):
    """Beside the two decisions, an invoice written by hand, whole but of a kind the store has no type for."""
    client = _store_with_a_decision_without_its_purpose(root)
    (root / "kb" / "invoice").mkdir()
    (root / "kb" / "invoice" / "march-takings.yaml").write_text(canonical.dump({
        "id": "invoice/march-takings", "type": "invoice", "schema_version": 1, "revision": 1, "title": "March takings",
    }))
    before.update(reported=[
        ("decision/prices-are-reviewed-monthly", "sections/0", "required"),
        ("invoice/march-takings", "", "kind"),
    ])
    return client


def _store_with_a_decision_without_its_purpose(root):
    """Two decisions that fit their type, then one of them edited by hand to lose the body of its purpose."""
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, DECISION_TYPE)
    create(client, "decision", {"title": "Price reviews happen weekly", "sections": SECTIONS})
    create(client, "decision", {"title": "Prices are reviewed monthly", "sections": SECTIONS})
    monthly = root / "kb" / "decision" / "prices-are-reviewed-monthly.yaml"
    held = canonical.load(monthly.read_text())
    del held["sections"][0]["body"]
    monthly.write_text(canonical.dump(held))
    return client


@then("that artifact is reported as a violation, naming the artifact and the kind it claims")
def _reported_as_of_no_type(checked):
    of_no_type = [fault for fault in checked.violations if fault.rule == "kind"]
    assert [fault.artifact for fault in of_no_type] == ["invoice/march-takings"]
    assert "'invoice'" in of_no_type[0].message


@then("everything else in the store is checked and reported alongside it")
def _the_rest_checked_alongside(checked, before):
    assert [(fault.artifact, fault.path, fault.rule) for fault in checked.violations] == before["reported"]
```

The invoice carries everything the store settles, so slice 78.2's loading takes it as an artifact.

- [ ] **Step 2: Run it red**

```bash
.venv/bin/python -m pytest -q -m "slice-81 or slice-1.20" 2>&1 | grep -E "^E  |passed|failed" | head -3
```

Expected: `1 failed, 1 passed`, slice 81's row on `FileNotFoundError: ... kb/schema/invoice.yaml`.

- [ ] **Step 3: The check reports a kind with no type and goes on**

In `src/kb/refusals.py`, replace:

```python
def no_type(kind_name: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        rule="kind", message=f"a kind must name a type the store holds; the store holds no type called {kind_name!r}",
    )
```

with:

```python
def no_type(kind_name: str, artifact: str = "") -> kb_pb2.Fault:
    """A kind the store holds no type for: asked for, or claimed by the artifact named."""
    return kb_pb2.Fault(
        artifact=artifact, rule="kind",
        message=f"a kind must name a type the store holds; the store holds no type called {kind_name!r}",
    )
```

Replace the whole of `src/kb/check.py` with:

```python
"""The check of the whole store: every artifact against the current version of its type, the stale listed beside
the violations, and a file that cannot be read, or an artifact of a kind with no type, reported as what it is, the
check going on past it."""
from kb import canonical, refusals, validation, values
from kb.contract import kb_pb2
from kb.store import Damaged, Store


def everything(store: Store) -> kb_pb2.ValidateResponse:
    """Every artifact checked against the current version of its type, and listed as stale when it was last
    checked against an older one; a file that cannot be read, or an artifact of a kind with no type, is reported and
    the check goes on."""
    violations, stale = [], []
    for artifact_id in store.ids():
        found = _with_type(store, artifact_id)
        if isinstance(found, kb_pb2.Fault):
            violations.append(found)
            continue
        artifact, schema = found
        if artifact["schema_version"] < schema["version"]:
            stale.append(kb_pb2.Stale(
                artifact=str(artifact_id), schema_version=artifact["schema_version"], current=schema["version"],
            ))
        content = {key: value for key, value in artifact.items() if key not in canonical.IDENTITY[:4]}
        violations += validation.validate(str(artifact_id), content, schema["schema"], store)
    return kb_pb2.ValidateResponse(violations=violations, stale=stale)


def _with_type(store: Store, artifact_id) -> tuple[dict, dict] | kb_pb2.Fault:
    """The artifact and its type as stored, or the one finding that stands in for checking it: the damage of the
    first of them whose file cannot be read, or that the store holds no type for its kind."""
    artifact = store.load(artifact_id)
    if isinstance(artifact, Damaged):
        return artifact.fault
    type_id = values.type_of(artifact_id.kind)
    if not store.holds(type_id):
        return refusals.no_type(artifact_id.kind.name, artifact=str(artifact_id))
    schema = store.load(type_id)
    return schema.fault if isinstance(schema, Damaged) else (artifact, schema)
```

In `CLAUDE.md`, replace the row

```markdown
| `check.py` | the check of the whole store: every artifact against the current version of its type, the stale listed beside the violations, a file that cannot be read reported and passed over | checks of its own, writes |
```

with:

```markdown
| `check.py` | the check of the whole store: every artifact against the current version of its type, the stale listed beside the violations, a file that cannot be read or an artifact of a kind with no type reported and passed over | checks of its own, writes |
```

- [ ] **Step 4: Run it green**

```bash
.venv/bin/python -m pytest -q -m "slice-81 or slice-1.20" 2>&1 | tail -1
.venv/bin/python -m pytest -q 2>&1 | tail -1
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before -
wc -l src/kb/check.py src/kb/refusals.py
```

Expected: `2 passed, 194 deselected`; `32 failed, 164 passed`; one line, `< FAILED tests/test_check_the_store.py::test_an_artifact_of_a_kind_the_store_holds_no_type_for_is_reported_as_a_violation`; `39` and `112`.

- [ ] **Step 5: Checkpoint and commit**

Append the slice 81 checkpoint, with the answer to its unknown (the check's reading gives the finding that stands in for checking an artifact, the damage or the missing type). Set slice 81's Status to `green`.

```bash
git add src/kb tests CLAUDE.md docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 81: A check reports an artifact whose kind has no type

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 11: Slice 82, a kind with no type is refused wherever it is asked by

**Slice plan entry:** Slice 82, capability. Unknown: can a kind be checked against the store's types once, before any question that takes one, with the fault Create already gives? Scenario:

- kb / list-artifacts-of-a-kind / Asking by a kind the store holds no type for is refused (three rows)

The answer, found in scratch: yes. Which type a kind names, refused when the store holds none, becomes one function, `composition.kind_type`, which Create's check moves into; List, and Search and Refs when given a type, ask it first. Before, each of the three answered an empty result, the same as an empty store.

**Files:**
- Modify: `tests/test_list_artifacts_of_a_kind.py` (the scenario's steps)
- Modify: `src/kb/composition.py` (docstring; new `kind_type`), `src/kb/edits.py` (`_create` asks it), `src/kb/query.py` (`listing`, `walk`, `found` ask it)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: Task 10's `refusals.no_type(kind_name)`; `values.type_of(kind)`.
- Produces: `composition.kind_type(kind: values.Kind, corpus) -> values.ArtifactId`, raising `Refused([refusals.no_type(kind.name)])` when the corpus does not hold the type.

- [ ] **Step 1: Save the failing ids, and write the steps**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
```

In `tests/test_list_artifacts_of_a_kind.py`, replace:

```python
import copy

from pytest_bdd import given, scenarios, then, when

from calls import CLIENT, DECISION_TYPE, create, define, listing
```

with:

```python
import copy
import re

from pytest_bdd import given, parsers, scenarios, then, when

from calls import CLIENT, DECISION_TYPE, create, define, listing, read, refs, search
```

and append at the end of the file:

```python
CALLS = {
    'lists the artifacts of the kind "invoice"':
        lambda client: listing(client, "invoice"),
    "searches the prose for restocking among artifacts of that kind":
        lambda client: search(client, "restocking", type_name="invoice"),
    "follows the links into a decision, only from artifacts of that kind":
        lambda client: refs(client, MONTHLY, 1, inward=True, type_name="invoice"),
}


@given('a store that holds no type called "invoice"')
def _no_invoice_type(client):
    assert [fault.rule for fault in read(client, "schema/invoice").faults] == ["not-found"]


@when(parsers.re(f"the client (?P<call>{'|'.join(map(re.escape, CALLS))})"), target_fixture="answered")
def _ask_by_that_kind(client, call):
    return CALLS[call](client)


@then("the call is rejected because a kind must name a type the store holds, and the kind asked for is given back")
def _rejected_for_its_kind(answered):
    assert [(fault.artifact, fault.path, fault.rule) for fault in answered.faults] == [("", "", "kind")]
    assert "a kind must name a type the store holds" in answered.faults[0].message
    assert "'invoice'" in answered.faults[0].message
```

- [ ] **Step 2: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-82 2>&1 | grep -E "^E  |passed|failed" | head -3
```

Expected: `3 failed`, each on `assert [] == [('', '', 'kind')]`: every call answered, with nothing.

- [ ] **Step 3: One answer to which type a kind names**

In `src/kb/composition.py`, replace the module docstring:

```python
"""A type read through what it is built on: the schemas of its composition, base first, and the type a kb: reference
names. kb's own keywords are read through the composition, so a type built on a base carries the base's first."""
```

with:

```python
"""A type read through what it is built on: the schemas of its composition, base first, the type a kb: reference
names, and the type a kind names. kb's own keywords are read through the composition, so a type built on a base
carries the base's first."""
```

replace `from kb import names, values` with `from kb import names, refusals, values`, and append at the end of the file:

```python
def kind_type(kind: values.Kind, corpus) -> values.ArtifactId:
    """The type a kind names. Raises Refused when the corpus holds none, since a kind must name a type the store
    holds, wherever it is given."""
    type_id = values.type_of(kind)
    if not corpus.holds(type_id):
        raise values.Refused([refusals.no_type(kind.name)])
    return type_id
```

`refusals` imports `names` and `values` only, so no cycle.

In `src/kb/edits.py`, in `_create`, replace:

```python
    kind = creation.kind
    if not draft.holds(values.type_of(kind)):
        raise Refused([refusals.no_type(kind.name)])
```

with:

```python
    kind = creation.kind
    composition.kind_type(kind, draft)
```

- [ ] **Step 4: Every question by a kind asks it first**

In `src/kb/query.py`, replace `from kb import journal, links, read, refusals, search, values` with `from kb import composition, journal, links, read, refusals, search, values`. In `listing`, replace its docstring line:

```python
    """Every artifact of a kind whose fields hold the values asked for, in path order, as stubs or names."""
```

with:

```python
    """Every artifact of a kind whose fields hold the values asked for, in path order, as stubs or names. Raises
    Refused for a kind the store holds no type for."""
    composition.kind_type(asked.kind, store)
```

In `walk`, replace:

```python
    once, by the shortest route, the one asked about never. A via or a type narrows every step. Raises Refused for
    a name the store lacks."""
    start = asked.locator.id
```

with:

```python
    once, by the shortest route, the one asked about never. A via or a type narrows every step. Raises Refused for
    a kind the store holds no type for, or a name the store lacks."""
    if asked.kind is not None:
        composition.kind_type(asked.kind, store)
    start = asked.locator.id
```

In `found`, replace:

```python
    artifacts of one kind when a type is given, with a stub of its artifact, most often first."""
```

with:

```python
    artifacts of one kind when a type is given, with a stub of its artifact, most often first. Raises Refused for a
    kind the store holds no type for."""
    if asked.kind is not None:
        composition.kind_type(asked.kind, store)
```

- [ ] **Step 5: Run it green**

```bash
.venv/bin/python -m pytest -q -m slice-82 2>&1 | tail -1
.venv/bin/python -m pytest -q 2>&1 | tail -1
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before -
grep -rn "refusals.no_type" src/kb
grep -c "try:" src/kb/servicer.py
wc -l src/kb/composition.py src/kb/edits.py src/kb/query.py
```

Expected: `3 passed, 193 deselected`; `29 failed, 167 passed`; three lines, each `< ... test_asking_by_a_kind_the_store_holds_no_type_for_is_refused[...]`; two lines, in `check.py` and `composition.py`; `1`; `52`, `192` and `137`.

- [ ] **Step 6: The batch's failures are all later slices'**

```bash
for n in 84 85 86 87 88 89 91 92 93 94; do echo "$n: $(.venv/bin/python -m pytest -q -m slice-$n 2>&1 | tail -1 | cut -d, -f1)"; done
git diff 172b006 --stat -- features
```

Expected: `84: 1 failed`, `85: 3 failed`, `86: 2 failed`, `87: 2 failed`, `88: 7 failed`, `89: 2 failed`, `91: 4 failed`, `92: 2 failed`, `93: 3 failed`, `94: 3 failed` (29 in all); no feature file changed.

- [ ] **Step 7: Checkpoint and commit**

Append the slice 82 checkpoint, with the answer to its unknown (one function says which type a kind names, read by Create and every question by a kind), and a line `slices 77 to 82, and 77.1, 78.1, 78.2, 79.1 and 79.2 among them, are green; suite 29 failed, 167 passed; next: slice 83, the fourth architecture review`. Set slice 82's Status to `green`.

```bash
git add src/kb tests docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 82: A kind with no type is refused wherever it is asked by

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```
