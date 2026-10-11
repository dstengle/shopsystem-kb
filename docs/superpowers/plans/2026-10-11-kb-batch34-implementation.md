# kb batch 34 Implementation Plan: an export and its import carry every version of a type

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Each task is one slice, implemented under shopsystem-bdd:bdd-red-green. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** close the regression batch 33's review found (the plan's Backlog, RELEASE GATE): a store holding an artifact behind its type is exported with every version of its types, each artifact as its own version declares, and imported into a fresh store with every version landing, so the artifact reads, lists, checks and replaces there as it did (slices 165.2 to 165.6).

**Architecture:** kb holds every version of a type in the adapter's `type_versions` table; the type's own row in `artifacts` is the version it stands at, and the port lists a type's held versions (`versions(type_id)`, slice 165.1) and reads one by its IRI (`type_version`). Export still writes one file per artifact and so one per type; the import keys files by the unversioned type IRI and lands only the standing version, reading every artifact through the latest. This batch moves the test helpers first, then the export, then splits `importing.py`, makes the import tell versions apart, and lands every version file.

**Tech Stack:** Python 3.11, SQLite, pytest-bdd 8.1, pytest-xdist.

**Spec:** `spec/capabilities/export-and-import-a-store.md` (Behaviour, and Implementation's layout lines), `spec/decisions.md` (decision/0027-each-type-version-is-its-own-iri, formulation-answers-k2, an-artifact-is-read-through-its-version, kb-numbers-type-versions). Slices: `docs/superpowers/plans/2026-09-24-kb-slices.md`, slices 165.2 to 165.6. Research: `.superpowers/scout/2026-10-10-batch34/export-import-versions.md` (the planner's notes; an implementer need not read them).

## Global Constraints

- Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts
- One task per slice, in slice order. The plan holds no code. The implementer writes the steps and the code under bdd-red-green, after the red run.
- Each task has a `Review:` and a `Model:` line, and the controller dispatches by them. `Review: per-task` with `Model: opus` goes to a task that touches concurrency, the published contract, data integrity or moving stored data. `Review: batch-end` with `Model: sonnet` goes to every other task, and gets no task review because the batch's branch review covers it.
- CLAUDE.md's rules hold:
  - No module under `src/kb/` may pass 250 lines, and `servicer.py` must stay under 150. A module that would pass its limit is split first; a new module gets a row in CLAUDE.md's map.
  - Rule 1: no broad `except` outside `servicer.py`'s wrapper.
  - Rule 4: draft, validate, land; a version lands with its set in the one transaction.
  - Rule 5: one canonical checker, applied to content after parsing and to bytes before writing.
  - Rule 6: only `names.py` decides what an IRI, a version's IRI or an export file's place looks like.
  - When a task changes what a module owns, it changes that module's row in CLAUDE.md's map too.
- No migration: the store's form stays `store: 2`.
- An implementer may change what an existing test asserts only where its task's "Tests the decisions break" lists it. Any other existing test that the decisions break is a `BLOCKED` reply naming it.
- Out of this batch: import into a store that already holds artifacts (slice 181), the skip analysis (slice 184), the client's export through the contract (slices 172 to 174), selection (slice 176). `kb init --seed` goes through the same import and is fixed with it; backup and restore copy the database whole and need nothing.
- At this batch's end, every scenario tagged up to `@slice-165.6` passes. Every failing test is then a scenario tagged `@slice-166` onward, or the published contract's rule-name test (slice 182, rule `differs`).

### Execution rules

- **Paths in, short replies out.** The controller dispatches with paths (brief, report, findings, review package, notes) and reads replies, `plan show` and `git log --oneline`. It does not open a diff, a report, a findings file or source: it writes a review package by redirecting `git` output to a file. The one exception is a `BLOCKED` or `NEEDS_CONTEXT` reply, where it reads the part of the report the reply names, to decide or to ask the person.
- **By step.** A task with Steps is dispatched one step at a time, each to a fresh `bdd-implementer` that is told the step and the task's one report file. One implementer at a time in a worktree. A `PARTIAL` reply is answered with a fresh implementer told it is a continuation, with the same report.
- **One review per `Review: per-task` task,** after its last step, from the commit before its first. The reviewer is given a findings file to write. A `Review: batch-end` task gets none. A diff over 8 production or 4 test files is reviewed by area, each reviewer given its paths and its own findings file, in parallel.
- **Fresh fixes.** Findings go to a fresh `bdd-implementer` as a fix round, with the report and the findings file, then to a scoped re-review. No agent is resumed. The branch review's reply is the one long reply the controller reads: it saves the issues to fix now as a findings file for the fix round.
- **Lanes.** Tasks in different lanes may run at once, each lane in its own git worktree and branch with its own virtualenv, and the dispatch tells each implementer it is in a lane. This replaces subagent-driven-development's rule against parallel implementers, for lanes only. Tasks in one lane run in order; a task with no `Lane:` runs in the main worktree, in order, and not beside a lane. A lane's task is reviewed in its lane, before the merge. A lane's implementer never commits the plan: its reply carries the checkpoint entry. The controller merges the lanes one at a time, runs the suite after each merge, and writes each slice's Status, the checkpoint entry from the reply and the `Suite:` entry itself with `plan`.

No task of this batch has a `Lane:`: Tasks 1, 2 and 5 share `tests/test_export_and_import_a_store.py`, and Tasks 3 to 5 share `importing.py`.

### Binding values, verbatim from the spec

- export-and-import-a-store, Behaviour: "the directory holds one file for each artifact, at a place that follows the path of its IRI, and for a type one file for each version the store holds and no other, at the type's place, `@` and the version's number, a version's file giving that version's own revision and title".
- "When the operator exports a store holding an artifact that conforms to an earlier version of its type, that artifact's file gives its content in the order the version it conforms to declares."
- "When the operator imports the export of a store that held an artifact conforming to an earlier version of its type, every version of that type lands as its file gives it, the artifact is checked against the version it conforms to, and afterwards it is read, listed, checked and replaced as it was in the store exported."
- "each artifact keeping its IRI, title, revision and type version."
- The layout, from Implementation: "`<dir>/<host>/<segment>/.../<segment>.yaml`, one file per artifact, its place the host and path of its IRI; each held version of a type at the place of the type's IRI followed by `@<n>`".

## Decisions this plan takes

1. **A version's file** carries what the version was made with: the version's content (its `version` the number kb gave), and the revision and title of the type at that version, with the identity keys in the canonical order. Its `id` and `type` are what the outline's Then lines and the files exported today for a type's standing version already show; the standing version's file is byte for byte what it is today.
2. **Export order** (the second Behaviour line above; decision/an-artifact-is-read-through-its-version). Each artifact's entries are written in the order the version it conforms to declares. `composition.latest_schema`'s use in `export.py` ends.
3. **One moment.** Every artifact and every version is read in the one view of the store the export already takes, before the directory is touched.
4. **The import keeps the numbers its files give** (QUESTION FOR THE SPEC in the plan log, recommended answer applied). Each version file of a type lands as that version, numbered as its file says; kb's own numbering applies to creates and replacements only. A version file alone lands. The type stands, after the import, at the highest version landed, with the revision and title that version's file gives.
5. **Checked through its own version** (the third Behaviour line). In the import's check and in its landing, each artifact is checked, and its links derived, through the version its file names, which the directory holds (a fresh store holds only the type that describes types). An artifact whose file names a version neither the directory nor the store holds is an error of the check, as a file claiming a type nobody holds is today.
6. **History** (QUESTION FOR THE SPEC in the plan log). The import's history gains one entry for each file that lands, a type's version files included, a type's versions in the order of their numbers, each type's versions before the artifacts conforming to them.
7. **The import stays into a freshly started store only** in this batch; the refusal of a store already holding artifacts is slice 181's to lift.

## Review Focus

1. **The round trip, as the review reproduced it**, through the operator's commands in-process: define a note type; create a note at its first version; change the type; export; start a fresh store; check the directory for import (clean) and import it; then read the note at a glance and whole, list notes, check the store (the note listed as behind, no violation) and replace the note. Owner: Task 5; the scenario is this, and one plain test holds each call separately.
2. **Two exports of one content are byte for byte the same** still (an existing Behaviour line), with several versions held. Owner: Task 2, a plain test: export, import into a fresh store, export again, and compare the two directories' files byte for byte once Task 5 lands (Task 5 adds the second half).
3. **A set landing two versions of one type** must not conflict with itself in the adapter's checks (a change read through a type the same set also lands), in a fresh store and under a concurrent reader. Owner: Task 5, port conformance cases.
4. **`kb init --seed`** from a directory holding two versions of a type lands both. Owner: Task 5, one plain test beside the seeding tests.

---

### Task 1: Slice 165.2. The tests' view of an export lists every version's file

Review: batch-end
Model: sonnet
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Check:** `make test` gives the same passed and failed tests as the record before it; the helpers that compare an export with what a store holds name a file for every held version of a type.
- [ ] **Why it fails today:** `tests/held.py` lists a store's artifacts and `tests/test_export_and_import_a_store.py`'s `_held_file` gives a type one file, at the version it stands at; an export of a type holding two versions will hold two files.
- [ ] **Where the change lands** (0 production, 2 test): `tests/held.py` (a view of every held version of every type beside `names`, read from the store as the other views are); `tests/test_export_and_import_a_store.py` (`_held_file` and the comparisons of an export's files with what a store holds use it).
- [ ] **Decisions applied:** 1.
- [ ] **Tests the decisions break:** none: while every type in those tests holds one version the comparisons give the same files, so no assertion changes.
- [ ] **Verify:** `make test` fails no test that passed at the record before it and passes none tagged `@slice-165.3` onward; the report names the helper for Task 2.
- [ ] **Checkpoint:** `plan status 165.2 green`, then `plan log "Suite: ..."`.

### Task 2: Slice 165.3. The operator's export gives every version of a type, each artifact as its version declares

Review: per-task
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Scenarios** (`@slice-165.3`, 2 scenarios, 3 collected), both export-and-import-a-store:
  - The operator exports the store to a directory that is empty or does not exist (2 examples)
  - An artifact that conforms to an earlier version of its type is exported in the order that version declares
- [ ] **Why it is red today:** neither has all its steps (the Given "a store holding a type for decisions at two versions, a type for work items at one version, two decisions and a work item"; the note type's two orders). Behind them, the export writes one file per artifact, so a type gets only the version it stands at, and orders every artifact's entries by its type's latest version.
- [ ] **Where the change lands** (2 production, 2 test):
  - `src/kb/export.py`: every held version of every type written at the type's place, `@` and its number, from the port's `versions`; each artifact ordered by the version it conforms to.
  - `src/kb/composition.py` only to drop `latest_schema` if nothing else calls it (the import op in `edits.py` still does until Task 5: then it stays).
  - `tests/test_export_and_import_a_store.py` (the steps), `tests/held.py` only if Task 1's helper needs one more view.
  - CLAUDE.md's `export.py` row.
- [ ] **Decisions applied:** 1, 2, 3. Review Focus 2 (first half: the export of a store holding two versions is the same twice).
- [ ] **Tests the decisions break:**
  - `tests/test_export_and_import_a_store.py::test_an_artifact_written_before_its_type_reordered_its_fields_exports_in_the_order_its_type_now_declares`: decision 2. Rewritten and renamed: the artifact, left at its version, exports in the order that version declares.
  - Any existing export or seeding test whose store holds a type at two versions now exports two files for it: with Task 1's helper the comparisons hold; a hard-coded single file for such a type is rewritten to the files decision 1 gives. One that breaks otherwise is a `BLOCKED` reply naming it.
  - Added after the hand-back at 398790a: the rewritten export-order test (`test_an_artifact_left_at_its_version_when_its_type_reordered_its_fields_exports_in_the_order_that_version_declares`) also runs the import check and the import on its export, which now holds two version files of the note type; the import cannot land them until Task 5. The test is split: its export half stays as rewritten; its import half becomes a test of its own, unchanged in what it asserts, skipped with the reason "the import of an export holding two versions of a type: slice 165.6", and Task 5 removes the skip.
  - The import of such an export is Task 5's: an existing test that exports a two-version type and imports it again, if any, is named in the reply as `BLOCKED` rather than changed.
- [ ] **Steps to reuse:** `calls.define`, `create`, `next_version` or `change_type`, `type_iri`, `version_iri`, `filed`; `tests/test_export_and_import_a_store.py`'s `_file`, `_read`, `_exported_names`; Task 1's helper.
- [ ] **Verify:** `.venv/bin/python -m pytest -q -m "slice-165.3"` gives 3 passed, and `make test` shows no new failure.
- [ ] **Checkpoint:** `plan status 165.3 green`, then `plan log "Suite: ..."`.

### Task 3: Slice 165.4. importing.py split before the import of versions grows it

Review: batch-end
Model: sonnet
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Check:** `make test` gives the same passed and failed tests as the record before it; `wc -l src/kb/importing.py` gives at most 180, and no module under `src/kb` is over 250.
- [ ] **Why it fails today:** `importing.py` is at 237 lines and Tasks 4 and 5 add to it.
- [ ] **Where the change lands** (2 production, 0 test): `src/kb/importing.py` and one new module that takes the examination of a directory (each file's errors against its type, and the files that would be skipped with their chains), leaving `importing.py` the import itself (found fresh, drafted and landed under the write lock, the report). Every public function other modules call keeps its name and module, or its callers move with it. CLAUDE.md's map gains the new module's row and `importing.py`'s row says what is left.
- [ ] **Tests the decisions break:** none: a refactor; tests use public functions and the operator's commands.
- [ ] **Verify:** the Check, with the `wc -l` output in the report.
- [ ] **Checkpoint:** `plan status 165.4 green`, then `plan log "Suite: ..."`.

### Task 4: Slice 165.5. An import tells the versions of one type apart

Review: batch-end
Model: sonnet
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Check:** `make test` gives the same passed and failed tests as the record before it; a plain test offers a directory holding two version files of one type and finds both, each named by its own version.
- [ ] **Why it fails today:** `offers.py` names a type's version file by the type's unversioned IRI, and the import keys what it examines and lands by that name, so the second version file of a type overwrites the first before anything is checked.
- [ ] **Where the change lands** (2 production, 1 test): `src/kb/offers.py` (a version file is offered under its version's IRI, by `names.py`'s spelling); `src/kb/importing.py` or the module Task 3 made (what is examined, skipped and landed is keyed by it); one test module, the plain test, beside the tests of offers. CLAUDE.md's rows for `offers.py` and the import modules.
- [ ] **Decisions applied:** 4 (the files' numbers are kept apart; landing them is Task 5's).
- [ ] **Tests the decisions break:** none: no existing test offers two versions of one type; with one version per type nothing a test sees changes. If the import's report or a skip chain names a type's file differently because of the new key, that is a `BLOCKED` reply naming the test and the two namings.
- [ ] **Verify:** the Check.
- [ ] **Checkpoint:** `plan status 165.5 green`, then `plan log "Suite: ..."`.

### Task 5: Slice 165.6. A store with an artifact behind its type comes back from its export

Review: per-task
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Scenarios** (`@slice-165.6`, 1 scenario, 1 collected): export-and-import-a-store / A store holding an artifact behind its type comes back from its export as it was.
- [ ] **Why it is red today:** the scenario has no steps. Behind them, the import checks each artifact against its kind's latest version and lands, for a type, only the version it stands at; the note's own version is not held in the new store, so every read, list, check and replacement of it is refused with `version`.
- [ ] **Where the change lands** (5 production, 2 test):
  - The import's check (the module Task 3 made): each artifact against the version its file names, held by the directory or the store (decision 5).
  - `src/kb/edits.py` (the import's operation acts through the version the file names), `src/kb/drafting.py` and `src/kb/draft.py` (a set holds, checks and hands over several versions of one type, each as its file gives it, the type standing at the highest; the links of an imported artifact derived through its own version), `src/kb/links.py` (its default to the latest version ends: it takes its type always).
  - `src/kb/sqlite_store.py` or `sqlite_types.py` only if landing several versions of one type in one set needs it.
  - `tests/test_export_and_import_a_store.py` (the steps and Review Focus 1's plain tests), `tests/test_the_storage_port.py` (Review Focus 3) and the seeding test module for Review Focus 4 (three test modules; the third holds one plain test).
  - CLAUDE.md's rows for every module whose ownership changes ("an import keeping the revision and type version its file gives" already stands in `drafting.py`'s).
- [ ] **Decisions applied:** 4, 5, 6, 7. Review Focus 1, 2 (second half), 3, 4.
- [ ] **Tests the decisions break:**
  - The import half of the export-order test, split off and skipped by Task 2 (reason naming slice 165.6): the skip is removed and it passes as it asserts.
  - Any existing import test asserting an artifact's file is checked against its type's latest version where the file names an earlier one the directory holds: decision 5. The scout found none by name; one that breaks is a `BLOCKED` reply naming it.
  - `tests/test_export_and_import_a_store.py`'s history assertions count "one import entry for each of the five artifacts" for directories holding each type at one version: unchanged under decision 6.
- [ ] **Steps:**
  1. A set lands several versions of one type: `drafting.py`, `draft.py`, `edits.py`, and the adapter if it needs it, with `tests/test_the_storage_port.py`'s cases and plain tests through `write.land` or the import's own entry: two version files of one type land as those versions, the type standing at the higher; Review Focus 3. Check: those tests pass; `make test` fails nothing that passed before.
  2. The import checks and links through each file's own version: the check module, `links.py`, `edits.py`/`drafting.py` as needed, with plain tests through the operator's commands in-process (a directory whose note fits its own version and not the latest checks clean and lands; one fitting the latest and not its own is reported). Check: those tests pass; `make test` fails nothing that passed before.
  3. The scenario and the pins: the step definitions, Review Focus 1's separate calls, Review Focus 2's second half, Review Focus 4, CLAUDE.md's rows. Check: `-m "slice-165.6"` gives 1 passed.
- [ ] **Verify:**
  - `.venv/bin/python -m pytest -q -m "slice-165.6"` gives 1 passed.
  - `make test` passes every scenario tagged up to `@slice-165.6`. Every failure is a scenario tagged `@slice-166` onward, or the rule-name test.
- [ ] **Checkpoint:** `plan status 165.6 green`, then `plan log "Suite: ..."`, saying the RELEASE GATE line of batch 33 is closed.
