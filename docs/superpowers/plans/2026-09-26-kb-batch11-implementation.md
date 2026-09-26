# kb Batch 11 Implementation Plan: slices 83.1 to 89.1, between the fourth and fifth architecture reviews

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Each task is one slice of `docs/superpowers/plans/2026-09-24-kb-slices.md`. Inside a capability task, follow `shopsystem-bdd:bdd-red-green` scenario by scenario; its stop conditions, hand-back and checkpoint apply, and they override any step here that conflicts with them. An enabling task (83.1, 83.2, 84.1, 87.1, 89.1) adds no scenario and changes no scenario's answer: its check is the suite's failing test ids unchanged, its structural target met, and, where it makes a crash unreachable or could move a file's bytes, a probe giving the answer the plan names.

**Goal:** The eleven slices after slice 83, the fourth architecture review, up to slice 90, the fifth, leaving out slice 89.2, which is blocked awaiting approval:
- The type a `kb:` reference names is read in one place (slice 83.1, enabling).
- Items are named at every depth by one rule, whatever they hold (slice 83.2, enabling).
- A type's version moves on whenever it changes (slice 84).
- What the store settles for every artifact is said in one place (slice 84.1, enabling).
- A set stopped for any reason leaves the store as it was (slice 85).
- Items keep their names through a change (slice 86).
- A removal is held back by a link inside an item, and frees the name (slice 87).
- A whole read takes its links from the one reading of links (slice 87.1, enabling).
- A read answers plainly what it cannot find, and what a filled-in link is (slice 88).
- Narrow what comes in to one link and one kind (slice 89).
- Which type a kind names is asked of composition alone (slice 89.1, enabling).

**Not in this plan:** slice 89.2, "The client follows the links out of one place inside an artifact". Its Given has a section carry a link, which the spec says a section never does; the slice plan's log holds the RE-FORMULATE entry, the proposed rewrite and the question. No task here touches that scenario, and it stays red (tagged `@slice-89.2`).

**Architecture:** kb is the Python package `kb` in `/home/vscode/shopsystem-kb`. A protobuf contract (`kb.contract`) sits in front of `KbServicer` (`servicer.py`), whose every rpc runs inside one boundary that turns `values.Refused` into that rpc's faults. `requests.py`/`values.py` convert requests; `canonical.py` is the one YAML checker, dump and load; `write.py` drafts a set and only then writes; `edits.py` says what each operation does to the draft; `names.py` is the grammar of names and the minting of item names; `places.py` resolves a place inside an artifact; `validation.py` holds the composed schema and kb's own checks; `composition.py` reads a type through what it is built on; `definitions.py` checks a type as it is written; `check.py` is the check of the whole store; `links.py` is the one reading of links; `read.py` and `query.py` answer reads and questions; `store.py` is files and git, and `Store.load` returns an artifact or `Damaged`. `CLAUDE.md` is the rulebook. This plan implements each rule it touches once:
- **Names live in one place (rule 6), with the module map.** What a `kb:` reference names is `composition.reference`, asked by `definitions.py` and by `composition.py` itself (Task 1). Naming items, at every depth, and reading the names a collection already holds are `names.items` and `names.held`, with what each item's type declares handed in by `edits.py`, since `names.py` reads no type (Task 2). Which type a kind names, or the fault that it names none, is `composition.named_type`, asked by the check (Task 11) as `composition.kind_type` already is by every question that takes a kind.
- **Parse, don't validate (rule 2).** Which values a title may be written as to give a name, text, a number, true or false, is `content.title`, asked by the conversion of an added item and by the naming (Task 2).
- **A new concern gets a new module; nothing beside.** What the store settles for every artifact whatever its type, the keys naming it and what each must be, its content without them, an artifact given them, and the order an artifact is written in as its type declares, is the new module `settled.py`; `canonical.py` is left YAML and nothing else (Task 4). CLAUDE.md's module map gains its row.
- **Loading returns a value (rule 3).** Unchanged; `store.readable` gains the annotations it lost (Task 4).
- **Fail-closed boundary (rule 1).** No rpc gains a `try`. The crashes Task 2 makes unreachable are made so by the one rule of naming, never by a catch.

**Provenance:** Every code block here was assembled in a scratch clone of this repository (`/tmp/kb11`, cloned at `5157a4f`, run with this checkout's `.venv` and `PYTHONPATH=/tmp/kb11/src`) on 2026-09-26, and the tasks were applied in order, one commit each. The red and green results, the suite counts, the failing-id comparisons, the line counts, the probes and the Review Focus reproductions are what those runs gave. This repository was not touched except to write this plan, the slice plan's entries, and the one tag line slice 89.2 needed. The plan was then replayed from its text alone in a second clone (`/tmp/kb11-replay`, from `672694c`, `PYTHONPATH=/tmp/kb11-replay/src`), each code block taken verbatim from this file, each replacement found exactly once: tasks 1 to 6 by one session, tasks 7 to 11 by a second, which started from task 6's commit and a suite of `23 failed, 173 passed`. Every Expected in tasks 7 to 11 held as written: the red runs and their messages, the suite counts (`21/175`, `21/175`, `14/182`, `13/183`, `13/183`), the failing-id diffs, the probes before and after, the greps and the line counts; the end state reads `89.2: 1`, `91: 4`, `92: 2`, `93: 3`, `94: 3` failed, the 13 left, with no diff under `features/`. The five Review Focus reproductions gave what is written there. The replay set each slice's Status and wrote no checkpoint prose, and its commits carry a scratch author; neither is something this plan's text decides. No text in this plan needed changing.

**Tech Stack:** Python 3.11, setuptools (src layout), protobuf + grpcio (generated code committed; no `.proto` change in this batch), python-jsonschema 4.26 with `referencing`, ruamel.yaml 0.19 (YAML 1.2), git via subprocess, pytest 9 + pytest-bdd 8.

**Spec:** `docs/superpowers/specs/2026-09-23-kb-design.md`, in particular:
- "Parts": an item's `id` minted by kb from its `title`, otherwise from its position, never supplied by the client.
- "Every schema carries an integer `version` that increments when it changes."
- "Store discovery": `KB_ROOT` naming a directory with no store is its own refusal, naming `KB_ROOT`.
- "Refs": locator, direction, optional via-field, optional type, depth.

The slice plan is `docs/superpowers/plans/2026-09-24-kb-slices.md`, and the feature files are in `features/`. Each capability slice's scenarios carry `@slice-<n>`, so `.venv/bin/python -m pytest -q -m slice-84` runs one slice. `CLAUDE.md` at the repository root is binding.

## Global Constraints

- Feature files are read-only for the implementer. Only `slicing-into-increments` edits a tag line, and only `formulating-features` edits a Given, When, or Then. Any diff under `features/` is a stop condition; this batch touches none.
- Code only what a scenario asserts (bdd-red-green). Where the scenarios are silent, the code is silent too, and the silence goes into the checkpoint entry as an open question. The decisions this plan makes are listed below, each tied to the scenario or slice that asks for it.
- **CLAUDE.md's rules are implemented once, never per row.** No rpc in `servicer.py` gains a `try`, a check, or a branch in this batch (`grep -c "try:" src/kb/servicer.py` stays `1`). No module but `names.py` mints an item's name or reads which names a collection holds; no module but `composition.py` decides what a `kb:` reference or a kind names; no module but `settled.py` lists the keys the store settles or orders an artifact's entries. No module catches a broad exception (`grep -nE "except (Exception|BaseException)|except:" src/kb/*.py` prints nothing).
- **Extend, never add beside.** Test helpers and shared test constants live in `tests/calls.py`; a step two feature files share word for word is one step definition in `tests/conftest.py`, never two. A test module never imports from `conftest.py`.
- **Size.** No module over 250 lines; `servicer.py` under 150. The line counts each task ends at are in its check. At the end of the batch the largest are `values.py` 226, `store.py` 211, `edits.py` 182, `requests.py` 181 and `canonical.py` 173.
- Errors are a typed list of `{ artifact, path, rule, message }`. A response that carries faults is a refusal, and nothing was written.
- kb is exercised through its in-process transport (`kb.client.connect`).
- `make test` runs the suite in this checkout's virtualenv (`.venv/bin/python -m pytest -q`). While any scenario is red, make's own error line comes last, so the steps run pytest directly to see the summary. A worktree needs its own `.venv` first (`make dev`).
- The contract's version stays `0.1`, `pyproject.toml` stays `0.1.0`. Version and tag are the user's call.
- Work on `main` in `/home/vscode/shopsystem-kb`. shop-knowledge pins kb at `v0.1.0`; nothing here touches or runs its suite.
- Commits: `git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit`, the message ending with the Co-Authored-By line of the model that made the commit, e.g. `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- "Append at the end of the file" means after two blank lines, as the files' top-level definitions are spaced.
- The suite prints pytest-bdd `PytestRemovedIn10Warning`s. That is the baseline, not a fault. The summary lines quoted as Expected leave out the `, N warnings in Xs` that pytest adds.
- Baseline before Task 1: `.venv/bin/python -m pytest -q` → `29 failed, 167 passed`. After each task the suite reads, failed/passed: 1 `29/167`; 2 `29/167`; 3 `28/168`; 4 `28/168`; 5 `25/171`; 6 `23/173`; 7 `21/175`; 8 `21/175`; 9 `14/182`; 10 `13/183`; 11 `13/183`. Every failure left after Task 11 is tagged for slice 89.2 or 91 and later (89.2: 1, 91: 4, 92: 2, 93: 3, 94: 3), and none of those goes green early.
- Every task's first step saves the failing ids (`.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before`). An enabling task's check compares them after (`... | sort | diff /tmp/failing-before -` prints nothing); a capability task's check shows only its own scenarios leaving (`diff` prints only `<` lines, one per row of the slice).
- A probe is a Python script run with `.venv/bin/python` from the repository root, given in full in the task, that drives the in-process client over a store in a temporary directory. Save it under `/tmp`, run it before the change and after, and compare.

## Decisions this plan makes (the spec left them open or silent)

1. **What a `kb:` reference names (slice 83.1).** `composition.reference(ref)` gives `None` for a reference that is not kb's, else `Reference(type_id, whole)`: the type's name, `None` when the reference names no type at all (a name that does not convert, or one of a kind other than `schema`), and whether it is to the whole type rather than a shape inside it. `definitions.faults` and `composition.type_schema` answer exactly as before.
2. **Naming at every depth (slice 83.2).** `names.items(parts, node, keep_named, inner)` walks every depth; `inner(part)` gives the collections an item's type declares, read through its composition by `edits.py`. An item that is not a set of named entries carries no name and is passed over, as links, places and names handed back already pass it over, and the ordering keeps it as written. An item's name is made from its title when `content.title` makes the title text (text, a number, true or false); a title that is nothing, a list or a mapping is as no title, and the item is named from its place, counted from 1. The stored title is left as it was written. `names.held(parts, node)` reads the names each collection holds, passing over a bare item.
3. **A type's version (slice 84).** When the draft holds the type being written and the new `schema` differs from the held one, the new `version` must be greater than the held one; otherwise the fault is `path: "version"`, `rule: "version"`, message `a type's version goes up whenever the type changes; 'schema/decision' changed at version 2`. A type's first write is not judged, a write that leaves the schema as it was is not judged, and a version more than one higher is accepted (Review Focus 3).
4. **What the store settles (slice 84.1).** `settled.py` holds `SETTLED`, `IDENTITY`, `given`, `content`, `checked`, `lacking` and `order` (with its `_section` and `_item`), moved unchanged in what they answer: no file's bytes move.
5. **A set stopped (slice 85), items through a change (slice 86), a removal held back and a name freed (slice 87).** These pass on their steps alone; `tests/calls.py` gains `removal(artifact_id)`, a removal inside a set.
6. **Which links a whole read fills in (slice 87.1).** Those `links.carried` finds in the artifact's own fields, alone or in a list (a place of the field's name, or the field's name, `/` and an index); a link inside an item stays a name, as before.
7. **A read of a place (slice 88).** A read whose locator names a place resolves it by `places.resolve` before anything else, and is refused by its faults (`not-found` with `holds nothing at '<place>'`, or `identity`); a read at a place that is held answers as it did, the artifact at the level asked (Review Focus 4). A read of a section it lacks was already refused (`not-found`, naming the title).
8. **A KB_ROOT that names no store (slice 88).** A `KB_ROOT` set to nothing names no store, and is never read as the working directory; the fault's message gives the value as it was set, `KB_ROOT names a directory that holds no store: <value>`, which for the directory rows is what it gave before (Review Focus 5).
9. **Which type a kind names (slice 89.1).** `composition.named_type(kind, corpus, artifact="")` gives the type's name or the `no_type` fault naming the artifact; `composition.kind_type` raises that fault, and the check returns it.

## Review Focus

In this project, tests are scenarios, and the feature files are the human gate, so no unit tests are added. Instead, each line below goes into the owning task's checkpoint entry as a `QUESTION FOR THE SPEC`, with the reproduction given here. Each was reproduced in scratch after all eleven tasks.

1. **An Append of a bare value, where the collection's item type admits it, still breaks off.** Reproduction: a type `flat` whose `steps` have items `{}`; create `flat/c` with `steps: [x]`; Append `x` to its steps: it raises `TypeError: string indices must be integers, not 'str'` through the client, as the addition's name is given back. No name can be given back; refusing it or accepting it with none is the spec's (slice 83's log). Task 2 logs it.
2. **A summary of an artifact holding a bare part breaks off.** Reproduction: the `flat/c` above, read at a glance: it raises `TypeError: string indices must be integers, not 'str'` as the parts are listed. Task 2 lets the Create through that makes it reachable (slice 83's log). Task 2 logs it.
3. **A type's version can go back down.** Reproduction: define the decision type, write it at version 2 with the same schema, then write it at version 1 with the same schema: accepted, the type reads back at version 1. Only a changed schema is held to a higher version. Task 3 logs it.
4. **A read of a place the artifact holds ignores the place.** Reproduction: a decision with sections Purpose and Rationale; Read it whole with the place `sections/purpose`: the whole decision comes back, both sections. Slice 88 refuses a place that is not held, as its scenario asks; what a held place answers has no scenario. Task 9 logs it.
5. **A KB_ROOT set to nothing is named back as nothing.** Reproduction: with `KB_ROOT` set to the empty string, outside any store, Read is refused with `KB_ROOT names a directory that holds no store: ` and nothing after the colon; `kb validate` prints the same on stderr and exits 2. A person may expect to be told it is empty. Task 9 logs it.

---

### Task 1: Slice 83.1, the type a kb: reference names is read in one place

**Slice plan entry:** Slice 83.1, enabling. Check: the suite's summary and failing ids unchanged; `grep -nE "names\.referred|values\.artifact_id" src/kb/definitions.py` → no lines (3 before).

**Files:**
- Modify: `src/kb/composition.py` (new `Reference`, `reference`; `composition` and `type_schema` ask it)
- Modify: `src/kb/definitions.py` (`faults` asks `composition.reference`; `_type_named` is gone)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `names.referred(ref) -> tuple[str, str] | None`; `values.artifact_id`, `values.TYPE_KIND`.
- Produces: `composition.Reference(type_id: ArtifactId | None, whole: bool)`; `composition.reference(ref: str) -> Reference | None`.

- [ ] **Step 1: Save the failing ids**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
grep -nE "names\.referred|values\.artifact_id" src/kb/definitions.py
```

Expected: three lines, 17, 29 and 33.

- [ ] **Step 2: One reading of a reference in composition.py**

In `src/kb/composition.py`, replace:

```python
from referencing.exceptions import NoSuchResource

from kb import names, refusals, values
```

with:

```python
from typing import NamedTuple

from referencing.exceptions import NoSuchResource

from kb import names, refusals, values
```

Replace:

```python
    ref = schema.get("$ref")
    referred = names.referred(ref) if isinstance(ref, str) else None
    if referred is not None and not referred[1]:
        built_on += composition(type_schema(ref, corpus), corpus)
    return [*built_on, schema]


def type_schema(uri: str, corpus) -> dict:
    """The JSON Schema of the type a kb: URI names, its name checked as any other name is. NoSuchResource if none."""
    referred = names.referred(uri)
    try:
        schema_id = values.artifact_id(referred[0]) if referred is not None else None
    except values.Refused:
        schema_id = None
    if schema_id is None or schema_id.kind != values.TYPE_KIND or not corpus.holds(schema_id):
        raise NoSuchResource(ref=uri)
    return corpus.artifact(schema_id)["schema"]
```

with:

```python
    ref = schema.get("$ref")
    referred = reference(ref) if isinstance(ref, str) else None
    if referred is not None and referred.whole:
        built_on += composition(type_schema(ref, corpus), corpus)
    return [*built_on, schema]


class Reference(NamedTuple):
    """What a kb: reference names: the type, None when it names no type at all, and whether it is to the whole type
    rather than to a shape inside it."""
    type_id: values.ArtifactId | None
    whole: bool


def reference(ref: str) -> Reference | None:
    """What a kb: reference names, the type's name checked as any other name is. None for a reference that is not
    kb's."""
    referred = names.referred(ref)
    if referred is None:
        return None
    name, fragment = referred
    try:
        type_id = values.artifact_id(name)
    except values.Refused:
        type_id = None
    if type_id is not None and type_id.kind != values.TYPE_KIND:
        type_id = None
    return Reference(type_id, not fragment)


def type_schema(uri: str, corpus) -> dict:
    """The JSON Schema of the type a kb: URI names. NoSuchResource if it names none the corpus holds."""
    referred = reference(uri)
    if referred is None or referred.type_id is None or not corpus.holds(referred.type_id):
        raise NoSuchResource(ref=uri)
    return corpus.artifact(referred.type_id)["schema"]
```

- [ ] **Step 3: The check of a type as it is written asks it**

In `src/kb/definitions.py`, replace `from kb import names, refusals, values` with `from kb import composition, refusals`, and `from kb.values import ArtifactId, Refused` with `from kb.values import ArtifactId`. Replace:

```python
    for place, ref in _refs(schema, "schema"):
        named = _type_named(ref)
        if named is None:
            continue
        if named == type_id and not names.referred(ref)[1]:
            found.append(refusals.built_on_itself(type_id, place, ref))
        elif named is False or not draft.holds(named):
            found.append(refusals.no_such_shape(type_id, place, ref))
```

with:

```python
    for place, ref in _refs(schema, "schema"):
        named = composition.reference(ref)
        if named is None:
            continue
        if named.type_id == type_id and named.whole:
            found.append(refusals.built_on_itself(type_id, place, ref))
        elif named.type_id is None or not draft.holds(named.type_id):
            found.append(refusals.no_such_shape(type_id, place, ref))
```

and delete the whole of `_type_named` (from `def _type_named(ref: str) -> ArtifactId | None | bool:` to its `return named if named.kind == values.TYPE_KIND else False`, and the two blank lines after it), so `_refs` follows `faults`.

- [ ] **Step 4: Check**

```bash
.venv/bin/python -m pytest -q 2>&1 | tail -1
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before -
grep -nE "names\.referred|values\.artifact_id" src/kb/definitions.py
wc -l src/kb/composition.py src/kb/definitions.py
```

Expected: `29 failed, 167 passed`; no diff; no lines; `73` and `53`.

- [ ] **Step 5: Checkpoint and commit**

Append the slice 83.1 checkpoint to the slice plan's log (what someone reading the code can now rely on, the check before and after, line counts, open questions: none) and set its Status to `green`.

```bash
git add src/kb docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 83.1: The type a kb: reference names is read in one place

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Slice 83.2, items are named at every depth by one rule, whatever they hold

**Slice plan entry:** Slice 83.2, enabling. Unknown: can the naming of items at every depth move into `names.py`, which reads no type, with what each item's type declares handed in by the caller? Check: the suite's summary and failing ids unchanged; `grep -n "def _named" src/kb/edits.py` → no lines (1 before); `grep -n 'item.get("id") for item' src/kb/edits.py` → no lines (1 before); `grep -nE "\(str, int, float\)" src/kb/*.py` → no lines (1 before); the probe below.

The answer, found in scratch: yes. `names.items` takes the collections the node's type declares and a function giving those an item's type declares, which `edits.py` makes from `composition.declared`; `names.py` imports nothing that reads a type. Two further places asked a bare item what it carries once the Create was accepted, and both are the same rule: the names a collection holds, read before the checks of names handed back (`names.held`), and the ordering of an item's entries (`canonical._item`).

**Files:**
- Modify: `src/kb/content.py` (new `title`)
- Modify: `src/kb/values.py` (`_titled` asks `content.title`)
- Modify: `src/kb/names.py` (`items` at every depth; new `held`)
- Modify: `src/kb/edits.py` (`_create` and `_revise` call `names.items` and `names.held`; `_named` becomes `_item_parts`)
- Modify: `src/kb/canonical.py` (`_item` keeps a bare item as written)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `content.text(value) -> str`; `composition.declared(schema, corpus) -> dict`.
- Produces: `content.title(value) -> str | None`; `names.items(parts: dict, node: dict, keep_named: bool, inner: Callable[[dict], dict]) -> None`; `names.held(parts: dict, node: dict) -> dict[str, set]`. Task 4 moves `canonical._item` as this task leaves it.

- [ ] **Step 1: Save the failing ids, and run the probe before**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
```

Save as `/tmp/probe-83-2.py`:

```python
"""Slice 83.2's probe: items named at every depth, whatever they hold."""
import sys
import tempfile
from pathlib import Path

from kb import client as kb_client
from kb.content import dumps, loads
from kb.contract import kb_pb2

ACTOR = kb_pb2.Actor(role="client")


def store():
    root = Path(tempfile.mkdtemp()) / "store"
    root.mkdir()
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=ACTOR))
    return client


def create(client, kind, title, content):
    return client.Create(kb_pb2.CreateRequest(type=kind, title=title, content=dumps(content), actor=ACTOR, message="m"))


def write(client, name, content):
    return client.Write(kb_pb2.WriteRequest(locator=kb_pb2.Locator(id=name), content=dumps(content), actor=ACTOR, message="m"))


def append(client, name, path, content):
    return client.Append(kb_pb2.AppendRequest(
        locator=kb_pb2.Locator(id=name, path=path), content=dumps(content) if isinstance(content, dict) else content,
        actor=ACTOR, message="m"))


def whole(client, name, collection):
    read = client.Read(kb_pb2.ReadRequest(locator=kb_pb2.Locator(id=name), level=kb_pb2.ReadRequest.WHOLE))
    return loads(read.content)[collection]


def show(label, call, then=None):
    try:
        response = call()
    except Exception as error:
        print(f"{label}: RAISES {type(error).__name__}: {error}")
        return
    faults = [(fault.path, fault.rule) for fault in response.faults]
    print(f"{label}: {faults or 'accepted'}{'' if faults or then is None else ' ' + repr(then(response))}")


client = store()
create(client, "schema", "Flat", {"version": 1, "schema": {"type": "object", "parts": {"steps": {"items": {}}}}})
create(client, "schema", "Proc", {"version": 1, "schema": {"type": "object", "parts": {"steps": {"items": {
    "type": "object", "parts": {"checks": {"items": {}}}}}}}})
create(client, "schema", "Decision", {"version": 1, "schema": {"type": "object", "parts": {"options": {"items": {
    "type": "object", "required": ["title"], "properties": {"title": {"type": "string"}}}}}}})
create(client, "decision", "D one", {})

show("create flat [x]", lambda: create(client, "flat", "A", {"steps": ["x"]}), lambda r: whole(client, r.id, "steps"))
show("create flat [{title: 12}]", lambda: create(client, "flat", "B", {"steps": [{"title": 12}]}),
     lambda r: whole(client, r.id, "steps"))
for label, check in [("[x]", "x"), ("[{title: 12}]", {"title": 12}), ("[{title: true}]", {"title": True}),
                     ("[{title: [1]}]", {"title": [1]}), ("[{title: null}]", {"title": None})]:
    show(f"create proc checks {label}", lambda: create(client, "proc", f"P {label}", {"steps": [{"title": "S", "checks": [check]}]}),
         lambda r: whole(client, r.id, "steps")[0]["checks"])
create(client, "proc", "E", {"steps": [{"title": "S"}]})
show("write proc/e checks [x]", lambda: write(client, "proc/e", {"steps": [{"id": "s", "title": "S", "checks": ["x"]}]}),
     lambda r: whole(client, "proc/e", "steps")[0]["checks"])
show("write proc/e checks [{title: 12}]",
     lambda: write(client, "proc/e", {"steps": [{"id": "s", "title": "S", "checks": [{"title": 12}]}]}),
     lambda r: whole(client, "proc/e", "steps")[0]["checks"])
show("append proc/e steps {title: T, checks: [x]}", lambda: append(client, "proc/e", "steps", {"title": "T", "checks": ["x"]}),
     lambda r: r.id)
show("append proc/e steps {title: 12}", lambda: append(client, "proc/e", "steps", {"title": 12}), lambda r: r.id)
show("append proc/e steps {title: '!!!'}", lambda: append(client, "proc/e", "steps", {"title": "!!!"}))
show("append decision options 'just words'", lambda: append(client, "decision/d-one", "options", "just words\n"))
show("append decision options {id: x, title: T}", lambda: append(client, "decision/d-one", "options", {"id": "x", "title": "T"}))
show("write flat/a, which holds a bare step", lambda: write(client, "flat/a", {"steps": ["x", {"title": "T"}]}),
     lambda r: whole(client, "flat/a", "steps"))
show("append flat/a steps {title: U}", lambda: append(client, "flat/a", "steps", {"title": "U"}), lambda r: r.id)
```

```bash
.venv/bin/python /tmp/probe-83-2.py
```

Expected, before:

```
create flat [x]: RAISES TypeError: 'str' object does not support item assignment
create flat [{title: 12}]: RAISES AttributeError: 'int' object has no attribute 'lower'
create proc checks [x]: RAISES TypeError: 'str' object does not support item assignment
create proc checks [{title: 12}]: RAISES AttributeError: 'int' object has no attribute 'lower'
create proc checks [{title: true}]: RAISES AttributeError: 'bool' object has no attribute 'lower'
create proc checks [{title: [1]}]: RAISES AttributeError: 'list' object has no attribute 'lower'
create proc checks [{title: null}]: RAISES AttributeError: 'NoneType' object has no attribute 'lower'
write proc/e checks [x]: RAISES TypeError: 'str' object does not support item assignment
write proc/e checks [{title: 12}]: RAISES AttributeError: 'int' object has no attribute 'lower'
append proc/e steps {title: T, checks: [x]}: RAISES TypeError: 'str' object does not support item assignment
append proc/e steps {title: 12}: accepted '12'
append proc/e steps {title: '!!!'}: [('title', 'title')]
append decision options 'just words': [('options/0', 'type')]
append decision options {id: x, title: T}: [('id', 'identity')]
write flat/a, which holds a bare step: [('', 'not-found')]
append flat/a steps {title: U}: [('', 'not-found')]
```

(The last two answer `not-found` before only because `flat/a` could not be created.)

- [ ] **Step 2: Which values a title may be written as, said once**

In `src/kb/content.py`, insert before `def text(value) -> str:`:

```python
def title(value) -> str | None:
    """A title as text: text as it is, and a number, true or false as YAML 1.2 writes it. None for anything a title
    is never written as: nothing, a list or a mapping."""
    if isinstance(value, (str, bool, int, float)):
        return text(value)
    return None


```

In `src/kb/values.py`, replace `from kb.content import entries, loads, text as text_of` with `from kb.content import entries, loads, title as title_of`, and in `_titled` replace:

```python
    if "title" not in tree or not isinstance(tree["title"], (str, int, float)):
        return Content(tree)
    title = text_of(tree["title"])
    if not names.slug(title):
```

with:

```python
    title = title_of(tree.get("title"))
    if title is None:
        return Content(tree)
    if not names.slug(title):
```

- [ ] **Step 3: Naming at every depth, and the names held, in names.py**

In `src/kb/names.py`, replace:

```python
import re
from typing import NamedTuple
```

with:

```python
import re
from typing import Callable, NamedTuple

from kb.content import title as title_of
```

Replace the whole of `items`:

```python
def items(schema: dict, content: dict, keep_named: bool) -> None:
    """Every item of every part collection given its name: from its title when it carries one, otherwise from its
    place in the collection, counted from 1, with a number added as an artifact's name has when an item beside it
    already has that name. On a write an item already carrying a name is the item of that name, moved or changed
    where it stands, and keeps it; a name is minted once and never worked out again."""
    for collection in schema.get("parts", {}):
        found = content.get(collection, [])
        taken = {item["id"] for item in found if keep_named and "id" in item}
        for place, item in enumerate(found, start=1):
            if keep_named and "id" in item:
                continue
            item["id"] = numbered(slug(item["title"]) if "title" in item else str(place), taken.__contains__)
            taken.add(item["id"])
```

with:

```python
def items(parts: dict, node: dict, keep_named: bool, inner: Callable[[dict], dict]) -> None:
    """Every item of every collection the node holds given its name, and the items of the collections inside each
    item in turn, at every depth. parts is the collections the node's type declares, and inner gives those an item's
    type declares from the collection's declaration. An item is named from its title when the title is text, a
    number, true or false, as an artifact's is, otherwise from its place in the collection, counted from 1, with a
    number added as an artifact's name has when an item beside it already has that name. On a write an item already
    carrying a name is the item of that name, moved or changed where it stands, and keeps it; a name is minted once
    and never worked out again. An item that is not a set of named entries carries no name, and is passed over."""
    for collection, part in parts.items():
        found = node.get(collection, [])
        taken = {item["id"] for item in found if isinstance(item, dict) and keep_named and "id" in item}
        for place, item in enumerate(found, start=1):
            if not isinstance(item, dict):
                continue
            if not (keep_named and "id" in item):
                title = title_of(item.get("title"))
                item["id"] = numbered(slug(title) if title is not None else str(place), taken.__contains__)
                taken.add(item["id"])
            items(inner(part), item, keep_named, inner)


def held(parts: dict, node: dict) -> dict[str, set]:
    """The names the items of each collection the node holds carry; an item that is not a set of named entries
    carries none."""
    return {
        collection: {item.get("id") for item in node.get(collection, []) if isinstance(item, dict)}
        for collection in parts
    }
```

- [ ] **Step 4: edits.py hands in what each item's type declares**

In `src/kb/edits.py`, in `_create` replace `    _named(draft, declared, content, keep_named=False)` with:

```python
    names.items(declared["parts"], content, False, _item_parts(draft))
```

In `_revise` replace:

```python
    held = {collection: {item.get("id") for item in current.get(collection, [])} for collection in declared["parts"]}
```

with:

```python
    held = names.held(declared["parts"], current)
```

and `    _named(draft, declared, content, keep_named=True)` with:

```python
    names.items(declared["parts"], content, True, _item_parts(draft))
```

Replace the whole of `_named`:

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

with:

```python
def _item_parts(draft: Draft):
    """What gives the collections an item's type declares, read through its composition, from the declaration of the
    collection the item is in."""
    return lambda part: composition.declared(part.get("items", {}), draft)["parts"]
```

- [ ] **Step 5: The ordering keeps a bare item as written**

In `src/kb/canonical.py`, in `_item`, replace:

```python
    """An item's id first, then its fields in the item schema's order."""
    ordered = {"id": item["id"]}
```

with:

```python
    """An item's id first, then its fields in the item schema's order; an item that is not a set of named entries as
    it was written."""
    if not isinstance(item, dict):
        return item
    ordered = {"id": item["id"]}
```

- [ ] **Step 6: Check**

```bash
.venv/bin/python -m pytest -q 2>&1 | tail -1
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before -
.venv/bin/python /tmp/probe-83-2.py
grep -n "def _named" src/kb/edits.py; grep -n 'item.get("id") for item' src/kb/edits.py; grep -nE "\(str, int, float\)" src/kb/*.py
wc -l src/kb/names.py src/kb/values.py src/kb/edits.py src/kb/content.py src/kb/canonical.py
```

Expected: `29 failed, 167 passed`; no diff; the probe, after:

```
create flat [x]: accepted ['x']
create flat [{title: 12}]: accepted [{'id': '12', 'title': 12}]
create proc checks [x]: accepted ['x']
create proc checks [{title: 12}]: accepted [{'title': 12, 'id': '12'}]
create proc checks [{title: true}]: accepted [{'title': True, 'id': 'true'}]
create proc checks [{title: [1]}]: accepted [{'title': [1], 'id': '1'}]
create proc checks [{title: null}]: accepted [{'title': None, 'id': '1'}]
write proc/e checks [x]: accepted ['x']
write proc/e checks [{title: 12}]: accepted [{'title': 12, 'id': '12'}]
append proc/e steps {title: T, checks: [x]}: accepted 't'
append proc/e steps {title: 12}: accepted '12'
append proc/e steps {title: '!!!'}: [('title', 'title')]
append decision options 'just words': [('options/0', 'type')]
append decision options {id: x, title: T}: [('id', 'identity')]
write flat/a, which holds a bare step: accepted ['x', {'id': 't', 'title': 'T'}]
append flat/a steps {title: U}: accepted 'u'
```

(an item inside an item has its id after its fields, as every item one level down already has; that is a question logged by slice 83); the three greps print nothing; `116`, `226`, `188`, `39`, `216`.

- [ ] **Step 7: Checkpoint and commit**

Append the slice 83.2 checkpoint, with the answer to its unknown and the probe before and after, and Review Focus 1 and 2 as `QUESTION FOR THE SPEC` lines with their reproductions (both are already questions in slice 83's log; the checkpoint confirms them against this code: Append `x` to `flat/c`'s steps raises `TypeError: string indices must be integers, not 'str'`, and the summary of `flat/c` raises the same). Set slice 83.2's Status to `green`.

```bash
git add src/kb docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 83.2: Items are named at every depth by one rule, whatever they hold

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Slice 84, a type's version moves on whenever it changes

**Slice plan entry:** Slice 84, capability. Unknown: can a type's new version be judged against the version the draft holds, as part of checking the type when it is written? Scenario:

- kb / define-a-type / A type changed without moving its version on is refused

The answer, found in scratch: yes. A Write of a type is checked by `definitions.faults` before the draft is given the new version, so `draft.artifact(type_id)` is still the version the draft holds, the store's or an earlier change's in the same set; a type's first write finds none and is not judged. A Write can change only a type's `version` and `schema` (its title is kept), so "the type changes" is its `schema` differing.

**Files:**
- Modify: `tests/test_define_a_type.py` (the Given, the When, two Thens)
- Modify: `src/kb/definitions.py` (docstring; `faults` adds `_version_kept`)
- Modify: `src/kb/refusals.py` (new `version_kept`)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `tests/calls.py`'s `DECISION_TYPE`, `next_version`, `write`, `read`; Task 1's `definitions.faults`.
- Produces: `refusals.version_kept(type_id: ArtifactId, held: int) -> kb_pb2.Fault`.

- [ ] **Step 1: Save the failing ids, and write the steps**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
```

In `tests/test_define_a_type.py`, replace `from calls import create, define, everything_under, read, request` with:

```python
from calls import DECISION_TYPE, create, define, everything_under, next_version, read, request, write
```

Append at the end of the file:

```python
@given("a type the store holds at its second version", target_fixture="held")
def _a_type_at_its_second_version(client):
    define(client, DECISION_TYPE)
    next_version(client, "decision", DECISION_TYPE)
    return read(client, "schema/decision", whole=True)


@when("the client changes what that type requires, leaving its version at two", target_fixture="changed")
def _change_the_type_leaving_its_version(client):
    schema = {**DECISION_TYPE["schema"], "required": ["title", "supersedes"]}
    return write(client, "schema/decision", {"version": 2, "schema": schema}, message="Revise Decision")


@then("the change is rejected because a type's version goes up whenever the type changes")
def _rejected_for_the_version_kept(changed):
    assert [(fault.artifact, fault.path, fault.rule) for fault in changed.faults] == [
        ("schema/decision", "version", "version"),
    ]
    assert changed.faults[0].message.startswith("a type's version goes up whenever the type changes")
    assert changed.revision == 0


@then("the type reads back as it was")
def _the_type_as_it_was(client, held):
    assert read(client, "schema/decision", whole=True) == held
```

- [ ] **Step 2: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-84 2>&1 | grep -E "^E  |passed|failed" | head -4
```

Expected: `1 failed, 195 deselected`, on `assert [] == [('schema/dec...', 'version')]`.

- [ ] **Step 3: A changed type moves its version on**

In `src/kb/definitions.py`, replace the module docstring:

```python
"""A type checked as it is written, against the types the draft holds: every shape it refers to belongs to a type the
store holds, it is not built on itself, and every link field says which kinds it may point at. What a type could never
check an artifact against is refused here, once, rather than by every create that uses it."""
```

with:

```python
"""A type checked as it is written, against the types the draft holds: every shape it refers to belongs to a type the
store holds, it is not built on itself, every link field says which kinds it may point at, and a change to it moves
its version on. What a type could never check an artifact against is refused here, once, rather than by every create
that uses it."""
```

Replace:

```python
    for place, name, field in _link_fields(schema, "schema"):
        if not isinstance(field["ref"], dict) or "targets" not in field["ref"]:
            found.append(refusals.no_targets(type_id, place, name))
    return found
```

with:

```python
    for place, name, field in _link_fields(schema, "schema"):
        if not isinstance(field["ref"], dict) or "targets" not in field["ref"]:
            found.append(refusals.no_targets(type_id, place, name))
    return found + _version_kept(type_id, content, draft)


def _version_kept(type_id: ArtifactId, content: dict, draft) -> list[kb_pb2.Fault]:
    """The fault of a type whose schema changed while its version did not go up from the version the draft holds;
    nothing for a type the draft does not hold yet."""
    if not draft.holds(type_id):
        return []
    held = draft.artifact(type_id)
    if content["schema"] == held["schema"] or content["version"] > held["version"]:
        return []
    return [refusals.version_kept(type_id, held["version"])]
```

In `src/kb/refusals.py`, insert before `def unwritable(`:

```python
def version_kept(type_id: ArtifactId, held: int) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(type_id), path="version", rule="version",
        message=f"a type's version goes up whenever the type changes; {str(type_id)!r} changed at version {held}",
    )


```

- [ ] **Step 4: Run it green**

```bash
.venv/bin/python -m pytest -q -m slice-84 2>&1 | tail -1
.venv/bin/python -m pytest -q 2>&1 | tail -1
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before -
wc -l src/kb/definitions.py src/kb/refusals.py
```

Expected: `1 passed, 195 deselected`; `28 failed, 168 passed`; one line, `< ... test_a_type_changed_without_moving_its_version_on_is_refused`; `65`, `119`.

- [ ] **Step 5: Checkpoint and commit**

Append the slice 84 checkpoint, with the answer to its unknown, and Review Focus 3 as a `QUESTION FOR THE SPEC` line with its reproduction. Set slice 84's Status to `green`.

```bash
git add src/kb tests docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 84: A type's version moves on whenever it changes

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Slice 84.1, what the store settles for every artifact is said in one place

**Slice plan entry:** Slice 84.1, enabling. Check: the suite's summary and failing ids unchanged; `grep -nE "IDENTITY|SETTLED|def order" src/kb/canonical.py src/kb/store.py` → no lines (5 before); `grep -nE '"revision": (1|current)' src/kb/*.py` → no lines (3 before); `grep -n "IDENTITY\[" src/kb/*.py` → no lines (1 before); `grep -nE "sections|parts|\"id\"" src/kb/canonical.py` → no lines; `store.readable` annotated; the byte probe below unchanged; CLAUDE.md's module map has the row.

**Files:**
- Create: `src/kb/settled.py`
- Modify: `src/kb/canonical.py` (`IDENTITY`, `order`, `_section`, `_item` leave)
- Modify: `src/kb/store.py` (`SETTLED` and `_unsettled` leave; `readable` annotated)
- Modify: `src/kb/check.py`, `src/kb/search.py`, `src/kb/places.py`, `src/kb/read.py`, `src/kb/values.py`, `src/kb/edits.py`, `src/kb/write.py` (ask `settled`)
- Modify: `CLAUDE.md` (module map row)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: Task 2's `canonical._item` (a bare item kept as written).
- Produces: `settled.SETTLED: dict[str, type]`; `settled.IDENTITY: tuple[str, ...]`; `settled.given(content: dict, artifact_id: str, kind: str, schema_version: int, revision: int, title: str) -> dict`; `settled.content(artifact: dict) -> dict`; `settled.checked(artifact: dict) -> dict`; `settled.lacking(loaded: dict) -> str`; `settled.order(artifact: dict, schema: dict) -> dict`; `store.readable(loaded: Loaded | Damaged) -> Loaded`.

- [ ] **Step 1: Save the failing ids, and run the byte probe before**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
```

Save as `/tmp/probe-84-1.py`:

```python
"""Slice 84.1's probe: the bytes of every artifact file a fixed sequence of calls writes, by path."""
import hashlib
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "tests")
from calls import CLIENT, DECISION_TYPE, PROCESS_TYPE, append, create, define, write  # noqa: E402
from kb import client as kb_client  # noqa: E402
from kb.contract import kb_pb2  # noqa: E402

root = Path(tempfile.mkdtemp()) / "store"
root.mkdir()
client = kb_client.connect(root)
client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
define(client, DECISION_TYPE)
define(client, PROCESS_TYPE)
create(client, "decision", {
    "title": "Price reviews happen weekly",
    "sections": [{"title": "Purpose", "body": "Keep prices in step.\n"}, {"title": "Rationale", "body": "Costs move.\n"}],
    "options": [{"title": "Weekly", "body": "Every Monday.\n"}, {"title": "Monthly"}],
})
create(client, "process", {"title": "Open the shop", "steps": [{"title": "Unlock the door"}, {"title": "Count the float"}]})
assert not write(client, "process/open-the-shop", {"body": "Count it twice.\n", "title": "Count the float"},
                 path="steps/count-the-float").faults
assert not append(client, "process/open-the-shop", "steps", {"title": "Turn on the lights"}).faults
store = root / "kb"
for path in sorted(store.rglob("*")):
    relative = path.relative_to(store)
    if path.is_file() and relative.parts[0] not in ("journal", ".git"):
        print(relative, hashlib.sha256(path.read_bytes()).hexdigest()[:16])
```

```bash
.venv/bin/python /tmp/probe-84-1.py > /tmp/probe-84-1.before
cat /tmp/probe-84-1.before
grep -nE "IDENTITY|SETTLED|def order" src/kb/canonical.py src/kb/store.py
grep -nE '"revision": (1|current)' src/kb/*.py
```

Expected: six lines, `decision/price-reviews-happen-weekly.yaml 1f44a40a29108128`, `process/open-the-shop.yaml f43184269cbd3e3f`, `schema/decision.yaml b9fa8a0d938a3845`, `schema/process.yaml 53eb5ea133f14c86`, `schema/schema.yaml 47fd035f39bc9771`, `store.yaml 945dfe29073d9aee`; five lines (canonical 12, 179 and 182, store 111 and 118); three lines (edits 62 and 150, write 43).

- [ ] **Step 2: The new module**

Create `src/kb/settled.py`:

```python
"""What the store settles for every artifact, whatever its type: the keys that say which artifact it is and what each
must be, its content without them, an artifact given them, and the order its entries are written in, as its type
declares them."""

SETTLED = {"id": str, "type": str, "schema_version": int, "revision": int, "title": str}
IDENTITY = tuple(SETTLED)


def given(content: dict, artifact_id: str, kind: str, schema_version: int, revision: int, title: str) -> dict:
    """The content as an artifact: with its name, its kind, the version of its type it was checked against, its own
    version and its title."""
    return {
        **content,
        "id": artifact_id, "type": kind, "schema_version": schema_version, "revision": revision, "title": title,
    }


def content(artifact: dict) -> dict:
    """What an artifact holds but the keys the store settles."""
    return {key: value for key, value in artifact.items() if key not in IDENTITY}


def checked(artifact: dict) -> dict:
    """What of an artifact its type checks: its content, and its title, which a type may say something of."""
    return {key: value for key, value in artifact.items() if key not in IDENTITY or key == "title"}


def lacking(loaded: dict) -> str:
    """What a stored artifact lacks of what the store settles, said as the problem with its file; empty when it lacks
    nothing. A yes-or-no is never a number here."""
    missing = [
        key for key, kind in SETTLED.items()
        if not isinstance(loaded.get(key), kind) or isinstance(loaded.get(key), bool)
    ]
    if not missing:
        return ""
    return f"it does not carry what the store settles for every artifact: {', '.join(missing)}"


def order(artifact: dict, schema: dict) -> dict:
    """Identity keys first, then fields in schema order, then sections, then part collections in schema order."""
    parts = schema.get("parts", {})
    ordered = {key: artifact[key] for key in IDENTITY}
    for name in schema.get("properties", {}):
        if name in artifact and name not in ordered:
            ordered[name] = artifact[name]
    for name, value in artifact.items():
        if name not in ordered and name != "sections" and name not in parts:
            ordered[name] = value
    if "sections" in artifact:
        ordered["sections"] = [_section(section) for section in artifact["sections"]]
    for name in parts:
        if name in artifact:
            ordered[name] = [_item(item, parts[name]["items"]) for item in artifact[name]]
    return ordered


def _section(section: dict) -> dict:
    ordered = {"title": section["title"], "body": section["body"]}
    if "sections" in section:
        ordered["sections"] = [_section(child) for child in section["sections"]]
    return ordered


def _item(item: dict, item_schema: dict) -> dict:
    """An item's id first, then its fields in the item schema's order; an item that is not a set of named entries as
    it was written."""
    if not isinstance(item, dict):
        return item
    ordered = {"id": item["id"]}
    for name in item_schema.get("properties", {}):
        if name in item and name not in ordered:
            ordered[name] = item[name]
    for name, value in item.items():
        if name not in ordered:
            ordered[name] = value
    return ordered
```

- [ ] **Step 3: canonical.py is YAML and nothing else**

In `src/kb/canonical.py`, delete the line `IDENTITY = ("id", "type", "schema_version", "revision", "title")` and the two blank lines after it, and delete everything from `def order(artifact: dict, schema: dict) -> dict:` to the end of the file (`order`, `_section` and `_item`, which Step 2 moved unchanged), with the blank lines before it, so the file ends with `_unreadable`'s `return` line and one newline.

- [ ] **Step 4: The store loads through it, and readable says what it takes**

In `src/kb/store.py`, replace `from typing import Mapping` with `from typing import Mapping, TypeVar`, and `from kb import canonical, refusals, values` with `from kb import canonical, refusals, settled, values`. Replace:

```python
def readable(loaded):
```

with:

```python
Loaded = TypeVar("Loaded")


def readable(loaded: Loaded | Damaged) -> Loaded:
```

In `Store.load`, replace `            problem = _unsettled(loaded)` with `            problem = settled.lacking(loaded)`. Delete `SETTLED = {...}` and the whole of `_unsettled` (from `SETTLED = {"id": str, ...}` to `return f"it does not carry what the store settles for every artifact: {', '.join(lacking)}"`, with the blank lines after), so `class Draft:` follows `Store.artifacts`.

- [ ] **Step 5: Every other reader asks settled**

- `src/kb/check.py`: replace `from kb import canonical, refusals, validation, values` with `from kb import refusals, settled, validation, values`, and replace:

  ```python
          content = {key: value for key, value in artifact.items() if key not in canonical.IDENTITY[:4]}
          violations += validation.validate(str(artifact_id), content, schema["schema"], store)
  ```

  with:

  ```python
          violations += validation.validate(str(artifact_id), settled.checked(artifact), schema["schema"], store)
  ```

- `src/kb/search.py`: replace `from kb.canonical import IDENTITY` with `from kb.settled import IDENTITY`.
- `src/kb/places.py`: replace `from kb import canonical, names, refusals` with `from kb import names, refusals, settled`, and `    if locator.place[0] in canonical.IDENTITY:` with `    if locator.place[0] in settled.IDENTITY:`.
- `src/kb/read.py`: replace `from kb import canonical, composition, links, refusals, values` with `from kb import composition, links, refusals, settled, values`, and in `_whole` replace:

  ```python
      content = {key: value for key, value in found.items() if key not in canonical.IDENTITY}
      return _response(found, dumps(content))
  ```

  with:

  ```python
      return _response(found, dumps(settled.content(found)))
  ```

- `src/kb/values.py`: replace `from kb import canonical, names` with `from kb import canonical, names, settled`, and `    for key in canonical.IDENTITY:` with `    for key in settled.IDENTITY:`.
- `src/kb/edits.py`: replace `from kb import canonical, composition, definitions, links, names, places, refusals, requests, validation, values` with `from kb import composition, definitions, links, names, places, refusals, requests, settled, validation, values`. In `_create` replace:

  ```python
      artifact = {
          **content,
          "id": str(artifact_id), "type": kind.name,
          "schema_version": schema["version"], "revision": 1, "title": creation.title,
      }
      draft.put(artifact_id, canonical.order(artifact, declared))
  ```

  with:

  ```python
      artifact = settled.given(content, str(artifact_id), kind.name, schema["version"], 1, creation.title)
      draft.put(artifact_id, settled.order(artifact, declared))
  ```

  In `_revise` replace:

  ```python
      artifact = {
          **content,
          "id": current["id"], "type": current["type"],
          "schema_version": schema["version"], "revision": current["revision"] + 1, "title": current["title"],
      }
      draft.put(artifact_id, canonical.order(artifact, declared))
  ```

  with:

  ```python
      artifact = settled.given(
          content, current["id"], current["type"], schema["version"], current["revision"] + 1, current["title"],
      )
      draft.put(artifact_id, settled.order(artifact, declared))
  ```

  In `_content_of` replace `    return copy.deepcopy({key: value for key, value in artifact.items() if key not in canonical.IDENTITY})` with `    return copy.deepcopy(settled.content(artifact))`.
- `src/kb/write.py`: replace `from kb import canonical, edits, journal, query, refusals, requests, values` with `from kb import canonical, edits, journal, query, refusals, requests, settled, values`, and in `start` replace:

  ```python
      metaschema = {"id": str(METASCHEMA_ID), "type": "schema", "schema_version": 1, "revision": 1, **METASCHEMA}
      text = canonical.dump(canonical.order(metaschema, METASCHEMA["schema"]))
  ```

  with:

  ```python
      metaschema = settled.given(settled.content(METASCHEMA), str(METASCHEMA_ID), "schema", 1, 1, METASCHEMA["title"])
      text = canonical.dump(settled.order(metaschema, METASCHEMA["schema"]))
  ```

- [ ] **Step 6: The module map**

In `CLAUDE.md`, insert after the row for `canonical.py`:

```
| `settled.py` | what the store settles for every artifact whatever its type: the keys naming it and what each must be, its content without them, an artifact given them, and the order its entries are written in as its type declares | I/O, checks against a type |
```

- [ ] **Step 7: Check**

```bash
.venv/bin/python -m pytest -q 2>&1 | tail -1
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before -
.venv/bin/python /tmp/probe-84-1.py | diff /tmp/probe-84-1.before -
grep -nE "IDENTITY|SETTLED|def order" src/kb/canonical.py src/kb/store.py
grep -nE '"revision": (1|current)' src/kb/*.py
grep -n "IDENTITY\[" src/kb/*.py
grep -nE "sections|parts|\"id\"" src/kb/canonical.py
grep -rn "canonical\.\(IDENTITY\|order\)" src tests
grep -n "def readable" src/kb/store.py
wc -l src/kb/settled.py src/kb/canonical.py src/kb/store.py src/kb/check.py src/kb/read.py src/kb/edits.py src/kb/write.py
```

Expected: `28 failed, 168 passed`; no diff; no diff; five greps print nothing; `25:def readable(loaded: Loaded | Damaged) -> Loaded:`; `77`, `173`, `210`, `38`, `113`, `182`, `121`.

- [ ] **Step 8: Checkpoint and commit**

Append the slice 84.1 checkpoint (what someone reading the code can now rely on, the check before and after, line counts, open questions: none) and set its Status to `green`.

```bash
git add src/kb CLAUDE.md docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 84.1: What the store settles for every artifact is said in one place

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Slice 85, a set stopped for any reason leaves the store as it was

**Slice plan entry:** Slice 85, capability. Unknown: none. Scenario:

- kb / make-several-changes-in-one-go / A set stopped for any reason at all leaves the store exactly as it was (three rows)

What scratch found: every row passes as soon as its steps exist. A set is drafted whole before anything is written (slice 6), a removal refuses while something points at what it removes (slice 41), and a damaged file refuses whoever reads it (slice 63); the scenario pins that each of these stops the whole set.

**Files:**
- Modify: `tests/calls.py` (new `removal`)
- Modify: `tests/test_make_several_changes_in_one_go.py` (imports; the When; three Thens for the reasons; two Thens for the store and its history)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `tests/calls.py`'s `MANGLED`, `apply`, `creation`, `replacement`, `create`, `write`, `read`; the module's own `_everything_under`, `_journal`, `SECTIONS`, `DECISION`, `WORK_ITEM`.
- Produces: `calls.removal(artifact_id) -> kb_pb2.Operation`.

- [ ] **Step 1: Save the failing ids, and write the steps**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
```

In `tests/calls.py`, insert before `def write(client, artifact_id, content, message="Change an artifact", actor=CLIENT, path=""):`:

```python
def removal(artifact_id):
    """A removal of a whole artifact inside a set."""
    return kb_pb2.Operation(delete=kb_pb2.Removal(locator=kb_pb2.Locator(id=artifact_id)))


```

In `tests/test_make_several_changes_in_one_go.py`, replace:

```python
import subprocess

from pytest_bdd import given, scenarios, then, when

from calls import (
    CLIENT, DECISION_TYPE, WORK_ITEM_TYPE, apply, create, creation, define, journal, read, replacement,
)
```

with:

```python
import re
import subprocess

from pytest_bdd import given, parsers, scenarios, then, when

from calls import (
    CLIENT, DECISION_TYPE, MANGLED, WORK_ITEM_TYPE, apply, create, creation, define, journal, read, removal,
    replacement, write,
)
```

Append at the end of the file:

```python
MONTHLY = "decision/prices-are-reviewed-monthly"


def _nothing_by_that_name(root, client):
    return replacement(DECISION, {"sections": SECTIONS})


def _still_pointed_at(root, client):
    create(client, "decision", {"title": "Price reviews happen weekly", "sections": SECTIONS})
    assert not write(client, WORK_ITEM, {"decisions": [DECISION]}).faults
    return removal(DECISION)


def _unreadable(root, client):
    create(client, "decision", {"title": "Price reviews happen weekly", "sections": SECTIONS})
    (root / "kb" / f"{DECISION}.yaml").write_text(MANGLED)
    return replacement(DECISION, {"sections": SECTIONS})


SECOND_CHANGES = {
    "the second change names an artifact the store holds nothing under": _nothing_by_that_name,
    "the second change removes an artifact something still points at": _still_pointed_at,
    "the second change touches an artifact whose stored file cannot be read": _unreadable,
}


@when(
    parsers.re(f"the client asks, in one go, for a set in which (?P<fault>{'|'.join(map(re.escape, SECOND_CHANGES))}), "
               "saying which role and why"),
    target_fixture="attempt",
)
def _ask_for_a_set_stopped(root, client, fault):
    second = SECOND_CHANGES[fault](root, client)
    before, history = _everything_under(root), _journal(root)
    response = apply(client, [creation("decision", "Prices are reviewed monthly", {"sections": SECTIONS}), second],
                     message="Record a decision and change another")
    return {"response": response, "before": before, "after": _everything_under(root), "history": history}


def _refused_with(attempt, faults):
    refused = attempt["response"]
    assert (refused.batch, list(refused.results)) == ("", [])
    assert [(fault.artifact, fault.path, fault.rule) for fault in refused.faults] == faults
    return refused.faults[0].message


@then("the set is rejected because the store holds nothing by that name, and the name asked for is given back")
def _rejected_for_nothing_there(attempt):
    assert DECISION in _refused_with(attempt, [(DECISION, "", "not-found")])


@then("the set is rejected because something still points at it")
def _rejected_for_a_link_in_the_way(attempt):
    assert WORK_ITEM in _refused_with(attempt, [(WORK_ITEM, "decisions/0", "on_delete")])


@then("the set is rejected because that file cannot be read, and the file is named")
def _rejected_for_an_unreadable_file(attempt):
    assert f"{DECISION}.yaml" in _refused_with(attempt, [(DECISION, "", "unreadable")])


@then("the store holds none of the changes in the set")
def _none_of_the_set_held(client, attempt):
    assert attempt["after"] == attempt["before"]
    assert [fault.rule for fault in read(client, MONTHLY).faults] == ["not-found"]


@then("the store's history holds no entry for any of them")
def _no_entry_for_the_set(root, attempt):
    assert _journal(root) == attempt["history"]
    assert not [entry for entry in attempt["history"] if entry.get("artifact") == MONTHLY]
```

- [ ] **Step 2: Run it**

```bash
.venv/bin/python -m pytest -q -m slice-85 2>&1 | tail -1
.venv/bin/python -m pytest -q 2>&1 | tail -1
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before -
```

Expected: `3 passed, 193 deselected` (before the steps, all three were red on `StepDefinitionNotFoundError`); `25 failed, 171 passed`; three lines, each `< ... test_a_set_stopped_for_any_reason_at_all_leaves_the_store_exactly_as_it_was[...]`. No production code changes; if a row is red here, stop and follow bdd-red-green.

- [ ] **Step 3: Checkpoint and commit**

Append the slice 85 checkpoint, noting that its rows passed on their steps alone and which earlier slices' behaviour they rest on; open questions: none. Set slice 85's Status to `green`.

```bash
git add tests docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 85: A set stopped for any reason leaves the store as it was

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Slice 86, items keep their names through a change

**Slice plan entry:** Slice 86, capability. Unknown: none. Scenarios:

- kb / change-an-artifact / The client changes one item of a collection
- kb / change-an-artifact / Items sent back with their names are the same items, and one without a name is new

What scratch found: both pass as soon as their steps exist. A placed Write keeps the item's name (slice 65), names handed back are the items of those names (slice 67), and a link into a part lands while the part is held (slice 72).

**Files:**
- Modify: `tests/test_change_an_artifact.py` (import `refs`; a note type and the When and three Thens of the first scenario; the When and two Thens of the second)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `tests/calls.py`'s `refs`, `define`, `create`, `write`, `read`; the module's `DECISION`, `SECTIONS`, `OPTIONS` and the Given "the decision carries two options".
- Produces: nothing later tasks use.

- [ ] **Step 1: Save the failing ids, and write the steps**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
```

In `tests/test_change_an_artifact.py`, replace `from calls import CLIENT, DECISION_TYPE, append, create, define, everything_under, read, write` with:

```python
from calls import CLIENT, DECISION_TYPE, append, create, define, everything_under, read, refs, write
```

Append at the end of the file:

```python
NOTE_TYPE = {
    "title": "Note",
    "version": 1,
    "schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "about": {
                "type": "string",
                "ref": {"targets": ["decision"], "cardinality": "one", "parts": True, "on_delete": "refuse"},
            },
        },
        "required": ["title"],
    },
}
MONTHLY = {"title": "Go monthly", "body": "Review on the first Monday of the month."}


@when("the client replaces one of the options, saying which role and why", target_fixture="changed")
def _replace_one_option(client):
    define(client, NOTE_TYPE)
    create(client, "note", {"title": "Why monthly", "about": f"{DECISION}#options/go-monthly"})
    before = read(client, DECISION, whole=True)
    response = write(client, DECISION, MONTHLY, message="Say when monthly", path="options/go-monthly")
    assert not response.faults, response.faults
    return {"response": response, "before": before, "after": read(client, DECISION, whole=True)}


@then("only that option changes")
def _only_that_option_changes(changed):
    before, after = loads(changed["before"].content), loads(changed["after"].content)
    assert changed["response"].revision == changed["before"].revision + 1
    assert after["options"][0] == before["options"][0]
    assert {key: value for key, value in after.items() if key != "options"} == {
        key: value for key, value in before.items() if key != "options"
    }
    assert {key: value for key, value in after["options"][1].items() if key != "id"} == MONTHLY


@then("it keeps the name it was given when it was created")
def _keeps_its_name(changed):
    assert [option["id"] for option in loads(changed["after"].content)["options"]] == ["keep-weekly", "go-monthly"]


@then("anything pointing at it still lands on it")
def _still_lands(client):
    assert list(client.Validate(kb_pb2.ValidateRequest()).violations) == []
    inward = refs(client, DECISION, 1, inward=True)
    assert [(reached.stub.id, reached.route[0].field) for reached in inward.reached] == [("note/why-monthly", "about")]


@when(
    "the client replaces the decision, sending both options back with the names they were given and a third option "
    "with no name, saying which role and why",
    target_fixture="changed",
)
def _send_both_back_and_a_third(client):
    options = [{"id": "keep-weekly", **OPTIONS[0]}, {"id": "go-monthly", **OPTIONS[1]}, {"title": "Go fortnightly"}]
    response = write(client, DECISION, {"sections": SECTIONS, "options": options}, message="Add a third option")
    assert not response.faults, response.faults
    return {"response": response, "after": loads(read(client, DECISION, whole=True).content)}


@then("the two options are the same items as before, keeping their names")
def _the_same_two(changed):
    assert changed["after"]["options"][:2] == [{"id": "keep-weekly", **OPTIONS[0]}, {"id": "go-monthly", **OPTIONS[1]}]


@then("the third option is new and is given a name of its own")
def _the_third_named(changed):
    assert changed["after"]["options"][2] == {"id": "go-fortnightly", "title": "Go fortnightly"}
```

- [ ] **Step 2: Run it**

```bash
.venv/bin/python -m pytest -q -m slice-86 2>&1 | tail -1
.venv/bin/python -m pytest -q 2>&1 | tail -1
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before -
```

Expected: `2 passed, 194 deselected` (red before the steps on `StepDefinitionNotFoundError`); `23 failed, 173 passed`; two `<` lines, `test_the_client_changes_one_item_of_a_collection` and `test_items_sent_back_with_their_names_are_the_same_items_and_one_without_a_name_is_new`. No production code changes.

- [ ] **Step 3: Checkpoint and commit**

Append the slice 86 checkpoint (passed on its steps alone; open questions: none) and set its Status to `green`.

```bash
git add tests docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 86: Items keep their names through a change

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Slice 87, a removal is held back by a link inside an item, and frees the name

**Slice plan entry:** Slice 87, capability. Unknown: none. Scenarios:

- kb / remove-an-artifact / A link from inside a part blocks a removal like any other
- kb / remove-an-artifact / A name is free again once what held it has been removed

What scratch found: both pass as soon as their steps exist. A removal reads links through `links.carried`, which finds links inside items (slice 64), and a created artifact is given the first name its title gives that the draft does not hold (`names.numbered`), which a removed artifact no longer holds.

**Files:**
- Modify: `tests/test_remove_an_artifact.py` (import `request`; a process type; two Givens, two Whens, three Thens)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `tests/calls.py`'s `request`, `remove`, `define`, `create`, `read`, `everything_under`; the module's `LOOSE` and the Then "the removal is rejected because something still points at it".
- Produces: nothing later tasks use.

- [ ] **Step 1: Save the failing ids, and write the steps**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
```

In `tests/test_remove_an_artifact.py`, replace `from calls import CLIENT, TAG_TYPE, create, define, everything_under, journal, listing, read, remove, tagged_decision_type` with:

```python
from calls import (
    CLIENT, TAG_TYPE, create, define, everything_under, journal, listing, read, remove, request, tagged_decision_type,
)
```

Append at the end of the file:

```python
PROCESS = "process/run-the-clearance-sale"
TAGGED_PROCESS_TYPE = {
    "title": "Process",
    "version": 1,
    "schema": {
        "type": "object",
        "properties": {"title": {"type": "string"}},
        "required": ["title"],
        "parts": {"steps": {"items": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "about": {
                    "type": "string",
                    "ref": {"targets": ["tag"], "cardinality": "one", "parts": False, "on_delete": "refuse"},
                },
            },
            "required": ["title"],
        }}},
    },
}


@given("a process one of whose steps points at the tag nothing else points at")
def _a_step_pointing_at_the_loose_tag(client):
    define(client, TAGGED_PROCESS_TYPE)
    create(client, "process", {"title": "Run the clearance sale", "steps": [
        {"title": "Mark the shelves"}, {"title": "Price the stock", "about": LOOSE},
    ]})


@when("the client removes that tag, saying which role and why", target_fixture="attempt")
def _remove_the_tag_a_step_points_at(root, client):
    before = everything_under(root)
    response = remove(client, LOOSE, message="Nothing is on clearance")
    return {"response": response, "before": before, "after": everything_under(root)}


@then("the client is given that link among the links that block it")
def _the_steps_link_among_them(client, attempt):
    faults = attempt["response"].faults
    assert [(fault.artifact, fault.path) for fault in faults] == [(PROCESS, "steps/1/about")]
    assert f"'{LOOSE}'" in faults[0].message
    assert not read(client, LOOSE).faults


@given("the client has removed the tag nothing points at")
def _the_loose_tag_removed(client):
    response = remove(client, LOOSE, message="Nothing is on clearance")
    assert not response.faults, response.faults


@when("the client creates a tag with the title the removed one had, saying which role and why", target_fixture="created")
def _create_a_tag_titled_as_the_removed_one(client):
    return request(client, "tag", "Clearance", {}, message="Clearance is back")


@then("the client is given the name the removed tag had, with no number added")
def _the_same_name(created):
    assert not created.faults, created.faults
    assert created.id == LOOSE


@then("the new tag is at its first version")
def _at_its_first_version(client, created):
    assert created.revision == 1
    assert read(client, LOOSE).revision == 1
```

- [ ] **Step 2: Run it**

```bash
.venv/bin/python -m pytest -q -m "slice-87 or slice-41" 2>&1 | tail -1
.venv/bin/python -m pytest -q 2>&1 | tail -1
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before -
```

Expected: `5 passed, 191 deselected` (slice 87 red before the steps on `StepDefinitionNotFoundError`); `21 failed, 175 passed`; two `<` lines, `test_a_link_from_inside_a_part_blocks_a_removal_like_any_other` and `test_a_name_is_free_again_once_what_held_it_has_been_removed`. No production code changes.

- [ ] **Step 3: Checkpoint and commit**

Append the slice 87 checkpoint (passed on its steps alone; open questions: none) and set its Status to `green`.

```bash
git add tests docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 87: A removal is held back by a link inside an item, and frees the name

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 8: Slice 87.1, a whole read takes its links from the one reading of links

**Slice plan entry:** Slice 87.1, enabling. Check: the suite's summary and failing ids unchanged; `grep -n "links.references" src/kb/*.py | grep -v "^src/kb/links.py"` → no lines (1 before, in read.py); the probe below unchanged.

**Files:**
- Modify: `src/kb/read.py` (`_resolved` reads `links.carried`; new `_own`)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `links.carried(artifact, schema, corpus) -> list[links.Link]`, each `Link(field, place, target, ref)`.
- Produces: nothing later tasks use; Task 9 edits `read.artifact` in the same file.

- [ ] **Step 1: Save the failing ids, and run the probe before**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
```

Save as `/tmp/probe-87-1.py`:

```python
"""Slice 87.1's probe: which links a whole read fills in."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "tests")
from calls import CLIENT, DECISION_TYPE, create, define, read  # noqa: E402
from kb import client as kb_client  # noqa: E402
from kb.content import loads  # noqa: E402
from kb.contract import kb_pb2  # noqa: E402

LINK = {"type": "string", "ref": {"targets": ["decision"], "cardinality": "one", "parts": False, "on_delete": "refuse"}}
root = Path(tempfile.mkdtemp()) / "store"
root.mkdir()
client = kb_client.connect(root)
client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
define(client, DECISION_TYPE)
define(client, {"title": "Process", "version": 1, "schema": {
    "type": "object", "properties": {"title": {"type": "string"}, "follows": LINK},
    "parts": {"steps": {"items": {"type": "object", "properties": {"title": {"type": "string"}, "uses": LINK}}}},
}})
define(client, {"title": "Work item", "version": 1, "schema": {"type": "object", "properties": {
    "title": {"type": "string"},
    "at": {"type": "string", "ref": {"targets": ["process"], "cardinality": "one", "parts": True, "on_delete": "refuse"}},
}}})
sections = [{"title": "Purpose", "body": "P.\n"}, {"title": "Rationale", "body": "R.\n"}]
create(client, "decision", {"title": "D one", "sections": sections})
create(client, "process", {"title": "Open the shop", "follows": "decision/d-one",
                           "steps": [{"title": "Count the till", "uses": "decision/d-one"}]})
create(client, "work-item", {"title": "W", "at": "process/open-the-shop#steps/count-the-till"})
whole = loads(read(client, "process/open-the-shop", whole=True, depth=1).content)
print("follows:", type(whole["follows"]).__name__, whole["follows"]["id"] if isinstance(whole["follows"], dict) else whole["follows"])
print("steps/0/uses:", whole["steps"][0]["uses"])
refused = read(client, "work-item/w", whole=True, depth=1)
print("work item:", [(fault.path, fault.rule) for fault in refused.faults])
```

```bash
.venv/bin/python /tmp/probe-87-1.py | tee /tmp/probe-87-1.before
```

Expected:

```
follows: dict decision/d-one
steps/0/uses: decision/d-one
work item: [('', 'locator')]
```

- [ ] **Step 2: The read takes its links from links.carried**

In `src/kb/read.py`, replace the whole of `_resolved`:

```python
def _resolved(store: Store, artifact_id: ArtifactId, depth: int, on_path: set) -> dict:
    """The artifact as stored, each link followed depth steps with the target, itself resolved, in place of its
    name. A target on the path already being filled in stays a name, so a loop ends."""
    found = store.artifact(artifact_id)
    if depth < 1:
        return found
    def fill(target):
        if target in on_path:
            return target
        return _resolved(store, values.artifact_id(target), depth - 1, on_path | {target})
    resolved = dict(found)
    for field in links.references(store.schema(artifact_id.kind)["schema"], store):
        value = found.get(field)
        if isinstance(value, list):
            resolved[field] = [fill(target) for target in value]
        elif value is not None:
            resolved[field] = fill(value)
    return resolved
```

with:

```python
def _resolved(store: Store, artifact_id: ArtifactId, depth: int, on_path: set) -> dict:
    """The artifact as stored, each link in its own fields followed depth steps with the target, itself resolved, in
    place of its name; a link inside one of its items stays a name. A target on the path already being filled in
    stays a name, so a loop ends."""
    found = store.artifact(artifact_id)
    if depth < 1:
        return found
    def fill(target):
        if target in on_path:
            return target
        return _resolved(store, values.artifact_id(target), depth - 1, on_path | {target})
    resolved = dict(found)
    carried = links.carried(found, store.schema(artifact_id.kind)["schema"], store)
    for field in {link.field for link in carried if _own(link)}:
        value = found[field]
        resolved[field] = [fill(target) for target in value] if isinstance(value, list) else fill(value)
    return resolved


def _own(link: links.Link) -> bool:
    """Whether a link sits in one of the artifact's own fields, alone or in a list, rather than inside an item."""
    head, _, rest = link.place.partition("/")
    return head == link.field and (not rest or rest.isdigit())
```

- [ ] **Step 3: Check**

```bash
.venv/bin/python -m pytest -q 2>&1 | tail -1
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before -
.venv/bin/python /tmp/probe-87-1.py | diff /tmp/probe-87-1.before -
grep -n "links.references" src/kb/*.py | grep -v "^src/kb/links.py"
wc -l src/kb/read.py
```

Expected: `21 failed, 175 passed`; no diff; no diff; no lines; `118`.

- [ ] **Step 4: Checkpoint and commit**

Append the slice 87.1 checkpoint (the check before and after; open questions: none new; slice 76's question on whether a whole read fills in an item's links still stands) and set its Status to `green`.

```bash
git add src/kb docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 87.1: A whole read takes its links from the one reading of links

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 9: Slice 88, a read answers plainly what it cannot find, and what a filled-in link is

**Slice plan entry:** Slice 88, capability. Unknown: none. Scenarios:

- kb / read-an-artifact / A read that names a place the artifact does not hold is refused (three rows)
- kb / read-an-artifact / A link filled in still says what it is
- kb / read-an-artifact / A KB_ROOT that names no store is refused, naming KB_ROOT (three rows)

What scratch found: four of the seven rows pass as soon as their steps exist (a section the decision lacks, already refused with `not-found` naming the title; a filled-in link, which is the stored artifact with its identity keys first; `KB_ROOT` naming a directory that is not there, or a file). Three are red on their steps: a read ignores the place its locator names, so the two place rows answer the whole decision; and a `KB_ROOT` set to nothing is read as `Path("")`, the working directory, and named back as `.`.

**Files:**
- Modify: `tests/test_read_an_artifact.py` (the fixture `refused` becomes `shown` throughout; the place When covers the slice's rows; a When for the section row; four Thens; the KB_ROOT Given)
- Modify: `src/kb/read.py` (`artifact` resolves a place first)
- Modify: `src/kb/store.py` (`locate`: an empty `KB_ROOT` names no store; the value named back as set)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `places.resolve(content, locator) -> Spot`, raising `Refused` with `refusals.nothing_at` or `refusals.settled_place`; Task 8's `read.py`.
- Produces: nothing later tasks use.

- [ ] **Step 1: Save the failing ids, and write the steps**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
```

The slice's place rows must answer the Then "no content comes back", which reads the fixture `shown`, while the read of a place slice 1.7 wrote gives the fixture `refused`, and one row's text matches that step as it stands. So the module's `refused` becomes `shown` everywhere, and one When covers every place row:

```bash
sed -i 's/\brefused\b/shown/g' tests/test_read_an_artifact.py
grep -c '\brefused\b' tests/test_read_an_artifact.py
```

Expected: `0`.

In `tests/test_read_an_artifact.py`, replace:

```python
import pytest
from pytest_bdd import given, parsers, scenarios, then, when
```

with:

```python
import re

import pytest
from pytest_bdd import given, parsers, scenarios, then, when
```

Replace:

```python
@when(parsers.parse('the client reads the place "{place}" inside the decision'), target_fixture="shown")
def _read_a_place_inside(client, place):
    return client.Read(kb_pb2.ReadRequest(locator=kb_pb2.Locator(id=DECISION, path=place)))
```

with:

```python
PLACES = {
    'the place "sections/../.." inside the decision': "sections/../..",
    'the place "sections/nowhere" inside the decision': "sections/nowhere",
    'the place "sections/purpose/body/first" inside the decision, which runs on past a piece of prose':
        "sections/purpose/body/first",
}
SECTIONS_NOT_HELD = {
    'the section of the decision titled "Consequences", which it holds no section under': "Consequences",
}


@pytest.fixture
def asked():
    """What a read asked for, filled in by the When that made it."""
    return {}


@when(parsers.re(f"the client reads (?P<what>{'|'.join(map(re.escape, PLACES))})"), target_fixture="shown")
def _read_a_place_inside(client, asked, what):
    asked["what"] = PLACES[what]
    return client.Read(kb_pb2.ReadRequest(locator=kb_pb2.Locator(id=DECISION, path=PLACES[what])))


@when(parsers.re(f"the client reads (?P<what>{'|'.join(map(re.escape, SECTIONS_NOT_HELD))})"), target_fixture="shown")
def _read_a_section_not_held(client, asked, what):
    asked["what"] = SECTIONS_NOT_HELD[what]
    return read(client, DECISION, section=SECTIONS_NOT_HELD[what])


@then("the read is rejected because the decision holds nothing at that place, and what was asked for is given back")
def _rejected_for_nothing_at_that_place(shown, asked):
    assert [(fault.artifact, fault.rule) for fault in shown.faults] == [(DECISION, "not-found")]
    assert repr(asked["what"]) in shown.faults[0].message
```

Append at the end of the file:

```python
@then("the older decision comes with its name, its kind, its title and the version it is at, ahead of its content")
def _older_says_what_it_is(whole):
    older = loads(whole.content)["supersedes"]
    assert list(older)[:5] == ["id", "type", "schema_version", "revision", "title"]
    assert (older["id"], older["type"], older["title"], older["revision"]) == (
        OLDER, "decision", "Prices are reviewed monthly", 1,
    )


KB_ROOTS = {
    "set to nothing at all": lambda tmp_path: "",
    "naming a directory that is not there": lambda tmp_path: str(tmp_path / "not-there"),
    "naming a file rather than a directory": lambda tmp_path: str(_a_file(tmp_path)),
}


def _a_file(tmp_path):
    path = tmp_path / "a-file"
    path.write_text("not a store\n")
    return path


@given(
    parsers.re(f"the client is working outside any store, with KB_ROOT (?P<state>{'|'.join(map(re.escape, KB_ROOTS))})"),
    target_fixture="kb_root",
)
def _outside_with_kb_root(tmp_path, monkeypatch, state):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    named = KB_ROOTS[state](tmp_path)
    monkeypatch.setenv("KB_ROOT", named)
    return named


@then("the read is rejected because KB_ROOT names no store, and KB_ROOT is named back")
def _rejected_as_kb_root_names_no_store(shown, kb_root):
    assert [(fault.rule, fault.message) for fault in shown.faults] == [
        ("store", f"KB_ROOT names a directory that holds no store: {kb_root}"),
    ]


@then("where the client is working is not fallen back on")
def _not_fallen_back_on(shown, tmp_path):
    message = shown.faults[0].message
    assert "no store was found" not in message
    assert str(tmp_path / "elsewhere") not in message and not message.endswith(".")
```

- [ ] **Step 2: Run it red**

```bash
.venv/bin/python -m pytest -q -m "slice-88" 2>&1 | grep -E "^E  |passed|failed" | grep -v "^E  *$" | head -12
.venv/bin/python -m pytest -q -m "slice-1.7 or slice-1.8 or slice-21" 2>&1 | tail -1
```

Expected: `3 failed, 4 passed, 189 deselected`: the rows `sections/nowhere` and `sections/purpose/body/first` on `assert [] == [('decision/p... 'not-found')]`, and `set to nothing at all` on `('store', 'KB_ROOT names a directory that holds no store: .') != ('store', 'KB_ROOT names a directory that holds no store: ')`. The renamed steps still serve their slices: `14 passed, 182 deselected`.

- [ ] **Step 3: A read resolves its place; KB_ROOT is taken as set**

In `src/kb/read.py`, replace `from kb import composition, links, refusals, settled, values` with `from kb import composition, links, places, refusals, settled, values`, and replace:

```python
    """The artifact at the level asked. Raises Refused for a name the store lacks, a section it lacks, or a stored
    file that cannot be read."""
    locator = reading.locator
    if not store.holds(locator.id):
        raise Refused([refusals.not_found(locator.id)])
```

with:

```python
    """The artifact at the level asked. Raises Refused for a name the store lacks, a place or a section it holds
    nothing at, or a stored file that cannot be read."""
    locator = reading.locator
    if not store.holds(locator.id):
        raise Refused([refusals.not_found(locator.id)])
    if locator.place:
        places.resolve(store.artifact(locator.id), locator)
```

In `src/kb/store.py`, in `locate`, replace:

```python
    named = Path(env["KB_ROOT"])
    if not (named / MARKER).is_file():
        return None, kb_pb2.Fault(
            rule="store", message=f"KB_ROOT names a directory that holds no store: {named}",
        )
```

with:

```python
    value = env["KB_ROOT"]
    named = Path(value)
    if not value or not (named / MARKER).is_file():
        return None, kb_pb2.Fault(
            rule="store", message=f"KB_ROOT names a directory that holds no store: {value}",
        )
```

The message keeps its words: the operator's scenario (slice 46) pins it byte for byte, and for a `KB_ROOT` given as a path it reads as before.

- [ ] **Step 4: Run it green**

```bash
.venv/bin/python -m pytest -q -m "slice-88" 2>&1 | tail -1
.venv/bin/python -m pytest -q 2>&1 | tail -1
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before -
wc -l src/kb/read.py src/kb/store.py
```

Expected: `7 passed, 189 deselected`; `14 failed, 182 passed`; seven `<` lines, the slice's rows; `120`, `211`.

- [ ] **Step 5: Checkpoint and commit**

Append the slice 88 checkpoint, noting which rows passed on their steps, and Review Focus 4 and 5 as `QUESTION FOR THE SPEC` lines with their reproductions. Set slice 88's Status to `green`.

```bash
git add src/kb tests docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 88: A read answers plainly what it cannot find, and what a filled-in link is

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 10: Slice 89, narrow what comes in to one link and one kind

**Slice plan entry:** Slice 89, capability. Unknown: none. Scenario:

- kb / follow-the-links / The client narrows the links to one link and one kind

What scratch found: it passes as soon as its two Givens exist; its When and Then were written by slice 31, and Refs has narrowed by field and by kind since then. Slice 89.2's scenario, in the same feature, is blocked and stays red.

**Files:**
- Modify: `tests/test_follow_the_links.py` (a note type, two Givens)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: the module's `WORK_ITEM_TYPE`, `WORK_ITEMS`, `DECISION`, `refs`, `write`, `define`, `create`.
- Produces: nothing later tasks use.

- [ ] **Step 1: Save the failing ids, and write the steps**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
```

Append at the end of `tests/test_follow_the_links.py`:

```python
NOTE = "note/weekly-reviews-need-cover"
NOTE_TYPE = {
    "title": "Note",
    "version": 1,
    "schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "decisions": copy.deepcopy(WORK_ITEM_TYPE["schema"]["properties"]["decisions"]),
        },
        "required": ["title"],
    },
}


@given("a note that is not a work item also points at the decision, through the same link the work items use")
def _a_note_pointing_at_the_decision(client):
    define(client, NOTE_TYPE)
    create(client, "note", {"title": "Weekly reviews need cover", "decisions": [DECISION]})


@given("one of the two work items points at the decision a second time, through a different link of its own")
def _a_work_item_pointing_twice(client):
    revised = copy.deepcopy(WORK_ITEM_TYPE["schema"])
    revised["properties"]["follows"] = {
        "type": "string", "ref": {"targets": ["decision"], "cardinality": "one", "parts": False, "on_delete": "refuse"},
    }
    changed = write(client, "schema/work-item", {"version": 2, "schema": revised}, message="Let work items follow a decision")
    assert not changed.faults, changed.faults
    changed = write(client, WORK_ITEMS[1], {"decisions": [DECISION], "follows": DECISION}, message="Follow it too")
    assert not changed.faults, changed.faults
    inward = refs(client, DECISION, depth=1, inward=True)
    assert {(found.stub.field, found.stub.id) for found in inward.reached} >= {("decisions", NOTE)}
```

The second Given's last assertion shows the note is among the links into the decision when nothing narrows them, so the Then's "nothing else" excludes something that is there.

- [ ] **Step 2: Run it**

```bash
.venv/bin/python -m pytest -q -m slice-89 2>&1 | tail -1
.venv/bin/python -m pytest -q 2>&1 | tail -1
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before -
```

Expected: `1 passed, 195 deselected` (red before the Givens on `StepDefinitionNotFoundError`); `13 failed, 183 passed`; one `<` line, `test_the_client_narrows_the_links_to_one_link_and_one_kind`. No production code changes.

- [ ] **Step 3: Checkpoint and commit**

Append the slice 89 checkpoint (passed on its Givens alone; open questions: none; slice 89.2 still blocked) and set its Status to `green`.

```bash
git add tests docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 89: Narrow what comes in to one link and one kind

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 11: Slice 89.1, which type a kind names is asked of composition alone

**Slice plan entry:** Slice 89.1, enabling. Check: the suite's summary and failing ids unchanged; `grep -nE "type_of|no_type|\.holds\(" src/kb/check.py` → no lines (3 before); `grep -n "refusals.no_type" src/kb/*.py` → lines in `composition.py` only; the probe below unchanged.

**Files:**
- Modify: `src/kb/composition.py` (new `named_type`; `kind_type` asks it)
- Modify: `src/kb/check.py` (`_with_type` asks `composition.named_type`)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `values.type_of(kind) -> ArtifactId`; `refusals.no_type(kind_name, artifact="") -> kb_pb2.Fault`.
- Produces: `composition.named_type(kind: values.Kind, corpus, artifact: str = "") -> values.ArtifactId | kb_pb2.Fault`.

- [ ] **Step 1: Save the failing ids, and run the probe before**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
```

Save as `/tmp/probe-89-1.py`:

```python
"""Slice 89.1's probe: a kind with no type, met by the check and by a List."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "tests")
from calls import CLIENT, DECISION_TYPE, create, define, listing  # noqa: E402
from kb import client as kb_client  # noqa: E402
from kb.contract import kb_pb2  # noqa: E402

root = Path(tempfile.mkdtemp()) / "store"
root.mkdir()
client = kb_client.connect(root)
client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
define(client, DECISION_TYPE)
create(client, "decision", {"title": "D one", "sections": [{"title": "Purpose", "body": "P.\n"}, {"title": "Rationale", "body": "R.\n"}]})
(root / "kb" / "invoice").mkdir()
(root / "kb" / "invoice" / "i-one.yaml").write_text(
    "id: invoice/i-one\ntype: invoice\nschema_version: 1\nrevision: 1\ntitle: I one\n")
checked = client.Validate(kb_pb2.ValidateRequest())
print("validate:", [(fault.artifact, fault.path, fault.rule, fault.message) for fault in checked.violations])
print("list invoice:", [(fault.artifact, fault.rule) for fault in listing(client, "invoice").faults])
```

```bash
.venv/bin/python /tmp/probe-89-1.py | tee /tmp/probe-89-1.before
```

Expected:

```
validate: [('invoice/i-one', '', 'kind', "a kind must name a type the store holds; the store holds no type called 'invoice'")]
list invoice: [('', 'kind')]
```

- [ ] **Step 2: composition says which type a kind names, or that it names none**

In `src/kb/composition.py`, replace `from kb import names, refusals, values` with:

```python
from kb import names, refusals, values
from kb.contract import kb_pb2
```

Replace the whole of `kind_type`:

```python
def kind_type(kind: values.Kind, corpus) -> values.ArtifactId:
    """The type a kind names. Raises Refused when the corpus holds none, since a kind must name a type the store
    holds, wherever it is given."""
    type_id = values.type_of(kind)
    if not corpus.holds(type_id):
        raise values.Refused([refusals.no_type(kind.name)])
    return type_id
```

with:

```python
def kind_type(kind: values.Kind, corpus) -> values.ArtifactId:
    """The type a kind names. Raises Refused when the corpus holds none, since a kind must name a type the store
    holds, wherever it is given."""
    found = named_type(kind, corpus)
    if isinstance(found, kb_pb2.Fault):
        raise values.Refused([found])
    return found


def named_type(kind: values.Kind, corpus, artifact: str = "") -> values.ArtifactId | kb_pb2.Fault:
    """The type a kind names, or, when the corpus holds none, the fault saying so, of the artifact named when an
    artifact claims the kind."""
    type_id = values.type_of(kind)
    if not corpus.holds(type_id):
        return refusals.no_type(kind.name, artifact=artifact)
    return type_id
```

- [ ] **Step 3: The check asks it**

In `src/kb/check.py`, replace `from kb import refusals, settled, validation, values` with `from kb import composition, settled, validation`, and in `_with_type` replace:

```python
    type_id = values.type_of(artifact_id.kind)
    if not store.holds(type_id):
        return refusals.no_type(artifact_id.kind.name, artifact=str(artifact_id))
    schema = store.load(type_id)
```

with:

```python
    type_id = composition.named_type(artifact_id.kind, store, artifact=str(artifact_id))
    if isinstance(type_id, kb_pb2.Fault):
        return type_id
    schema = store.load(type_id)
```

- [ ] **Step 4: Check**

```bash
.venv/bin/python -m pytest -q 2>&1 | tail -1
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before -
.venv/bin/python /tmp/probe-89-1.py | diff /tmp/probe-89-1.before -
grep -nE "type_of|no_type|\.holds\(" src/kb/check.py
grep -n "refusals.no_type" src/kb/*.py
wc -l src/kb/composition.py src/kb/check.py
```

Expected: `13 failed, 183 passed`; no diff; no diff; no lines; one line, `src/kb/composition.py:82`; `83`, `38`.

- [ ] **Step 5: The batch's end state**

```bash
for tag in 89.2 91 92 93 94; do echo "$tag: $(.venv/bin/python -m pytest -q -m slice-$tag 2>&1 | tail -1 | cut -d, -f1)"; done
grep -c "try:" src/kb/servicer.py
grep -nE "except (Exception|BaseException)|except:" src/kb/*.py
git diff 18f1f0b --stat -- features/
wc -l src/kb/*.py | sort -n | tail -5
```

Expected: `89.2: 1 failed`, `91: 4 failed`, `92: 2 failed`, `93: 3 failed`, `94: 3 failed` (the 13 left); `1`; no lines; nothing under `features/` changed; the largest `canonical.py` 173, `requests.py` 181, `edits.py` 182, `store.py` 211, `values.py` 226.

- [ ] **Step 6: Checkpoint and commit**

Append the slice 89.1 checkpoint (the check before and after; open questions: none) and set its Status to `green`. Then append the batch line: slices 83.1 to 89.1 green, suite 13 failed, 183 passed, next slice 89.2 if approved, otherwise slice 90, the fifth architecture review.

```bash
git add src/kb docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 89.1: Which type a kind names is asked of composition alone

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```
