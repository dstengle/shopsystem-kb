# kb batch 38 Implementation Plan: sets checked only, names, and parts a create names

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Each task is one slice, implemented under shopsystem-bdd:bdd-red-green.

**Goal:** a client asks for a set of creates or replacements to be checked only and is answered as it would land, with nothing written and never refused as busy (177); every name a call carries is refused for its shape before anything is looked up (178); a create may name its parts, the store names the rest, and a part is read by its artifact's IRI, `#` and its place (179); links in a set land on parts and placeholders the set makes (180). Two modules near their size limit are split first (176.1, 176.2).

**Spec:** `spec/capabilities/{make-several-changes-in-one-go,name-what-is-asked-for,name-artifacts-and-items,change-the-store,check-a-change}.md`, `spec/decisions.md` (decision/check-only-sets, iri-grammar, rules-for-iri-refusals and those the capabilities rest on). Slices: `docs/superpowers/plans/2026-09-24-kb-slices.md`. Research, with its consequence sweep: `.superpowers/scout/2026-10-11-batch38/research.md` (the planner's notes).

## Global Constraints

- Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts
- One task per slice. The plan holds no code.
- `Review: per-task` goes to a task that changes concurrency, a transaction or a read moment, or the published contract's behaviour; every other task is covered by the batch's branch review. `Model:` follows the work.
- The suite is green between slices: `make test` prints 0 failed; tests of slices the living plan lists as not green are expected failures. To see a slice's scenarios fail for real while building it: `.venv/bin/python -m pytest -q -p no:cacheprovider -m "slice-<n>" --runxfail`. A slice's whole-suite record is made after `plan status <n> green`, in the form "N passed, M expected to fail, K unexpectedly passing, 0 failed", and K must be 0: rows on `tests/passing_before_their_slice.txt` come off when their slice lands (three of slice 179's are on it; the suite demands it).
- CLAUDE.md's rules hold: no module under `src/kb/` over 250 lines, `servicer.py` under 150; rule 1 (one fail-closed wrapper, in `boundary.py`); rule 2 (a request field becomes a value in `values.py` before anything else sees it); rule 4 (draft, validate, land); rule 6 (only `names.py`, and the module that takes over item names, decide what a name looks like and whether it is free); a new concern gets a new module with a row in the map; a module's row changes when what it owns changes.
- An implementer may change an existing test's setup, with no assertion changed, where the task's decisions require it, and may rewrite tests written earlier in this batch; each is listed in its report. Changing what any other existing test asserts is allowed only where the task's "Tests the decisions break" lists it; otherwise it is a `BLOCKED` reply naming the test.
- At this batch's end every scenario tagged up to `@slice-180` passes and the only expected failures are scenarios of slices 180.2 onward and the rule-names test (slice 182).

### Execution rules

- **Paths in, short replies out.** The controller dispatches with paths and reads replies, `plan show` and `git log --oneline`.
- **By step** where an order must be seen green alone; otherwise one dispatch that may reply `PARTIAL`.
- **One review per `Review: per-task` task,** after its last step.
- **Fresh fixes.** Findings go to a fresh implementer as a fix round, then to a scoped re-review.
- **Lanes.** Tasks in different lanes may run at once, each lane in its own git worktree and branch with its own virtualenv; a lane's implementer never commits the plan and its reply carries the checkpoint entry. The controller merges lanes one at a time and runs the suite after each. Task 2 (slice 177) is lane A: its files (the contract, `servicer.py`, `boundary.py`, `write.py`, the make-several tests) are disjoint from Tasks 1, 3 and 4.

## Decisions this plan takes

1. **A checked-only set is a read** (decision/check-only-sets; QUESTION FOR THE SPEC logged). `BatchCreateRequest` and `BatchReplaceRequest` gain a flag. A set so flagged is drafted and checked exactly as it would be to land, against one read moment, and answered as it would land (each change's IRI and the revision it would leave, in the set's order) or refused with every fault it would be refused with (a replacement saying a revision its artifact no longer stands at included). It takes no write lock, reads no clock, mints nothing, lands nothing and leaves no history entry. It is never refused as busy, and it is answered while a server owns the store, directly or through the server, since it writes nothing: the wrapper decides "does this call write" by the request, not by the rpc alone.
2. **No name for a checked set:** the answer's set name is empty.
3. **Only sets of creates and of replacements** carry the flag; single changes, `BatchAdd` and `BatchRemove` do not.
4. **A part is named by its artifact's IRI, `#` and its place** (name-artifacts-and-items). A read, and a change that names a part, may give that IRI as its name; an artifact's own IRI on a create still may not carry a `#` or a `@` (refused `locator`, as today). Both spellings a client can already use (a locator's id and place; the part's IRI) name the same thing.
5. **Names a create gives its parts** (QUESTION FOR THE SPEC logged). A part's `id` in a create's content is the name the client gives it: kept when it is a plain name not carried twice in its collection; a name that is not a plain name, and a name two parts of one collection carry, are each refused with the reason the scenario's line gives, naming the place. Parts given no name are named by the store from their title or their place as today, the given names taken first so a minted name never clashes with one. A change keeps its present rules and wording.
6. **Wording.** Where a scenario's Then gives a reason in words the code does not yet use (178's "a name is an IRI, never a path"; the quoted `"@"`; 179's two create refusals), the fault's message gains those words without losing what existing tests assert of it.
7. **A link in a set into a part a create of the set names, or to an IRI nothing holds under a type the set itself defines,** is judged against the state the whole set leaves (rule 4), so it lands (180's Pins); nothing is built unless the red run shows otherwise.
8. **Not in this batch** (consequence sweep rows no slice owns): the kinds that lists, searches, follows and exports name already refuse a malformed IRI as `locator` and stay as they are; the export of a 512-character IRI with a very long segment stays a backlog line; the import naming items is slice 180.2.

## Review Focus

1. **A checked set and a landing set agree.** For the same set against the same store, the checked answer equals what landing then gives (IRIs, revisions, faults), except the set's name and that nothing is written. Owner: Task 2, a plain test over several sets, sound and unsound.
2. **Nothing is written by a check:** no artifact, no version, no link, no history entry, no revision moved, the database file's change counter still. Owner: Task 2.
3. **Never busy, never served-refused:** a checked set is answered while another change holds the write lock, and while a server owns the store, in process and through the server. Owner: Task 2.
4. **Given and minted names together:** a create giving one part the name the store would have minted for another. Owner: Task 4.
5. **A part's two spellings agree:** a read by `<IRI>#<place>` and by the locator's id and place give the same node; a part's IRI that names nothing is refused as the locator's place is today. Owner: Task 4.

---

### Task 1: Slices 176.1 and 176.2. The item names leave names.py; content conversion leaves values.py

Review: batch-end
Model: sonnet
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Check:** `make test` gives the same result as the record before it after each move; `wc -l src/kb/names.py` at most 160; `wc -l src/kb/values.py` at most 185; no module over 250.
- [ ] **Where the change lands:** the grammar, minting, uniqueness and reuse of item names move from `names.py` to a module of their own; the conversion of content trees (and the helpers only it uses) moves from `values.py` to a module of its own. Every importer moves with each in the same commit; no re-export is left. CLAUDE.md's map gains two rows, `names.py`'s and `values.py`'s rows are cut to what is left, and rule 6 names both name modules.
- [ ] **Tests the decisions break:** none: imports and qualified names only.
- [ ] **Checkpoint:** `plan status 176.1 green`, `plan status 176.2 green`, each with its `plan log "Suite: ..."`.

### Task 2: Slice 177. A set can be checked only

Review: per-task
Model: opus
Lane: A
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Scenarios** (`@slice-177`, 4 scenarios; count the collected runs with `features count --by-tag`), all make-several-changes-in-one-go: a set of creates or replacements asked to be checked only answers as it would land and lands nothing; one that would be refused is refused with every fault; a replacement that says a revision its artifact no longer stands at is refused; a set asked to be checked only while another change is being written is answered, not refused as busy.
- [ ] **Why it is red today:** no steps; the requests have no flag; every set takes the write path.
- [ ] **Where the change lands** (4 production, 3 test): `src/kb/contract/kb.proto` with its generated code; `src/kb/write.py` (the check beside the landing: the same draft, at one read moment); `src/kb/servicer.py` and `src/kb/boundary.py` (a flagged set takes the read path: not refused while a server owns the store, not taken under the server's lock); `tests/test_make_several_changes_in_one_go.py`, `tests/calls.py`, `tests/contract_v2.golden` (and the published contract's field sets).
- [ ] **Decisions applied:** 1, 2, 3. Review Focus 1 to 3.
- [ ] **Tests the decisions break:** the golden and the two requests' pinned field sets. The table of rpcs that write (`tests/test_a_served_store_takes_changes_only_through_its_server.py`) keeps `BatchCreate` and `BatchReplace` as writing for an unflagged set; a row or a test is added for the flagged one.
- [ ] **Steps:** (1) the contract: the flag, generated code, the golden, the pinned sets; nothing reads it. (2) the check and the read path, with Review Focus 1 to 3 as plain tests. (3) the scenarios' steps.
- [ ] **Verify:** `-m slice-177 --runxfail` passes every collected run.
- [ ] **Checkpoint:** the reply carries the checkpoint entry (this task is in a lane).

### Task 3: Slice 178. Every name a call carries is an IRI of kb's grammar

Review: batch-end
Model: sonnet
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Scenarios** (`@slice-178`, 6 scenarios; count the collected runs with `features count --by-tag`), all name-what-is-asked-for.
- [ ] **Why it is red today:** step definitions, and the words two refusals give (decision 6); the grammar's refusals themselves hold since batch 32.
- [ ] **Where the change lands** (1 production, 3 test): `src/kb/values.py` (the two messages' wording); `tests/test_read_an_artifact.py`, `tests/test_create_an_artifact.py`, `tests/test_change_an_artifact.py`. A scenario red on behaviour once its steps exist is a `BLOCKED` reply with the Then line and what the store answered.
- [ ] **Decisions applied:** 6, 8.
- [ ] **Tests the decisions break:** none: existing tests assert the present words as substrings or the rule; the new words are added, the old kept. One that asserts a whole message is a `BLOCKED` reply naming it.
- [ ] **Verify:** `-m slice-178 --runxfail` passes every collected run; after `plan status 178 green`, `make test` gives 0 failed.
- [ ] **Checkpoint:** `plan status 178 green`, then `plan log "Suite: ..."`.

### Task 4: Slice 179. A create may name its parts

Review: per-task
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Scenarios** (`@slice-179`, 8 scenarios; count the collected runs with `features count --by-tag`), all name-artifacts-and-items.
- [ ] **Why it is red today:** steps; a create overwrites every part's name with one it mints; nothing refuses a name given twice or a name that is not plain on a create; a read by a part's IRI is refused for its `#`. Three of its outline rows pass already and are on `tests/passing_before_their_slice.txt`.
- [ ] **Where the change lands** (5 production, 3 test): the item-names module (Task 1's) and `src/kb/naming.py` (given names kept and taken first); `src/kb/edits.py` (a create keeps them); `src/kb/refusals.py` (the create's two faults, worded as the lines say; a change's wording unchanged); `src/kb/values.py` or `src/kb/requests.py` (a read or a change naming a part by its IRI, through the conversion that already reads a link's target into IRI and part); `tests/test_create_an_artifact.py`, `tests/test_add_an_item_to_a_collection.py`, `tests/passing_before_their_slice.txt`.
- [ ] **Decisions applied:** 4, 5, 6. Review Focus 4, 5.
- [ ] **Tests the decisions break:** `tests/passing_before_their_slice.txt` loses this slice's three rows when it lands. `tests/test_an_artifacts_iri.py`'s refusal of a `#` on a create's own IRI stays. `tests/test_change_an_artifact.py`'s wording for a change's misnamed item stays.
- [ ] **Steps:** (1) given names kept, with the two refusals and Review Focus 4 as plain tests through the contract. (2) a part read and changed by its IRI, with Review Focus 5. (3) the scenarios' steps and the list.
- [ ] **Verify:** `-m slice-179 --runxfail` passes every collected run; after `plan status 179 green`, `make test` gives 0 failed and 0 unexpectedly passing.
- [ ] **Checkpoint:** `plan status 179 green`, then `plan log "Suite: ..."`.

### Task 5: Slice 180. Links in a set land on parts and placeholders the set makes

Review: batch-end
Model: sonnet
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Scenarios** (`@slice-180`, 2 scenarios; count the collected runs with `features count --by-tag`), both make-several-changes-in-one-go.
- [ ] **Why it is red today:** step definitions; the first needs slice 179's given part names. Decision 7 expects no production change.
- [ ] **Where the change lands** (0 production, 1 test): `tests/test_make_several_changes_in_one_go.py`. A scenario red on behaviour once its steps exist is a `BLOCKED` reply with the Then line and what the store answered.
- [ ] **Decisions applied:** 7.
- [ ] **Tests the decisions break:** none.
- [ ] **Verify:** `-m slice-180 --runxfail` passes every collected run; after `plan status 180 green`, `make test` gives 0 failed and the only expected failures are scenarios of slices 180.2 onward and the rule-names test.
- [ ] **Checkpoint:** `plan status 180 green`, then `plan log "Suite: ..."`.
