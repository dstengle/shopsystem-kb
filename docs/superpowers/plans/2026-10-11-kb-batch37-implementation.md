# kb batch 37 Implementation Plan: export through the contract, and selection by path

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Each task is one slice, implemented under shopsystem-bdd:bdd-red-green.

**Goal:** a client takes the store's canonical files through the contract, one at a time from one moment, with the history position they reflect, in process and through a server; lists, follows and exports select by the path below the type; each history entry gives its position (slices 170.6, 170.7, 171, 172, 173, 174, 174.1, 175, 176).

**Architecture:** the operator's `kb export` already writes one file per held version of a type and each artifact in its own version's order, from one read moment (`export.py`). This batch gives the same list of files to a client as kb's first server-streamed rpc. Two modules are at their size limits and are split first: the one fail-closed wrapper leaves `servicer.py`, and the port's value classes leave `port.py`. Selection by path is a new field on List and Follow and then on Export.

**Tech Stack:** Python 3.11, grpcio/protobuf (`make contract`), SQLite, pytest-bdd 8.1, pytest-xdist.

**Spec:** `spec/capabilities/{export-through-the-contract,keep-the-history,query-the-store,name-what-is-asked-for,export-and-import-a-store}.md`, `spec/decisions.md` (decision/0029, 0030-export-streams-and-carries-its-position, path-selection-is-a-segment-prefix, export-selections-combine, journal-position-is-an-entry, each-type-version-a-file, an-artifact-is-read-through-its-version, busy-rule). Slices: `docs/superpowers/plans/2026-09-24-kb-slices.md`. Research, with its consequence sweep: `.superpowers/scout/2026-10-11-batch37/research.md` (the planner's notes).

## Global Constraints

- Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts
- One task per slice, in slice order. The plan holds no code.
- Each task has a `Review:` and a `Model:` line. `Review: per-task` goes to a task that changes concurrency, a transaction or a read moment, or the published contract's behaviour; every other task is covered by the batch's branch review. `Model:` follows the work: `opus` where behaviour or the contract changes, `sonnet` for a refactor, a contract field nothing reads yet, or step definitions.
- The suite is green between slices: `make test` prints 0 failed; tests of slices the living plan lists as not green are expected failures (`tests/slices.py`). To see a slice's scenarios fail for real while building it: `.venv/bin/python -m pytest -q -m "slice-<n>" --runxfail`. A slice's whole-suite record is made after `plan status <n> green`, in the form "N passed, M expected to fail, K unexpectedly passing, 0 failed", and K must be 0: a row that passes before its slice goes on `tests/passing_before_their_slice.txt`, and comes off when its slice lands (the suite demands both).
- CLAUDE.md's rules hold:
  - No module under `src/kb/` over 250 lines; `servicer.py` under 150. A new concern gets a new module with a row in the map.
  - Rule 1: every rpc, the streamed one included, runs inside the one fail-closed wrapper; no other module catches broad exceptions.
  - Rule 2: a request field becomes a value in `values.py` before anything else sees it.
  - Rule 3: a database that cannot be read is one fault, for the streamed rpc too.
  - Rule 6: only `names.py` decides what a path below a type is and whether an IRI sits under it.
  - When a task changes what a module owns, it changes that module's row in CLAUDE.md's map.
- An implementer may change an existing test's setup, with no assertion changed, where the task's decisions require it, and may rewrite tests written earlier in this batch that pinned an interim state; each is listed in its report. Changing what any other existing test asserts is allowed only where the task's "Tests the decisions break" lists it; otherwise it is a `BLOCKED` reply naming the test.
- At this batch's end every scenario tagged up to `@slice-176` passes and the only expected failures are scenarios of slices 177 onward and the rule-names test (slice 182).

### Execution rules

- **Paths in, short replies out.** The controller dispatches with paths and reads replies, `plan show` and `git log --oneline`.
- **By step.** A task with Steps is dispatched one step at a time where an order must be seen green alone (a contract or port change before what uses it); otherwise in one dispatch that may reply `PARTIAL`.
- **One review per `Review: per-task` task,** after its last step. A `Review: batch-end` task gets none.
- **Fresh fixes.** Findings go to a fresh implementer as a fix round, then to a scoped re-review.
- **Lanes.** Tasks in different lanes may run at once, each lane in its own git worktree and branch with its own virtualenv; a lane's implementer never commits the plan and its reply carries the checkpoint entry. The controller merges lanes one at a time and runs the suite after each.

### Binding values, verbatim from the spec

- export-through-the-contract: the client "is given every canonical file of the store, one at a time and at its place, from one moment"; "is told the position of the last history entry landed at that moment"; an export is a read: it is answered through a server exactly as in process, and "while another change is being written".
- keep-the-history: "an export's position is the `id` of the last entry landed".
- decision/path-selection-is-a-segment-prefix: a path below the type selects by whole segments.
- decision/export-selections-combine: a path and a type given together both apply.
- name-what-is-asked-for: "lists, searches, follows links or exports restricted to a kind the store holds no type for" are refused, the kind given back.

## Decisions this plan takes

The research's consequence sweep found four things no slice owned; decisions 6 to 9 settle them.

1. **The stream** (decision/0030). `Export` is a server-streamed rpc. Its messages are, in order: one for each file (its place as the export layout gives it, and its canonical text), then one last message carrying the position. A refusal is the stream's only message, built as every refusal is (a response holds its result or its refusal, never both); it is never a bare transport status from kb itself.
2. **One moment.** The files and the position are read in one read moment that stays open until the last message is sent; the store is opened by the wrapper and closed when the stream ends, is abandoned by the client, or fails. A fault before the first message is a refusal message; a fault after files have been sent ends the stream with a refusal message, and the client is told the export is not complete.
3. **The position** is the `id` of the entry that landed last, by the order entries landed in (not by their moments, which may go back when a clock does). A store always has one (its first entry lands when it starts); if a read finds none, the position is empty. kb promises no order between two positions: a position names an entry.
4. **A read, never busy.** `Export` writes nothing, is not taken under the server's lock, is allowed while a server owns the store, and is never refused as busy; through a server the channel stays open until the stream ends.
5. **Selection** (slice 176). A type selects that type's version files and the artifacts conforming to any version of it. A path selects, across every type, the artifacts whose IRI's path below their own type is that path or under it, by whole segments, and no type's files. Both together give the type's version files and its artifacts at or under the path. (QUESTIONS FOR THE SPEC in the plan log, recommended answers applied.)
6. **`kb export` gains no selection**: the operator's export writes the whole store (export-and-import-a-store's first line); the capability says the operator's export is not this one.
7. **Search, History, Snapshot and Placeholders take no path**: query-the-store gives a path to list and follow only.
8. **Positions after an import, a backup and a restore**: an import's entries land in the order the import lands them and the position is the last of them; a backup copies the history whole, so a restored store's positions are the backed-up store's. No slice builds anything for this; one plain test in Task 4 pins the restored store's export position.
9. **A long export** holds one of the server's worker threads for its length; nothing bounds it in this batch (backlog).
10. **List without a kind** (slice 175): a list by a path may leave the kind out and then spans every type but the type that describes types; a list with neither is refused as a list with no kind is today. Follow narrowed by a path keeps only steps whose artifact's path below its own type matches.

## Review Focus

1. **The read moment under a stream.** A change landing while an export is being read by a slow client is not in that export, and the position is the one before it. Owner: Task 4, a plain test in process; Task 5, through a server.
2. **A client that stops reading** (abandons the stream) leaves no read transaction or store handle open. Owner: Task 4 in process, Task 5 through a server.
3. **Every refusal every rpc gives** (a store that cannot be read, an earlier kb's, a later kb's, no store found, a connection that cannot be reached) arrives as the stream's one message. Owner: Task 4 and the every-rpc tables; Task 5 for the unreachable server.
4. **The position when the clock goes back.** Entries landed at moments out of order: the position is the last landed. Owner: Task 4, a plain test with the tests' clock.
5. **Whole segments.** A path `plan` selects `…/plan` and `…/plan/a`, not `…/planning`. Owner: Task 8, for List, Follow and (Task 9) Export.

---

### Task 1: Slice 170.6. The one wrapper leaves servicer.py

Review: batch-end
Model: sonnet
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Check:** `make test` gives the same result as the record before it; `wc -l src/kb/servicer.py` at most 100; no module over 250.
- [ ] **Where the change lands** (2 production, 0 test): the fail-closed wrapper (the functions that open the store, convert, call the domain once, turn an escaping exception into a fault, hold a read moment, guard a write while a server owns the store) moves from `servicer.py` to a module of its own; `servicer.py` keeps the rpc adapter and which rpcs write. `starting.py` and `operating.py` call the wrapper "inside `servicer.py`'s one wrapper" per CLAUDE.md: they import it from its new module. CLAUDE.md's map gains the row; rule 1's sentence names the new module; every row that says "`servicer.py`'s one wrapper" is reworded.
- [ ] **Tests the decisions break:** none: a refactor. A test importing a private name that moves is a `BLOCKED` reply naming it.
- [ ] **Checkpoint:** `plan status 170.6 green`, then `plan log "Suite: ..."`.

### Task 2: Slice 170.7. The port's values leave port.py

Review: batch-end
Model: sonnet
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Check:** `make test` gives the same result as the record before it; `wc -l src/kb/port.py` at most 180; no module over 250.
- [ ] **Where the change lands** (8 production, 1 to 2 test): the values the port takes and gives (the link, change, entry, version and candidate values and the helpers that judge them) move from `port.py` (246 lines) to a module of their own; `port.py` keeps the interface every adapter answers and its refusals. Every importer moves with it in the same commit (`sqlite_checks.py`, `sqlite_store.py`, `sqlite_reads.py`, `draft.py`, `journal.py`, `export.py`, and whatever else a search finds; no re-export left behind); `tests/test_the_storage_port.py` and any other test naming a moved value change their imports only. CLAUDE.md's map gains the row and `port.py`'s row is cut to what is left.
- [ ] **Tests the decisions break:** none: imports only; no assertion changes.
- [ ] **Checkpoint:** `plan status 170.7 green`, then `plan log "Suite: ..."`.

### Task 3: Slice 171. Each history entry gives its position

Review: batch-end
Model: sonnet
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Scenarios** (`@slice-171`, 1 scenario, 1 collected): keep-the-history / Each entry read from the history gives its position in the history.
- [ ] **Why it is red today:** step definitions only; an entry's `id` is its position already.
- [ ] **Where the change lands** (0 production, 1 test): `tests/test_read_the_journal.py`. If the scenario is red on behaviour once its steps exist, stop and report `BLOCKED` with the Then line and what the store answered.
- [ ] **Tests the decisions break:** none.
- [ ] **Verify:** `-m slice-171 --runxfail` gives 1 passed; after `plan status 171 green`, `make test` gives 0 failed.
- [ ] **Checkpoint:** `plan status 171 green`, then `plan log "Suite: ..."`.

### Task 4: Slice 172. The client exports the store through the contract

Review: per-task
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Scenarios** (`@slice-172`, 2 scenarios, 2 collected), both export-through-the-contract:
  - The client exports the store
  - The client exports the store, and is told the position of the last history entry landed at that moment
- [ ] **Why it is red today:** no steps; no rpc gives the files; nothing reads the entry landed last.
- [ ] **Where the change lands** (about 8 production, 4 test):
  - The port's read of the entry landed last, inside the read moment already open (`port.py`, `sqlite_reads.py`).
  - `src/kb/export.py`: the files as a sequence of (place, canonical text) read in one moment, which `written` writes to disk and the stream sends; the position beside them.
  - `src/kb/contract/kb.proto` with its generated code: the rpc and its messages (decision 1).
  - The wrapper's module (Task 1): a streamed boundary that keeps the store and the read moment open until the stream ends (decision 2) and turns every fault into a refusal message.
  - `src/kb/responses.py` (the stream's messages), `src/kb/servicer.py` (the method), `src/kb/client.py` (`Export` in process; a refusal the client itself makes, such as no store found, as a one-message stream).
  - `tests/test_export_through_the_contract.py` (the steps), `tests/calls.py` (a helper), `tests/contract_v2.golden`, the tables every rpc must appear in (`tests/test_every_call_is_refused_when_the_store_cannot_be_read.py`, `tests/test_the_published_contract.py`: `Export` among the reads, its messages' field sets).
- [ ] **Decisions applied:** 1, 2, 3, 4, 8. Review Focus 1 to 4.
- [ ] **Tests the decisions break:** the golden and the published contract's lists gain the rpc and its messages; the every-rpc table gains its row and must read a streamed answer's refusal. The operator's export tests (`tests/test_export_and_import_a_store.py`) keep every assertion: `written` gives the same files byte for byte.
- [ ] **Steps:**
  1. The position and the files as a sequence: the port's read, `sqlite_reads.py`, `export.py`, with a conformance case and plain tests (the last landed when the clock goes back; `written` unchanged byte for byte). Check: those tests pass; `make test` 0 failed.
  2. The contract and the boundary: `kb.proto`, generated code, the golden, the published contract's test, the streamed boundary, `responses.py`, `servicer.py`, `client.py` in process, the every-rpc tables; then the scenarios' steps and Review Focus 1 to 3 in process. Check: `-m slice-172 --runxfail` gives 2 passed.
- [ ] **Verify:** `-m slice-172 --runxfail` gives 2 passed; after `plan status 172 green`, `make test` gives 0 failed, 0 unexpectedly passing.
- [ ] **Checkpoint:** `plan status 172 green`, then `plan log "Suite: ..."`.

### Task 5: Slice 173. An export is a read, served or not

Review: per-task
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Scenarios** (`@slice-173`, 2 scenarios, 2 collected), both export-through-the-contract:
  - While a server serves the store, the client exports through it
  - While another change is being written to the store, the client exports it
- [ ] **Why it is red today:** no steps; the network transport returns a unary response inside a channel it closes on return, so a stream would be read after its channel closed.
- [ ] **Where the change lands** (2 production, 1 to 2 test): `src/kb/network.py` (a streamed call keeps its channel until the stream ends; a transport error, at the start or partway, becomes a refusal message with `unreachable` naming the address), `src/kb/client.py` (the network branch); `tests/test_export_through_the_contract.py`; a shared step moved to `tests/conftest.py` only if two modules need it. `server.py` is expected to need nothing (a read passes through unlocked): say so or say what it needed.
- [ ] **Decisions applied:** 2, 4, 9. Review Focus 1, 2 (through a server), 3 (the unreachable server).
- [ ] **Tests the decisions break:** none expected; the reach-a-served-store tables gain `Export` where they list every rpc.
- [ ] **Verify:** `-m slice-173 --runxfail` gives 2 passed; after `plan status 173 green`, `make test` gives 0 failed.
- [ ] **Checkpoint:** `plan status 173 green`, then `plan log "Suite: ..."`.

### Task 6: Slice 174. Each version of a type is exported as a file of its own

Review: batch-end
Model: sonnet
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Scenarios** (`@slice-174`, 1 scenario, 1 collected): export-through-the-contract / The client exports a store holding several versions of a type.
- [ ] **Why it is red today:** step definitions only; the stream sends the same files the operator's export writes, which already holds one per held version.
- [ ] **Where the change lands** (0 production, 1 test): `tests/test_export_through_the_contract.py`. Red on behaviour once its steps exist is a `BLOCKED` reply with the Then line and what the stream gave.
- [ ] **Tests the decisions break:** none.
- [ ] **Verify:** `-m slice-174 --runxfail` gives 1 passed; after `plan status 174 green`, `make test` gives 0 failed.
- [ ] **Checkpoint:** `plan status 174 green`, then `plan log "Suite: ..."`.

### Task 7: Slice 174.1. List and Follow requests carry a path

Review: batch-end
Model: sonnet
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Check:** `make test` gives the same result as the record before it; the descriptor test passes against the golden with `path` on `ListRequest` and `FollowRequest`; nothing reads the fields yet.
- [ ] **Where the change lands** (1 production, 2 test): `src/kb/contract/kb.proto` with its generated code; `tests/contract_v2.golden`; `tests/test_the_published_contract.py` (the two requests' field sets).
- [ ] **Tests the decisions break:** the golden and those two field sets.
- [ ] **Checkpoint:** `plan status 174.1 green`, then `plan log "Suite: ..."`.

### Task 8: Slice 175. Lists and follows select by the path below the type

Review: per-task
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Scenarios** (`@slice-175`, 2 scenarios, 2 collected), both query-the-store:
  - The client lists by a path below the type
  - The client follows links narrowed to a path below the type
- [ ] **Why it is red today:** no steps; a list requires a kind and takes no path; a follow narrows by kind only.
- [ ] **Where the change lands** (6 production, 3 test): `src/kb/names.py` (an artifact's path below its type, and the whole-segment match), `src/kb/values.py` (the path as a value), `src/kb/requests.py` (the list's kind taken only when given, and the path; the follow's path), `src/kb/query.py`, the port's `ids` taking a path and `src/kb/sqlite_reads.py`; `tests/test_list_artifacts_of_a_kind.py`, `tests/test_follow_the_links.py`, `tests/calls.py`.
- [ ] **Decisions applied:** 7, 10. Review Focus 5.
- [ ] **Tests the decisions break:** a test asserting that a list with no kind is refused stays true when no path is given either (decision 10); if one asserts the refusal for a request that now carries a path, it is a `BLOCKED` reply naming it.
- [ ] **Steps:**
  1. The port's `ids` by a path, default none, with conformance cases (whole segments; every type; the type of types left out). Check: `tests/test_the_storage_port.py` passes whole; `make test` 0 failed.
  2. The domain and the scenarios: `names.py`, `values.py`, `requests.py`, `query.py`, the steps, Review Focus 5 for List and Follow. Check: `-m slice-175 --runxfail` gives 2 passed.
- [ ] **Verify:** `-m slice-175 --runxfail` gives 2 passed; after `plan status 175 green`, `make test` gives 0 failed.
- [ ] **Checkpoint:** `plan status 175 green`, then `plan log "Suite: ..."`.

### Task 9: Slice 176. An export selects by path and by type

Review: per-task
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Scenarios** (`@slice-176`, 4 scenarios; count the collected runs with `features count --by-tag`): export-through-the-contract / The client exports selecting a path below the type; … selecting a type; … selecting a path below the type and a type together; name-what-is-asked-for / Listing, searching, following links or exporting by a kind the store holds no type for is refused.
- [ ] **Why it is red today:** no steps; `ExportRequest` is empty.
- [ ] **Where the change lands** (3 to 4 production, 4 test): `src/kb/contract/kb.proto` with its generated code (`ExportRequest` gains the path and the type), `src/kb/requests.py` (their conversion), `src/kb/export.py` (the selection, decision 5), `src/kb/servicer.py` only for the method's one line; `tests/test_export_through_the_contract.py`, the module binding the name-what-is-asked-for outline, `tests/calls.py`, `tests/contract_v2.golden` (and the published contract's field set for the request).
- [ ] **Decisions applied:** 5, 6. Review Focus 5 for Export.
- [ ] **Tests the decisions break:** the golden and the request's field set. The operator's `kb export` tests keep every assertion (decision 6).
- [ ] **Verify:** `-m slice-176 --runxfail` passes every collected run; after `plan status 176 green`, `make test` gives 0 failed and the only expected failures are scenarios of slices 177 onward and the rule-names test.
- [ ] **Checkpoint:** `plan status 176 green`, then `plan log "Suite: ..."`.
