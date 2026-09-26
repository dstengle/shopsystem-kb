# kb Batch 8 Implementation Plan: slices 70, 70.1, 71, 71.1, 72 and 73

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Each task is one slice of `docs/superpowers/plans/2026-09-24-kb-slices.md`. Inside a capability task, follow `shopsystem-bdd:bdd-red-green` scenario by scenario; its stop conditions, hand-back and checkpoint apply, and they override any step here that conflicts with them. An enabling task (70.1, 71.1) adds no scenario and changes no behaviour: its check is the suite's failing test ids unchanged and its structural target met.

**Goal:** The six slices after slice 69, the second architecture review:
- Each change a set makes to one artifact records the version that change left behind (slice 70).
- The reading of links, and a type read through its bases, leave `validation.py` for modules of their own (slice 70.1, enabling).
- A type built on a base carries the base's collections and the fields it shows at a glance, as it already carries its fields and sections (slice 71).
- `names.py` alone decides how an artifact's name, a link's place and a type's reference are written and read (slice 71.1, enabling).
- A link into a part counts as a link into the artifact holding it, in the count at a glance as it already does in the links coming in and in removal (slice 72).
- kb's own rules run beside JSON Schema, so faults found by different rules come back together (slice 73).

**Architecture:** kb is the Python package `kb` in `/home/vscode/shopsystem-kb`. A protobuf contract (`kb.contract`) sits in front of `KbServicer` (`servicer.py`), whose every rpc runs inside one boundary that turns `values.Refused` into that rpc's faults. `requests.py`/`values.py` convert requests; `write.py` drafts a set and only then writes; `edits.py` says what each operation does to the draft (`store.Draft`); `read.py` and `query.py` answer questions; `validation.py` holds the composed schema and kb's own checks; `names.py` owns every name; `refusals.py` makes the domain's faults; `places.py` resolves a place; `definitions.py` checks a type as it is written; `store.py` is files and git. `CLAUDE.md` is the rulebook. This plan implements each rule it touches once:
- **Draft, validate, write (rule 4).** What each operation did is settled as it is applied, in `edits.apply`, and carried on its `Change`: the version its entry records and the artifact as it left it. The write phase reads nothing and writes each artifact's file once, for the last change the set makes to it (Task 1).
- **A new concern gets a new module.** `composition.py` reads a type through what it is built on; `links.py` is the one reading of links. Both go into CLAUDE.md's module map in the task that makes them (Task 2).
- **kb's keywords are read through the composition, once.** `composition.declared(schema, corpus)` gives a type's `properties`, `parts` and `summary` with its bases', base first. Every reader of those keywords (the composed schema, naming items, ordering a file, the reading of links, a summary, an addition's collection) reads them there (Task 3).
- **Names live in one place (rule 6).** `names.py` writes and reads an artifact's name (`kind/name`), splits a link's `#`, names the kind every type is of (`schema`), and reads a `kb:` reference. `values.type_of(kind)` is the one maker of a type's name from a kind (Task 4).
- **One reading of links.** Whether a link points at an artifact is `links.points_at`, and the count at a glance now uses it too (Task 5).
- **Every fault at once.** `validation.validate` reports JSON Schema's faults and kb's own together; kb's rules skip only a node JSON Schema found misshapen (Task 6).

**Provenance:** Every code block here was assembled in a scratch clone of this repository (`/tmp/batch8/kb`, cloned at `3d231dc`, its own `.venv` from `make dev`) on 2026-09-26, and the tasks were applied in order, one commit each. The red and green results, the suite counts, the failing-id comparisons, the line counts and the Review Focus reproductions are what those runs gave. The plan was then replayed from its own text on a fresh clone (`/tmp/batch8-replay`, at `3d231dc`, its own `.venv`) by an agent that had not seen the scratch run: every "replace" text was found verbatim once (twice where it says both), every red, green, suite count, failing-id diff and line count matched, pyflakes reported nothing, and the 54 failures left were exactly the later slices listed below. Its notes on the text (four red commands whose `head` cut off pytest's summary, and a before-count in Task 3 of eleven lines where there were ten) are fixed here. This repository was not touched except to log slice 69, place its refactor slices in the slice plan, and write this plan.

**Tech Stack:** Python 3.11, setuptools (src layout), protobuf + grpcio (generated code committed; no `.proto` change in this batch), python-jsonschema 4.26 with `referencing`, ruamel.yaml 0.19 (YAML 1.2), git via subprocess, pytest 9 + pytest-bdd 8.

**Spec:** `docs/superpowers/specs/2026-09-23-kb-design.md`, in particular:
- "Journal entry": "`revision`, `schema_version`, `digest` (sha256 of the canonical bytes after the write) ... `batch`: the id of the `Apply` that wrote it".
- "Schema language": "kb's own structural rules, the section tree ..., part collections whose items carry an `id`, ... are JSON Schema fragments that kb composes with the type's schema into one effective schema per artifact"; a type built on a base by `allOf` and `$ref: kb:schema/<type>`.
- "Artifact model", Fields: "A reference is a field type"; `ref.parts`: a link may name a part inside an artifact after `#`.
- "Write path", step 4: "Collect every error; if any, stop here."

The slice plan is `docs/superpowers/plans/2026-09-24-kb-slices.md`, and the feature files are in `features/`. Each capability slice's scenarios carry `@slice-<n>`, so `.venv/bin/python -m pytest -q -m slice-70` runs one slice. `CLAUDE.md` at the repository root is binding.

## Global Constraints

- Feature files are read-only for the implementer. Only `slicing-into-increments` edits a tag line, and only `formulating-features` edits a Given, When, or Then. Any other diff under `features/` is a stop condition.
- Code only what a scenario asserts (bdd-red-green). Where the scenarios are silent, the code is silent too, and the silence goes into the checkpoint entry as an open question. The decisions this plan makes are listed below, each tied to the scenario or slice that asks for it.
- **CLAUDE.md's rules are implemented once, never per row.** No rpc in `servicer.py` gains a `try`, a check, or a branch in this batch (`grep -c "try:" src/kb/servicer.py` stays `1`). No module but `composition.py` reads a type through its bases. No module but `links.py` finds links or says what one points at. No module but `names.py` decides what a name, a link's place or a type's reference looks like.
- **Extend, never add beside.** A new concern gets a new module (`composition.py`, `links.py`), and each goes into CLAUDE.md's module map in the task that makes it. Test helpers live in `tests/calls.py`; a step two scenarios word for word share is one step definition, never two.
- **Size.** No module over 250 lines; `servicer.py` under 150. After Task 2, `validation.py` is 170 lines; after Task 6, 180. Slice 73.1 moves the store-wide check out before slice 74 adds to it.
- Errors are a typed list of `{ artifact, path, rule, message }`. A response that carries faults is a refusal, and nothing was written.
- kb is exercised through its in-process transport (`kb.client.connect`).
- `make test` runs the suite in this checkout's virtualenv (`.venv/bin/python -m pytest -q`). While any scenario is red, make's own error line comes last, so the steps run pytest directly to see the summary. A worktree needs its own `.venv` first (`make dev`).
- The contract's version stays `0.1`, `pyproject.toml` stays `0.1.0`. Version and tag are the user's call.
- Work on `main` in `/home/vscode/shopsystem-kb`. shop-knowledge pins kb at `v0.1.0`; nothing here touches or runs its suite.
- Commits: `git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit`, the message ending with the Co-Authored-By line of the model that made the commit, e.g. `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- "Append at the end of the file" means after two blank lines, as the files' top-level definitions are spaced.
- The suite prints pytest-bdd `PytestRemovedIn10Warning`s. That is the baseline, not a fault. The summary lines quoted as Expected leave out the `, N warnings in Xs` that pytest adds.
- Baseline before Task 1: `.venv/bin/python -m pytest -q` → `60 failed, 136 passed`. After Tasks 1 to 6 the suite reads `59/137`, `59/137`, `56/140`, `56/140`, `55/141` and `54/142` (failed/passed). Every failure left after Task 6 is tagged for slice 74 or later (74: 7, 75: 7, 77: 1, 78: 1, 79: 2, 80: 3, 81: 1, 82: 3, 84: 1, 85: 3, 86: 2, 87: 2, 88: 7, 89: 2, 91: 4, 92: 2, 93: 3, 94: 3), and none of those goes green early.
- An enabling task's first step saves the failing ids (`.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before`), and its check compares them after (`... | sort | diff /tmp/failing-before -` prints nothing).

## Decisions this plan makes (the spec left them open or silent)

1. **Each change settled as it is applied (slice 70).** `edits.Change` gains `left`, the artifact as that operation left it (None for a removal), and `edits.apply` fills `revision` and `schema_version` from it for a create, a write and an addition, as `_delete` already does for a removal. Each journal entry records its own change's `revision`, `schema_version`, and the digest of the canonical text of `left`: the spec's "canonical bytes after the write", taken per operation. The file is written once, with the text of the last change the set makes to that artifact; an earlier change's text is fingerprinted and never written (Review Focus 5).
2. **Two new modules (slice 70.1).** `composition.py`: `TYPE_URI` (until Task 4 moves it), `composition(schema, corpus)`, `type_schema(uri, corpus)` (was `validation._type_schema`). `links.py`: `Link`, `references(schema, corpus)`, `carried(artifact, schema, corpus)` (was `validation.links`; renamed so the module and the function do not share a name), `points_at(target, artifact_id)`. `validation.py` keeps `compose`, `registry`, `validate`, `check`, `_lands`, `_holds_part`, `_sections`. `validation._item` leaves an item with no collections of its own unchanged, rather than giving it an empty `allOf`.
3. **A base carried in full (slice 71).** `composition.declared(schema, corpus)` → `{"properties": {...}, "parts": {...}, "summary": [...]}`, read over `composition(schema, corpus)` base first; a type naming a field or collection its base names has its own; a field shown at a glance is listed once. `validation.compose(schema, corpus)` now takes the corpus and gives the shape of every collection `declared` gives. `names.items` and `names.handed_back`, `canonical.order`, `links.references` and `links.carried`, `read`'s summary and stubs, and `edits._append`'s collection check are all given `declared` in place of the type's own schema. The base's link field needs nothing new: links were already read through the composition (that row passes as soon as its steps exist).
4. **Names (slice 71.1).** In `names.py`: `TYPES = "schema"`, `TYPE_URI = "kb:"`, `written(kind, slug)`, `parted(text)`, `linked(text)`, `referred(ref)`. In `values.py`: `TYPE_KIND = Kind(names.TYPES)` and `type_of(kind) -> ArtifactId`, and `target` no longer wraps a stored link in a contract `Locator` (both `locator` and `target` go through `_located(name, path)`). `names.referred` drops what follows `#` for every caller; `referencing` already retrieves a URI without its fragment, so `composition.type_schema` answers as before.
5. **A link into a part (slice 72).** `read._inbound` counts a link by `links.points_at`, so a link into a part counts for the artifact holding it. A read of the linking artifact itself (its summary's stubs, Refs out, a whole read following links) still takes the link as a whole name and is refused (Review Focus 1).
6. **Faults together (slice 73).** `validation.validate` reports JSON Schema's faults, then kb's section rule, then kb's link rule. A kb rule reads a node only if JSON Schema reported nothing at that node or inside it, and no `type` fault at a node holding it (`validation._misread`). The section rule's node is `sections`; a link's node is its place. The Then `the artifact is rejected with both faults, each naming the artifact, the place in it and the rule broken`, which slice 7 and slice 73 share word for word, compares against the faults its When says it expects.

## Review Focus

In this project, tests are scenarios, and the feature files are the human gate, so no unit tests are added. Instead, each line below goes into the owning task's checkpoint entry as a `QUESTION FOR THE SPEC`, with the reproduction given here. Each was reproduced in scratch after all six tasks.

1. **A link into a part, read from the artifact holding the link, is refused.** Reproduction: Task 5's Given; then Read `work-item/check-the-till-float` at a glance, or Refs out of it at depth 1, or Read it whole at depth 1. Each is refused with rule `locator`, `a name is a kind and a plain name ...; 'process/open-the-shop#steps/count-the-till' is not`, since `read._summary`, `read._resolved` and `query._outward` convert a link's whole text as a name. A person expects the stub of the process (or of the step). Slice 89 follows links out of a place; no scenario reads out of a link that names one. Task 5 logs it.
2. **A create and a removal of one artifact in one set.** Reproduction: Apply `[create tag "T", delete tag/t]`. After Task 1 it raises `FileNotFoundError` at the unlink of a file the set never wrote, with one journal entry left uncommitted; before, it raised `CalledProcessError` at `git add` with two entries left. Either way a client gets a crash and debris. The batch 4 question (Review Focus 2 there) is still open. Task 1 logs it.
3. **A fault inside the section tree hides kb's section rule.** Reproduction: create a decision with `sections: [{title: Purpose}]` (no body, no Rationale). It is refused with `sections/0 required` alone; the missing Rationale is not reported until the body is given, since kb's section rule skips `sections` when JSON Schema faulted anything inside it. That is the "fix one thing, be told the next" the slice 73 scenario pins against, one level down. Task 6 logs it.
4. **A base changed under its artifacts does not make them stale.** Reproduction: define `schema/base` with a collection `notes` (items require `title`), `schema/decision` built on it, create a decision with one note; write `schema/base` at version 2 requiring `by` on each note. Validate reports `decision/d` `notes/0 required` as a violation, with nothing stale, since staleness compares only the decision type's own version. It held for a base's fields since slice 3; Task 3 extends it to collections and the fields at a glance. Task 3 logs it.
5. **An entry's digest may name bytes that never landed.** Reproduction: Task 1's When. The first entry's `digest` is the sha256 of the work item as the first change left it, which the set never writes to disk: no commit holds a file with that digest. That is the spec's "canonical bytes after the write" per operation, but a person checking an entry against the commit it sits in will find no match. Task 1 logs it.

---

### Task 1: Slice 70, each change in a set records the version it left behind

**Slice plan entry:** Slice 70, capability. Unknown: can each operation's own result be settled in the draft as it is applied, while the artifact is still written once, as the set leaves it? Scenario:

- kb / make-several-changes-in-one-go / Two changes to one artifact in one set each leave their own entry

**Files:**
- Modify: `src/kb/edits.py` (`Change.left`; `apply` settles each change)
- Modify: `src/kb/write.py` (`Landing`, `land`, `_drafted`, `_serialised`, `_written`, new `_file`)
- Modify: `tests/test_make_several_changes_in_one_go.py` (one When, three Thens, appended)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: in the test module, `WORK_ITEM`, `_journal(root)`, `apply`, `replacement`, `read`, and the Background's `client` (a work item at version 1).
- Produces: `edits.Change(op, artifact_id, path="", item="", revision=0, schema_version=0, left: dict | None = None)`, with `revision` and `schema_version` set for every op. `write.Landing(change: Change, text: str | None, last: bool)`. `write._serialised(changes: list[Change]) -> list[Landing]` (no draft). `write._drafted(store, operations) -> list[Change]`.

- [ ] **Step 1: The steps**

Append at the end of `tests/test_make_several_changes_in_one_go.py`:

```python
@when("the client asks, in one go, for the work item to be changed twice, saying which role and why", target_fixture="applied")
def _change_the_work_item_twice(client):
    return apply(client, [replacement(WORK_ITEM, {"decisions": []}), replacement(WORK_ITEM, {})],
                 message="Change the work item twice")


@then("the store's history holds an entry for each of the two changes")
def _an_entry_for_each_change(root, applied):
    assert not applied.faults, applied.faults
    in_set = [entry for entry in _journal(root) if entry["batch"] == applied.batch]
    assert [(entry["op"], entry["artifact"]) for entry in in_set] == [("write", WORK_ITEM), ("write", WORK_ITEM)]


@then("each entry records the version that change left behind")
def _each_entry_its_own_version(root, applied):
    in_set = [entry for entry in _journal(root) if entry["batch"] == applied.batch]
    assert [entry["revision"] for entry in in_set] == [2, 3]
    assert [(result.id, result.revision) for result in applied.results] == [(WORK_ITEM, 2), (WORK_ITEM, 3)]


@then("the work item's version has gone up by two")
def _two_versions_on(client):
    assert read(client, WORK_ITEM).revision == 3
```

- [ ] **Step 2: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-70 2>&1 | grep -m1 -E "^E  "
.venv/bin/python -m pytest -q -m slice-70 2>&1 | tail -1
```

Expected: `E       assert [3, 3] == [2, 3]`, `1 failed`: both entries record the version the set left, read from the draft after every operation.

- [ ] **Step 3: Each change settled as it is applied, in `edits.py`**

In `src/kb/edits.py`, replace

```python
class Change(NamedTuple):
    """What one operation did, to which artifact, at which place in it, and, for an item added, the item's name. A
    removal carries the version its entry records and the version of the type it was last checked against."""
    op: str
    artifact_id: ArtifactId
    path: str = ""
    item: str = ""
    revision: int = 0
    schema_version: int = 0


def apply(draft: Draft, operation) -> Change:
    """One operation applied to the draft. Returns what it did; raises Refused."""
    if isinstance(operation, requests.Create):
        return Change("create", _create(draft, operation))
    if isinstance(operation, requests.Add):
        return _append(draft, operation)
    if isinstance(operation, requests.Remove):
        return _delete(draft, operation)
    return Change("write", _replace(draft, operation))
```

with

```python
class Change(NamedTuple):
    """What one operation did, to which artifact, at which place in it, and, for an item added, the item's name; the
    version its entry records and the version of the type it was last checked against; and the artifact as this
    operation left it, None for a removal."""
    op: str
    artifact_id: ArtifactId
    path: str = ""
    item: str = ""
    revision: int = 0
    schema_version: int = 0
    left: dict | None = None


def apply(draft: Draft, operation) -> Change:
    """One operation applied to the draft. Returns what it did, settled as it did it; raises Refused."""
    if isinstance(operation, requests.Remove):
        return _delete(draft, operation)
    change = _changed(draft, operation)
    left = draft.artifact(change.artifact_id)
    return change._replace(revision=left["revision"], schema_version=left["schema_version"], left=left)


def _changed(draft: Draft, operation) -> Change:
    if isinstance(operation, requests.Create):
        return Change("create", _create(draft, operation))
    if isinstance(operation, requests.Add):
        return _append(draft, operation)
    return Change("write", _replace(draft, operation))
```

`left` is safe to hold: `_revise` and `_create` put a new dict in the draft each time, and `_content_of` deep-copies before anything is changed, so a later operation never mutates an earlier one's `left`.

- [ ] **Step 4: The write phase writes what each change settled, in `write.py`**

In `src/kb/write.py`, replace

```python
class Landing(NamedTuple):
    """A change as it will be written: its canonical text, None for a removal, and the versions its entry records."""
    change: Change
    text: str | None
    revision: int
    schema_version: int
```

with

```python
class Landing(NamedTuple):
    """A change as it will be written: its canonical text as the change left the artifact, None for a removal, and
    whether the file is written with it, which it is only for the last change the set makes to that artifact."""
    change: Change
    text: str | None
    last: bool
```

Replace

```python
    draft, changes = _drafted(store, operations)
    return _written(store, _serialised(draft, changes), signed)
```

with

```python
    changes = _drafted(store, operations)
    return _written(store, _serialised(changes), signed)
```

Replace `def _drafted(store: Store, operations: list) -> tuple[Draft, list[Change]]:` with `def _drafted(store: Store, operations: list) -> list[Change]:`, and at the end of that function replace `    return draft, changes` with `    return changes`.

Replace the whole of `_serialised`

```python
def _serialised(draft: Draft, changes: list[Change]) -> list[Landing]:
    """Each change as it will be written, settled from the draft; refused if any cannot be written."""
    landings, found = [], []
    for change in changes:
        if change.op == "delete":
            landings.append(Landing(change, None, change.revision, change.schema_version))
            continue
        artifact = draft.artifact(change.artifact_id)
        try:
            landings.append(Landing(change, canonical.dump(artifact), artifact["revision"], artifact["schema_version"]))
        except canonical.NotCanonical as fault:
            found.append(refusals.unwritable(change.artifact_id, str(fault)))
    if found:
        raise Refused(found)
    return landings
```

with

```python
def _serialised(changes: list[Change]) -> list[Landing]:
    """Each change as it will be written, settled as the change left its artifact; refused if any cannot be written."""
    last = {change.artifact_id: index for index, change in enumerate(changes)}
    landings, found = [], []
    for index, change in enumerate(changes):
        try:
            text = None if change.left is None else canonical.dump(change.left)
        except canonical.NotCanonical as fault:
            found.append(refusals.unwritable(change.artifact_id, str(fault)))
            continue
        landings.append(Landing(change, text, last[change.artifact_id] == index))
    if found:
        raise Refused(found)
    return landings
```

In `_written`, replace

```python
    for seq, (change, text, revision, schema_version) in enumerate(landings, start=1):
        if text is None:
            path = store.remove(change.artifact_id)
        else:
            path = store.save(change.artifact_id, text)
        entry = journal.write(
            store.dir, signed=signed, op=change.op, artifact=str(change.artifact_id), path=change.path,
            revision=revision, schema_version=schema_version, text=text, seq=seq, batch=batch,
        )
        batch = batch or entry.stem
        written += [path, entry]
        results.append(Result(change.artifact_id, revision, change.item))
```

with

```python
    for seq, (change, text, last) in enumerate(landings, start=1):
        if last:
            written.append(_file(store, change.artifact_id, text))
        entry = journal.write(
            store.dir, signed=signed, op=change.op, artifact=str(change.artifact_id), path=change.path,
            revision=change.revision, schema_version=change.schema_version, text=text, seq=seq, batch=batch,
        )
        batch = batch or entry.stem
        written.append(entry)
        results.append(Result(change.artifact_id, change.revision, change.item))
```

Append at the end of the file:

```python
def _file(store: Store, artifact_id: ArtifactId, text: str | None):
    """The artifact's file written with its text, or taken out when there is none; where it is."""
    return store.remove(artifact_id) if text is None else store.save(artifact_id, text)
```

`Draft` is still imported: `_drafted` makes one.

- [ ] **Step 5: Run it green**

```bash
.venv/bin/python -m pytest -q -m slice-70 2>&1 | tail -1
.venv/bin/python -m pytest -q 2>&1 | tail -1
wc -l src/kb/edits.py src/kb/write.py
```

Expected: `1 passed`; `59 failed, 137 passed`; `170` and `121`.

- [ ] **Step 6: Checkpoint and commit**

Append the slice 70 checkpoint, with Review Focus 2 and 5 as `QUESTION FOR THE SPEC` lines, and set slice 70's Status to `green`.

```bash
git add src/kb tests docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 70: Each change in a set records the version it left behind

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Slice 70.1, one reading of links stands apart from the checks

**Slice plan entry:** Slice 70.1, enabling. Unknown: can the reading of links leave `validation.py` when it reads a type through its bases, as validation's own checks do, without two modules importing each other? Check: the suite's failing ids unchanged; `validation.py` under 200 lines (246 before); `grep -nE "validation\.(links|points_at|references|Link)\b" src/kb/*.py` → no lines (8 before); no import cycle; no empty `allOf` on an item's composed schema; a module-map row for each new module.

The answer to the unknown: the composition goes into a module of its own, `composition.py`, which both `links.py` and `validation.py` import, and which imports neither.

**Files:**
- Create: `src/kb/composition.py`, `src/kb/links.py`
- Modify: `src/kb/validation.py` (seven definitions out, imports, `_item`)
- Modify: `src/kb/edits.py`, `src/kb/read.py`, `src/kb/query.py`, `src/kb/definitions.py` (callers)
- Modify: `CLAUDE.md` (module map), `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: nothing from Task 1.
- Produces: `composition.TYPE_URI`; `composition.composition(schema: dict, corpus) -> list[dict]`; `composition.type_schema(uri: str, corpus) -> dict` (raises `referencing.exceptions.NoSuchResource`). `links.Link(field, place, target, ref)`; `links.references(schema: dict, corpus) -> dict[str, dict]`; `links.carried(artifact: dict, schema: dict, corpus) -> list[Link]`; `links.points_at(target: str, artifact_id) -> bool`. `validation.compose(schema: dict) -> dict` (unchanged here; Task 3 adds `corpus`).

- [ ] **Step 1: Save the failing ids**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
wc -l < /tmp/failing-before
grep -nE "validation\.(links|points_at|references|Link)\b" src/kb/*.py | wc -l
```

Expected: `59`; `8`.

- [ ] **Step 2: `composition.py`**

Create `src/kb/composition.py`:

```python
"""A type read through what it is built on: the schemas of its composition, base first, and the type a kb: reference
names. kb's own keywords are read through the composition, so a type built on a base carries the base's first."""
from referencing.exceptions import NoSuchResource

from kb import values
from kb.values import Kind

TYPE_URI = "kb:"


def composition(schema: dict, corpus) -> list[dict]:
    """The schema and every schema it is built on, base first: its allOf members in order, a whole type it names by
    $ref followed to that type's schema, and last the schema itself. kb's keywords are read through this list."""
    built_on = []
    for member in schema.get("allOf", []):
        built_on += composition(member, corpus)
    ref = schema.get("$ref")
    if isinstance(ref, str) and ref.startswith(TYPE_URI) and "#" not in ref:
        built_on += composition(type_schema(ref, corpus), corpus)
    return [*built_on, schema]


def type_schema(uri: str, corpus) -> dict:
    """The JSON Schema of the type a kb: URI names, its name checked as any other name is. NoSuchResource if none."""
    try:
        schema_id = values.artifact_id(uri.removeprefix(TYPE_URI)) if uri.startswith(TYPE_URI) else None
    except values.Refused:
        schema_id = None
    if schema_id is None or schema_id.kind != Kind("schema") or not corpus.holds(schema_id):
        raise NoSuchResource(ref=uri)
    return corpus.artifact(schema_id)["schema"]
```

- [ ] **Step 3: `links.py`**

Create `src/kb/links.py`:

```python
"""The one reading of links: every link an artifact carries, wherever it sits, read through its type's composition,
and whether a link points at an artifact. The checks, removal, reads and walks all read links here."""
from typing import NamedTuple

from kb.composition import composition


class Link(NamedTuple):
    """One link an artifact carries: the field that holds it, the place of that field in the artifact, the name it
    points at, and the field's `ref`, which says what it may land on."""
    field: str
    place: str
    target: str
    ref: dict


def references(schema: dict, corpus) -> dict[str, dict]:
    """Every field that links to other artifacts, from every schema in the composition, base first, with its `ref`."""
    return {
        name: field["ref"]
        for part in composition(schema, corpus)
        for name, field in part.get("properties", {}).items()
        if "ref" in field
    }


def carried(artifact: dict, schema: dict, corpus) -> list[Link]:
    """Every link an artifact carries, wherever it sits: in its own fields, and in the fields of each item of each of
    its collections, at every depth."""
    return _links_in(artifact, references(schema, corpus), schema.get("parts", {}), "", corpus)


def _links_in(node: dict, refs: dict[str, dict], parts: dict, at: str, corpus) -> list[Link]:
    """The links in one node, an artifact or an item, its place in the artifact before each of theirs."""
    found = []
    for field, ref in refs.items():
        value = node.get(field)
        if isinstance(value, list):
            found += [Link(field, f"{at}{field}/{index}", target, ref) for index, target in enumerate(value)]
        elif value is not None:
            found.append(Link(field, f"{at}{field}", value, ref))
    for collection, part in parts.items():
        items = node.get(collection)
        if not isinstance(items, list):
            continue
        item_schema = part.get("items", {})
        item_refs = references(item_schema, corpus)
        for index, item in enumerate(items):
            if isinstance(item, dict):
                found += _links_in(item, item_refs, item_schema.get("parts", {}), f"{at}{collection}/{index}/", corpus)
    return found


def points_at(target: str, artifact_id) -> bool:
    """Whether a link lands on the artifact or on a part inside it."""
    return target.partition("#")[0] == str(artifact_id)
```

These are `validation.py`'s definitions moved as they stand, `links` renamed `carried`.

- [ ] **Step 4: `validation.py` keeps the composed schema and the checks**

In `src/kb/validation.py`, delete these definitions whole, each from its `def` or `class` line to the blank lines before the next definition: `_type_schema`, `references`, `Link`, `links`, `_links_in`, `points_at`, `composition`.

Replace the module docstring and imports

```python
"""Schema validation: the type's JSON Schema composed with kb's own structural rules, checked in one pass, then
what the schema language cannot say, checked in code: required sections in their declared order, and links that
land on an artifact the corpus holds, of a kind the type allows.

kb's keywords are read through the type's composition, so a type built on a base carries the base's first.
"""
from typing import NamedTuple

from jsonschema import Draft202012Validator
from referencing import Registry
from referencing.exceptions import NoSuchResource
from referencing.jsonschema import DRAFT202012

from kb import canonical, values
from kb.contract import kb_pb2
from kb.store import Damaged, Store
from kb.values import Kind

TYPE_URI = "kb:"
```

with

```python
"""Schema validation: the type's JSON Schema composed with kb's own structural rules, checked in one pass, then
what the schema language cannot say, checked in code: required sections in their declared order, and links that
land on an artifact the corpus holds, of a kind the type allows. kb's keywords are read through kb.composition.
"""
from jsonschema import Draft202012Validator
from referencing import Registry
from referencing.jsonschema import DRAFT202012

from kb import canonical, links, values
from kb.composition import composition, type_schema
from kb.contract import kb_pb2
from kb.store import Damaged, Store
from kb.values import Kind
```

Replace `create_resource(_type_schema(uri, corpus))` with `create_resource(type_schema(uri, corpus))`, and `    for link in links(content, schema, corpus):` with `    for link in links.carried(content, schema, corpus):`.

Replace

```python
def _item(item_schema: dict) -> dict:
    return {**item_schema, "allOf": [*item_schema.get("allOf", []), *_collections(item_schema)]}
```

with

```python
def _item(item_schema: dict) -> dict:
    """An item's schema with the shape of each collection it declares beside it; unchanged when it declares none."""
    collections = _collections(item_schema)
    if not collections:
        return item_schema
    return {**item_schema, "allOf": [*item_schema.get("allOf", []), *collections]}
```

- [ ] **Step 5: The callers**

In `src/kb/edits.py`: replace `from kb import canonical, definitions, names, places, refusals, requests, validation, values` with `from kb import canonical, definitions, links, names, places, refusals, requests, validation, values`; replace `validation.links(draft.artifact(other_id), schema, draft)` with `links.carried(draft.artifact(other_id), schema, draft)`; replace `validation.points_at(link.target, locator.id)` with `links.points_at(link.target, locator.id)`.

In `src/kb/read.py`: replace `from kb import canonical, refusals, validation, values` with `from kb import canonical, links, refusals, values`; replace `validation.links(found, schema, store)` with `links.carried(found, schema, store)`, `validation.references(` with `links.references(`, and `validation.links(other, schema, store)` with `links.carried(other, schema, store)`.

In `src/kb/query.py`: replace `from kb import journal, read, refusals, search, validation, values` with `from kb import journal, links, read, refusals, search, values`; replace `validation.links(artifact, schema, store)` with `links.carried(artifact, schema, store)`, `validation.links(other, schema, store)` with `links.carried(other, schema, store)`, and `validation.points_at(link.target, artifact_id)` with `links.points_at(link.target, artifact_id)`.

In `src/kb/definitions.py`: replace `from kb.validation import TYPE_URI` with `from kb.composition import TYPE_URI`.

- [ ] **Step 6: The module map**

In `CLAUDE.md`, insert before the row beginning `` | `definitions.py` | ``:

```markdown
| `composition.py` | a type read through what it is built on: its composition, base first, and the type a `kb:` reference names | checks, file access |
| `links.py` | the one reading of links: every link an artifact carries, wherever it sits, and whether a link points at an artifact | checks, file access |
```

- [ ] **Step 7: The check**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before -
.venv/bin/python -m pytest -q 2>&1 | tail -1
wc -l src/kb/validation.py src/kb/links.py src/kb/composition.py
grep -nE "validation\.(links|points_at|references|Link)\b" src/kb/*.py
grep -nE "^from kb|^import kb" src/kb/composition.py src/kb/links.py
.venv/bin/python -c "from kb import validation; print(validation.compose({'parts': {'s': {'items': {'type': 'object'}}}}))" | grep -c "'allOf': \[\]"
```

Expected: no diff; `59 failed, 137 passed`; `170`, `56` and `31`; no lines; `composition.py`'s two lines import from `kb.values` and `links.py`'s one from `kb.composition` (so no cycle: neither imports `validation`, `read`, `query` or `edits`); `0`.

- [ ] **Step 8: Checkpoint and commit**

Append the slice 70.1 checkpoint (the check's results, before and after), and set slice 70.1's Status to `green`.

```bash
git add src/kb CLAUDE.md docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 70.1: One reading of links stands apart from the checks

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Slice 71, a base is carried in full

**Slice plan entry:** Slice 71, capability. Unknown: can collections and the fields shown at a glance be read through a type's composition, as its fields and sections already are? Scenario (an outline of three rows):

- kb / define-a-type / A type built on a base carries everything the base declares, of every kind

**Files:**
- Modify: `src/kb/composition.py` (`declared`)
- Modify: `src/kb/validation.py` (`compose`, `_collections`, `_item` take the corpus and read `declared`)
- Modify: `src/kb/links.py`, `src/kb/edits.py`, `src/kb/read.py` (read `declared`)
- Modify: `tests/test_define_a_type.py` (`DECISION_ON_BASE_TYPE` gains a field of its own shown at a glance; one Given, three Thens, appended)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: Task 2's `composition.composition`, `links.references`, `links.carried`.
- Produces: `composition.declared(schema: dict, corpus) -> dict` with keys `properties` (dict), `parts` (dict), `summary` (list). `validation.compose(schema: dict, corpus) -> dict`. `names.items(declared, content, keep_named)` and `names.handed_back(declared, content, held)` are given `declared` (their signatures do not change: they read its `parts`). `canonical.order(artifact, declared)` likewise reads `properties` and `parts`.

- [ ] **Step 1: The steps**

In `tests/test_define_a_type.py`, replace `from kb import canonical` with

```python
from kb import canonical
from kb.content import loads
```

In `DECISION_ON_BASE_TYPE`, replace

```python
        "properties": {"title": {"type": "string"}},
        "required": ["title"],
        "sections": [{"title": "Rationale"}],
    },
}
```

with

```python
        "properties": {"title": {"type": "string"}, "outcome": {"type": "string"}},
        "required": ["title"],
        "sections": [{"title": "Rationale"}],
        "summary": ["outcome"],
    },
}
```

(Slice 3's scenario defines the same type; `outcome` is optional, so it is unaffected.)

Append at the end of the file:

```python
LINK = {"type": "string", "ref": {"targets": ["tag"], "cardinality": "one", "parts": False, "on_delete": "refuse"}}

BASES = {
    "a collection of notes every artifact may carry": {
        "type": "object",
        "parts": {"notes": {"items": {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]}}},
    },
    "which fields are shown at a glance": {
        "type": "object", "properties": {"owner": {"type": "string"}}, "summary": ["owner"],
    },
    "a link field every artifact may carry": {"type": "object", "properties": {"about": LINK}},
}

RATIONALE = [{"title": "Rationale", "body": "Costs move weekly.\n"}]


@given(parsers.re(f"a base type declaring (?P<declared>{'|'.join(map(re.escape, BASES))})"))
def _a_base_type_declaring(client, declared):
    define(client, {"title": "Base", "version": 1, "schema": BASES[declared]})


@then("a decision of that type can be given notes, and each note is named by the store")
def _given_notes_named_by_the_store(client):
    created = create(client, "decision", {
        "title": "Price reviews happen weekly", "sections": RATIONALE,
        "notes": [{"title": "Check the costs"}, {"title": "Ask the supplier"}],
    })
    notes = loads(read(client, created.id, whole=True).content)["notes"]
    assert [(note["id"], note["title"]) for note in notes] == [
        ("check-the-costs", "Check the costs"), ("ask-the-supplier", "Ask the supplier"),
    ]


@then("reading a decision of that type at a glance shows the base's fields as well as the type's own")
def _the_bases_fields_at_a_glance(client):
    created = create(client, "decision", {
        "title": "Price reviews happen weekly", "owner": "shopkeeper", "outcome": "Weekly", "sections": RATIONALE,
    })
    assert loads(read(client, created.id).content) == {"owner": "shopkeeper", "outcome": "Weekly"}


@then("a decision of that type pointing through that field at a kind the base does not allow is rejected")
def _a_link_through_the_base_refused(client):
    other = create(client, "decision", {"title": "Prices are reviewed monthly", "sections": RATIONALE})
    refused = request(client, "decision", "Price reviews happen weekly", {"about": other.id, "sections": RATIONALE})
    assert (refused.id, refused.revision) == ("", 0)
    assert [(fault.artifact, fault.path, fault.rule) for fault in refused.faults] == [
        ("decision/price-reviews-happen-weekly", "about", "ref"),
    ]
```

The When, `the client defines a decision type built on that base, adding a rationale section of its own`, is slice 3's, word for word; it is not defined again.

- [ ] **Step 2: Run it red**

```bash
.venv/bin/python -m pytest -q -m "slice-71 or slice-3" 2>&1 | grep -E "^E +(KeyError|AssertionError)"
.venv/bin/python -m pytest -q -m "slice-71 or slice-3" 2>&1 | tail -1
```

Expected: `KeyError: 'id'` (the notes were never named) and `AssertionError: assert {'outcome': 'Weekly'} == {'owner': 'sh...me': 'Weekly'}` (the base's field not shown); `2 failed, 2 passed`. The passing two are slice 3 and the link row: links have been read through the composition since slice 64. That row is still this slice's, as a row of its outline.

- [ ] **Step 3: `declared`, in `composition.py`**

Append at the end of `src/kb/composition.py`:

```python
def declared(schema: dict, corpus) -> dict:
    """kb's own keywords as a type declares them together with everything it is built on, base first: its fields
    (`properties`), its collections (`parts`) and the fields shown at a glance (`summary`). A type naming a field or
    a collection its base names too has its own."""
    whole = {"properties": {}, "parts": {}, "summary": []}
    for part in composition(schema, corpus):
        whole["properties"].update(part.get("properties", {}))
        whole["parts"].update(part.get("parts", {}))
        whole["summary"] += [name for name in part.get("summary", []) if name not in whole["summary"]]
    return whole
```

- [ ] **Step 4: The composed schema carries every collection declared**

In `src/kb/validation.py`, replace `from kb.composition import composition, type_schema` with `from kb.composition import composition, declared, type_schema`.

Replace

```python
def compose(schema: dict) -> dict:
    """One effective schema: the type's, with kb's structural rules and the shape of each collection it declares
    beside it under allOf.
```

with

```python
def compose(schema: dict, corpus) -> dict:
    """One effective schema: the type's, with kb's structural rules and the shape of each collection it and its bases
    declare beside it under allOf.
```

Replace `        "allOf": [*schema.get("allOf", []), STRUCTURE, *_collections(schema)],` with `        "allOf": [*schema.get("allOf", []), STRUCTURE, *_collections(schema, corpus)],`.

Replace

```python
def _collections(schema: dict) -> list[dict]:
    """The collections a schema declares, each a list whose items fit the item's type, and the collections that
    type declares in turn."""
    parts = schema.get("parts", {})
    if not parts:
        return []
    return [{"properties": {
        name: {"type": "array", "items": _item(part.get("items", {}))} for name, part in parts.items()
    }}]


def _item(item_schema: dict) -> dict:
    """An item's schema with the shape of each collection it declares beside it; unchanged when it declares none."""
    collections = _collections(item_schema)
```

with

```python
def _collections(schema: dict, corpus) -> list[dict]:
    """The collections a schema and its bases declare, each a list whose items fit the item's type, and the
    collections that type declares in turn."""
    parts = declared(schema, corpus)["parts"]
    if not parts:
        return []
    return [{"properties": {
        name: {"type": "array", "items": _item(part.get("items", {}), corpus)} for name, part in parts.items()
    }}]


def _item(item_schema: dict, corpus) -> dict:
    """An item's schema with the shape of each collection it declares beside it; unchanged when it declares none."""
    collections = _collections(item_schema, corpus)
```

Replace `Draft202012Validator(compose(schema), registry=registry(corpus))` with `Draft202012Validator(compose(schema, corpus), registry=registry(corpus))`.

- [ ] **Step 5: Every other reader of those keywords reads `declared`**

In `src/kb/links.py`, replace `from kb.composition import composition` with `from kb.composition import declared`, and replace

```python
    return {
        name: field["ref"]
        for part in composition(schema, corpus)
        for name, field in part.get("properties", {}).items()
        if "ref" in field
    }
```

with

```python
    return {name: field["ref"] for name, field in declared(schema, corpus)["properties"].items() if "ref" in field}
```

Replace `    return _links_in(artifact, references(schema, corpus), schema.get("parts", {}), "", corpus)` with `    return _links_in(artifact, references(schema, corpus), declared(schema, corpus)["parts"], "", corpus)`, and `                found += _links_in(item, item_refs, item_schema.get("parts", {}), f"{at}{collection}/{index}/", corpus)` with `                found += _links_in(item, item_refs, declared(item_schema, corpus)["parts"], f"{at}{collection}/{index}/", corpus)`.

In `src/kb/edits.py`, replace `from kb import canonical, definitions, links, names,` with `from kb import canonical, composition, definitions, links, names,` (the rest of that line unchanged). In `_create`, replace

```python
    names.items(schema["schema"], content, keep_named=False)
    artifact = {
        **content,
        "id": str(artifact_id), "type": kind.name,
        "schema_version": schema["version"], "revision": 1, "title": creation.title,
    }
    draft.put(artifact_id, canonical.order(artifact, schema["schema"]))
```

with

```python
    declared = composition.declared(schema["schema"], draft)
    names.items(declared, content, keep_named=False)
    artifact = {
        **content,
        "id": str(artifact_id), "type": kind.name,
        "schema_version": schema["version"], "revision": 1, "title": creation.title,
    }
    draft.put(artifact_id, canonical.order(artifact, declared))
```

In `_append`, replace

```python
    if spot.holder is not content or spot.key not in draft.schema(locator.id.kind)["schema"].get("parts", {}):
```

with

```python
    collections = composition.declared(draft.schema(locator.id.kind)["schema"], draft)["parts"]
    if spot.holder is not content or spot.key not in collections:
```

In `_revise`, replace

```python
    schema = draft.schema(artifact_id.kind)
    held = {collection: {item.get("id") for item in current.get(collection, [])}
            for collection in schema["schema"].get("parts", {})}
    faults = [refusals.misnamed(artifact_id, found) for found in names.handed_back(schema["schema"], content, held)]
```

with

```python
    schema = draft.schema(artifact_id.kind)
    declared = composition.declared(schema["schema"], draft)
    held = {collection: {item.get("id") for item in current.get(collection, [])} for collection in declared["parts"]}
    faults = [refusals.misnamed(artifact_id, found) for found in names.handed_back(declared, content, held)]
```

and in the same function replace `    names.items(schema["schema"], content, keep_named=True)` with `    names.items(declared, content, keep_named=True)` and `    draft.put(artifact_id, canonical.order(artifact, schema["schema"]))` with `    draft.put(artifact_id, canonical.order(artifact, declared))`.

In `src/kb/read.py`, replace `from kb import canonical, links, refusals, values` with `from kb import canonical, composition, links, refusals, values`. In `stub`, replace `        fields=dumps(_summary_fields(target, schema)),` with `        fields=dumps(_summary_fields(target, composition.declared(schema, store))),`. In `_summary`, replace

```python
    schema = store.schema(locator.id.kind)["schema"]
    response = _response(found, dumps(_summary_fields(found, schema)))
```

with

```python
    schema = store.schema(locator.id.kind)["schema"]
    declared = composition.declared(schema, store)
    response = _response(found, dumps(_summary_fields(found, declared)))
```

and `    for collection in schema.get("parts", {}):` with `    for collection in declared["parts"]:`. Replace

```python
def _summary_fields(found: dict, schema: dict) -> dict:
    return {name: found[name] for name in schema.get("summary", []) if name in found}
```

with

```python
def _summary_fields(found: dict, declared: dict) -> dict:
    return {name: found[name] for name in declared["summary"] if name in found}
```

- [ ] **Step 6: Run it green**

```bash
grep -nE 'schema\.get\("(parts|summary)"|\]\.get\("(parts|summary)"' src/kb/*.py
.venv/bin/python -m pytest -q -m "slice-71 or slice-3" 2>&1 | tail -1
.venv/bin/python -m pytest -q 2>&1 | tail -1
wc -l src/kb/composition.py src/kb/validation.py
```

Expected: three lines, `canonical.py`'s `parts = schema.get("parts", {})` in `order` and `names.py`'s two `for collection in schema.get("parts", {}):` in `items` and `handed_back`, each a function now given `declared` (ten lines before this task, in `edits.py`, `read.py`, `links.py` and `validation.py` too); `4 passed`; `56 failed, 140 passed`; `43` and `170`.

- [ ] **Step 7: Checkpoint and commit**

Append the slice 71 checkpoint, with Review Focus 4 as a `QUESTION FOR THE SPEC` line, and set slice 71's Status to `green`.

```bash
git add src/kb tests docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 71: A base is carried in full

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Slice 71.1, an artifact's name is written and read in one place

**Slice plan entry:** Slice 71.1, enabling. Unknown: can `names.py` own the written form of a name while the values that carry a name are made in `values.py`, which imports `names.py`? Check: the suite's failing ids unchanged; `grep -nE 'kind\.name\}/|\{self\.kind\.name\}|partition\("[/#]"\)|Kind\("schema"\)|"kb:"|TYPE_URI|kb_pb2\.Locator\(' src/kb/*.py | grep -v "^src/kb/names.py\|^src/kb/contract"` → no lines (21 before); `names.py` still imports nothing that reads or writes.

The answer to the unknown: `names.py` deals in text only (a kind's name, a name, a place), and `values.py` wraps what it gives in `Kind` and `ArtifactId`. `values.type_of(kind)` is the one maker of a type's name.

**Files:**
- Modify: `src/kb/names.py` (`TYPES`, `TYPE_URI`, `written`, `parted`, `linked`, `referred`)
- Modify: `src/kb/values.py` (`ArtifactId.__str__`, `TYPE_KIND`, `type_of`, `artifact_id`, `locator`/`target`/`_located`, `named`)
- Modify: `src/kb/requests.py`, `src/kb/store.py`, `src/kb/write.py`, `src/kb/edits.py`, `src/kb/validation.py`, `src/kb/links.py`, `src/kb/composition.py`, `src/kb/definitions.py`
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: Task 3's `composition.py` and `links.py`.
- Produces: `names.TYPES = "schema"`, `names.TYPE_URI = "kb:"`; `names.written(kind: str, slug: str) -> str`; `names.parted(text: str) -> tuple[str, str]`; `names.linked(text: str) -> tuple[str, str]`; `names.referred(ref: str) -> tuple[str, str] | None` (the type's written name, and `#...` or `""`). `values.TYPE_KIND: Kind`; `values.type_of(kind: Kind) -> ArtifactId`. `composition.TYPE_URI` is gone.

- [ ] **Step 1: Save the failing ids and count**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort > /tmp/failing-before
G='kind\.name\}/|\{self\.kind\.name\}|partition\("[/#]"\)|Kind\("schema"\)|"kb:"|TYPE_URI|kb_pb2\.Locator\('
grep -nE "$G" src/kb/*.py | grep -v "^src/kb/names.py\|^src/kb/contract" | wc -l
```

Expected: 56 ids saved; `21`.

- [ ] **Step 2: `names.py` owns the written forms**

In `src/kb/names.py`, replace

```python
"""Names: the grammar of an artifact's and an item's name, the name a title gives, and the numbering that keeps a name
free. Nothing here reads or writes; whether a name is taken is asked of the caller."""
import re
from typing import NamedTuple

PLAIN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
```

with

```python
"""Names: the grammar of an artifact's and an item's name, how an artifact's name is written and read, how a link
names a place inside one and a type is referred to, the name a title gives, and the numbering that keeps a name free.
Nothing here reads or writes; whether a name is taken is asked of the caller."""
import re
from typing import NamedTuple

PLAIN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")

TYPES = "schema"
TYPE_URI = "kb:"


def written(kind: str, slug: str) -> str:
    """An artifact's name as it is written: its kind, a slash, and its own name."""
    return f"{kind}/{slug}"


def parted(text: str) -> tuple[str, str]:
    """A written name read back as its kind and its own name, neither yet checked."""
    kind, _, slug = text.partition("/")
    return kind, slug


def linked(text: str) -> tuple[str, str]:
    """A link as a field holds it read as the name it points at and, after `#`, the place inside that artifact."""
    name, _, place = text.partition("#")
    return name, place


def referred(ref: str) -> tuple[str, str] | None:
    """What a `kb:` reference names: the written name of a type, and what follows it from `#` on, empty when the
    reference is to the whole type. None for a reference that is not kb's."""
    if not ref.startswith(TYPE_URI):
        return None
    name, mark, fragment = ref.removeprefix(TYPE_URI).partition("#")
    return name, mark + fragment
```

`referred` keeps the `#` with the fragment, so `kb:schema/a#` (an empty fragment) is still not a whole type, as `"#" not in ref` said before.

- [ ] **Step 3: `values.py` wraps them**

In `src/kb/values.py`, replace

```python
    def __str__(self) -> str:
        return f"{self.kind.name}/{self.slug}"
```

with

```python
    def __str__(self) -> str:
        return names.written(self.kind.name, self.slug)


TYPE_KIND = Kind(names.TYPES)


def type_of(kind: Kind) -> ArtifactId:
    """The name of the type the artifacts of a kind are of."""
    return ArtifactId(TYPE_KIND, kind.name)
```

Replace `    kind_name, _, slug = text.partition("/")` with `    kind_name, slug = names.parted(text)`, and `    at = f"{kind.name}/{names.slug(title)}"` with `    at = names.written(kind.name, names.slug(title))`.

Replace

```python
def locator(request: kb_pb2.Locator) -> Locator:
    """A locator's name and its place, each checked; both faults when both fail."""
    faults = []
    try:
        converted = artifact_id(request.id)
    except Refused as refused:
        faults += refused.faults
    place = tuple(request.path.split("/")) if request.path else ()
    if not all(names.plain(part) for part in place):
        faults.append(kb_pb2.Fault(
            artifact=request.id, path=request.path, rule="locator",
            message=f"a place inside an artifact is named by parts of the same plain alphabet, or a collection and an item in it; {request.path!r} is not",
        ))
    if faults:
        raise Refused(faults)
    return Locator(converted, place)


def target(text: str) -> Locator:
    """A link as a field holds it: a name, or a name and, after `#`, a place inside that artifact. Checked as a
    locator is."""
    name, _, place = text.partition("#")
    return locator(kb_pb2.Locator(id=name, path=place))
```

with

```python
def locator(request: kb_pb2.Locator) -> Locator:
    """A locator's name and its place, each checked; both faults when both fail."""
    return _located(request.id, request.path)


def target(text: str) -> Locator:
    """A link as a field holds it: a name, or a name and, after `#`, a place inside that artifact. Checked as a
    locator is."""
    return _located(*names.linked(text))


def _located(name: str, path: str) -> Locator:
    faults = []
    try:
        converted = artifact_id(name)
    except Refused as refused:
        faults += refused.faults
    place = tuple(path.split("/")) if path else ()
    if not all(names.plain(part) for part in place):
        faults.append(kb_pb2.Fault(
            artifact=name, path=path, rule="locator",
            message=f"a place inside an artifact is named by parts of the same plain alphabet, or a collection and an item in it; {path!r} is not",
        ))
    if faults:
        raise Refused(faults)
    return Locator(converted, place)
```

- [ ] **Step 4: Every other module asks**

In `src/kb/requests.py`, replace `    at = f"{kind.name}/{names.slug(creation.title)}"` with `    at = names.written(kind.name, names.slug(creation.title))`.

In `src/kb/store.py`, replace both `return self.artifact(ArtifactId(Kind("schema"), kind.name))` (in `Store.schema` and `Draft.schema`) with `return self.artifact(values.type_of(kind))`.

In `src/kb/write.py`, replace `from kb import canonical, edits, journal, query, refusals, requests` with `from kb import canonical, edits, journal, query, refusals, requests, values`; replace `from kb.values import Actor, ArtifactId, Kind, Refused, Root, Signed` with `from kb.values import Actor, ArtifactId, Refused, Root, Signed`; replace `METASCHEMA_ID = ArtifactId(Kind("schema"), "schema")` with `METASCHEMA_ID = values.type_of(values.TYPE_KIND)` (the type of types is the type of the kind `schema`).

In `src/kb/edits.py`, replace `from kb.values import ArtifactId, Kind, Refused` with `from kb.values import ArtifactId, Refused`; replace `    if not draft.holds(ArtifactId(Kind("schema"), kind.name)):` with `    if not draft.holds(values.type_of(kind)):`; replace `    if not faults and artifact_id.kind == Kind("schema"):` with `    if not faults and artifact_id.kind == values.TYPE_KIND:`.

In `src/kb/validation.py`, delete the line `from kb.values import Kind`, and replace `    schema = store.load(values.ArtifactId(Kind("schema"), artifact_id.kind.name))` with `    schema = store.load(values.type_of(artifact_id.kind))`.

In `src/kb/links.py`, replace `from kb.composition import declared` with

```python
from kb import names
from kb.composition import declared
```

and replace `    return target.partition("#")[0] == str(artifact_id)` with `    return names.linked(target)[0] == str(artifact_id)`.

In `src/kb/composition.py`, replace

```python
from kb import values
from kb.values import Kind

TYPE_URI = "kb:"
```

with

```python
from kb import names, values
```

replace

```python
    ref = schema.get("$ref")
    if isinstance(ref, str) and ref.startswith(TYPE_URI) and "#" not in ref:
        built_on += composition(type_schema(ref, corpus), corpus)
```

with

```python
    ref = schema.get("$ref")
    referred = names.referred(ref) if isinstance(ref, str) else None
    if referred is not None and not referred[1]:
        built_on += composition(type_schema(ref, corpus), corpus)
```

and replace

```python
    try:
        schema_id = values.artifact_id(uri.removeprefix(TYPE_URI)) if uri.startswith(TYPE_URI) else None
    except values.Refused:
        schema_id = None
    if schema_id is None or schema_id.kind != Kind("schema") or not corpus.holds(schema_id):
```

with

```python
    referred = names.referred(uri)
    try:
        schema_id = values.artifact_id(referred[0]) if referred is not None else None
    except values.Refused:
        schema_id = None
    if schema_id is None or schema_id.kind != values.TYPE_KIND or not corpus.holds(schema_id):
```

In `src/kb/definitions.py`, replace

```python
from kb import refusals, values
from kb.contract import kb_pb2
from kb.composition import TYPE_URI
from kb.values import ArtifactId, Kind, Refused
```

with

```python
from kb import names, refusals, values
from kb.contract import kb_pb2
from kb.values import ArtifactId, Refused
```

replace `        if named == type_id and "#" not in ref:` with `        if named == type_id and not names.referred(ref)[1]:`, and replace

```python
    if not ref.startswith(TYPE_URI):
        return None
    try:
        named = values.artifact_id(ref.removeprefix(TYPE_URI).partition("#")[0])
    except Refused:
        return False
    return named if named.kind == Kind("schema") else False
```

with

```python
    referred = names.referred(ref)
    if referred is None:
        return None
    try:
        named = values.artifact_id(referred[0])
    except Refused:
        return False
    return named if named.kind == values.TYPE_KIND else False
```

- [ ] **Step 5: The check**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sort | diff /tmp/failing-before -
.venv/bin/python -m pytest -q 2>&1 | tail -1
G='kind\.name\}/|\{self\.kind\.name\}|partition\("[/#]"\)|Kind\("schema"\)|"kb:"|TYPE_URI|kb_pb2\.Locator\('
grep -nE "$G" src/kb/*.py | grep -v "^src/kb/names.py\|^src/kb/contract"
grep -nE "^import|^from" src/kb/names.py
wc -l src/kb/names.py src/kb/values.py
```

Expected: no diff; `56 failed, 140 passed`; no lines; `import re` and `from typing import NamedTuple` only; `99` and `216`.

- [ ] **Step 6: Checkpoint and commit**

Append the slice 71.1 checkpoint (the check's results, 21 lines before and none after), and set slice 71.1's Status to `green`.

```bash
git add src/kb docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 71.1: An artifact's name is written and read in one place

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Slice 72, a link into a part is a link into the artifact holding it

**Slice plan entry:** Slice 72, capability. Unknown: can one rule of what a link lands on serve the count at a glance, the links coming in, and what blocks a removal? Scenario:

- kb / follow-the-links / A link into a part counts as a link into the artifact holding it

**Files:**
- Modify: `src/kb/read.py` (`_inbound` counts by `links.points_at`)
- Modify: `tests/test_follow_the_links.py` (imports; one Given, one When, three Thens, appended)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: Task 4's `links.points_at` (through `names.linked`). In the test module: the Background's `client` (a store holding the tag, decision and work-item types, whose work-item type is `WORK_ITEM_TYPE` at version 1); `calls.PROCESS_TYPE`, `create`, `define`, `read`, `refs`, `remove`, `write`.
- Produces: `read._inbound(store, artifact_id: ArtifactId) -> dict` (was given the name as text).

- [ ] **Step 1: The steps**

In `tests/test_follow_the_links.py`, replace

```python
from pytest_bdd import given, parsers, scenarios, then, when

from calls import CLIENT, TAG_TYPE, WORK_ITEM_TYPE, create, define, refs, tagged_decision_type, write
```

with

```python
import copy

from pytest_bdd import given, parsers, scenarios, then, when

from calls import (
    CLIENT, PROCESS_TYPE, TAG_TYPE, WORK_ITEM_TYPE, create, define, read, refs, remove, tagged_decision_type, write,
)
```

Append at the end of the file:

```python
PROCESS = "process/open-the-shop"
INTO_A_STEP = "work-item/check-the-till-float"


@given(
    "a store holding a process, and a work item that points at one step of that process rather than at the whole "
    "process"
)
def _a_work_item_pointing_into_a_process(client):
    define(client, PROCESS_TYPE)
    create(client, "process", {"title": "Open the shop", "steps": [{"title": "Unlock the door"}, {"title": "Count the till"}]})
    following = copy.deepcopy(WORK_ITEM_TYPE["schema"])
    following["properties"]["follows"] = {
        "type": "string", "ref": {"targets": ["process"], "cardinality": "one", "parts": True, "on_delete": "refuse"},
    }
    revised = write(client, "schema/work-item", {"version": 2, "schema": following}, message="Let work items follow a step")
    assert not revised.faults, revised.faults
    create(client, "work-item", {"title": "Check the till float", "follows": f"{PROCESS}#steps/count-the-till"})


@when("the client follows the links into the process", target_fixture="reached")
def _follow_into_the_process(client):
    response = refs(client, PROCESS, depth=1, inward=True)
    assert not response.faults, response.faults
    return list(response.reached)


@then("the client is given a stub of that work item")
def _a_stub_of_the_work_item(reached):
    assert [(found.stub.field, found.stub.id) for found in reached] == [("follows", INTO_A_STEP)]


@then("reading the process at a glance counts that work item among the things pointing at it")
def _counted_at_a_glance(client):
    summary = read(client, PROCESS)
    assert not summary.faults, summary.faults
    assert [(count.type, count.field, count.count) for count in summary.inbound] == [("work-item", "follows", 1)]


@then("removing the process is refused while that work item points into it")
def _removal_refused(client):
    refused = remove(client, PROCESS)
    assert [(fault.artifact, fault.path, fault.rule) for fault in refused.faults] == [(INTO_A_STEP, "follows", "on_delete")]
    assert read(client, PROCESS).revision == 1
```

The Background's work items point at the decision, not the process, so the process's links come only from this Given's work item.

- [ ] **Step 2: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-72 2>&1 | grep -m1 -E "^E  "
.venv/bin/python -m pytest -q -m slice-72 2>&1 | tail -1
```

Expected: `E       AssertionError: assert [] == [('work-item', 'follows', 1)]`, `1 failed`: the links in, which came first in the scenario, already find the work item; the count at a glance compares a link's whole text to the process's name.

- [ ] **Step 3: The count reads a link by the one rule**

In `src/kb/read.py`, replace

```python
def _inbound(store: Store, artifact_id: str) -> dict:
    """How many artifacts point at this one, by their type and the field they use."""
```

with

```python
def _inbound(store: Store, artifact_id: ArtifactId) -> dict:
    """How many artifacts point at this one or at a part inside it, by their type and the field they use."""
```

replace

```python
        pointing = {link.field for link in links.carried(other, schema, store) if link.target == artifact_id}
```

with

```python
        pointing = {link.field for link in links.carried(other, schema, store) if links.points_at(link.target, artifact_id)}
```

and in `_summary` replace `    for (type_name, field), count in _inbound(store, str(locator.id)).items():` with `    for (type_name, field), count in _inbound(store, locator.id).items():`.

- [ ] **Step 4: Run it green**

```bash
grep -n "link.target ==" src/kb/*.py
.venv/bin/python -m pytest -q -m slice-72 2>&1 | tail -1
.venv/bin/python -m pytest -q 2>&1 | tail -1
```

Expected: no lines (every comparison of a link to an artifact is `links.points_at`); `1 passed`; `55 failed, 141 passed`.

- [ ] **Step 5: Checkpoint and commit**

Append the slice 72 checkpoint, with Review Focus 1 as a `QUESTION FOR THE SPEC` line, and set slice 72's Status to `green`.

```bash
git add src/kb tests docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 72: A link into a part is a link into the artifact holding it

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Slice 73, faults found by different rules come back together

**Slice plan entry:** Slice 73, capability. Unknown: can kb's own rules run alongside JSON Schema over content of any shape, without tripping on what JSON Schema already refuses? Scenario:

- kb / create-an-artifact / Faults found by different rules all come back together

**Files:**
- Modify: `src/kb/validation.py` (`validate`; new `_place`, `_misread`)
- Modify: `tests/test_create_an_artifact.py` (slice 7's When says which faults it expects, the shared Then compares against them; one When, appended)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: Task 3's `validation.compose(schema, corpus)`, `links.carried`.
- Produces: `validation.validate(artifact_id: str, content: dict, schema: dict, corpus) -> list[kb_pb2.Fault]`, unchanged in signature, now JSON Schema's faults followed by kb's. In the test module, the fixture `attempt` of both "two faults" Whens is a dict with `response`, `before`, `after` and `faults`, a list of `(path, rule)` in sorted order.

- [ ] **Step 1: The steps**

The Then `the artifact is rejected with both faults, each naming the artifact, the place in it and the rule broken` and the And `the store is unchanged` are already defined, for slice 7, and slice 73's scenario uses them word for word. So one definition serves both, and each When says which faults it expects.

In `tests/test_create_an_artifact.py`, replace

```python
        "supersedes": "decision/prices-are-reviewed-monthly",
        "sections": [SECTIONS[1]],
    }, message="Record it")
    return {"response": response, "before": before, "after": everything_under(tmp_path)}


@then("the artifact is rejected with both faults, each naming the artifact, the place in it and the rule broken")
def _rejected_with_both_faults(attempt):
    refused = attempt["response"]
    assert (refused.id, refused.revision) == ("", 0)
    assert sorted((fault.artifact, fault.path, fault.rule) for fault in refused.faults) == [
        ("decision/price-reviews-happen-weekly", "sections", "sections"),
        ("decision/price-reviews-happen-weekly", "supersedes", "ref"),
    ]
```

with

```python
        "supersedes": "decision/prices-are-reviewed-monthly",
        "sections": [SECTIONS[1]],
    }, message="Record it")
    return {
        "response": response, "before": before, "after": everything_under(tmp_path),
        "faults": [("sections", "sections"), ("supersedes", "ref")],
    }


@then("the artifact is rejected with both faults, each naming the artifact, the place in it and the rule broken")
def _rejected_with_both_faults(attempt):
    refused = attempt["response"]
    assert (refused.id, refused.revision) == ("", 0)
    assert sorted((fault.artifact, fault.path, fault.rule) for fault in refused.faults) == [
        ("decision/price-reviews-happen-weekly", path, rule) for path, rule in attempt["faults"]
    ]
```

Append at the end of the file:

```python
@when(
    "the client creates a decision whose options are of a shape the type does not allow and which is also missing its "
    "purpose, saying which role and why",
    target_fixture="attempt",
)
def _create_with_two_kinds_of_fault(root, client):
    before = everything_under(root)
    response = request(client, "decision", "Price reviews happen weekly", {"sections": SECTIONS[1:], "options": "Keep weekly"})
    return {
        "response": response, "before": before, "after": everything_under(root),
        "faults": [("options", "type"), ("sections", "sections")],
    }
```

- [ ] **Step 2: Run it red**

```bash
.venv/bin/python -m pytest -q -m "slice-73 or slice-7" 2>&1 | grep -m1 -E "^E  "
.venv/bin/python -m pytest -q -m "slice-73 or slice-7" 2>&1 | tail -1
```

Expected: `E       AssertionError: assert [('decision/p...ons', 'type')] == [('decision/p..., 'sections')]`, `1 failed, 1 passed`: JSON Schema's fault alone, since kb's rules ran only when JSON Schema found nothing; slice 7 still passes through the shared Then.

- [ ] **Step 3: kb's rules beside JSON Schema's**

In `src/kb/validation.py`, replace the whole of `validate`

```python
def validate(artifact_id: str, content: dict, schema: dict, corpus) -> list[kb_pb2.Fault]:
    """Every violation, as artifact, path, rule, message. A kb:schema/<type> reference resolves against the corpus.

    kb's own rules read content that fits the composed schema, so they run only when it does.
    """
    faults = [
        kb_pb2.Fault(
            artifact=artifact_id,
            path="/".join(str(step) for step in error.absolute_path),
            rule=error.validator,
            message=error.message,
        )
        for error in Draft202012Validator(compose(schema, corpus), registry=registry(corpus)).iter_errors(content)
    ]
    if faults:
        return faults
    required = [section for part in composition(schema, corpus) for section in part.get("sections", [])]
    faults = _sections(artifact_id, content.get("sections", []), required, "sections")
    for link in links.carried(content, schema, corpus):
        if not _lands(link.target, link.ref, corpus):
            faults.append(kb_pb2.Fault(
                artifact=artifact_id, path=link.place, rule="ref",
                message=f"a link must land on a node of a kind the type allows; {link.target!r} does not",
            ))
    return faults
```

with

```python
def validate(artifact_id: str, content: dict, schema: dict, corpus) -> list[kb_pb2.Fault]:
    """Every violation, as artifact, path, rule, message, JSON Schema's and kb's own rules' together. A
    kb:schema/<type> reference resolves against the corpus.

    kb's own rules read a node only where JSON Schema found it in the shape they read it in.
    """
    errors = list(Draft202012Validator(compose(schema, corpus), registry=registry(corpus)).iter_errors(content))
    faults = [
        kb_pb2.Fault(artifact=artifact_id, path=_place(error), rule=error.validator, message=error.message)
        for error in errors
    ]
    if not _misread("sections", errors):
        required = [section for part in composition(schema, corpus) for section in part.get("sections", [])]
        faults += _sections(artifact_id, content.get("sections", []), required, "sections")
    for link in links.carried(content, schema, corpus):
        if not _misread(link.place, errors) and not _lands(link.target, link.ref, corpus):
            faults.append(kb_pb2.Fault(
                artifact=artifact_id, path=link.place, rule="ref",
                message=f"a link must land on a node of a kind the type allows; {link.target!r} does not",
            ))
    return faults


def _place(error) -> str:
    return "/".join(str(step) for step in error.absolute_path)


def _misread(place: str, errors: list) -> bool:
    """Whether JSON Schema found fault with the node at a place, or with anything inside it, or found a node holding
    it of the wrong type, so that kb's own rules cannot read it."""
    steps = place.split("/")
    for error in errors:
        at = _place(error).split("/") if error.absolute_path else []
        if at[:len(steps)] == steps or (error.validator == "type" and steps[:len(at)] == at):
            return True
    return False
```

`links.carried` already passes over a collection that is not a list and an item that is not a mapping, and a link whose value JSON Schema refused (a number where text belongs) is `_misread` at its own place, so `_lands` never sees it. A root that is not a mapping never reaches `validate`: slice 75 refuses it as it converts.

- [ ] **Step 4: Run it green**

```bash
.venv/bin/python -m pytest -q -m "slice-73 or slice-7" 2>&1 | tail -1
.venv/bin/python -m pytest -q 2>&1 | tail -1
wc -l src/kb/validation.py
```

Expected: `2 passed`; `54 failed, 142 passed`; `180`.

- [ ] **Step 5: The batch's failures are all later slices'**

```bash
.venv/bin/python -m pytest -q -rf 2>&1 | grep FAILED | sed 's/\[.*//' | sort | uniq -c
```

Expected: 54 failures across the test functions of slices 74, 75, 77 to 82, 84 to 89 and 91 to 94, and none of slices 70 to 73.

- [ ] **Step 6: Checkpoint and commit**

Append the slice 73 checkpoint, with Review Focus 3 as a `QUESTION FOR THE SPEC` line, and set slice 73's Status to `green`.

```bash
git add src/kb tests docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 73: Faults found by different rules come back together

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```
