# kb batch 35 Implementation Plan: placeholders

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Each task is one slice, implemented under shopsystem-bdd:bdd-red-green. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** a link may point at an IRI the store does not hold, under a type it holds that the link field allows, and lands on a placeholder: the client finds placeholders again by asking for them, reads mark such links, the check lists them apart from violations, and creating the artifact fills them (slices 165.7, 166, 166.1, 167 to 170).

**Architecture:** a placeholder is not stored: it is an IRI linked to and not held; a link's target is kept as the IRI it names. Today a link to an IRI not held is refused twice, by the domain's check (`validation.py`) and by the adapter's landing check (`sqlite_checks.py`). Slice 165.7 lets the adapter accept one the domain vouches for (the held type the IRI sits under, handed on the link) while the domain still refuses all. Slice 166 lets the domain accept it and keeps reads of the linking artifact working. Slice 166.1 adds the query and its rpc. Slices 167 and 168 are step definitions over that behaviour. Slice 169 marks such links in reads; slice 170 lists placeholders in the check and in `kb validate`.

**Tech Stack:** Python 3.11, grpcio/protobuf (`make contract`), SQLite, pytest-bdd 8.1, pytest-xdist.

**Spec:** `spec/capabilities/{check-a-change,query-the-store,read-an-artifact,check-the-store,operate-a-store,name-what-is-asked-for,change-the-store}.md`, `spec/decisions.md` (decision/0024-a-link-may-land-on-a-placeholder, 0025, removal-still-refused-under-placeholders, links-into-parts-of-placeholders, placeholders-seen-in-stubs-not-read, what-links-to-a-placeholder, an-iri-belongs-to-its-nearest-type, a-link-to-a-removed-artifact-waits-on-a-placeholder). Slices: `docs/superpowers/plans/2026-09-24-kb-slices.md`, slices 165.7 to 170. Research: `.superpowers/scout/2026-10-10-batch34/research.md` (written before batch 34; the planner's notes).

## Global Constraints

- Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts
- One task per slice, in slice order (Tasks 4 and 7 are slices 167 and 168; Task 7 runs after Task 4, before Task 6). The plan holds no code. The implementer writes the steps and the code under bdd-red-green, after the red run.
- Each task has a `Review:` and a `Model:` line, and the controller dispatches by them. `Review: per-task` with `Model: opus` goes to a task that touches concurrency, the published contract, data integrity or moving stored data. `Review: batch-end` with `Model: sonnet` goes to every other task, and gets no task review because the batch's branch review covers it.
- CLAUDE.md's rules hold:
  - No module under `src/kb/` may pass 250 lines, and `servicer.py` must stay under 150 (it is at 137). A module that would pass its limit is split first; a new module gets a row in CLAUDE.md's map.
  - Rule 1: no broad `except` outside `servicer.py`'s wrapper.
  - Rule 2: a request field becomes a value in `values.py` before anything else sees it.
  - Rule 4: draft, validate, land; the adapter re-checks every link inside the landing transaction.
  - Rule 6: only `names.py` decides what an IRI looks like or which IRIs one sits under.
  - The adapter knows nothing of what a type declares: what it must check about a link, the domain hands it on the link.
  - When a task changes what a module owns, it changes that module's row in CLAUDE.md's map too.
- An implementer may change what an existing test asserts only where its task's "Tests the decisions break" lists it. Any other existing test that the decisions break is a `BLOCKED` reply naming it.
- At this batch's end, every scenario tagged up to `@slice-170` passes. Every failing test is then a scenario tagged `@slice-171` onward, or the published contract's rule-name test (slice 182, rule `differs`).

### Execution rules

- **Paths in, short replies out.** The controller dispatches with paths (brief, report, findings, review package, notes) and reads replies, `plan show` and `git log --oneline`. It does not open a diff, a report, a findings file or source: it writes a review package by redirecting `git` output to a file. The one exception is a `BLOCKED` or `NEEDS_CONTEXT` reply, where it reads the part of the report the reply names, to decide or to ask the person.
- **By step.** A task with Steps is dispatched one step at a time, each to a fresh `bdd-implementer` that is told the step and the task's one report file. One implementer at a time in a worktree. A `PARTIAL` reply is answered with a fresh implementer told it is a continuation, with the same report.
- **One review per `Review: per-task` task,** after its last step, from the commit before its first. The reviewer is given a findings file to write. A `Review: batch-end` task gets none. A diff over 8 production or 4 test files is reviewed by area, each reviewer given its paths and its own findings file, in parallel.
- **Fresh fixes.** Findings go to a fresh `bdd-implementer` as a fix round, with the report and the findings file, then to a scoped re-review. No agent is resumed. The branch review's reply is the one long reply the controller reads: it saves the issues to fix now as a findings file for the fix round.
- **Lanes.** Tasks in different lanes may run at once, each lane in its own git worktree and branch with its own virtualenv, and the dispatch tells each implementer it is in a lane. This replaces subagent-driven-development's rule against parallel implementers, for lanes only. Tasks in one lane run in order; a task with no `Lane:` runs in the main worktree, in order, and not beside a lane. A lane's task is reviewed in its lane, before the merge. A lane's implementer never commits the plan: its reply carries the checkpoint entry. The controller merges the lanes one at a time, runs the suite after each merge, and writes each slice's Status, the checkpoint entry from the reply and the `Suite:` entry itself with `plan`.

Tasks 4 and 7 (lane A, in order) and Task 5 (lane B) carry `Lane:` lines: the two lanes' files are disjoint and neither needs the other's code.

### Binding values, verbatim from the spec

- check-a-change: "When an artifact points at an IRI the store does not hold, under a type the store holds that the link field allows, the artifact is accepted and the link lands on a placeholder at that IRI."
- check-a-change, Implementation: "A placeholder is not stored: it is an IRI linked to and not held. A link's target is kept as the IRI it names, whether or not anything is held there, and an artifact created at that IRI is what the link lands on from then."
- decision/an-iri-belongs-to-its-nearest-type: "an IRI under both belongs to the nearest type: the longest type IRI that is a whole-segment prefix of it ... a placeholder at such an IRI takes the nearest type."
- change-the-store: "When one client removes an artifact while another adds a link to it, each is judged against the store as the other left it: a removal that lands second is refused because something still points at it, and a link that lands second lands on a placeholder at the removed artifact's IRI, its type still held."
- read-an-artifact: "When the client reads an artifact holding a link to an IRI the store does not hold, at any level and following links or not, that link comes back marked as landing on nothing held and is never filled in, while a link that lands carries no such mark."
- check-the-store: placeholders are "listed apart, each with the links into it".

## Decisions this plan takes

1. **A placeholder's type** is the nearest held type its IRI sits under (`composition.nearest_type`); types not held are unknown to kb, so an IRI under a nearer type nobody holds takes the nearest one held. An IRI under no held type is refused as today.
2. **Where the typing is checked.** The domain decides (`validation.py`): the nearest held type's IRI must be among the link field's `targets`. It hands the adapter, on the link, the held type the unheld target sits under; the adapter, inside the landing transaction, accepts a link whose target is not held only when that type is held and is one the link allows, and still refuses a link to an unheld IRI that carries none. A link to a held target is checked as today.
3. **A link into a part of a placeholder** lands when the field may point into a part; the part is not checked, since nothing is held there (decision/links-into-parts-of-placeholders). A link into a part a held artifact lacks stays refused.
4. **A placeholder leaves no trace** when the last link to it goes: nothing is stored for it.
5. **The placeholders listing** gives one entry for each IRI linked to and not held, with every link into it (the linking artifact, the field and the place), in kb's order of names; a link into a part a held artifact lacks... is refused at write, so every entry is an IRI not held, or a held IRI's part that a link written before the artifact's create still names (slice 168's last scenario), listed with that part. No type is shown. Implicit links (an artifact's link to its type) are never placeholders.
6. **The contract** (slice 166.1): a new rpc `Placeholders`, its request empty, its response the usual `result` or `refusal`; a result holds a repeated message, one per placeholder, with its IRI (and part, when the link names one) and its repeated links (artifact IRI, field, place). It is a read: listed among the reads in the published contract's test, answered at one moment, never refused as busy. Slice 170 reuses that message for `Checked`'s placeholders; slice 169 adds the mark to `Stub` and, for a whole read's links, to `Artifact`.
7. **Reads before slice 169** (slice 166's guard). Once a link to an unheld IRI can be stored, a read of the linking artifact must not fail: at a glance its stub is the IRI alone, with no kind, title or fields; a whole read following links leaves it as the IRI, not filled in; Follow gives the same bare stub and does not walk on from it. Slice 169 then adds the mark the spec asks for to these.
8. **Inbound counts** count links from held artifacts into a held artifact, as today; a placeholder is never read, so it has none to show.
9. **Removal** (decision/removal-still-refused-under-placeholders; decision/a-link-to-a-removed-artifact-waits-on-a-placeholder). A removal is refused while anything points at its target, as today; a link made after the removal lands on a placeholder.

10. **Every link carries the held type its target sits under** (added after Task 1, whose port takes it only for a target not held). `links.handed` fills it for a held target too, so a link drafted while its target was held, whose target is removed before it lands, lands as a link to an IRI not held instead of being refused at the port: the second row of change-the-store's outline. The adapter still checks a held target as it does today and reads the carried type only when the target is not held.

## Review Focus

1. **The landing race, both orders,** at the port and through the contract: a removal and a new link made at once (the re-formulated outline), and a create at an IRI made while a link to it as a placeholder is landing. Owner: Tasks 1 and 2.
2. **An artifact cannot land under a type the store does not hold** through the placeholder path: the implicit link to its type is still refused when the type is not held. Owner: Task 1, a port conformance case.
3. **No held artifact is unreadable** after Task 2: every read level and Follow of an artifact holding a link to an unheld IRI answers. Owner: Task 2, plain tests through the contract.
4. **Filling.** After a create at a placeholder's IRI, the placeholders listing no longer gives it, reads of the linking artifact show the link as landing, and removing the new artifact is refused for the link. Owner: Task 4 (slice 168), by its scenarios and one plain test for the removal.
5. **The import** already lets a link wait on something a directory holds later; with the domain accepting unheld targets, `examining.py`'s own handling of a link to a file not yet read may be redundant. Nothing is removed in this batch; Task 2 reports what it finds. Slice 183 owns the import's placeholders.

---

### Task 1: Slice 165.7. The port lands a link to an IRI not held, under a held type the link allows

Review: per-task
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Check:** `make test` gives the same passed and failed tests as the record before it, with the port's conformance cases as rewritten below; the domain still refuses every link to an IRI not held, so nothing a client sees changes.
- [ ] **Why it fails today:** the adapter's landing check refuses any link whose target is not held; a link carries nothing saying which held type an unheld target sits under.
- [ ] **Where the change lands** (3 production, 1 test):
  - `src/kb/port.py`: a link may carry the held type its unheld target sits under (decision 2), absent for a held target; `land`'s words.
  - `src/kb/links.py`: `handed` fills it, from `composition.nearest_type`, for a target the corpus does not hold.
  - `src/kb/sqlite_checks.py`: the landing check accepts a link to a target not held when the type it carries is held and is one the link allows; refuses one that carries none or whose type is not held or not allowed.
  - `tests/test_the_storage_port.py`.
  - CLAUDE.md's rows for `port.py`, `links.py`, `sqlite_checks.py`.
- [ ] **Decisions applied:** 1, 2, 9. Review Focus 1 (at the port), 2.
- [ ] **Tests the decisions break** (decision 2; decision/0024):
  - `tests/test_the_storage_port.py::test_a_link_must_land_on_an_artifact_or_part_of_a_kind_it_allows`, the row whose target is an unheld IRI under a held type: rewritten: that link lands when it carries its held type, and is refused when it carries none or one the link does not allow. The rows for a held target of a kind not allowed and for a part a held artifact lacks stay.
  - `tests/test_the_storage_port.py::test_a_set_refused_for_a_link_that_does_not_land...`: its astray link is given an IRI under no held type, so the refusal it asserts stays.
  - `tests/test_the_storage_port.py`, the race of a removal and a new link on two connections ("never both land"): rewritten to the two orders of change-the-store's line: the removal landing second is refused; the link landing second lands, carrying its held type, as a link to an IRI not held.
- [ ] **Verify:** the rewritten and new conformance cases pass; `make test` fails no test that passed at the record before it.
- [ ] **Checkpoint:** `plan status 165.7 green`, then `plan log "Suite: ..."`.

### Task 2: Slice 166. A link to an IRI not held lands, and its artifact still reads

Review: per-task
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Scenarios** (`@slice-166`, 2 scenarios, 3 collected):
  - name-what-is-asked-for / A read by an IRI links point at that the store does not hold is refused
  - change-the-store / A removal and a new link to the same artifact made at once are each judged against what the other left (2 examples)
- [ ] **Why it is red today:** the first has no Given (a store holding a decision that links to an IRI the store does not hold cannot be made: the domain refuses the link); the second's row where the removal lands first expects the link to land, and the domain refuses it ("a link must land on a node of a kind the type allows").
- [ ] **Where the change lands** (3 production, 3 test):
  - `src/kb/validation.py`: a link to an IRI not held is accepted when the nearest held type it sits under is one the field allows, into a part when the field may point into a part (decisions 1 to 3); refused as today otherwise.
  - `src/kb/read.py`, `src/kb/query.py`: decision 7's guard.
  - `src/kb/links.py`: decision 10 (one line of what `handed` fills), with the port's conformance case of a link drafted to a held target that is removed before it lands.
  - `tests/test_read_an_artifact.py`, `tests/test_remove_an_artifact.py` (the outline's binding and steps), one test module for Review Focus 3's plain tests.
  - CLAUDE.md's rows for `validation.py`, `read.py`, `query.py`.
- [ ] **Decisions applied:** 1, 2, 3, 7, 8, 9, 10. Review Focus 1 (through the contract), 3, 5.
- [ ] **Tests the decisions break:**
  - `tests/test_remove_an_artifact.py`, the binding and steps of the old outline "A removal and a new link to the same artifact made at once never both land" (its title and second row changed in the feature): rebound to the new title; the step "the new decision is rejected because a link must land on a node of a kind the type allows" gives way to the new row's Then (the new decision lands, its link on a placeholder at the removed tag's IRI; the store holds the new decision and not the tag). The first row's assertions stay.
  - Added after the hand-back at f723d5d:
    - `tests/test_links_as_the_port_takes_them.py::test_a_link_carries_the_held_type_a_target_not_held_sits_under[held]` (written by Task 1 of this batch): decision 10. The `held` row expects the type the held target sits under.
    - `tests/test_a_type_moving_under_a_change.py::test_a_create_naming_an_earlier_version_is_held_to_the_links_that_version_makes`: it used the refusal of a link to a tag not held as its evidence that the earlier version makes `about` a link; decisions 1 and 2 land that link. Rewritten to assert the create lands and the note holds a link in `about` to that IRI (the links the earlier version makes), where a field the earlier version does not make a link holds none.
    - `tests/test_export_and_import_a_store.py::test_a_link_to_nothing_in_a_field_only_the_version_a_file_names_reads_as_a_link_is_reported`: its file's link names an IRI under a held type the field allows, which now waits on a placeholder. Its setup changes so the link names an IRI under a type neither the directory nor the store holds; its assertion (the check exits 1 with a `ref` error naming the file) stays.
  - Tests asserting a link to an IRI not held is refused where the IRI sits under a held type the field allows: none found by the scout beyond the above; the refusals under a type not held or not allowed (`tests/test_create_an_artifact.py`, `tests/test_add_an_item_to_a_collection.py`) stay as they are.
- [ ] **Steps to reuse:** `tests/test_remove_an_artifact.py`'s `_one_lands_first` and `at_once`'s helpers; `tests/test_read_an_artifact.py`'s read steps; `calls.create`, `request`, `read`, `refs`, `remove`.
- [ ] **Verify:** `.venv/bin/python -m pytest -q -m slice-166` gives 3 passed, and `make test` shows no new failure.
- [ ] **Checkpoint:** `plan status 166 green`, then `plan log "Suite: ..."`.

### Task 3: Slice 166.1. The client asks for the placeholders

Review: per-task
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Scenarios** (`@slice-166.1`, 2 scenarios, 2 collected):
  - query-the-store / The client asks for the placeholders
  - check-a-change / An artifact pointing at an IRI the store does not hold, under a type it holds that the link allows, lands its link on a placeholder
- [ ] **Why it is red today:** neither has all its steps; no rpc gives the placeholders, and nothing in the port lists links whose targets are not held.
- [ ] **Where the change lands** (6 production, 4 test):
  - `src/kb/contract/kb.proto` with its generated code (`make contract`): the rpc and its messages (decision 6).
  - `src/kb/port.py`, `src/kb/sqlite_reads.py`: the read of every link whose target is not held, or whose part its held target lacks, implicit links left out.
  - `src/kb/query.py`: the placeholders, each with its links, in kb's order.
  - `src/kb/servicer.py` (one method, answered at one moment), `src/kb/client.py`.
  - `tests/test_check_the_store.py` (where the query-the-store scenario is bound), `tests/test_create_an_artifact.py`, `tests/test_the_published_contract.py` (the rpc among the reads, the response's fields), `tests/contract_v2.golden`; `tests/calls.py` and `tests/test_every_call_is_refused_when_the_store_cannot_be_read.py` only for the rows every rpc must have.
  - CLAUDE.md's rows for `port.py`, `sqlite_reads.py`, `query.py`, `servicer.py`, `client.py`.
- [ ] **Decisions applied:** 4, 5, 6.
- [ ] **Tests the decisions break:** `tests/contract_v2.golden` and the published contract's lists of rpcs and reads gain the rpc; the table-driven test of every rpc refused when the store cannot be read gains its row. No assertion is otherwise changed.
- [ ] **Steps:**
  1. The contract and its boundary: `kb.proto`, generated code, the golden, the published contract's test, `servicer.py`, `client.py`, the every-rpc tables, with the rpc answering an empty list. Check: the descriptor and published-contract tests pass; `make test` fails nothing that passed before.
  2. The read and the scenarios: `port.py`, `sqlite_reads.py`, `query.py`, with a conformance case in `tests/test_the_storage_port.py`, then the step definitions in `tests/test_check_the_store.py` and `tests/test_create_an_artifact.py`. Check: `-m "slice-166.1"` gives 2 passed.
- [ ] **Verify:** `.venv/bin/python -m pytest -q -m "slice-166.1"` gives 2 passed, and `make test` shows no new failure.
- [ ] **Checkpoint:** `plan status 166.1 green`, then `plan log "Suite: ..."`.

### Task 4: Slice 167. A placeholder is typed by the type its IRI sits under

Review: batch-end
Model: sonnet
Lane: A
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Scenarios** (`@slice-167`, 4 scenarios, 4 collected), all check-a-change:
  - An artifact pointing at an IRI under a type the store does not hold is refused
  - An artifact pointing at an IRI the store does not hold, under a type the link does not allow, is refused
  - An item pointing at an IRI under a type the store does not hold is refused
  - An artifact with several faults reports them all
- [ ] **Why it is red today:** step definitions only; the refusals hold already. The scout found the Givens and Whens whose wording changed or is missing (an IRI "under a type the store does not hold"; "under the process type" with its process-type Given; the item's step).
- [ ] **Where the change lands** (0 production, 2 test): `tests/test_create_an_artifact.py`, `tests/test_add_an_item_to_a_collection.py`. If a scenario is red on behaviour once its steps exist, that is a finding: stop and report `BLOCKED` with the Then line and what the store answered; production is not this task's.
- [ ] **Decisions applied:** 1, 2.
- [ ] **Tests the decisions break:** none: the existing refusal steps (`_rejected_for_the_link`, `_rejected_with_both_faults`, `_rejected_for_its_link`) are reused as they assert.
- [ ] **Verify:** `.venv/bin/python -m pytest -q -m slice-167` gives 4 passed, and `make test` shows no new failure.
- [ ] **Checkpoint:** the reply carries the checkpoint entry for slice 167 (this task is in a lane).

### Task 5: Slice 169. Reads mark a link that lands on nothing held

Review: per-task
Model: opus
Lane: B
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Scenarios** (`@slice-169`, 2 scenarios, 5 collected), both read-an-artifact:
  - At a glance, the stub of a link to an IRI the store does not hold is marked as not held
  - A link to an IRI the store does not hold comes back marked as landing on nothing held, at any level and following links or not (4 examples)
- [ ] **Why it is red today:** the Given "the decision also points at a decision under an IRI the store does not hold" has no step and the feature's Background store has one link field; a stub and a whole read's link carry no mark (Task 2 gives them bare, decision 7).
- [ ] **Where the change lands** (2 production, 3 test): `src/kb/contract/kb.proto` with its generated code (`Stub` gains the mark; `Artifact` gains what marks a whole read's links that land on nothing held); `src/kb/read.py` (and `query.py` only for Follow's stubs to carry the same mark); `tests/test_read_an_artifact.py`, `tests/test_the_published_contract.py` (`Stub`'s and `Artifact`'s field sets), `tests/contract_v2.golden`.
- [ ] **Decisions applied:** 6, 7.
- [ ] **Tests the decisions break:** `tests/contract_v2.golden` and the published contract's field sets for `Stub` and `Artifact` gain the fields. Task 2's plain tests of the bare stub (this batch) are rewritten to expect the mark.
- [ ] **Verify:** `.venv/bin/python -m pytest -q -m slice-169` gives 5 passed, and `make test` shows no new failure.
- [ ] **Checkpoint:** the reply carries the checkpoint entry for slice 169 (this task is in a lane).

### Task 6: Slice 170. The check lists placeholders apart from violations

Review: per-task
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Scenarios** (`@slice-170`, 5 scenarios, 5 collected):
  - check-the-store / A store holding links to IRIs it does not hold lists each placeholder with what links to it
  - check-the-store / A store whose only findings are placeholders reports no violation
  - check-the-store / Every violation is reported
  - operate-a-store / The operator checks the whole store
  - operate-a-store / The operator checks a store whose only findings are placeholders
- [ ] **Why it is red today:** their Givens have no steps (one existing step's wording, "another points at something the store does not hold", is stale: that is now a placeholder, and the scenario's second fault is a field of a shape its type does not allow); `Checked` has no placeholders, the check lists none, and `kb validate` prints none.
- [ ] **Where the change lands** (3 production, 4 test): `src/kb/contract/kb.proto` with its generated code (`Checked` gains the placeholders, in Task 3's message); `src/kb/check.py`; `src/kb/cli.py` (a third list, not counted as a violation; `cli.py` is at 226 lines); `tests/test_check_the_store.py`, `tests/test_look_after_a_store.py`, `tests/test_the_published_contract.py`, `tests/contract_v2.golden`.
- [ ] **Decisions applied:** 5, 6.
- [ ] **Tests the decisions break:** `tests/contract_v2.golden` and the published contract's field set for `Check` gain the field. `tests/test_check_the_store.py`'s `_store_with_two_faults` (bound to no feature line today) is rewritten to the scenario's two faults.
- [ ] **Steps:**
  1. The check: `kb.proto`, generated code, the golden, the published contract's test, `check.py`, `tests/test_check_the_store.py`. Check: the three check-the-store scenarios pass.
  2. The operator: `cli.py`, `tests/test_look_after_a_store.py`. Check: `-m slice-170` gives 5 passed.
- [ ] **Verify:**
  - `.venv/bin/python -m pytest -q -m slice-170` gives 5 passed.
  - `make test` passes every scenario tagged up to `@slice-170`. Every failure is a scenario tagged `@slice-171` onward, or the rule-name test.
- [ ] **Checkpoint:** `plan status 170 green`, then `plan log "Suite: ..."`.

### Task 7: Slice 168. A placeholder is filled by creating what it names

Review: batch-end
Model: sonnet
Lane: A
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Scenarios** (`@slice-168`, 4 scenarios, 4 collected), all check-a-change:
  - An artifact pointing into a part of an IRI the store does not hold, under a type it holds that the link allows, lands its link on a placeholder
  - An artifact pointing into a part a held artifact does not have is refused
  - Creating an artifact at an IRI links already point at fills the placeholder
  - Creating an artifact without the part a link points into leaves that link on a placeholder
- [ ] **Why it is red today:** step definitions only; the behaviour is Tasks 1 to 3's. Missing: the decision type that "may link to the decision they supersede or into one of its options", and "a decision that supersedes a decision the store does not hold, at an IRI under the decision type".
- [ ] **Where the change lands** (0 production, 1 test): `tests/test_create_an_artifact.py`. If a scenario is red on behaviour once its steps exist, that is a finding: stop and report `BLOCKED` with the Then line and what the store answered; production is not this task's.
- [ ] **Decisions applied:** 3, 4, 5. Review Focus 4 (the plain test of the removal refused after filling).
- [ ] **Tests the decisions break:** none.
- [ ] **Verify:** `.venv/bin/python -m pytest -q -m slice-168` gives 4 passed, and `make test` shows no new failure.
- [ ] **Checkpoint:** the reply carries the checkpoint entry for slice 168 (this task is in a lane).

---

Tasks 8 and 9 were added on 2026-10-11 from slice 165.7's review (decision/a-types-place-is-settled-by-what-sits-under-it). They run after Task 3 and before the lanes.

11. **A type holding placeholders is not removed.** A removal of a type is refused, with the reason and rule a removal carries while artifacts of its kind exist, while any stored link's target is an IRI not held whose nearest held type is that type; the refusal names each linking artifact once, in kb's order, beside whatever else stands in the way. It is checked against the state the whole set leaves and holds at landing: a link landing under the type at the same moment as its removal does not leave both landed.
12. **A type is not defined over what sits under another.** A define of a type T at an IRI under a held type U's IRI is refused, with rule `identity`, while the store holds an artifact that conforms to a version of U at an IRI under T's, or a stored link waits on an IRI under T's that is not held; the refusal names each such IRI. A define with nothing under it is accepted as today, and so is a type whose IRI sits under no other type's. It holds at landing against a create or a link landing under T's IRI at the same moment.

### Task 8: Slice 166.2. A type is not removed while a link waits under it

Review: per-task
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Scenarios** (`@slice-166.2`, 1 scenario, 1 collected): define-a-type / Removing a type while a link waits on an IRI under it is refused.
- [ ] **Why it is red today:** no steps; the removal lands, and the store's check then reports a link violation on the artifact that holds the link.
- [ ] **Where the change lands** (about 4 production, 3 test): the read of links waiting under a type (`port.py`, `sqlite_reads.py`, the draft's equivalent), the removal's refusal where slice 165.1 put the referring-types refusal (`drafting.py`), the adapter's landing check for the race (`sqlite_checks.py`) only if the domain's draft under the write lock (slice 165.1's rule for a set that removes a type) does not already hold it; `tests/test_define_a_type.py`, `tests/test_the_storage_port.py`, one module for the race.
- [ ] **Decisions applied:** 11, 1.
- [ ] **Tests the decisions break:** `tests/test_the_storage_port.py`, slice 165.7's case of a type removed while a link waits under it (it pins that the removal lands at the port): rewritten to what the port must now do, or kept if the refusal is the domain's alone and the port still lands what it is handed; the implementer says which and why.
- [ ] **Verify:** `.venv/bin/python -m pytest -q -m "slice-166.2"` gives 1 passed; the race in both orders by a plain test with `at_once`; `make test` shows no new failure.
- [ ] **Checkpoint:** `plan status 166.2 green`, then `plan log "Suite: ..."`.

### Task 9: Slice 166.3. A type is not defined over what already sits under another

Review: per-task
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Scenarios** (`@slice-166.3`, 1 scenario outline, 2 collected): define-a-type / Defining a type under another type's IRI, over what already sits there, is refused (a held decision; a link waiting on a decision not held).
- [ ] **Why it is red today:** no steps; the define lands, after which the held decision sits under a type it was not checked against, and an artifact of the new type may be created where the link waits for a decision.
- [ ] **Where the change lands** (about 4 production, 2 test): what sits under an IRI, held or waited on (`port.py`, `sqlite_reads.py`, the draft's equivalent, reusing Task 8's read where it serves), the define's refusal beside slice 158's identity check (`edits.py` or `drafting.py`, `refusals.py`); `tests/test_define_a_type.py`, one module for the race.
- [ ] **Decisions applied:** 12, 1.
- [ ] **Tests the decisions break:** any existing test that defines a type under another type's IRI above held artifacts and expects it to land (the batch 32 review's reproduction was a probe, not a test; the scout found none). One that breaks is a `BLOCKED` reply naming it, unless its setup alone can change with no assertion changed.
- [ ] **Verify:** `.venv/bin/python -m pytest -q -m "slice-166.3"` gives 2 passed; the race (a create under the new type's IRI at the same moment as its define) in both orders by a plain test; `make test` shows no new failure.
- [ ] **Checkpoint:** `plan status 166.3 green`, then `plan log "Suite: ..."`.

---

Tasks 10 and 11 were added on 2026-10-11 from the batch's branch review. Task 10 rests on decision/a-link-that-waits-keeps-waiting; Task 11 is the review's refactors A, B and C.

13. **A link that waits keeps waiting.** A change to an artifact (a replacement of the whole or of a node, an item added or removed, any change in a set) that leaves in place a link into a part its held target lacks, as the store holds that link before the change (the same field and place, the same target IRI and part), lands, and the link still waits. A link the change adds, or alters in target or part, into a part a held artifact lacks is refused as today (`ref`). A create is always new. The port's landing check accepts the same: the domain says on the link that it already waits, as it says the held type an unheld target sits under, and the adapter accepts a link so marked only when the store already holds that very link for that artifact. The store's check lists it as a placeholder by the same judgement (it replaces slice 170's own rule in `check.py`).

14. **Which link is "that link"** (added after Task 10's review). A waiting link is the same link, left as it is, when the artifact before and after the change holds a link to the same target IRI and part in the same field of the same thing: the artifact itself, or the item of the same name in the same collection. Where it stands in a list (an item's position among its collection's items; a link's position among a field's several links) does not count, so removing or reordering other items or other links of the field leaves it waiting. A link moved to another field or another item is new.

### Task 10: Slice 170.1. A link that waits keeps waiting when its artifact changes

Review: per-task
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Scenarios** (`@slice-170.1`, 1 scenario, 1 collected): check-a-change / Changing an artifact that holds a link waiting on a part its target lacks leaves the link waiting.
- [ ] **Why it is red today:** no steps; behind them every change to such an artifact is refused with `ref` at the link (the draft's check refuses a link into a part its held target lacks, and so does the adapter's landing check).
- [ ] **Where the change lands** (about 5 production, 3 test): the one judgement of "this very link already waits" beside "whether a link lands" (`validation.py` or a module of its own if `validation.py` would pass its limit), used by the draft's check (`drafting.py`/`validation.py`), handed to the port on the link (`port.py`, `links.py`) and checked at landing (`sqlite_checks.py`), and by `check.py` in place of its own rule; `tests/test_create_an_artifact.py` or `tests/test_change_an_artifact.py` (the steps, where the scenario's Givens already live), `tests/test_the_storage_port.py`, one module of plain tests.
- [ ] **Decisions applied:** 13, 5.
- [ ] **Tests the decisions break:** slice 170's plain tests of `check.py`'s exemption keep their assertions (the judgement moves, the answers do not). The port's case that a link into a part a held artifact lacks is refused stays for a link not so marked. Another test that breaks is a `BLOCKED` reply naming it, unless it was written in this batch and pinned an interim state.
- [ ] **Verify:** `.venv/bin/python -m pytest -q -m "slice-170.1"` gives 1 passed; plain tests through the contract: each kind of change that leaves the link lands; a change that alters the link's part to another lacking part is refused; a change that adds a second link into a lacking part is refused while the first still waits; a set of changes; the race of a change to the linker against the target gaining the part, both orders; the whole-store check and `kb validate` unchanged for it; `make test` shows no new failure.
- [ ] **Checkpoint:** `plan status 170.1 green`, then `plan log "Suite: ..."`.

### Task 11: Slice 170.2. drafting.py, cli.py and edits.py split before batch 36 grows them

Review: batch-end
Model: sonnet
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Check:** `make test` gives the same passed and failed tests as the record before it; `wc -l` gives `src/kb/drafting.py` at most 215, `src/kb/cli.py` at most 200, `src/kb/edits.py` at most 200, and no module under `src/kb` over 250.
- [ ] **Where the change lands** (about 6 production, 0 test): what stands in the way of a type's removal and the questions "does this set remove a type" and "does it define one" move from `drafting.py` to `standing.py` (the function that also finds waiting links renamed for what it finds); the printing of the check's three lists and of the import's report moves from `cli.py` to a module of its own; a create's identity and naming move from `edits.py` to a module of its own. Each new module gets a row in CLAUDE.md's map and each cut module's row says what is left. Behaviour, messages and printed output are unchanged.
- [ ] **Tests the decisions break:** none: a refactor; tests use the contract, the operator's commands and public functions. A test importing a name that moves is a `BLOCKED` reply naming it.
- [ ] **Verify:** the Check, with the `wc -l` output in the report.
- [ ] **Checkpoint:** `plan status 170.2 green`, then `plan log "Suite: ..."`.
