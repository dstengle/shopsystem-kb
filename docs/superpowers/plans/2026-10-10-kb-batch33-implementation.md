# kb batch 33 Implementation Plan: every version of a type is held

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Each task is one slice, implemented under shopsystem-bdd:bdd-red-green. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** kb holds every version of a type, numbered by the store and fixed once made, each read at its own IRI; a create names the version it conforms to, an artifact keeps its version until a write names a later one, the store's check reads each artifact against its own version, and `kb:` references and link fields name a type or a version of one (slices 160.1, 160.2, 161 to 165).

**Architecture:** slice 161 was over the budget and is cut as expand, migrate, capability. 160.1 adds a table of type versions beside `artifacts` in the SQLite adapter, read through the port and used by nothing. 160.2 moves every read of a type's schema onto it. 161 then makes a change to a type land a new numbered version and retires the rule that made the client move the number. 162 to 165 build on held versions. The type's own row in `artifacts` stays throughout and is the version the type stands at.

**Tech Stack:** Python 3.11, grpcio/protobuf (`make contract`), SQLite, pytest-bdd 8.1, pytest-xdist.

**Spec:** `spec/capabilities/{define-a-type,check-a-change,change-the-store,check-the-store,name-what-is-asked-for,read-an-artifact}.md`, `spec/decisions.md` (decision/0027-each-type-version-is-its-own-iri, kb-numbers-type-versions, unused-type-versions-kept, references-name-a-version, an-artifact-keeps-its-version, rules-for-iri-refusals). Slices: `docs/superpowers/plans/2026-09-24-kb-slices.md`, slices 160.1 to 165. Research: `.superpowers/scout/2026-10-10-batch33/research.md` and `.superpowers/scout/2026-10-10-sizing/slices-161-165.md` (the planner's notes; an implementer need not read them).

## Global Constraints

- Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts
- One task per slice, in slice order. The plan holds no code. The implementer writes the steps and the code under bdd-red-green, after the red run.
- Each task has a `Review:` and a `Model:` line, and the controller dispatches by them. `Review: per-task` with `Model: opus` goes to a task that touches concurrency, the published contract, data integrity or moving stored data. `Review: batch-end` with `Model: sonnet` goes to every other task, and gets no task review because the batch's branch review covers it.
- CLAUDE.md's rules hold:
  - No module under `src/kb/` may pass 250 lines, and `servicer.py` must stay under 150. A module that would pass its limit is split first; a new module gets a row in CLAUDE.md's map.
  - Rule 1: no broad `except` outside `servicer.py`'s wrapper.
  - Rule 2: a request field becomes a value in `values.py` (or `signatures.py`) before anything else sees it.
  - Rule 4: draft, validate, land; a version lands with its set in the one transaction.
  - Rule 6: only `names.py` decides what an IRI, a version's IRI or a name looks like.
  - When a task changes what a module owns, it changes that module's row in CLAUDE.md's map too.
- No migration: the store's form stays `store: 2`. Nothing of form 2 has been released, so the new table is simply part of form 2.
- An implementer may change what an existing test asserts only where its task's "Tests the decisions break" lists it. Any other existing test that the decisions break is a `BLOCKED` reply naming it.
- At this batch's end, every scenario tagged up to `@slice-165` passes. Every failing test is then a scenario tagged `@slice-166` onward, or the published contract's rule-name test (slice 182, rule `differs`).

### Execution rules

- **Paths in, short replies out.** The controller dispatches with paths (brief, report, findings, review package, notes) and reads replies, `plan show` and `git log --oneline`. It does not open a diff, a report, a findings file or source: it writes a review package by redirecting `git` output to a file. The one exception is a `BLOCKED` or `NEEDS_CONTEXT` reply, where it reads the part of the report the reply names, to decide or to ask the person.
- **By step.** A task with Steps is dispatched one step at a time, each to a fresh `bdd-implementer` that is told the step and the task's one report file. One implementer at a time in a worktree. A `PARTIAL` reply is answered with a fresh implementer told it is a continuation, with the same report.
- **One review per `Review: per-task` task,** after its last step, from the commit before its first. The reviewer is given a findings file to write. A `Review: batch-end` task gets none. A diff over 8 production or 4 test files is reviewed by area, each reviewer given its paths and its own findings file, in parallel.
- **Fresh fixes.** Findings go to a fresh `bdd-implementer` as a fix round, with the report and the findings file, then to a scoped re-review. No agent is resumed. The branch review's reply is the one long reply the controller reads: it saves the issues to fix now as a findings file for the fix round.
- **Lanes.** Tasks in different lanes may run at once, each lane in its own git worktree and branch with its own virtualenv, and the dispatch tells each implementer it is in a lane. This replaces subagent-driven-development's rule against parallel implementers, for lanes only. Tasks in one lane run in order; a task with no `Lane:` runs in the main worktree, in order, and not beside a lane. A lane's task is reviewed in its lane, before the merge. A lane's implementer never commits the plan: its reply carries the checkpoint entry. The controller merges the lanes one at a time, runs the suite after each merge, and writes each slice's Status, the checkpoint entry from the reply and the `Suite:` entry itself with `plan`.

No task of this batch has a `Lane:`: every pair shares a production module or `tests/test_define_a_type.py`, and each needs the one before it.

### Binding values, verbatim from the spec

- define-a-type: each version of a type is "numbered by the store and fixed once made"; "kb numbers a type's versions: the first is 1 ... Every held version is kept as it was made"; "the store gives the new version the next number".
- decision/kb-numbers-type-versions: "When a type is changed, kb gives the new version the next number; the client no longer moves a type's version on, so a change that does not is no longer refused."
- decision/an-artifact-keeps-its-version: "a write naming no version keeps the version its artifact conforms to ... an artifact moves only to a later version ... that a write names".
- decision/rules-for-iri-refusals: "a version not held, or not later than the one an artifact conforms to, carries `version`."
- The IRI grammar: "a type version's IRI is a type's IRI followed by `@<n>`".

## Decisions this plan takes

Each decision rests on the line or ledger entry named, so that the implementer does not decide it alone.

1. **Where versions are kept.** Version rows live in a table of their own in the SQLite adapter, outside `artifacts`, keyed by the version's IRI, with the type's IRI, the number, and the content, revision and title the version was made with. The table is not named `versions` (that name is the per-revision history's). The type's own row in `artifacts` stays and is the version the type stands at, so `ids()`, listings, export and import are unchanged until their own slices (174, 181).
2. **The store's form** stays `store: 2` (Global Constraints; no migration).
3. **Numbering** (decision/kb-numbers-type-versions; define-a-type: "each change to the type makes the next"). Every accepted change to a type makes the next number, an unchanged schema included. Two changes to one type in one set make two versions, in the order of the set.
4. **A `version` key in a type's content** (QUESTION FOR THE SPEC in the plan log, recommended answer applied). A type's content keeps its integer `version`, and kb writes the number it gives there: on a define it is 1, on a change the next number, whatever the client sent. A client's number is neither required nor refused. So a type's content reads back with the number kb gave, and the metaschema is unchanged.
5. **Reads** (define-a-type: each earlier version "reads back as it was made"; define-a-type.feature's Then lines decide the details). A read at a type's IRI gives the version it stands at, as today. A read at `<type IRI>@<n>` gives that version: its content, and the revision and title it was made with. Where a Then line says what `id` or `type` a version reads back with, it decides; where none does, `id` is the version's IRI.
6. **Rule `version` stays** in `rules.py` and the published list, for a version not held and for a replacement naming an earlier version or another type's (decision/rules-for-iri-refusals; change-the-store). Only its use for a change that does not move a type's version is retired (`definitions.version_kept`, `type_refusals.version_kept`).
7. **A create names its version** (slice 162; check-a-change). A create is drafted and checked, content and links, against the version it names, when that version is held; the latest is not consulted.
8. **An artifact keeps its version** (slice 163; decision/an-artifact-keeps-its-version). A change naming no version leaves the artifact's `type` as it is and checks it against that version. A replacement naming a later version of the artifact's own type moves it there and checks it against that. One naming an earlier version, or a version of another type, is refused with `version`. On the wire, `ReplaceRequest` and each replace of `BatchReplaceRequest` gain an optional `type`, the version's IRI; the golden file gains the fields.
9. **The check** (slice 164; check-the-store). Each artifact is read against the version it conforms to. It is listed as behind when its type stands at a later version. A violation is only what does not fit its own version.
10. **References and link fields** (slice 165; decision/references-name-a-version). A `kb:<type IRI>@<n>` reference resolves to that held version whatever the type stands at now; one naming a version not held is refused when the type is written. A link field's `targets` names a type by its IRI and reaches artifacts of any version of it. Changing a base type no longer leaves a reference to its earlier version dangling (the person's ruling of 2026-10-10: slice 165 holds the version, restores the relink tests removed in bd159cd, and pins it).

## Review Focus

1. **A version is fixed once made.** After a type changes twice, its first version read at its IRI is byte for byte what the define gave (with `version` 1). Owner: Task 3, a plain test through the contract.
2. **A version lands with its set or not at all.** A set that changes a type and is refused for another change leaves no version row. Owner: Task 3, a plain test through the port or the contract.
3. **A type changed while a create naming its earlier version is being written.** The create lands at the version it named (it is held), where slice 156 refused it. Owner: Task 4, by restoring or adjusting the concurrency case in `tests/test_a_type_moving_under_a_change.py` only if the task's "Tests the decisions break" lists it; otherwise a new plain test.
4. **A removed type's versions.** Removing a type nothing conforms to removes its versions with it, and defining a type there again starts at 1. No line says so. Owner: Task 3 reports what happens today as an open question in its checkpoint; nothing is built for it.
5. **A store file made before this batch** has no versions table. Nothing of form 2 is released, so nothing is done for it; Task 1 searches `tests/` and `features/` for stored database fixtures and reports any.

QUESTION FOR THE SPEC (logged, recommended answer applied as decision 4): once kb numbers versions, whether a type's content still carries `version`, and what a number the client sends means.

---

### Task 1: Slice 160.1. The store keeps each type's version beside the type

Review: per-task
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Check:** `make test` gives the same passed and failed tests as the record before it; the storage port's conformance tests of a type version read by its IRI pass; nothing outside the port and its adapter reads the versions yet.
- [ ] **Why it fails today:** the store holds one row per type, in `artifacts`; a version's IRI resolves to nothing; the port has no read of a version.
- [ ] **Where the change lands** (4 production, 1 test):
  - A new SQLite adapter module for type versions (their table's schema, a version written, a version read), because `sqlite_store.py` is at 225 lines and slices 160.1 and 161 would take it past 250. It gets a row in CLAUDE.md's map; `sqlite_store.py`'s row says the version of a type is written through it when a type lands.
  - `src/kb/sqlite_store.py`: the table made with the database; when a type's change lands, the version it stands at is written in the same transaction (today that is always the one version, replaced in place when the type changes, since nothing numbers a second yet).
  - `src/kb/port.py`: the read of a type version by its IRI, in the interface every adapter answers.
  - `src/kb/sqlite_reads.py`: that read over the connection, inside the read moment already open.
  - `tests/test_the_storage_port.py`: added conformance cases only: a type's version read back by its IRI with the content, revision and title it was made with; `ids()` does not list versions; the type that describes types has its version from the start of a store.
- [ ] **Decisions applied:** 1, 2. Review Focus 5.
- [ ] **Tests the decisions break:** none: the scout checked `tests/test_the_storage_port.py`'s `ids()` cases, export and import tests (version rows stay out of `artifacts`).
- [ ] **Verify:** the new conformance cases pass; `make test` fails no test that passed at the record before it and passes no scenario tagged `@slice-161` onward.
- [ ] **Checkpoint:** `plan status 160.1 green`, then `plan log "Suite: ..."`.

### Task 2: Slice 160.2. Types are read through the versions the store keeps

Review: batch-end
Model: sonnet
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Check:** `make test` gives the same passed and failed tests as the record before it; a plain test reads the version a type stands at by that version's IRI through the contract; a search shows a type's schema is read for checking only through the kept versions.
- [ ] **Why it fails today:** `composition.py` reads a type's schema from the type's one row in `artifacts`, and a read at a version's IRI is not found.
- [ ] **Where the change lands** (3 production, 1 test):
  - `src/kb/composition.py`: the held check, a type's schema, a kind's schema and the type a version names read the kept version, their signatures kept so their callers do not change.
  - `src/kb/draft.py`: a type read through its kept version, the draft's own changes to a type seen first, as today.
  - `src/kb/read.py`: a read whose locator is a version's IRI gives that version (decision 5).
  - One test module: the plain test of the read at a version's IRI, beside the existing plain tests of reads or of an artifact's IRI.
  - CLAUDE.md's rows for `composition.py`, `draft.py` and `read.py`.
- [ ] **Decisions applied:** 1, 5.
- [ ] **Tests the decisions break:** none: the behaviour is unchanged while one version is held; the scout checked the callers of `kind_schema` and `artifact_schema`.
- [ ] **Verify:** the plain test passes; `make test` fails no test that passed at the record before it; the search named in the Check is in the report with its result.
- [ ] **Checkpoint:** `plan status 160.2 green`, then `plan log "Suite: ..."`.

### Task 3: Slice 161. Every version of a type is held, numbered by the store

Review: per-task
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Scenarios** (`@slice-161`, 4 scenarios, 4 collected), all define-a-type:
  - The client changes a type
  - The client changes a type and the store numbers the new version
  - While an artifact conforms to a version of a type, the store holds that version
  - When no artifact conforms to a version of a type any longer, the store still holds that version
- [ ] **Why it is red today:** none has all its steps (the Givens "… changed once since it was defined", "… at its first version, and an artifact conforming to that version", "… at its second version, and the only artifact conforming to its first version", the When "the client changes that type", and the Thens on the first version still held). Behind them, a change to a type replaces its one version, and a change that does not move the content's `version` is refused with rule `version`.
- [ ] **Where the change lands** (7 production, 3 test):
  - `src/kb/port.py`, the adapter's type-versions module and `src/kb/sqlite_store.py`: a change to a type carries the version it makes; landing adds that version's row and leaves the earlier ones as they were.
  - `src/kb/edits.py`, `src/kb/drafting.py`, `src/kb/draft.py`: a type's change is given the next number from the versions held and the draft's own (two changes in one set make two), and that number is written into the type's content (decisions 3, 4).
  - `src/kb/definitions.py`, `src/kb/type_refusals.py`: `version_kept` retired (decision 6). `rules.py` is not touched.
  - `tests/test_define_a_type.py`, `tests/test_every_change_in_a_set.py`, `tests/test_the_storage_port.py`.
  - CLAUDE.md's rows for every module whose ownership changes (`edits.py`'s "a type's version moved on from the one it acted on", `type_refusals.py`'s "a version kept while the type changed", `drafting.py`, `port.py`, the adapter).
- [ ] **Decisions applied:** 1, 3, 4, 5, 6. Review Focus 1, 2, 4.
- [ ] **Tests the decisions break:**
  - `tests/test_define_a_type.py`, the orphan steps `_change_the_type_leaving_its_version` and `_rejected_for_the_version_kept` (no feature line uses them; they assert rule `version` for a change that leaves the version): decisions 3 and 6. Deleted.
  - `tests/test_every_change_in_a_set.py::test_a_type_changed_twice_in_a_set_moves_its_version_on_each_time` (asserts one `version` fault): decision 3. Rewritten to assert both changes land and the type stands at the third version, each of the three held at its IRI.
  - `tests/test_every_change_in_a_set.py`, the parametrized row whose change leaves `schema` out and expects a `version` fault beside `required`: decision 6. Rewritten to expect `required` alone.
  - `tests/calls.py` `next_version` and every test that sends `version` in a type's content (`test_change_an_artifact.py`, `test_make_several_changes_in_one_go.py`, `test_follow_the_links.py`, `test_add_an_item_to_a_collection.py`, `test_the_link_index.py`, `test_a_type_moving_under_a_change.py`): not broken under decision 4 (a sent number is neither required nor refused, and each sends the number kb would give). They stay as they are. If one fails, it is a `BLOCKED` reply.
  - `tests/test_define_a_type.py` `_version_held_at` and `_the_type_of_types`: not broken under decision 4 (content keeps `version`).
- [ ] **Steps:**
  1. The store lands a numbered version: `port.py`, the adapter's type-versions module, `sqlite_store.py`, `tests/test_the_storage_port.py`. A change carrying a version lands its row beside the earlier ones; Review Focus 2 pinned at the port. Check: the new conformance cases pass; `make test` fails nothing that passed before.
  2. kb numbers a type's change: `edits.py`, `drafting.py`, `draft.py`, `definitions.py`, `type_refusals.py`, and the tests listed under "Tests the decisions break" (the version rule must go in the same step as the numbering, or a change that leaves the number is still refused). Check: the three rewritten or deleted tests are as decided; `make test` fails nothing else that passed before.
  3. The scenarios: the step definitions in `tests/test_define_a_type.py`, Review Focus 1 pinned by a plain test through the contract, whatever production the red run still asks for, CLAUDE.md's rows. Check: `-m slice-161` gives 4 passed.
- [ ] **Verify:** `.venv/bin/python -m pytest -q -m slice-161` gives 4 passed, and `make test` shows no new failure.
- [ ] **Checkpoint:** `plan status 161 green`, then `plan log "Suite: ..."`. Its open questions carry what Review Focus 4 found.

### Task 4: Slice 162. A create names the version of its type it conforms to

Review: per-task
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Scenarios** (`@slice-162`, 2 scenarios, 3 collected):
  - check-a-change / An artifact created naming a version of its type is checked against that version
  - name-what-is-asked-for / A create naming a type version the store does not hold is refused (2 examples)
- [ ] **Why it is red today:** their Givens have no steps ("a store holding two versions of the decision type, where the later one requires a section the earlier one does not"; "a store holding a decision type, at its first version, whose artifacts require …"). Behind them, a create is drafted and checked against the version its type stands at, and a create naming any other version is refused with `version` (batch 32's decision 4). The unheld-version refusal exists already, so the two outline rows may pass on their steps alone.
- [ ] **Where the change lands** (4 production, 1 test; 5 if `links.py` reads a create's links through the latest version):
  - `src/kb/composition.py`: the schema of the version a create names.
  - `src/kb/edits.py`, `src/kb/drafting.py`, `src/kb/draft.py`: the create acts on, is stamped with, and is checked against the version it names (decision 7).
  - `tests/test_create_an_artifact.py`: the steps.
- [ ] **Decisions applied:** 7. Review Focus 3.
- [ ] **Tests the decisions break:**
  - Any test asserting that a create naming an earlier, held version is refused with `version`: decision 7 makes it land. The scout found none by name; slice 156's report says the concurrency test of a kind's type moving was changed to use a replacement because a create drafted before its type moved was refused. Review Focus 3 asks for the create's case as a new plain test in `tests/test_a_type_moving_under_a_change.py`; the existing replacement case stays.
  - None else: the scout checked `tests/test_create_an_artifact.py` and the create helpers in `tests/calls.py` (`creating` sends `held_version` unless told).
- [ ] **Steps to reuse:** `calls.version_iri`, `calls.creating(... version=)`, `calls.next_version`, `test_create_an_artifact.py`'s `_records_that_version`, the name-what-is-asked-for refusal steps.
- [ ] **Verify:** `.venv/bin/python -m pytest -q -m slice-162` gives 3 passed, and `make test` shows no new failure.
- [ ] **Checkpoint:** `plan status 162 green`, then `plan log "Suite: ..."`.

### Task 5: Slice 163. An artifact keeps its version until a write names a later one

Review: per-task
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Scenarios** (`@slice-163`, 6 scenarios, 8 collected):
  - change-the-store / A change naming no version of its type keeps the artifact at the version it conforms to
  - change-the-store / A replacement naming a later version of the artifact's type moves the artifact to it
  - change-the-store / A replacement naming an earlier version of the artifact's type, or a version of another type, is refused
  - check-a-change / Changing an artifact that is behind its type naming no version keeps it at the version it conforms to
  - check-a-change / Changing an artifact that is behind its type naming the latest version, with content that fits it, brings it up to date
  - check-a-change / Changing an artifact that is behind its type naming a later version, with content that does not fit it, is refused
- [ ] **Why it is red today:** the "two versions" and "behind its type" Givens and the "naming the latest version" Whens have no steps; a replacement cannot name a version on the wire; every write moves its artifact to the version its type stands at.
- [ ] **Where the change lands** (5 production, 3 test):
  - `src/kb/contract/kb.proto` with its generated code (`make contract`): `ReplaceRequest` and the replace of a set gain `type` (decision 8).
  - `src/kb/changes.py`: the replacement's named version converted through `values.py`'s existing conversion of a version's IRI (rule 2).
  - `src/kb/edits.py`, `src/kb/drafting.py`, `src/kb/composition.py`: an artifact keeps its version on every change; a replacement moves it only to a later version of its own type; the change is checked against the version it ends at. `edits.py` is at 193 lines: if this takes it past 250, split first and say so.
  - `tests/test_change_an_artifact.py`, `tests/calls.py` (`replace` and `replacing` take an optional version), `tests/contract_v2.golden`.
- [ ] **Decisions applied:** 8, 6.
- [ ] **Tests the decisions break:**
  - `tests/contract_v2.golden`: gains the two `type` fields.
  - Any test asserting that a change to an artifact behind its type is checked against, or moved to, the latest version: decision 8. The scout names `tests/test_change_an_artifact.py`'s `_behind_a_type_that_now_wants_an_owner` and `_stale` steps and line 229's assertion (which already expects the artifact to keep its version) as the ones to re-read; a step bound to a scenario still in the features keeps its assertion, and a step no feature line uses is deleted. A test not named here that breaks is a `BLOCKED` reply naming it.
- [ ] **Steps:**
  1. The contract: `kb.proto`, the generated code, `tests/contract_v2.golden`. The fields exist and nothing reads them. Check: the descriptor test passes; `make test` fails nothing that passed before.
  2. The rule: `changes.py`, `edits.py`, `drafting.py`, `composition.py`, `tests/calls.py`, with plain tests through the contract for keep, move forward, and the two refusals. Check: those plain tests pass; `make test` fails nothing that passed before.
  3. The scenarios: the step definitions in `tests/test_change_an_artifact.py`, CLAUDE.md's rows. Check: `-m slice-163` gives 8 passed.
- [ ] **Verify:** `.venv/bin/python -m pytest -q -m slice-163` gives 8 passed, and `make test` shows no new failure.
- [ ] **Checkpoint:** `plan status 163 green`, then `plan log "Suite: ..."`.

### Task 6: Slice 164. The store's check reads each artifact against its own version

Review: batch-end
Model: sonnet
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Scenarios** (`@slice-164`, 3 scenarios, 4 collected):
  - check-the-store / An artifact that conforms to a version of its type a later version has followed is listed as behind its type
  - check-the-store / An artifact behind its type is checked against the version of its type it conforms to
  - define-a-type / A type is changed so that artifacts the store holds would no longer fit it
- [ ] **Why it is red today:** the Givens "a store holding a decision that conforms to the first version of the decision type" and "a decision type the store holds at its first version, which does not require an owner, and a decision with no owner" have no steps; `check.py` composes each kind's latest schema and reads every artifact against it.
- [ ] **Where the change lands** (2 production, 2 test; `fault_order.py` or `draft.py` only if the order an artifact's faults are given in reads the latest version's declared order):
  - `src/kb/check.py`: each artifact read against the version it conforms to; behind listed against the number its type stands at (decision 9).
  - `src/kb/composition.py`: an artifact's own version's schema, and the number a type stands at.
  - `tests/test_check_the_store.py`, `tests/test_define_a_type.py`: the steps.
- [ ] **Decisions applied:** 9.
- [ ] **Tests the decisions break:** none: the scout checked `tests/test_check_the_store.py`'s `_listed_as_stale` (it expects the artifact's version and the type's standing number, which stays right) and `_not_a_violation`.
- [ ] **Steps to reuse:** `test_check_the_store.py`'s `_store_with_a_decision`, `_listed_as_stale`, `_not_a_violation`; `calls.check`, `calls.next_version`.
- [ ] **Verify:** `.venv/bin/python -m pytest -q -m slice-164` gives 4 passed, and `make test` shows no new failure.
- [ ] **Checkpoint:** `plan status 164 green`, then `plan log "Suite: ..."`.

### Task 7: Slice 165. Links and references name a type or a version of one

Review: per-task
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Scenarios** (`@slice-165`, 3 scenarios, 6 collected), all define-a-type:
  - A link field naming a kind by its type's IRI may point at an artifact of any version of that type
  - A type refers to a shape another type defines, naming the version it reads
  - A type that could never check an artifact is refused when it is written (4 examples)
- [ ] **Why it is red today:** the Givens "a binding type the store holds at its second version", "a type that defines the shape of a binding, whose first version requires … and whose second version requires …" and "a decision type the store holds at its second version, a decision conforming to its first version and a decision conforming to its second" have no steps, and the When naming the first version differs from the existing "refers to that shape" step. The could-never-check faults exist; a reference to an earlier version resolves once versions are held (Tasks 2 and 3), so parts of this slice may pass on their steps alone.
- [ ] **Where the change lands** (2 production, 2 test; `validation.py` or `type_refusals.py` only if the red run asks):
  - `src/kb/composition.py`: a `kb:` reference resolved to the held version it names, whatever the type stands at (decision 10).
  - `src/kb/definitions.py`: a reference naming a version not held refused as the scenario's row says.
  - `tests/test_define_a_type.py`: the steps.
  - `tests/test_a_type_moving_under_a_change.py`: the base-type cases removed in bd159cd restored (the `TYPES` entry "the type its type is built on" and `test_a_type_changed_while_a_type_built_on_it_moved_relinks_through_the_types_as_they_now_stand`), their `$ref` written as `kb:<base type IRI>@1`; and one plain test pinning that changing a base type leaves a type built on its first version creating and relinking as before (the dangling-reference fault of the batch 32 ledger: `store: NoSuchResource`).
- [ ] **Decisions applied:** 10.
- [ ] **Tests the decisions break:** none are broken; the restored cases are named above (`git show bd159cd -- tests/test_a_type_moving_under_a_change.py` shows what was removed).
- [ ] **Steps to reuse:** `test_define_a_type.py`'s `_a_type_at_its_second_version`, `_a_base_type`, `_define_a_type_at`, `_a_type_and_two_artifacts`; `test_a_type_moving_under_a_change.py`'s `_typed`, `TYPES`, and `at_once`'s helpers.
- [ ] **Verify:**
  - `.venv/bin/python -m pytest -q -m slice-165` gives 6 passed.
  - `make test` passes every scenario tagged up to `@slice-165`. Every failure is a scenario tagged `@slice-166` onward, or the rule-name test.
- [ ] **Checkpoint:** `plan status 165 green`, then `plan log "Suite: ..."`.
