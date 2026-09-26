# kb Batch 7 Implementation Plan: slices 63 to 68

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Each task is one slice of `docs/superpowers/plans/2026-09-24-kb-slices.md`. Inside a task, follow `shopsystem-bdd:bdd-red-green` scenario by scenario. Its stop conditions, hand-back, and checkpoint apply, and they override any step here that conflicts with them.

**Goal:** The first six slices cut from the scenarios approved in `02be9f5`:
- Every call that meets a stored file it cannot read refuses with that file's fault, and writes nothing (slice 63).
- A link inside an item of a collection is checked, found and followed like any other link (slice 64).
- A change aimed at a place that names nothing real is refused before anything is touched (slice 65).
- An item is checked against its own item type (slice 66).
- The names a change hands back on items are checked: known, given once, plain (slice 67).
- A type that could never check anything is refused when it is written (slice 68).

**Architecture:** kb is the Python package `kb` in `/home/vscode/shopsystem-kb`. A protobuf contract (`kb.contract`) sits in front of `KbServicer` (`servicer.py`), whose every rpc runs inside one boundary that turns `values.Refused` into that rpc's faults. `requests.py`/`values.py` convert requests; `write.py` drafts a set and only then writes; `edits.py` says what each operation does to the draft (`store.Draft`); `read.py` and `query.py` answer questions; `validation.py` holds the composed schema and kb's own checks; `names.py` owns every name; `refusals.py` makes the domain's faults; `store.py` is files and git. `CLAUDE.md` is the rulebook. This plan implements each of its named rules once:
- **Loading returns a value (rule 3), behind the one boundary (rule 1).** `Store.load` returns the artifact or a `Damaged` value holding the fault; one function, `store.readable`, turns damage into a `Refused`, and `Store.artifact`/`Draft.artifact` are the readers that cannot go on without the artifact. The `Unreadable` exception goes. No rpc gets a check of its own (Task 1).
- **One reading of links** wherever they sit, items included, which checks, removals, reads and walks share (Task 2).
- **One resolution of a place**, a new module `places.py`, which replacement and addition share (Task 3), and reads and walks will share in slices 88 and 89.
- **The composed schema** gains each collection's shape, so items are checked by JSON Schema with everything else (Task 4).
- **Names in one place (rule 6).** `names.handed_back` decides whether an item's name could be one the store gave (Task 5).
- **A type checked once, when written**, in a new module `definitions.py` (Task 6).
- **Draft, validate, write (rule 4)** already holds: every refusal here is raised while the draft is being built, before `write._written`. No task touches the write phase.

**Provenance:** Every code block here was assembled in a scratch clone of this repository (`/tmp/batch7/kb`, cloned at `b6dd998` and rebased onto `2a7fd5e`) on 2026-09-26, with its own `.venv` from `make dev`, and the tasks were applied in order. The red and green results, the suite counts, and the Review Focus reproductions below are what those runs gave. The plan was then replayed from its own text on a fresh clone (`/tmp/batch7-replay`, at `2a7fd5e`, its own `.venv`) by an agent that had not seen the scratch run: every "replace" text was found verbatim, every red, green and suite count matched, pyflakes reported nothing, and the 60 failures left were exactly the listed later slices. Its two notes on the text (a summary command that printed make's error line, and a count of five callers where the grep shows six lines) are fixed here. This repository was not touched except to place the new scenarios in the slice plan, tag them, and write this plan.

**Tech Stack:** Python 3.11, setuptools (src layout), protobuf + grpcio (generated code committed; no `.proto` change in this batch), python-jsonschema 4.26 with `referencing`, ruamel.yaml 0.19 (YAML 1.2), git via subprocess, pytest 9 + pytest-bdd 8.

**Spec:** `docs/superpowers/specs/2026-09-23-kb-design.md`, in particular:
- "Input safety": "A stored file that fails to parse is reported by load and by `Validate` as a violation naming the file ... Nothing raises."
- "Artifact model", Nodes: "Every node is addressable by a path from the artifact root"; Fields: "A reference is a field type"; Parts: "Each item carries an `id` unique within its collection ... minted by kb and never supplied by the client ... On a `Write` of a collection, an item carrying an id is the existing item of that id ... An id that names no existing item is refused. Items have fields per the item schema, which may itself declare nested collections."
- "Schema language": `ref` is `{ targets: [type...], ... }`; "Cross-schema `$ref` resolves ... against a registry of every `schema/*` artifact"; "kb's own structural rules, the section tree ..., part collections whose items carry an `id`, ... are JSON Schema fragments that kb composes with the type's schema into one effective schema per artifact".
- "Write path", step 4: "References must resolve to a node of a permitted type. Part ids must be unique per collection. ... Collect every error; if any, stop here."

The slice plan is `docs/superpowers/plans/2026-09-24-kb-slices.md`, slices 63 to 68, and the feature files are in `features/`. Each slice's scenarios carry `@slice-<n>`, so `.venv/bin/python -m pytest -q -m slice-63` runs one slice. `CLAUDE.md` at the repository root is binding.

## Global Constraints

- Feature files are read-only for the implementer. Only `slicing-into-increments` edits a tag line, and only `formulating-features` edits a Given, When, or Then. Any other diff under `features/` is a stop condition.
- Code only what a scenario asserts (bdd-red-green). Where the scenarios are silent, the code is silent too, and the silence goes into the checkpoint entry as an open question. The decisions this plan makes are listed below, each tied to the scenario that asks for it.
- **CLAUDE.md's rules are implemented once, never per row.** No rpc in `servicer.py` gains a `try`, a check, or a branch in this batch (`grep -c "try:" src/kb/servicer.py` stays `1`). No module but `store.py` turns a damaged file into a refusal (`store.readable`). No module but `names.py` decides what an item's name may be. No module but `places.py` walks a place.
- **Extend, never add beside.** A new concern gets a new module (`places.py`, `definitions.py`), and each goes into CLAUDE.md's module map in the task that creates it. Faults are made in `refusals.py`. Test helpers live in `tests/calls.py`; a Given or Then two feature files share lives in `tests/conftest.py` rather than being copied.
- **Size.** No module over 250 lines; `servicer.py` under 150. After Task 4, `validation.py` is 246 lines: no task here adds to it again, and the next slice that would must split it first (slice 69's review will say how).
- Errors are a typed list of `{ artifact, path, rule, message }`. A response that carries faults is a refusal, and nothing was written.
- kb is exercised through its in-process transport (`kb.client.connect`).
- `make test` runs the suite in this checkout's virtualenv (`.venv/bin/python -m pytest -q`). While any scenario is red, make's own error line comes last, so the steps run pytest directly to see the summary. A worktree needs its own `.venv` first (`make dev`).
- The contract's version stays `0.1`, `pyproject.toml` stays `0.1.0`. Version and tag are the user's call.
- Work on `main` in `/home/vscode/shopsystem-kb`. shop-knowledge pins kb at `v0.1.0`; nothing here touches or runs its suite.
- Commits: `git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit`, the message ending with the Co-Authored-By line of the model that made the commit, e.g. `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- "Append at the end of the file" means after two blank lines, as the files' top-level definitions are spaced.
- The suite prints pytest-bdd `PytestRemovedIn10Warning`s. That is the baseline, not a fault. The summary lines quoted as Expected leave out the `, N warnings in Xs` that pytest adds.
- Baseline before Task 1: `.venv/bin/python -m pytest -q` → `63 failed, 117 passed`. Task 1 adds a test module that collects 16 more examples. After Tasks 1 to 6 the suite reads `72/124`, `71/125`, `67/129`, `66/130`, `63/133` and `60/136` (failed/passed). Every failure left after Task 6 is tagged for slice 70 or later (70: 1, 71: 3, 72: 1, 73: 1, 74: 7, 75: 7, 77: 1, 78: 1, 79: 2, 80: 3, 81: 1, 82: 3, 84: 1, 85: 3, 86: 2, 87: 2, 88: 7, 89: 2, 91: 4, 92: 2, 93: 3, 94: 3), and none of those goes green early.

## Decisions this plan makes (the spec left them open or silent)

1. **Damage is a value (slice 63).** `store.Damaged(fault)` is what `Store.load` and `Draft.load` give for a file that cannot be read; they never raise for what a file holds. `store.readable(loaded)` is the one place damage becomes `Refused([fault])`. `Store.artifact(id)`, `Draft.artifact(id)`, `schema(kind)` and `Store.artifacts()` go through it; every domain reader uses those. Only the whole-store check (`validation.check`) takes `load` and reports the damage instead. The fault is unchanged: rule `unreadable`, the artifact's name, message `the stored file <kind>/<slug>.yaml cannot be read: <problem>`, now made by `refusals.unreadable`. The boundary is not widened to catch other exceptions: what fault an unforeseen failure gives is still an open question (the architecture review's, logged 2026-09-26).
2. **Links wherever they sit (slice 64).** `validation.links` returns `Link(field, place, target, ref)` records for the artifact's own link fields and, recursively, for the link fields of each item of each collection the schema declares (`parts`), and of the collections those items' schemas declare. An item's link has the place `<collection>/<index>/<field>`, the index being where the item stands in the content checked. A link is checked against its own field's `ref`, so an item's field and an artifact's field of the same name never mix. The summary's references, Refs out, inbound counts and removal blocks read items' links too (Review Focus 3).
3. **A place (slice 65).** `places.resolve(content, locator)` walks a non-empty place over an artifact's content (identity keys stripped) and answers a `Spot(holder, key, collection)`, where `holder[key]` is the node. It refuses, in this order:
   - a place whose first step is an identity key (`id`, `type`, `schema_version`, `revision`, `title`): rule `identity`, `a place inside an artifact never names what only the store settles; '<place>' begins at '<key>'`;
   - a pair of a collection and an item that is not there, or a "collection" that is not a list (prose, a field): rule `not-found`, the existing `'<id>' holds nothing at '<place>'`.
   An addition must resolve to a collection at the artifact's top that its type declares; anything else, an empty place included, is refused with rule `collection`, `an item is added to a collection, and '<place>' in '<id>' is not one`. This replaces `refusals.no_collection`, whose message no scenario pinned.
4. **Collections in the composed schema (slice 66).** `validation.compose` adds, under `allOf`, one member giving each collection in the schema's `parts` the shape `{"type": "array", "items": <item schema>}`, the item schema composed the same way for the collections it declares. JSON Schema then reports an item's faults at `<collection>/<index>` with its own rule (`required` for a missing field). Collections declared by a base are not composed yet: that is slice 71's unknown.
5. **Names handed back (slice 67).** On every revision (`edits._revise`: a whole write, a placed write, an addition), `names.handed_back(schema, content, held)` returns a `Misnamed(collection, index, name, why)` for each item carrying an `id` that is not plain (`not-plain`), is on an earlier item of the same collection (`repeated`), or names no item the collection held before the change (`unknown`). `refusals.misnamed` makes each a fault with rule `item-name` at `<collection>/<index>/id`, with the messages the scenarios' reasons begin with. These faults come before the content's own, in one refusal.
6. **A type checked as a type (slice 68).** When an artifact of kind `schema` fits the type of types, `definitions.faults(type_id, content, draft)` checks it further, each fault at its place under `schema/...`:
   - every `$ref` beginning `kb:` must name a type the draft holds, or the fault is rule `shape`, `a shape a type refers to must belong to a type the store holds; '<ref>' does not`;
   - a whole-type `$ref` (no `#`) to the type being written is rule `built-on`, `a type cannot be built on itself; '<id>' names '<ref>'`;
   - every property declaring `ref` must give `ref.targets`, or the fault is rule `targets`, `a link field says which kinds it may point at; '<field>' does not`, at `schema/.../properties/<field>`.
   It runs on Create and on every Write of a type, through one helper in `edits.py` (`_fits`). A cycle through two types is not caught (Review Focus 2).
7. **Shared test steps.** The Given `someone edited the decision's file by hand and left it in a shape the store cannot read` moves from `tests/test_read_an_artifact.py` to `tests/conftest.py`, since `a-file-the-store-cannot-read.feature` uses it word for word; it mangles `decision/price-reviews-happen-weekly`, the decision both features' Backgrounds hold.

## Review Focus

In this project, tests are scenarios, and the feature files are the human gate, so no unit tests are added. Instead, each line below goes into the owning task's checkpoint entry as a `QUESTION FOR THE SPEC`, with the reproduction given here. Each was reproduced in scratch after all six tasks.

1. **A type that another type refers to, left unreadable, crashes a Create.** Reproduction: define `schema/tool` with `$defs.binding`, and `schema/tool-use` whose field `b` is `{"$ref": "kb:schema/tool#/$defs/binding"}`; write `title: [` over `kb/schema/tool.yaml`; create a `tool-use` with `b: {}`. It raises `_WrappedReferencingError: Unresolvable` through the client: the registry's retrieval raises `Refused` inside `referencing`, which wraps it. A person expects the damaged file named, as every other call now does. Slice 79 pins a damaged type met directly; this path through a `$ref` has no scenario. Task 1 logs it.
2. **Two types built on each other.** Reproduction: define `schema/a`, then `schema/b` with `allOf: [{"$ref": "kb:schema/a"}]`, then write `schema/a` at version 2 with `allOf: [{"$ref": "kb:schema/b"}]`. It is accepted, and every create of an `a` raises `RecursionError` through the client. Slice 68 refuses a type built on itself directly; a cycle through another type has no scenario. Task 6 logs it.
3. **Items' links now show wherever links show.** Reproduction: a process whose step `uses: step/count`. Its summary Read now lists a stub `('uses', 'step/count')`, Refs out reaches `step/count`, and removing `step/count` is refused at `steps/0/uses`. That follows from one reading of links, but a reader of the summary may not expect an item's link among the artifact's own. Task 2 logs it. (Slice 87's removal scenario asserts the last of these.)
4. **A sound artifact refused for another's damage.** Reproduction: with `decision/d`'s file mangled, removing `tag/t` (nothing points at it) and reading `tag/t` at a glance are each refused with `decision/d`'s `unreadable` fault, since removal and the inbound count read every artifact. Failing closed is what rule 1 asks, but the fault names a file the call did not ask about. The batch 4 question (should a read answer, leaving the damaged file to Validate) is still open. Task 1 logs it.
5. **A write of an artifact holding an item that never fit its item type.** After Task 4, every revision checks every item, so an artifact holding an item that a later version of its item type no longer accepts cannot be written at all, even by a change to one section, until that item is fixed in the same write. That is the spec's "a write to a stale artifact validates against the current version", now reaching items. Reproduction: the setup of Task 4's When, stopping after the type write (the process's two steps have no role): a placed write to `steps/unlock-the-door` alone is refused with a `required` fault for `steps/1` too. Task 4 logs it.

---

### Task 1: Slice 63, every call refuses a file it cannot read, naming the file

**Slice plan entry:** Slice 63, capability. Unknown: can a stored file be loaded as the artifact or the fault naming it, in one place every reader goes through, so that no call raises on it? Scenario (one outline, seven rows):

- kb / a-file-the-store-cannot-read / Every call refuses a file it cannot read, naming the file

Needs: a test module binding `a-file-the-store-cannot-read.feature`, which nothing collects today. That module also collects the feature's other three scenarios (slices 74 and 79). They stay red here, for want of steps.

**Files:**
- Create: `tests/test_a_file_the_store_cannot_read.py`
- Modify: `tests/conftest.py` (the mangling Given, moved)
- Modify: `tests/test_read_an_artifact.py` (the mangling Given and `MANGLED` taken out)
- Modify: `src/kb/store.py` (`Damaged`, `readable`, `load`, `artifact`, `schema`, `artifacts`, `Draft.load`/`artifact`/`schema`; `Unreadable` removed)
- Modify: `src/kb/refusals.py` (`unreadable`)
- Modify: `src/kb/read.py`, `src/kb/query.py`, `src/kb/edits.py`, `src/kb/write.py` (read through `artifact`)
- Modify: `src/kb/validation.py` (`check` and `_with_type`; `_type_schema` and `_lands` read through `artifact`)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `calls.write`, `calls.append`, `calls.remove`, `calls.listing`, `calls.search`, `calls.refs`, `calls.define`, `calls.create`, `calls.everything_under`, `calls.DECISION_TYPE`, `calls.PROCESS_TYPE`, `calls.TAG_TYPE`; conftest's `root` and `before` fixtures.
- Produces: `store.Damaged` (frozen dataclass, field `fault: kb_pb2.Fault`); `store.readable(loaded: dict | Damaged) -> dict` (raises `Refused`); `Store.load(id) -> dict | Damaged`; `Store.artifact(id) -> dict`; `Draft.load(id) -> dict | Damaged`; `Draft.artifact(id) -> dict`; `refusals.unreadable(artifact_id: ArtifactId, file, problem: str) -> kb_pb2.Fault`. Every later task reads an artifact through `artifact`, never `load`, unless it reports damage itself.

- [ ] **Step 1: Move the shared Given**

In `tests/test_read_an_artifact.py`, delete these lines (and the two blank lines after them):

```python
MANGLED = "title: [a bracket opened by hand and never closed\n"


@given("someone edited the decision's file by hand and left it in a shape the store cannot read")
def _decision_file_mangled_by_hand(root, monkeypatch):
    (root / "kb" / f"{DECISION}.yaml").write_text(MANGLED)
    monkeypatch.chdir(root)
    monkeypatch.delenv("KB_ROOT", raising=False)
```

Append at the end of `tests/conftest.py`:

```python
MANGLED = "title: [a bracket opened by hand and never closed\n"


@given("someone edited the decision's file by hand and left it in a shape the store cannot read")
def _decision_file_mangled_by_hand(root, monkeypatch):
    """The decision a feature's Background holds, decision/price-reviews-happen-weekly, left unreadable, with the
    client working in the store and nothing naming it."""
    (root / "kb" / "decision" / "price-reviews-happen-weekly.yaml").write_text(MANGLED)
    monkeypatch.chdir(root)
    monkeypatch.delenv("KB_ROOT", raising=False)
```

Run: `.venv/bin/python -m pytest -q 2>&1 | tail -1`
Expected: `63 failed, 117 passed` (the read scenario of slice 1.19 still passes, on the conftest step).

- [ ] **Step 2: The test module**

Create `tests/test_a_file_the_store_cannot_read.py`:

```python
import re

from pytest_bdd import given, parsers, then, when, scenarios

from calls import (
    CLIENT, DECISION_TYPE, PROCESS_TYPE, TAG_TYPE, append, create, define, everything_under, listing, refs, remove,
    search, write,
)
from kb import client as kb_client
from kb.contract import kb_pb2

scenarios("a-file-the-store-cannot-read.feature")

DECISION = "decision/price-reviews-happen-weekly"
SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]

CALLS = {
    "replaces the decision, saying which role and why":
        lambda client: write(client, DECISION, {"sections": SECTIONS}),
    "adds an item to a collection of the decision, saying which role and why":
        lambda client: append(client, DECISION, "options", {"title": "Go monthly"}),
    "removes the decision, saying which role and why":
        lambda client: remove(client, DECISION),
    "lists the decisions":
        lambda client: listing(client, "decision"),
    "searches the prose for a word that decision holds":
        lambda client: search(client, "weekly"),
    "follows the links into the decision":
        lambda client: refs(client, DECISION, 1, inward=True),
    "follows the links out of the decision":
        lambda client: refs(client, DECISION, 1),
}


@given("a store holding a decision, a process and a tag, each of a kind the store holds a type for",
       target_fixture="client")
def _store_with_a_decision_a_process_and_a_tag(root):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    for type_content in (DECISION_TYPE, PROCESS_TYPE, TAG_TYPE):
        define(client, type_content)
    create(client, "decision", {"title": "Price reviews happen weekly", "sections": SECTIONS})
    create(client, "process", {"title": "Open the shop", "steps": [{"title": "Unlock"}, {"title": "Count the float"}]})
    create(client, "tag", {"title": "Pricing"})
    return client


@when(parsers.re(f"the client (?P<call>{'|'.join(map(re.escape, CALLS))})"), target_fixture="answered")
def _the_client_calls(client, root, before, call):
    before.update(held=everything_under(root))
    return CALLS[call](client)


@then("the call is rejected because that file cannot be read, and the file is named")
def _rejected_as_unreadable(answered):
    assert [(fault.artifact, fault.rule) for fault in answered.faults] == [(DECISION, "unreadable")]
    assert f"{DECISION}.yaml cannot be read" in answered.faults[0].message


@then("the client is given that fault as it is given any other, the call never breaking off")
def _given_as_any_other_fault(answered):
    assert type(answered).__module__ == kb_pb2.__name__
    assert answered.faults


@then("nothing is written anywhere in the store")
def _nothing_written(root, before):
    assert everything_under(root) == before["held"]
```

- [ ] **Step 3: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-63 2>&1 | grep -E "^E  " | sort | uniq -c; .venv/bin/python -m pytest -q -m slice-63 2>&1 | tail -1
```

Expected: `7 failed`, each with `E  kb.store.Unreadable: the stored file decision/price-reviews-happen-weekly.yaml cannot be read: ...` raised through the client.

- [ ] **Step 4: The fault, in `refusals.py`**

In `src/kb/refusals.py`, just above `def unwritable(`, add:

```python
def unreadable(artifact_id: ArtifactId, file, problem: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(artifact_id), rule="unreadable", message=f"the stored file {file} cannot be read: {problem}",
    )


```

- [ ] **Step 5: Loading returns a value, in `store.py`**

In `src/kb/store.py`, replace

```python
import os
import subprocess
from pathlib import Path
from typing import Mapping

from kb import canonical, values
```

with

```python
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from kb import canonical, refusals, values
```

Replace the `Unreadable` class

```python
class Unreadable(Exception):
    """A stored file that cannot be read. Carries the fault that names it."""

    def __init__(self, fault: kb_pb2.Fault):
        super().__init__(fault.message)
        self.fault = fault
```

with

```python
@dataclass(frozen=True)
class Damaged:
    """What loading a stored file that cannot be read gives in place of the artifact: the fault that names the file."""
    fault: kb_pb2.Fault


def readable(loaded: dict | Damaged) -> dict:
    """The artifact loaded; a file that cannot be read refuses the call with the fault naming it. The one place a
    damaged file becomes a refusal."""
    if isinstance(loaded, Damaged):
        raise Refused([loaded.fault])
    return loaded
```

In `class Store`, replace `load` and `schema`

```python
    def load(self, artifact_id: ArtifactId) -> dict:
        """The artifact as stored. A file that cannot be read raises Unreadable, naming the file."""
        path = self.path(artifact_id)
        try:
            return canonical.load(path.read_text(encoding="utf-8"))
        except canonical.NotCanonical as error:
            raise Unreadable(kb_pb2.Fault(
                artifact=str(artifact_id), rule="unreadable",
                message=f"the stored file {path.relative_to(self.dir)} cannot be read: {error}",
            )) from None

    def schema(self, kind: Kind) -> dict:
        """The schema artifact of a kind; its JSON Schema is under `schema`."""
        return self.load(ArtifactId(Kind("schema"), kind.name))
```

with

```python
    def load(self, artifact_id: ArtifactId) -> dict | Damaged:
        """The artifact as stored, or, when its file cannot be read, the fault naming the file. Never raises for what
        a file holds."""
        path = self.path(artifact_id)
        try:
            return canonical.load(path.read_text(encoding="utf-8"))
        except canonical.NotCanonical as error:
            return Damaged(refusals.unreadable(artifact_id, path.relative_to(self.dir), str(error)))

    def artifact(self, artifact_id: ArtifactId) -> dict:
        """The artifact as stored, for a reader that cannot go on without it. Raises Refused for a damaged file."""
        return readable(self.load(artifact_id))

    def schema(self, kind: Kind) -> dict:
        """The schema artifact of a kind; its JSON Schema is under `schema`. Raises Refused for a damaged file."""
        return self.artifact(ArtifactId(Kind("schema"), kind.name))
```

and replace `artifacts`

```python
    def artifacts(self):
        """Every artifact in the store, schemas included, in path order. A file that cannot be read raises Unreadable."""
        for artifact_id in self.ids():
            yield self.load(artifact_id)
```

with

```python
    def artifacts(self):
        """Every artifact in the store, schemas included, in path order. Raises Refused at a damaged file."""
        for artifact_id in self.ids():
            yield self.artifact(artifact_id)
```

In `class Draft`, replace

```python
    def load(self, artifact_id: ArtifactId) -> dict:
        if artifact_id in self._pending:
            return self._pending[artifact_id]
        return self._store.load(artifact_id)

    def schema(self, kind: Kind) -> dict:
        return self.load(ArtifactId(Kind("schema"), kind.name))
```

with

```python
    def load(self, artifact_id: ArtifactId) -> dict | Damaged:
        if artifact_id in self._pending:
            return self._pending[artifact_id]
        return self._store.load(artifact_id)

    def artifact(self, artifact_id: ArtifactId) -> dict:
        return readable(self.load(artifact_id))

    def schema(self, kind: Kind) -> dict:
        return self.artifact(ArtifactId(Kind("schema"), kind.name))
```

- [ ] **Step 6: Every domain reader reads through `artifact`**

These four modules call `load` only where they cannot go on without the artifact, so each such call becomes `artifact`:

```bash
sed -i 's/draft\.load(/draft.artifact(/g; s/store\.load(/store.artifact(/g' src/kb/edits.py src/kb/read.py src/kb/query.py src/kb/write.py
grep -n '\.load(' src/kb/edits.py src/kb/read.py src/kb/query.py src/kb/write.py
```

Expected: the grep prints nothing.

In `src/kb/read.py`, replace `from kb.store import Store, Unreadable` with `from kb.store import Store`, and in `artifact` replace

```python
    try:
        if reading.level == "whole":
            return _whole(store, locator, reading.depth)
        if reading.level == "section":
            return _section(store, locator, reading.section)
        return _summary(store, locator)
    except Unreadable as unreadable:
        raise Refused([unreadable.fault]) from None
```

with

```python
    if reading.level == "whole":
        return _whole(store, locator, reading.depth)
    if reading.level == "section":
        return _section(store, locator, reading.section)
    return _summary(store, locator)
```

- [ ] **Step 7: The whole-store check reports damage as a value**

In `src/kb/validation.py`:
- replace `from kb.store import Store, Unreadable` with `from kb.store import Damaged, Store`;
- in `_type_schema`, replace `    return corpus.load(schema_id)["schema"]` with `    return corpus.artifact(schema_id)["schema"]`;
- in `_lands`, replace `_holds_part(corpus.load(link.id), link.place)` with `_holds_part(corpus.artifact(link.id), link.place)`;
- in `check`, replace

```python
        try:
            artifact = store.load(artifact_id)
            schema = store.schema(artifact_id.kind)
        except Unreadable as unreadable:
            violations.append(unreadable.fault)
            continue
```

with

```python
        loaded = _with_type(store, artifact_id)
        if isinstance(loaded, Damaged):
            violations.append(loaded.fault)
            continue
        artifact, schema = loaded
```

- and just above `def references(`, add:

```python
def _with_type(store: Store, artifact_id) -> tuple[dict, dict] | Damaged:
    """The artifact and its type as stored, or the damage of the first of them whose file cannot be read."""
    artifact = store.load(artifact_id)
    if isinstance(artifact, Damaged):
        return artifact
    schema = store.load(values.ArtifactId(Kind("schema"), artifact_id.kind.name))
    return schema if isinstance(schema, Damaged) else (artifact, schema)


```

- [ ] **Step 8: Run it green, and the rule's checks**

```bash
.venv/bin/python -m pytest -q -m slice-63 2>&1 | tail -1
.venv/bin/python -m pytest -q 2>&1 | tail -1
grep -rn "Unreadable" src/kb/
grep -rnE "except( Exception|:)" src/kb/
grep -c "try:" src/kb/servicer.py
```

Expected: `7 passed`; `72 failed, 124 passed` (the 9 other examples the new module collects are slices 74 and 79, red for want of steps); neither grep prints anything; `1`.

- [ ] **Step 9: Checkpoint and commit**

Append the slice 63 checkpoint to the slice plan's log, in the shape bdd-red-green gives (what someone can now do, the assumption and its evidence, surprises, open questions), with Review Focus 1 and 4 as `QUESTION FOR THE SPEC` lines, and set slice 63's Status to `green`.

```bash
git add src/kb tests docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 63: Every call refuses a file it cannot read, naming the file

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Slice 64, a link inside an item is checked like any other

**Slice plan entry:** Slice 64, capability. Unknown: can an artifact's links be found wherever they sit, inside items as well as at its top, by the one reading of links that the checks, removal and the walks share? Scenario:

- kb / add-an-item-to-a-collection / An item pointing at something that is not there is refused

**Files:**
- Modify: `src/kb/validation.py` (`Link`, `links`, `_links_in`; `validate` checks each link against its own `ref`)
- Modify: `src/kb/read.py`, `src/kb/query.py`, `src/kb/edits.py` (read `Link` fields by name)
- Modify: `tests/test_add_an_item_to_a_collection.py` (one When, one Then, appended)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: Task 1's `Draft.artifact`. In the test module: `PROCESS`, `append`, `read`, and the existing Then `the process holds the steps it held before, at the version it held before` (fixture `attempt`: a dict with `response` and `before`, a whole `ReadResponse`).
- Produces: `validation.Link(field: str, place: str, target: str, ref: dict)` (a `NamedTuple`); `validation.links(artifact: dict, schema: dict, corpus) -> list[Link]`, now reading items at every depth. Every caller reads `link.field`, `link.place`, `link.target`, `link.ref`, never unpacks.

- [ ] **Step 1: The steps**

Append at the end of `tests/test_add_an_item_to_a_collection.py`:

```python
@when("the client adds a step that points at a shared step the store does not hold, saying which role and why", target_fixture="attempt")
def _add_a_step_pointing_nowhere(client):
    before = read(client, PROCESS, whole=True)
    response = append(client, PROCESS, "steps", {"title": "Count the change", "uses": "step/count-the-change"})
    return {"response": response, "before": before}


@then("the item is rejected because a link must land on a node of a kind the type allows")
def _rejected_for_its_link(attempt):
    assert [(fault.artifact, fault.path, fault.rule) for fault in attempt["response"].faults] == [
        (PROCESS, "steps/2/uses", "ref"),
    ]
    assert "'step/count-the-change'" in attempt["response"].faults[0].message
```

- [ ] **Step 2: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-64 2>&1 | grep -E "^E  " | head -3
```

Expected: `1 failed`, `AssertionError: assert [] == [('process/op...uses', 'ref')]`: the step was added, pointing nowhere.

- [ ] **Step 3: One reading of links**

In `src/kb/validation.py`, replace the line `from jsonschema import Draft202012Validator` with

```python
from typing import NamedTuple

from jsonschema import Draft202012Validator
```

Replace the whole of `links`

```python
def links(artifact: dict, schema: dict, corpus) -> list[tuple[str, str, str]]:
    """Every link an artifact carries, as the field, the place in the artifact, and the name it points at."""
    found = []
    for field in references(schema, corpus):
        value = artifact.get(field)
        if isinstance(value, list):
            found += [(field, f"{field}/{index}", target) for index, target in enumerate(value)]
        elif value is not None:
            found.append((field, field, value))
    return found
```

with

```python
class Link(NamedTuple):
    """One link an artifact carries: the field that holds it, the place of that field in the artifact, the name it
    points at, and the field's `ref`, which says what it may land on."""
    field: str
    place: str
    target: str
    ref: dict


def links(artifact: dict, schema: dict, corpus) -> list[Link]:
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
```

In `validate`, replace

```python
    allowed = references(schema, corpus)
    for field, place, target in links(content, schema, corpus):
        if not _lands(target, allowed[field], corpus):
            faults.append(kb_pb2.Fault(
                artifact=artifact_id, path=place, rule="ref",
                message=f"a link must land on a node of a kind the type allows; {target!r} does not",
            ))
```

with

```python
    for link in links(content, schema, corpus):
        if not _lands(link.target, link.ref, corpus):
            faults.append(kb_pb2.Fault(
                artifact=artifact_id, path=link.place, rule="ref",
                message=f"a link must land on a node of a kind the type allows; {link.target!r} does not",
            ))
```

- [ ] **Step 4: Every caller reads a `Link` by name**

In `src/kb/query.py`, replace

```python
    return [(field, values.artifact_id(target)) for field, _, target in validation.links(artifact, schema, store)]
```

with

```python
    return [(link.field, values.artifact_id(link.target)) for link in validation.links(artifact, schema, store)]
```

and replace

```python
        for field, _, target in validation.links(other, schema, store):
            if validation.points_at(target, artifact_id):
                pointing.append((field, other_id))
```

with

```python
        for link in validation.links(other, schema, store):
            if validation.points_at(link.target, artifact_id):
                pointing.append((link.field, other_id))
```

In `src/kb/read.py`, replace

```python
    for field, _, target in validation.links(found, schema, store):
        response.references.append(stub(store, field, values.artifact_id(target)))
```

with

```python
    for link in validation.links(found, schema, store):
        response.references.append(stub(store, link.field, values.artifact_id(link.target)))
```

and replace

```python
        pointing = {field for field, _, target in validation.links(other, schema, store) if target == artifact_id}
```

with

```python
        pointing = {link.field for link in validation.links(other, schema, store) if link.target == artifact_id}
```

In `src/kb/edits.py`, replace

```python
        for field, place, target in validation.links(draft.artifact(other_id), schema, draft):
            if validation.points_at(target, locator.id):
                blocking.append(refusals.still_linked(locator.id, other_id, place))
```

with

```python
        for link in validation.links(draft.artifact(other_id), schema, draft):
            if validation.points_at(link.target, locator.id):
                blocking.append(refusals.still_linked(locator.id, other_id, link.place))
```

- [ ] **Step 5: Run it green**

```bash
grep -n "links(" src/kb/*.py | grep -v "def \|_links_in"
.venv/bin/python -m pytest -q -m slice-64 2>&1 | tail -1
.venv/bin/python -m pytest -q 2>&1 | tail -1
wc -l src/kb/validation.py
```

Expected: six lines, each binding `link` (five callers and `validate`'s own loop); `1 passed`; `71 failed, 125 passed`; `230`.

- [ ] **Step 6: Checkpoint and commit**

Append the slice 64 checkpoint, with Review Focus 3 as a `QUESTION FOR THE SPEC` line, and set slice 64's Status to `green`.

```bash
git add src/kb tests docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 64: A link inside an item is checked like any other

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Slice 65, a place that names nothing real is refused before anything is touched

**Slice plan entry:** Slice 65, capability. Unknown: can one resolution of a place inside an artifact answer either the node there or the refusal, for a replacement and an addition alike? Scenario (one outline, four rows):

- kb / change-an-artifact / Every way the place a change is aimed at can be wrong is refused

The first row (a place holding nothing) is refused already, by the walk this task replaces. Its step still goes red first, for want of the step. The other three rows are red on behaviour: one raises `AttributeError` through the client, one is accepted, and one gets rule `not-found`.

**Files:**
- Create: `src/kb/places.py`
- Modify: `src/kb/edits.py` (`_placed` and `_append` resolve through `places`; `_node_name` removed)
- Modify: `src/kb/refusals.py` (`not_a_collection` replaces `no_collection`; `settled_place` added)
- Modify: `CLAUDE.md` (module map row for `places.py`)
- Modify: `tests/test_change_an_artifact.py` (imports; one When, three Thens appended)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: Task 1's `Draft.artifact`; `values.Locator(id, place: tuple[str, ...])`; `canonical.IDENTITY`; `names.slug`; `refusals.nothing_at(locator)`. In the tests: `DECISION`, `write`, `append`, the existing Then `reading the decision gives what it held before, at the version it held before` (fixture `attempt`: `response` and `before`, the decision file's bytes).
- Produces: `places.Spot(holder: dict | list, key: str | int, collection: str = "")`; `places.resolve(content: dict, locator: Locator) -> Spot` (raises `Refused`; the place must not be empty); `refusals.not_a_collection(locator) -> Fault` (rule `collection`); `refusals.settled_place(locator) -> Fault` (rule `identity`). Slices 77, 88 and 89 resolve places through `places.resolve`.

- [ ] **Step 1: The steps**

In `tests/test_change_an_artifact.py`, replace `import copy` with

```python
import copy
import re
```

and replace `from calls import CLIENT, DECISION_TYPE, create, define, everything_under, read, write` with `from calls import CLIENT, DECISION_TYPE, append, create, define, everything_under, read, write`. Append at the end of the file:

```python
PURPOSE = {"title": "Purpose", "body": "Keep prices in step with what they cost us.\n"}
MISPLACED = {
    "replaces a place inside the decision the decision holds nothing under":
        lambda client: write(client, DECISION, PURPOSE, path="sections/nowhere"),
    "replaces a place inside the decision that runs on past a piece of prose":
        lambda client: write(client, DECISION, PURPOSE, path="sections/purpose/body/first"),
    "replaces a place inside the decision beginning at the decision's own version":
        lambda client: write(client, DECISION, PURPOSE, path="revision"),
    "adds an item at a place inside the decision that is not a collection":
        lambda client: append(client, DECISION, "sections/purpose", {"title": "Go monthly"}),
}


@when(
    parsers.re(f"the client (?P<call>{'|'.join(map(re.escape, MISPLACED))}), saying which role and why"),
    target_fixture="attempt",
)
def _aim_at_a_wrong_place(root, client, call):
    before = (root / "kb" / f"{DECISION}.yaml").read_bytes()
    return {"response": MISPLACED[call](client), "before": before}


@then("the change is rejected because the decision holds nothing at that place")
def _rejected_for_nothing_there(attempt):
    faults = attempt["response"].faults
    assert [(fault.artifact, fault.rule) for fault in faults] == [(DECISION, "not-found")]
    assert f"holds nothing at {faults[0].path!r}" in faults[0].message


@then("the change is rejected because a place inside an artifact never names what only the store settles")
def _rejected_for_a_settled_place(attempt):
    faults = attempt["response"].faults
    assert [(fault.artifact, fault.path, fault.rule) for fault in faults] == [(DECISION, "revision", "identity")]
    assert faults[0].message.startswith("a place inside an artifact never names what only the store settles")


@then("the change is rejected because an item is added to a collection, and that place is not one")
def _rejected_for_no_collection(attempt):
    faults = attempt["response"].faults
    assert [(fault.artifact, fault.path, fault.rule) for fault in faults] == [(DECISION, "sections/purpose", "collection")]
    assert faults[0].message.startswith("an item is added to a collection")
```

- [ ] **Step 2: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-65 2>&1 | grep -E "^E  " | cut -c1-120; .venv/bin/python -m pytest -q -m slice-65 2>&1 | tail -1
```

Expected: `3 failed, 1 passed`: `AttributeError: 'str' object has no attribute 'get'` (past the prose), `assert [] == [(... 'identity')]` (the version, accepted), and `('...', 'sections/purpose', 'not-found') != (..., 'collection')`. The row holding nothing passes now that it has steps; it is credited to this slice with the others.

- [ ] **Step 3: The faults**

In `src/kb/refusals.py`, replace the whole of `no_collection`

```python
def no_collection(artifact_id: ArtifactId, collection: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(artifact_id), path=collection, rule="not-found",
        message=f"{str(artifact_id)!r} holds no collection called {collection!r}",
    )
```

with

```python
def not_a_collection(locator: Locator) -> kb_pb2.Fault:
    place = "/".join(locator.place)
    return kb_pb2.Fault(
        artifact=str(locator.id), path=place, rule="collection",
        message=f"an item is added to a collection, and {place!r} in {str(locator.id)!r} is not one",
    )
```

and just above `def whole_only(`, add:

```python
def settled_place(locator: Locator) -> kb_pb2.Fault:
    place = "/".join(locator.place)
    return kb_pb2.Fault(
        artifact=str(locator.id), path=place, rule="identity",
        message=f"a place inside an artifact never names what only the store settles; {place!r} begins at {locator.place[0]!r}",
    )


```

- [ ] **Step 4: `places.py`**

Create `src/kb/places.py`:

```python
"""Places inside an artifact: pairs of a collection and the name of an item in it, a section named by its title's name
and a part by its id, which may end in a field. A place is resolved here, once, to where its node stands, or refused
saying why nothing stands there."""
from typing import NamedTuple

from kb import canonical, names, refusals
from kb.values import Locator, Refused


class Spot(NamedTuple):
    """Where a place's node stands: what holds it, the key or index it stands under there, and, when it is an item,
    the collection it is an item of."""
    holder: dict | list
    key: str | int
    collection: str = ""


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


def _index(collection: str, items, name: str) -> int | None:
    """Where in a collection the item of that name stands, or None when the collection is not one or lacks it."""
    if not isinstance(items, list):
        return None
    for index, item in enumerate(items):
        if isinstance(item, dict) and _name(collection, item) == name:
            return index
    return None


def _name(collection: str, item: dict) -> str | None:
    """How a place names an item: a section by its title's name, a part by its id."""
    if collection == "sections":
        return names.slug(item["title"]) if isinstance(item.get("title"), str) else None
    return item.get("id")
```

- [ ] **Step 5: Replacement and addition resolve through it**

In `src/kb/edits.py`, replace `from kb import canonical, names, refusals, requests, validation, values` with `from kb import canonical, names, places, refusals, requests, validation, values`.

Replace the whole of `_append`

```python
def _append(draft: Draft, addition: requests.Add) -> Change:
    """One item put at the end of a collection the artifact's type declares, and named there."""
    locator = addition.locator
    if not draft.holds(locator.id):
        raise Refused([refusals.not_found(locator.id)])
    if addition.item.problems:
        raise Refused(addition.item.refusal(str(locator.id)))
    item, collection = addition.item.tree, "/".join(locator.place)
    if collection not in draft.schema(locator.id.kind)["schema"].get("parts", {}):
        raise Refused([refusals.no_collection(locator.id, collection)])
    current = draft.artifact(locator.id)
    content = _content_of(current)
    content.setdefault(collection, []).append(item)
    _revise(draft, locator.id, current, content)
    return Change("append", locator.id, f"{collection}/{item['id']}", item["id"])
```

with

```python
def _append(draft: Draft, addition: requests.Add) -> Change:
    """One item put at the end of a collection the artifact's type declares, and named there."""
    locator = addition.locator
    if not draft.holds(locator.id):
        raise Refused([refusals.not_found(locator.id)])
    if addition.item.problems:
        raise Refused(addition.item.refusal(str(locator.id)))
    if not locator.place:
        raise Refused([refusals.not_a_collection(locator)])
    current = draft.artifact(locator.id)
    content = _content_of(current)
    spot = places.resolve(content, locator)
    if spot.holder is not content or spot.key not in draft.schema(locator.id.kind)["schema"].get("parts", {}):
        raise Refused([refusals.not_a_collection(locator)])
    item = addition.item.tree
    content.setdefault(spot.key, []).append(item)
    _revise(draft, locator.id, current, content)
    return Change("append", locator.id, f"{spot.key}/{item['id']}", item["id"])
```

Replace the whole of `_placed` and `_node_name`

```python
def _placed(artifact: dict, locator: values.Locator, node: dict) -> dict:
    """The artifact's content with the node at the locator's place replaced by the one given. A place is pairs of a
    list and an item in it, a section named by its title's name and a part by its id, and may end in a field."""
    content = _content_of(artifact)
    holder, steps = content, list(locator.place)
    while len(steps) > 1:
        collection, name = steps.pop(0), steps.pop(0)
        found = holder.get(collection, [])
        index = next((index for index, item in enumerate(found) if _node_name(collection, item) == name), None)
        if index is None:
            raise Refused([refusals.nothing_at(locator)])
        if not steps:
            found[index] = node if collection == "sections" else {"id": name, **node}
            return content
        holder = found[index]
    holder[steps[0]] = node
    return content


def _node_name(collection: str, item: dict) -> str:
    """How a place names an item: a section by its title's name, a part by its id."""
    return names.slug(item["title"]) if collection == "sections" else item.get("id")
```

with

```python
def _placed(artifact: dict, locator: values.Locator, node: dict) -> dict:
    """The artifact's content with the node at the locator's place replaced by the one given; an item keeps its
    name."""
    content = _content_of(artifact)
    spot = places.resolve(content, locator)
    if spot.collection and spot.collection != "sections":
        node = {"id": locator.place[-1], **node}
    spot.holder[spot.key] = node
    return content
```

- [ ] **Step 6: The module map**

In `CLAUDE.md`, just above the row beginning `` | `read.py` ``, add:

```markdown
| `places.py` | resolving a place inside an artifact to where its node stands, or the refusal saying why nothing does | I/O, what an operation does there |
```

- [ ] **Step 7: Run it green**

```bash
.venv/bin/python -m pytest -q -m slice-65 2>&1 | tail -1
.venv/bin/python -m pytest -q 2>&1 | tail -1
grep -n "holder.get\|_node_name\|no_collection" src/kb/*.py
```

Expected: `4 passed`; `67 failed, 129 passed`; one line, `src/kb/places.py` (`items = holder.get(collection)`).

- [ ] **Step 8: Checkpoint and commit**

Append the slice 65 checkpoint and set slice 65's Status to `green`.

```bash
git add src/kb tests CLAUDE.md docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 65: A place that names nothing real is refused before anything is touched

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Slice 66, an item is checked against its own type

**Slice plan entry:** Slice 66, capability. Unknown: can the collections a type declares join its composed schema, so that each item is checked against its item's type along with everything else? Scenario:

- kb / add-an-item-to-a-collection / An item missing something its own type requires is refused

The Background's process type does not require a role on a step, and its two steps name none. So the When first makes it so: it writes the process type at version 2, whose steps must name a role, and gives the two steps a role each, before it takes what the process holds and adds a step naming none.

**Files:**
- Modify: `src/kb/validation.py` (`compose`, `_collections`, `_item`)
- Modify: `tests/test_add_an_item_to_a_collection.py` (import; the Then `the process holds ...` compares with what the When read; a helper, one When, one Then appended)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `calls.PROCESS_TYPE`, `calls.write`, `STEPS`, `PROCESS`, `append`, `read` in the test module.
- Produces: `validation.compose(schema)` now carries each collection's shape. Items' faults come back at `<collection>/<index>` with JSON Schema's rule.

- [ ] **Step 1: The steps**

In `tests/test_add_an_item_to_a_collection.py`, replace the first line `from pytest_bdd import given, parsers, scenarios, then, when` with

```python
import copy

from pytest_bdd import given, parsers, scenarios, then, when
```

In the Then `the process holds the steps it held before, at the version it held before`, delete its last line, `    assert _steps(client) == STEPS`. The line before it already compares the process with what the When read just before its call, and the new When changes the steps before it reads.

Append at the end of the file:

```python
def _steps_must_name_a_role(client):
    """The process type at its next version, whose steps must each name a role, and the process's two steps given
    one, so the process fits it."""
    staffed = copy.deepcopy(PROCESS_TYPE["schema"])
    step = staffed["parts"]["steps"]["items"]
    step["properties"]["role"] = {"type": "string"}
    step["required"] = ["title", "role"]
    assert not write(client, "schema/process", {"version": 2, "schema": staffed}, message="Steps name a role").faults
    staffed_steps = [{**STEPS[0], "role": "opener"}, {**STEPS[1], "role": "opener"}]
    assert not write(client, PROCESS, {"steps": staffed_steps}, message="Say who does each step").faults


@when("the client adds a step with no role named, where a step must name a role, saying which role and why", target_fixture="attempt")
def _add_a_step_naming_no_role(client):
    _steps_must_name_a_role(client)
    before = read(client, PROCESS, whole=True)
    response = append(client, PROCESS, "steps", {"title": "Count the float"})
    return {"response": response, "before": before}


@then("the item is rejected because the content does not fit the type")
def _rejected_for_its_type(attempt):
    faults = attempt["response"].faults
    assert [(fault.artifact, fault.path, fault.rule) for fault in faults] == [(PROCESS, "steps/2", "required")]
    assert "'role'" in faults[0].message
```

- [ ] **Step 2: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-66 2>&1 | grep -E "^E  " | head -3; .venv/bin/python -m pytest -q 2>&1 | tail -1
```

Expected: `AssertionError: assert [] == [('process/op..., 'required')]`: the step was added with no role. The suite reads `67 failed, 129 passed`: the scenario of slice 39 whose Then lost its line still passes.

- [ ] **Step 3: Collections in the composed schema**

In `src/kb/validation.py`, replace the whole of `compose`

```python
def compose(schema: dict) -> dict:
    """One effective schema: the type's, with kb's structural rules beside it under allOf.

    The type stays the root, so its own `#` references still resolve; kb's shapes sit under `$defs/kb-*`.
    """
    return {
        **schema,
        "allOf": [*schema.get("allOf", []), STRUCTURE],
        "$defs": {**schema.get("$defs", {}), "kb-section": SECTION},
    }
```

with

```python
def compose(schema: dict) -> dict:
    """One effective schema: the type's, with kb's structural rules and the shape of each collection it declares
    beside it under allOf.

    The type stays the root, so its own `#` references still resolve; kb's shapes sit under `$defs/kb-*`.
    """
    return {
        **schema,
        "allOf": [*schema.get("allOf", []), STRUCTURE, *_collections(schema)],
        "$defs": {**schema.get("$defs", {}), "kb-section": SECTION},
    }


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
    return {**item_schema, "allOf": [*item_schema.get("allOf", []), *_collections(item_schema)]}
```

- [ ] **Step 4: Run it green**

```bash
.venv/bin/python -m pytest -q -m slice-66 2>&1 | tail -1
.venv/bin/python -m pytest -q 2>&1 | tail -1
wc -l src/kb/validation.py
```

Expected: `1 passed`; `66 failed, 130 passed`; `246`. Nothing else in this batch adds to `validation.py` (Global Constraints, Size).

- [ ] **Step 5: Checkpoint and commit**

Append the slice 66 checkpoint, with Review Focus 5 as a `QUESTION FOR THE SPEC` line, and set slice 66's Status to `green`.

```bash
git add src/kb tests docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 66: An item is checked against its own type

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Slice 67, an item's name is the store's to give and the client's only to hand back

**Slice plan entry:** Slice 67, capability. Unknown: can the names a change hands back be judged against the collection as the draft holds it, by the one module that decides names, without that module reading anything? Scenario (one outline, three rows):

- kb / change-an-artifact / Every way an item's name can be wrong on a change is refused

Needs: the Given `the decision carries two options`, which slice 86 will use too.

**Files:**
- Modify: `src/kb/names.py` (`Misnamed`, `handed_back`)
- Modify: `src/kb/refusals.py` (`MISNAMED`, `misnamed`)
- Modify: `src/kb/edits.py` (`_revise` checks the names handed back)
- Modify: `tests/test_change_an_artifact.py` (the Then `reading the decision gives what it held before ...` reads the version from the bytes it kept; one Given, one When, three Thens appended)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: Task 3's module state (`re` imported in the test module), `SECTIONS`, `DECISION`, `write`, `read`, `loads`, `canonical`, `parsers`.
- Produces: `names.Misnamed(collection: str, index: int, name: object, why: str)` with `why` one of `"not-plain"`, `"repeated"`, `"unknown"`; `names.handed_back(schema: dict, content: dict, held: dict[str, set]) -> list[Misnamed]`; `refusals.misnamed(artifact_id, found: Misnamed) -> Fault` (rule `item-name`, path `<collection>/<index>/id`). The test module's `OPTIONS` and the Given `the decision carries two options` are slice 86's too.

- [ ] **Step 1: The steps**

In `tests/test_change_an_artifact.py`, in the Then `reading the decision gives what it held before, at the version it held before`, replace

```python
    assert read(client, DECISION).revision == 1
```

with

```python
    assert read(client, DECISION).revision == canonical.load(attempt["before"].decode())["revision"]
```

The version was always 1 when this Then was written; the new Given moves it to 2 before the When.

Append at the end of the file:

```python
OPTIONS = [{"title": "Keep weekly", "body": "Review every Monday."}, {"title": "Go monthly", "body": "Review on the first."}]


@given("the decision carries two options")
def _two_options(client):
    response = write(client, DECISION, {"sections": SECTIONS, "options": OPTIONS}, message="Weigh two options")
    assert not response.faults, response.faults
    assert [option["id"] for option in loads(read(client, DECISION, whole=True).content)["options"]] == [
        "keep-weekly", "go-monthly",
    ]


HANDED_BACK = {
    "one of which carries a name no option of that decision has": ["keep-weekly", "go-fortnightly"],
    "both of which carry the same name": ["keep-weekly", "keep-weekly"],
    "one of which carries a name that is not a plain name": ["keep-weekly", "Go Monthly!"],
}


@when(
    parsers.re(f"the client replaces the decision with options (?P<items>{'|'.join(map(re.escape, HANDED_BACK))}), saying which role and why"),
    target_fixture="attempt",
)
def _replace_with_misnamed_options(root, client, items):
    before = (root / "kb" / f"{DECISION}.yaml").read_bytes()
    options = [{"id": name, **option} for name, option in zip(HANDED_BACK[items], OPTIONS)]
    response = write(client, DECISION, {"sections": SECTIONS, "options": options}, message="Rename the options")
    return {"response": response, "before": before}


def _misnamed(attempt, message):
    faults = attempt["response"].faults
    assert [(fault.artifact, fault.path, fault.rule) for fault in faults] == [(DECISION, "options/1/id", "item-name")]
    assert faults[0].message.startswith(message)


@then("the change is rejected because a name on an item names an item already in that collection")
def _rejected_for_an_unknown_name(attempt):
    _misnamed(attempt, "a name on an item names an item already in that collection")


@then("the change is rejected because the items of a collection each have a name of their own")
def _rejected_for_a_repeated_name(attempt):
    _misnamed(attempt, "the items of a collection each have a name of their own")


@then("the change is rejected because a name is a plain name of lower-case letters, digits and single hyphens")
def _rejected_for_a_name_not_plain(attempt):
    _misnamed(attempt, "a name is a plain name of lower-case letters, digits and single hyphens")
```

- [ ] **Step 2: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-67 2>&1 | grep -E "^E  " | head -3; .venv/bin/python -m pytest -q -m slice-67 2>&1 | tail -1
.venv/bin/python -m pytest -q 2>&1 | tail -1
```

Expected: `3 failed`, each `AssertionError: assert [] == [('decision/p... 'item-name')]`: every one of the names was stored as sent. The suite reads `66 failed, 130 passed` (the Then's change keeps its scenarios green).

- [ ] **Step 3: What a handed-back name may be, in `names.py`**

In `src/kb/names.py`, replace `import re` with

```python
import re
from typing import NamedTuple
```

and append at the end of the file:

```python
class Misnamed(NamedTuple):
    """A name handed back on an item that the store could not have given it: where it is, the name, and why not:
    "not-plain", "repeated", or "unknown" when no item of that collection had it."""
    collection: str
    index: int
    name: object
    why: str


def handed_back(schema: dict, content: dict, held: dict[str, set]) -> list[Misnamed]:
    """Every name on an item of a collection that is not the name of an item the collection held, given once. held
    is the names each collection held before the change."""
    found = []
    for collection in schema.get("parts", {}):
        seen = set()
        for index, item in enumerate(content.get(collection, [])):
            if not isinstance(item, dict) or "id" not in item:
                continue
            name = item["id"]
            if not isinstance(name, str) or not plain(name):
                found.append(Misnamed(collection, index, name, "not-plain"))
            elif name in seen:
                found.append(Misnamed(collection, index, name, "repeated"))
            elif name not in held.get(collection, set()):
                found.append(Misnamed(collection, index, name, "unknown"))
            seen.add(name)
    return found
```

- [ ] **Step 4: The fault, in `refusals.py`**

In `src/kb/refusals.py`, replace `from kb.values import ArtifactId, Locator` with

```python
from kb.names import Misnamed
from kb.values import ArtifactId, Locator
```

and just above `def unwritable(`, add:

```python
MISNAMED = {
    "not-plain": "a name is a plain name of lower-case letters, digits and single hyphens; {name!r} is not",
    "repeated": "the items of a collection each have a name of their own; {name!r} is on more than one",
    "unknown": "a name on an item names an item already in that collection; {collection!r} held no item named {name!r}",
}


def misnamed(artifact_id: ArtifactId, found: Misnamed) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(artifact_id), path=f"{found.collection}/{found.index}/id", rule="item-name",
        message=MISNAMED[found.why].format(name=found.name, collection=found.collection),
    )


```

- [ ] **Step 5: Every revision checks the names it hands back**

In `src/kb/edits.py`, in `_revise`, replace the docstring and the lines down to the first `names.items` call

```python
    """The artifact's next version put in the draft: the content checked against the current version of its type,
    its items named, its version up by one, its title kept. Raises Refused with every fault."""
    schema = draft.schema(artifact_id.kind)
    faults = validation.validate(str(artifact_id), {"title": current["title"], **content}, schema["schema"], draft)
    if faults:
        raise Refused(faults)
    names.items(schema["schema"], content, keep_named=True)
```

with

```python
    """The artifact's next version put in the draft: the names its items hand back checked against those the artifact
    held, the content checked against the current version of its type, its new items named, its version up by one,
    its title kept. Raises Refused with every fault."""
    schema = draft.schema(artifact_id.kind)
    held = {collection: {item.get("id") for item in current.get(collection, [])}
            for collection in schema["schema"].get("parts", {})}
    faults = [refusals.misnamed(artifact_id, found) for found in names.handed_back(schema["schema"], content, held)]
    faults += validation.validate(str(artifact_id), {"title": current["title"], **content}, schema["schema"], draft)
    if faults:
        raise Refused(faults)
    names.items(schema["schema"], content, keep_named=True)
```

- [ ] **Step 6: Run it green, and the rule's check**

```bash
.venv/bin/python -m pytest -q -m slice-67 2>&1 | tail -1
.venv/bin/python -m pytest -q 2>&1 | tail -1
grep -nE "\[a-z0-9\]|re\.sub|-\{number\}|plain\(" src/kb/*.py | grep -v "^src/kb/names.py"
```

Expected: `3 passed`; `63 failed, 133 passed`; the grep prints three lines, all in `src/kb/values.py`, each a conversion asking `names.plain(...)`, as slice 55 left them; no line outside `names.py` decides a name itself.

- [ ] **Step 7: Checkpoint and commit**

Append the slice 67 checkpoint and set slice 67's Status to `green`.

```bash
git add src/kb tests docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 67: An item's name is the store's to give and the client's only to hand back

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Slice 68, a type that could never check anything is refused when it is defined

**Slice plan entry:** Slice 68, capability. Unknown: can a type be checked as it is written against the types the draft holds, so that it is resolved once, here, rather than by every create that uses it? Scenario (one outline, three rows):

- kb / define-a-type / A type the store could never check anything against is refused when it is written

**Files:**
- Create: `src/kb/definitions.py`
- Modify: `src/kb/refusals.py` (`no_such_shape`, `built_on_itself`, `no_targets`)
- Modify: `src/kb/edits.py` (`_fits`, used by `_create` and `_revise`)
- Modify: `CLAUDE.md` (module map row for `definitions.py`)
- Modify: `tests/test_define_a_type.py` (imports; one When, a helper, four Thens appended)
- Modify: `docs/superpowers/plans/2026-09-24-kb-slices.md` (checkpoint)

**Interfaces:**
- Consumes: `validation.TYPE_URI`, `values.artifact_id`, `Draft.holds`, and Task 5's `_revise` (whose `validation.validate` call becomes `_fits`). In the tests: `calls.request`, `calls.everything_under`.
- Produces: `definitions.faults(type_id: ArtifactId, content: dict, draft) -> list[kb_pb2.Fault]`; `edits._fits(draft, artifact_id, content, schema) -> list` (private); `refusals.no_such_shape(type_id, place, ref)` (rule `shape`), `refusals.built_on_itself(type_id, place, ref)` (rule `built-on`), `refusals.no_targets(type_id, place, field)` (rule `targets`). Slice 84 (a type's version moves on) adds its check to `definitions.faults`.

- [ ] **Step 1: The steps**

In `tests/test_define_a_type.py`, replace

```python
from pytest_bdd import given, scenarios, then, when

from calls import create, define, read, request
```

with

```python
import re

from pytest_bdd import given, parsers, scenarios, then, when

from calls import create, define, everything_under, read, request
```

and append at the end of the file:

```python
NEVER_CHECKABLE = {
    "refers to a shape from a type the store does not hold": ("Tool use", {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "bindings": {"type": "array", "items": {"$ref": "kb:schema/nothing#/$defs/binding"}},
        },
    }),
    "names itself as the type it is built on": ("Decision", {
        "allOf": [{"$ref": "kb:schema/decision"}],
        "type": "object",
        "properties": {"title": {"type": "string"}},
    }),
    "declares a link field without saying which kinds it may point at": ("Note", {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "relates_to": {"type": "string", "ref": {"cardinality": "one", "parts": False, "on_delete": "refuse"}},
        },
    }),
}


@when(parsers.re(f"the client defines a type that (?P<fault>{'|'.join(map(re.escape, NEVER_CHECKABLE))})"), target_fixture="attempt")
def _define_a_type_never_checkable(root, client, fault):
    before = everything_under(root)
    title, schema = NEVER_CHECKABLE[fault]
    response = request(client, "schema", title, {"version": 1, "schema": schema}, message=f"Define {title}")
    return {"response": response, "before": before, "after": everything_under(root)}


def _type_rejected(attempt, rule, path, message):
    faults = attempt["response"].faults
    assert (attempt["response"].id, attempt["response"].revision) == ("", 0)
    assert [(fault.path, fault.rule) for fault in faults] == [(path, rule)]
    assert faults[0].message.startswith(message)


@then("the type is rejected because a shape a type refers to must belong to a type the store holds")
def _rejected_for_a_shape_not_held(attempt):
    _type_rejected(attempt, "shape", "schema/properties/bindings/items/$ref",
                   "a shape a type refers to must belong to a type the store holds")


@then("the type is rejected because a type cannot be built on itself")
def _rejected_for_building_on_itself(attempt):
    _type_rejected(attempt, "built-on", "schema/allOf/0/$ref", "a type cannot be built on itself")


@then("the type is rejected because a link field says which kinds it may point at")
def _rejected_for_a_link_without_kinds(attempt):
    _type_rejected(attempt, "targets", "schema/properties/relates_to", "a link field says which kinds it may point at")


@then("nothing is written anywhere in the store")
def _nothing_written(attempt):
    assert attempt["after"] == attempt["before"]
```

- [ ] **Step 2: Run it red**

```bash
.venv/bin/python -m pytest -q -m slice-68 2>&1 | grep -E "^E  " | head -2; .venv/bin/python -m pytest -q -m slice-68 2>&1 | tail -1
```

Expected: `3 failed`, the first `AssertionError: assert ('schema/tool-use', 1) == ('', 0)`: each type was stored.

- [ ] **Step 3: The faults**

In `src/kb/refusals.py`, just above `def unwritable(`, add:

```python
def no_such_shape(type_id: ArtifactId, place: str, ref: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(type_id), path=place, rule="shape",
        message=f"a shape a type refers to must belong to a type the store holds; {ref!r} does not",
    )


def built_on_itself(type_id: ArtifactId, place: str, ref: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(type_id), path=place, rule="built-on",
        message=f"a type cannot be built on itself; {str(type_id)!r} names {ref!r}",
    )


def no_targets(type_id: ArtifactId, place: str, field: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(type_id), path=place, rule="targets",
        message=f"a link field says which kinds it may point at; {field!r} does not",
    )


```

- [ ] **Step 4: `definitions.py`**

Create `src/kb/definitions.py`:

```python
"""A type checked as it is written, against the types the draft holds: every shape it refers to belongs to a type the
store holds, it is not built on itself, and every link field says which kinds it may point at. What a type could never
check an artifact against is refused here, once, rather than by every create that uses it."""
from kb import refusals, values
from kb.contract import kb_pb2
from kb.validation import TYPE_URI
from kb.values import ArtifactId, Kind, Refused


def faults(type_id: ArtifactId, content: dict, draft) -> list[kb_pb2.Fault]:
    """Every way the type's schema could never be checked against, each at its place in the type."""
    schema = content.get("schema")
    found = []
    for place, ref in _refs(schema, "schema"):
        named = _type_named(ref)
        if named is None:
            continue
        if named == type_id and "#" not in ref:
            found.append(refusals.built_on_itself(type_id, place, ref))
        elif named is False or not draft.holds(named):
            found.append(refusals.no_such_shape(type_id, place, ref))
    for place, name, field in _link_fields(schema, "schema"):
        if not isinstance(field["ref"], dict) or "targets" not in field["ref"]:
            found.append(refusals.no_targets(type_id, place, name))
    return found


def _type_named(ref: str) -> ArtifactId | None | bool:
    """The type a kb: reference names; None for a reference that is not kb's, False for one naming no type at all."""
    if not ref.startswith(TYPE_URI):
        return None
    try:
        named = values.artifact_id(ref.removeprefix(TYPE_URI).partition("#")[0])
    except Refused:
        return False
    return named if named.kind == Kind("schema") else False


def _refs(node, place: str):
    """Every $ref in a schema, with its place, at every depth."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "$ref" and isinstance(value, str):
                yield f"{place}/$ref", value
            else:
                yield from _refs(value, f"{place}/{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _refs(value, f"{place}/{index}")


def _link_fields(node, place: str):
    """Every field declared with a `ref`, with its place and name, at every depth: the type's own, its items', its
    bases' and its shapes'."""
    if isinstance(node, dict):
        properties = node.get("properties")
        if isinstance(properties, dict):
            for name, field in properties.items():
                if isinstance(field, dict) and "ref" in field:
                    yield f"{place}/properties/{name}", name, field
        for key, value in node.items():
            yield from _link_fields(value, f"{place}/{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _link_fields(value, f"{place}/{index}")
```

- [ ] **Step 5: One check of content against its type, a type's included**

In `src/kb/edits.py`, replace `from kb import canonical, names, places, refusals, requests, validation, values` with `from kb import canonical, definitions, names, places, refusals, requests, validation, values`.

In `_create`, replace

```python
    faults = validation.validate(at, {"title": creation.title, **content}, schema["schema"], draft)
```

with

```python
    faults = _fits(draft, artifact_id, {"title": creation.title, **content}, schema)
```

In `_revise`, replace

```python
    faults += validation.validate(str(artifact_id), {"title": current["title"], **content}, schema["schema"], draft)
```

with

```python
    faults += _fits(draft, artifact_id, {"title": current["title"], **content}, schema)
```

Just above `def _content_of(`, add:

```python
def _fits(draft: Draft, artifact_id: ArtifactId, content: dict, schema: dict) -> list:
    """Every fault of the content against its type; a type, once it fits the type of types, checked as a type too."""
    faults = validation.validate(str(artifact_id), content, schema["schema"], draft)
    if not faults and artifact_id.kind == Kind("schema"):
        faults = definitions.faults(artifact_id, content, draft)
    return faults


```

In `_create`, the `artifact_id` is always bound where `_fits` is called: when the title gave no name, the title's faults were raised just before.

- [ ] **Step 6: The module map**

In `CLAUDE.md`, just below the row beginning `` | `validation.py` ``, add:

```markdown
| `definitions.py` | a type checked as it is written: what it refers to is held, it is not built on itself, its link fields say what they may point at | file access, checking artifacts against a type |
```

- [ ] **Step 7: Run it green, and the batch's structural checks**

```bash
.venv/bin/python -m pytest -q -m slice-68 2>&1 | tail -1
.venv/bin/python -m pytest -q -m "slice-63 or slice-64 or slice-65 or slice-66 or slice-67 or slice-68" 2>&1 | tail -1
.venv/bin/python -m pytest -q 2>&1 | tail -1
wc -l src/kb/*.py | sort -n | tail -4
grep -c "try:" src/kb/servicer.py
```

Expected: `3 passed`; `19 passed`; `60 failed, 136 passed`; the largest modules `validation.py` 246 and `values.py` 205, none over 250, total about 2249; `1`.

- [ ] **Step 8: Checkpoint and commit**

Append the slice 68 checkpoint, with Review Focus 2 as a `QUESTION FOR THE SPEC` line, and set slice 68's Status to `green`. Its "Next" line: slice 69, the second architecture review, which is not part of this plan.

```bash
git add src/kb tests CLAUDE.md docs/superpowers/plans/2026-09-24-kb-slices.md
git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit -m "Slice 68: A type that could never check anything is refused when it is defined

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## After slice 68

Slice 69 is the second architecture review: an Opus review of `src/kb/` against `CLAUDE.md` after these six slices, each refactor it calls for cut as a slice with a check. `validation.py` at 246 lines is the first thing it should weigh, since slices 71, 73 and 81 will each touch it. The whole-batch defect review runs as usual before it.
