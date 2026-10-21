---
id: initiative-archive/missingmass.io/shopsystem/kb/2026-10-11-kb-batch39-implementation
kind: initiative-archive
about: bounded-context/missingmass.io/shopsystem/kb
---
# kb batch 39 Implementation Plan: the import into a store that holds artifacts

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Each task is one slice, implemented under shopsystem-bdd:bdd-red-green.

**Goal:** the operator imports a directory into a store that already holds artifacts: every item named as a write names it (180.2); what the store holds identically passed over and the rest landed (181); refused while a server serves the store (181.1); a differing file refused with rule `differs`, skipped or not (182); each file held to its type's place (182.1); links waiting on placeholders, a lacking part included (183); only a broken type version's reach skipped (184); the command line's help saying so (185). Two modules near their size limit are split first (180.1.1, 180.1.2).

**Spec:** `spec/capabilities/export-and-import-a-store.md`, `spec/capabilities/operate-a-store.md`, `spec/capabilities/reach-a-served-store.md`, `spec/decisions.md` (its last seven entries, decision/a-link-that-waits-keeps-waiting, decision/0024). Slices: `.shop/records/archive/plans/2026-09-24-kb-slices.md`. Research, with its probes and consequence sweep: `.superpowers/scout/2026-10-11-batch39/research.md` (each task names its section; an implementer reads its own section, and the section "CLAUDE.md map: words these slices make untrue").

## Global Constraints

- Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts
- One task per slice. The plan holds no code.
- `Review: per-task` goes to a task that changes concurrency, a transaction or a read moment, the port, or the published contract's behaviour; every other task is covered by the batch's branch review. `Model:` follows the work.
- The suite is green between slices: `make test` prints 0 failed; tests of slices the living plan lists as not green are expected failures. To see a slice's scenarios fail for real while building it: `.venv/bin/python -m pytest -q -p no:cacheprovider -m "slice-<n>" --runxfail`. A slice's whole-suite record is made after `plan status <n> green`, in the form "N passed, M expected to fail, K unexpectedly passing, 0 failed at <hash> in <s> s", and K must be 0: a row on `tests/passing_before_their_slice.txt` and a `@waits_on("<n>")` marker come off when their slice lands.
- CLAUDE.md's rules hold: no module under `src/kb/` over 250 lines; rule 1 (one fail-closed wrapper); rule 2 (parse, don't validate); rule 4 (draft, validate, land: nothing reads the store between handing a set over and its landing); a new concern gets a new module with a row in the map; a module's row changes when what it owns changes (the research lists the words each slice makes untrue). Never change CLAUDE.md's size rules.
- The living plan is edited only with `plan` (`status`, `log`); feature files are not edited.
- An implementer may change an existing test's setup, with no assertion changed, where the task's decisions require it, may rewrite tests written earlier in this batch, and may remove a step or helper bound to no scenario; each is listed in its report. Changing what any other existing test asserts is allowed only where the task's "Tests the decisions break" lists it; otherwise it is a `BLOCKED` reply naming the test.
- Scratch stays out of the checkout, `/dev/shm` and `/tmp/x`; use a directory made with `mktemp -d`.
- At this batch's end every scenario passes; nothing is expected to fail.

### Execution rules

- **Paths in, short replies out.** The controller dispatches with paths and reads replies, `plan show` and `git log --oneline`.
- **By step** where an order must be seen green alone; otherwise one dispatch that may reply `PARTIAL`.
- **One review per `Review: per-task` task,** after its last step.
- **Fresh fixes.** Findings go to a fresh implementer as a fix round, then to a scoped re-review.
- **Lanes.** Tasks in different lanes may run at once, each lane in its own git worktree and branch with its own virtualenv; a lane's implementer never commits the plan and its reply carries the checkpoint entry. The controller merges lanes one at a time and runs the suite after each. Task 1 is lane A (read.py, edits.py's place walk, composition.py). Task 9 is lane C (examining.py's skip analysis and its steps). Task 2 runs in the main worktree beside them; Tasks 3 to 8 and 10 follow in the main worktree, in order.

## Decisions this plan takes

1. **What leaves read.py** (180.1.1): the read of a part, and the read of a type version as an artifact, each to a module of its own; what a place's node's type declares has one home that both `read` and `edits` ask.
2. **A file's given item names are checked as a create's are** (QUESTION FOR THE SPEC logged): a name that is not a plain name, or carried twice in one collection, is an error of the check with rule `item-name`, naming the file.
3. **Naming on import** (decision/an-import-names-items-as-a-write-does): names a file carries are kept and taken first; an item with none is named exactly as a create names it; the imported artifact is then written in the order its type's version declares, so a new name stands where kb writes names. The export of a store kb wrote imports and exports again byte for byte (the existing test is the guard). The check drafts files the same way, so the check and the landing agree.
4. **The import keeps the write lock from before the directory is read until it has landed**, as today: what is identical or differing is judged against the store as it stands when the import lands, a client's change made meanwhile is refused `busy`, and the busy line stays true.
5. **Identical is passed over** (capability, Implementation): a file is compared with what the store holds at its IRI as it would land (named and ordered, decision 3), by everything it gives but its revision; an identical one is left as the store holds it, has no import entry and prints nothing. A type version's file is compared with the version the store keeps at that number, the same way; the type that describes types as today.
6. **A type gaining a version by import:** the new version lands with the revision its file gives, the change read at the revision the store's type stands at; the versions the store already keeps identically are passed over.
7. **The title is compared** (QUESTION FOR THE SPEC logged).
8. **Differs** (decision/an-import-never-skips-a-difference): a file that differs from what the store holds at its IRI, or a type version's file that differs from the version kept at its number, is an error of the check with the new published rule `differs`, its message naming the IRI. The import is refused with one `differs` fault for each such IRI, in the order of names, whether or not errors are skipped, and nothing lands; other errors stay in the report. A directory with errors but no difference is refused as today (`the check found errors`).
9. **A type version below the store's that the store does not keep** is not built here (backlog line; QUESTION FOR THE SPEC logged).
10. **How the port learns an import's link may wait** (183): the import says so on the link it hands, with a mark of its own beside `waits` (which keeps its meaning: the store's own account of a link it held waiting); the adapter lets a marked link into a part its held target lacks land without its own record. A create's or a replacement's link into a lacking part is refused exactly as today.
11. **Every imported link into a part its target lacks waits** (QUESTION FOR THE SPEC logged), the target held by the directory or the store; the check calls such a file clean, agreeing with the landing.
12. **A held type counts as landing** (184): a link waits under any type the store holds or of which a version lands; only a type with no version in the store and none landing leaves the files linking under it out. That is worked out from the files that land and the store, never asked of the check's own draft (which holds broken versions too).
13. **The chain for a file skipped for its link** is the file, then the broken version file of that type with the lowest number (QUESTION FOR THE SPEC logged).
14. **An import into a served store** (decision/an-import-is-held-as-a-change-is) is refused with rule `served`, naming the address, as a change asked directly is; `kb import --check`, `kb export` and `kb backup` are answered as today.
15. **A file is held to its type's place** (same decision): the check reports, with rule `identity`, a file whose IRI does not sit under the type it conforms to or sits under a nearer type the directory or the store holds, and a type's file whose IRI stands where decision/a-types-place-is-settled-by-what-sits-under-it refuses a define; with errors skipped such a file is left out as any broken file.
16. **185 runs last**, so the help never promises what `kb import` refuses.

## Review Focus

1. **The check and the landing agree.** For many directories against many stores (fresh, holding the same, holding other things, holding a type at more versions or fewer), `kb import --check` clean means `kb import` lands, and what the check calls an error or a skip is what the import refuses or leaves out. Owner: Tasks 4, 6, 8, 9.
2. **Round trip.** A store's export imported into a fresh store, and into the store it came from (everything passed over, no history entry), exports the same bytes. Owner: Tasks 3, 4.
3. **Nothing lands on a refusal:** differing, served, busy, errors. Owner: Tasks 4, 5, 6.
4. **Only an import's link may wait unrecorded:** a create or replacement cannot set the mark through the contract. Owner: Task 8.
5. **The lock:** the import holds it throughout; a change made meanwhile is refused busy and never merged. Owner: Task 4.

---

### Task 1: Slice 180.1.1. The part read leaves read.py and the place walk has one home

Review: batch-end
Model: sonnet
Lane: A
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Check:** `make test` gives the same result as the record before it; `wc -l src/kb/read.py` at most 200; `grep -n '\[::2\]\|\[:-1:2\]' src/kb/read.py src/kb/edits.py` prints nothing; no module over 250.
- [ ] **Where the change lands** (5 production, 0 test; research section "Slice 180.1.1"): `read.py` loses the read of a part and the read of a type version as an artifact, each to a new module with its map row (decision 1); the walk of a place to what its node's type declares gets one home (composition.py has 24 lines of room; a new module if it would pass 240), asked by the part read and by `edits.py`. CLAUDE.md's `read.py` and `places.py` rows are made true (the review found `places.py`'s row omits `parts` and `node`).
- [ ] **Tests the decisions break:** none: no test names the moved functions (the scout searched `read\._` over tests).
- [ ] **Checkpoint:** the reply carries the checkpoint entry (this task is in a lane).

### Task 2: Slice 180.1.2. Each change as the port takes it leaves drafting.py

Review: batch-end
Model: sonnet
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Check:** `make test` gives the same result as the record before it; `wc -l src/kb/drafting.py` at most 180; no module over 250.
- [ ] **Where the change lands** (2 production, 0 test; research section "Slice 180.1.2"): the five functions that make each change as the port takes it leave `drafting.py` for a new module with its map row; the helper both halves use becomes a public function of the new module (the new module cannot import `drafting.py`). `drafting.py`'s row is cut to what is left.
- [ ] **Tests the decisions break:** none (the scout searched `drafting\._` over src and tests).
- [ ] **Checkpoint:** `plan status 180.1.2 green` and its `plan log "Suite: ..."`.

### Task 3: Slice 180.2. An import names every item as a write does

Review: batch-end
Model: sonnet
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Scenarios** (`@slice-180.2`: 1 scenario; and the two tests waiting on 180.2 in `tests/test_a_link_that_waits_keeps_waiting.py`): a file holding an item that carries no name.
- [ ] **Why it is red today:** four steps missing; an import puts its artifact whole, naming nothing (research section "Slice 180.2", probes P4, P10).
- [ ] **Where the change lands** (3 production, 2 test): `edits.py` (an import's artifact), `naming.py` (the naming of an import's items beside a create's), `examining.py` only as far as the check must draft a file as it would land (decision 3); `tests/test_export_and_import_a_store.py`, `tests/test_a_link_that_waits_keeps_waiting.py`.
- [ ] **Decisions applied:** 2, 3. Review Focus 2.
- [ ] **Tests the decisions break:** `tests/test_a_link_that_waits_keeps_waiting.py:352` asserts the imported option has no `id`: it asserts instead that the option holds a name the store gave it, and the comment above it is made true; the `@waits_on("180.2")` marker at :376 comes off. `test_the_export_of_a_store_imported_into_a_fresh_store_exports_the_same_files_byte_for_byte` must pass unchanged.
- [ ] **Verify:** `-m slice-180.2 --runxfail` passes; the two brought-back tests pass; a plain test that an unnamed item's new name is written where a create writes it, and that a file's bad or repeated name is an error of the check.
- [ ] **Checkpoint:** `plan status 180.2 green`, its suite record; the backlog's RELEASE GATE line on an unnamed item's waiting link is closed with `plan backlog "CLOSED by slice 180.2: ..."`.

### Task 4: Slice 181. An import lands in a store already holding artifacts

Review: per-task
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Scenarios** (`@slice-181`: 3 scenarios): imports a directory that checks clean into a store, saying which role; the history shows each type landing before its artifacts (one entry for each of six files); an artifact the store already holds identically is passed over and the rest lands.
- [ ] **Why it is red today:** steps missing; the import refuses a store that is not fresh; with that refusal gone an identical file, and a new version of a held type, meet an escaped `Conflict` (research section "Slice 181", probes P1, Q1 to Q9).
- [ ] **Where the change lands** (4 production, 2 test): `importing.py` (the fresh check goes; what the store holds identically is left out of the landing); `file_refusals.py` (the fresh refusal goes); a new module, with its map row, that compares a file with what the store holds (shared with slice 182); the module that reads a change's revision after Task 2 (a type gaining a version, decision 6). Docstrings that say "freshly started store only" in `cli.py`, `staging.py`, `importing.py` are made true except the help text (Task 10). `tests/test_export_and_import_a_store.py`, `tests/test_an_import_holds_the_store_fresh.py`.
- [ ] **Decisions applied:** 4, 5, 6, 7. Review Focus 1, 2, 3, 5.
- [ ] **Tests the decisions break:** `tests/test_export_and_import_a_store.py` `_imported` (asserts the first entry is the store's start and takes every later entry as the import's): it selects the import's own entries; `_lands_as_one_signed_set` (asserts the store holds exactly the directory's names): it asserts the directory's names are held and the import's entries are exactly the directory's files that landed. The steps at about :999 to :1026 are bound to no scenario and are replaced. `tests/test_an_import_holds_the_store_fresh.py`: its assertions stand (decision 4); the module is renamed and its docstring made true.
- [ ] **Steps:** (1) the comparison and the passing over, with plain tests: a store's own export imported into it lands nothing and adds no history entry; a held type gaining a version; the fresh refusal gone. (2) the three scenarios' steps.
- [ ] **Verify:** `-m slice-181 --runxfail` passes every collected run; Review Focus 2 as a plain test.
- [ ] **Checkpoint:** `plan status 181 green`, its suite record.

### Task 5: Slice 181.1. An import into a served store is refused

Review: batch-end
Model: sonnet
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Scenarios** (`@slice-181.1`: 1 scenario): importing into a store a server serves is refused.
- [ ] **Why it is red today:** the operator's import runs as a command that never writes, so nobody asks whether the store is served (research, open decision 12, probe Q0b).
- [ ] **Where the change lands** (2 production, 1 test): `operating.py` and `boundary.py` (the import is a command that writes: refused through `served.py` as a change asked directly is); `tests/test_export_and_import_a_store.py` (reuse the Given "a server serves that store" of the reach-a-served-store steps). `kb init --seed`, `kb serve --start` and `kb restore`, which import or start in a staging place no server owns, are unchanged.
- [ ] **Decisions applied:** 14. Review Focus 3.
- [ ] **Tests the decisions break:** none expected: the scout found no test importing beside a server; the table of commands and rpcs that write, if it lists the operator's commands, gains the import.
- [ ] **Verify:** `-m slice-181.1 --runxfail` passes; plain tests that the check, an export and a backup are still answered beside the server, and that the import lands once the server has stopped.
- [ ] **Checkpoint:** `plan status 181.1 green`, its suite record.

### Task 6: Slice 182. An import that differs from what the store holds is refused

Review: per-task
Model: sonnet
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Scenarios** (`@slice-182`: 2 outlines, 5 runs; and the rule-names test waiting on 182): the check reports each differing decision naming its IRI; the import is refused naming each, with errors skipped or not, and nothing lands.
- [ ] **Why it is red today:** steps missing; nothing compares a file with what is held; `rules.py` has no `differs` (research section "Slice 182", probes P3, P3b, Q3).
- [ ] **Where the change lands** (4 production, 2 test): `rules.py`, `file_refusals.py`, the comparison module of Task 4 (a differing file is an error of its file), `importing.py` (a difference refuses whatever is skipped); `tests/test_export_and_import_a_store.py`, `tests/test_the_published_contract.py` (the marker comes off).
- [ ] **Decisions applied:** 5, 7, 8, 9. Review Focus 1, 3.
- [ ] **Tests the decisions break:** none: the Then "the import is rejected because the check found errors" keeps its line for a directory with errors and no difference.
- [ ] **Verify:** `-m slice-182 --runxfail` passes every collected run; the rule-names test passes unmarked; a plain test that a file with only its revision changed is not a difference, and that a type version's file differing from the version kept is one.
- [ ] **Checkpoint:** `plan status 182 green`, its suite record.

### Task 7: Slice 182.1. An import holds each file to its type's place

Review: batch-end
Model: sonnet
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Scenarios** (`@slice-182.1`: 1 outline, 2 runs): a work item's file whose IRI sits under the type for decisions, or under no held type, is reported as an error naming the file.
- [ ] **Why it is red today:** steps missing; an import never runs the checks a create's and a define's IRI are held to (research, open decision 13, probe Q0).
- [ ] **Where the change lands** (3 production, 1 test): `examining.py` (the file's errors gain it; 37 lines of room: the check itself lives where a create's does, in `naming.py`, asked over the directory's files and the store together), `file_refusals.py` if the fault needs the file's wording; `tests/test_export_and_import_a_store.py`.
- [ ] **Decisions applied:** 15. Review Focus 1.
- [ ] **Tests the decisions break:** none known; a test that imports a file under another type's IRI on purpose would be a `BLOCKED` reply.
- [ ] **Verify:** `-m slice-182.1 --runxfail` passes both runs; plain tests for a type's file standing where a define would be refused, and that with errors skipped such a file is left out and the rest lands.
- [ ] **Checkpoint:** `plan status 182.1 green`, its suite record.

### Task 8: Slice 183. An import's links wait on placeholders

Review: per-task
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Scenarios** (`@slice-183`: 3 outlines, 10 runs): each error reported by file and reason (6 rows); a link to an IRI neither holds under a held type lands on a placeholder (2 rows); a link into a part the artifact at its IRI lacks waits (2 rows).
- [ ] **Why it is red today:** the check outline's table of faults lacks three keys; steps missing; a link into a lacking part is `ref` at the check and `Unlanded` at the port (research section "Slice 183", probes P5 to P7, P6c).
- [ ] **Where the change lands** (6 production, 3 test): `validation.py`, the module that hands each change to the port after Task 2, `drafting.py`, `examining.py`, `links.py`, `sqlite_checks.py`, `port_values.py` (the mark, decision 10: seven files named, at most six changed, said in the report); `tests/test_export_and_import_a_store.py`, `tests/test_the_storage_port.py`, `tests/passing_before_their_slice.txt` (its three rows come off).
- [ ] **Decisions applied:** 10, 11. Review Focus 1, 4.
- [ ] **Tests the decisions break:** `tests/test_links_as_the_port_takes_them.py:52` and the port's tests of a link into a lacking part (`tests/test_the_storage_port.py` about :545 to :600) keep what they assert (`waits` is the store's own account; a link that only says it waits, unrecorded, is refused): the port's tests gain the marked link. The dead builder `_linking_to_nothing` and its key in the faults table are replaced by a link under a type nobody holds.
- [ ] **Steps:** (1) the check outline's rows and the unheld-IRI outline (tests only, once Task 4 is in). (2) the lacking part: the port's mark with its plain tests, then the import and its check. (3) the lacking-part outline's steps.
- [ ] **Verify:** `-m slice-183 --runxfail` passes every collected run; the release gate's reproduction (a note waiting on a part, the target created without it, export, import into a fresh store) as a plain test; a create with such a link is still refused.
- [ ] **Checkpoint:** `plan status 183 green`, its suite record; `plan backlog "CLOSED by slice 183: ..."` for the RELEASE GATE line on a link into a lacking part.

### Task 9: Slice 184. Only a broken type version's reach is skipped

Review: batch-end
Model: opus
Lane: C
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Scenarios** (`@slice-184`: 2 outlines, 9 runs): the check names what would be skipped with its chain (4 rows); the import with errors skipped (5 rows).
- [ ] **Why it is red today:** steps missing; the skip analysis follows a link to an artifact's file, and does not foresee a link under a type no version of which lands, which the landing then refuses whole (research section "Slice 184", probes P8a to P8d).
- [ ] **Where the change lands** (2 production, 1 test): `examining.py` (links to artifacts' files no longer followed; a file linking under a type no version of which lands leads to that type's broken version file) and `importing.py` only if the report changes; `tests/test_export_and_import_a_store.py`. Only the skip analysis and this slice's steps are touched: other tasks edit the same two files in other places, and this lane's branch is merged after them.
- [ ] **Decisions applied:** 12, 13. Review Focus 1.
- [ ] **Tests the decisions break:** the steps and tables bound to no scenario that assert a file linking to a broken file is skipped (`LINKING`, `SKIPPED`, the regex Given at about :599, `TOGETHER_WITH`, the parse Given at about :1088, `LEFT_OUT`'s old keys, `_with_an_error_and_one_linking`, `_with_an_error_and_two_linking`) are replaced. `_told_what_was_skipped` maps one file per name: it is widened to a version's file. `tests/test_the_import_follows_a_file_to_the_version_it_names.py` passes unchanged.
- [ ] **Verify:** `-m slice-184 --runxfail` passes every collected run; a plain test that the check's skips are exactly what the import with errors skipped leaves out, for each row's directory.
- [ ] **Checkpoint:** the reply carries the checkpoint entry (this task is in a lane).

### Task 10: Slice 185. The command line offers import into a store

Review: batch-end
Model: sonnet
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Scenarios** (`@slice-185`: 1 scenario): the command line offers setting up, checking, exporting, backing up, restoring and importing.
- [ ] **Why it is red today:** the Then's text is missing; the help says "into a freshly started store" (research section "Slice 185").
- [ ] **Where the change lands** (1 production, 1 test): `cli.py` (the help and the module's docstring), `tests/test_look_after_a_store.py` (the Then at about :241 is bound to no scenario and is replaced). CLAUDE.md's `client.py`, `cli.py` row is made true.
- [ ] **Tests the decisions break:** none beyond the replaced step.
- [ ] **Verify:** `-m slice-185 --runxfail` passes; `make test` prints 0 failed and nothing expected to fail.
- [ ] **Checkpoint:** `plan status 185 green`, its suite record.
