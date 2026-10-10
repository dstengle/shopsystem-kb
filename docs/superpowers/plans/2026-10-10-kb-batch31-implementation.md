# kb batch 31 Implementation Plan: back up a store whole and restore it (K1)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Each task is one slice, implemented under shopsystem-bdd:bdd-red-green. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** the operator backs a running store up to one file, its history and journal included, at one moment and without stopping writers or a server, and restores that file as a store in a directory holding none (149-153).

**Architecture:** two operator commands beside export and import, never rpcs. `kb backup <file>` finds its store as every operator command does (the client's `_operated` path: discovery, a connection refused as `store.directly` refuses it), runs inside the servicer's one boundary over the store opened as it is for `kb validate` (so an earlier or a later kb's store and an unreadable database are refused there, once), and copies the database at one moment with SQLite's online backup into a file that carries the store's form. `kb restore <file> <root>` reads that form before anything is made, then, through `staging.py`, puts a store in place whole: the backup copied in as the database, the marker written last, one rename. A restore signs nothing and lands nothing, so it needs no role.

**Tech Stack:** Python 3.11, SQLite (WAL) through `sqlite3`, pytest-bdd 8.1, pytest-xdist.

**Spec:** `spec/capabilities/operate-a-store.md` (Behaviour lines on backing up and restoring, Implementation lines naming `kb backup <file>` and `kb restore <file> <root>`, commits d2d4e02 and b295586), `spec/decisions.md` decision/0028-backup-and-restore-beside-export. Slices: `docs/superpowers/plans/2026-09-24-kb-slices.md`, slices 149-153.

## Global Constraints

- Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.10.0/scripts
- One task per slice. The plan holds no code: the implementer writes steps and code under bdd-red-green, after the red run.
- `Review: per-task`, `Model: opus` for a task touching concurrency, the published contract, data integrity or moving stored data (Tasks 1 and 2); `Review: batch-end`, `Model: sonnet` for every other task; the batch's branch review covers those.
- CLAUDE.md holds: no module under `src/kb/` over 250 lines, `servicer.py` under 150. Today `cli.py` is 197, `store.py` 238, `sqlite_store.py` 221, `refusals.py` 223: backup's SQLite work does not go into `sqlite_store.py`, and nothing is added to `store.py`. If `cli.py` would cross 250 with both commands, it is split first. Rule 1: no broad `except` outside `servicer.py`'s wrapper. A new concern gets a new module, with its row in CLAUDE.md's module map in the task that makes it; a module's row changes in the task that changes what it owns (`cli.py`, `client.py`, `staging.py`, `operating.py`).
- No new rule name: kb's rules are published (decision/published-contract-v1-in-0-7-0). Every fault below uses a rule `rules.py` already names.
- No scenario or step definition names the staging directory (`.kb-starting`) or the database's file name (spec Testing). A plain test of a module's public functions may.
- `tests/test_look_after_a_store.py` is 580 lines. Backup and restore steps go in a step module of their own under `tests/`, imported into it so `scenarios("operate-a-store.feature")` binds them; the file itself grows only by that import.
- Baseline at a43eaea (plan log): **683 passed, 28 failed** in 21 s: the 18 backup and restore scenarios, outlines expanded.

### Binding values, verbatim from the spec

- "When the operator backs up a store, the backup holds the store whole, its history and its journal included."
- "When the operator backs up a store, the backup holds the store as it stood at one moment, each set landing meanwhile either in it whole or not at all."
- "When the operator restores a backup in a directory with no store inside it, there is a store inside that directory holding everything the store backed up held, its history and its journal included, and no role is needed."
- "When the operator restores a backup, the restored store's history ends with the last entry the store held when backed up."
- Implementation: "The commands are … `kb backup <file>` and `kb restore <file> <root>`"; "`kb backup <file>` writes the backup as one file."; "Backing up and restoring are the operator's commands only, not rpcs: the contract does not change for them."

## Decisions this plan takes

1. **What a backup is.** One SQLite database file: the store's database copied by SQLite's online backup (`sqlite3.Connection.backup`, all pages in one step, so one read transaction and one moment), with kb's mark and the store's form set in the copy's header (`PRAGMA application_id` a constant of kb's, `PRAGMA user_version` = `store.STORE_FORM`). The marker file is not in it; the restore writes this kb's marker. Rests on "writes the backup as one file" and "holds the store whole".
2. **Telling a backup apart, before anything is made.** A file that is not a SQLite database, or whose `application_id` is not kb's, is not a backup kb made; `user_version` below `STORE_FORM` is an earlier kb's, above it a later kb's. All three are refused with rule `unreadable` (as a store this kb cannot read is, answer-a-damaged-file), each with its own message: "not a backup kb made", "made by an earlier kb, which this kb cannot read", "made by a later version of kb, which is needed to read it". Rests on the three restore lines and "nothing is made".
3. **"Holds the store whole, its history and its journal included."** The history is the `versions`, `sets` and `entries` tables, the journal the entries (journal.py); all are in the one database, so a whole-database copy carries them. Compared in steps through the contract only: every artifact read whole, each one's `History`, and the journal (`Journal`/snapshot reads) of the restored store equal the backed-up store's. No step opens the database.
4. **No role, nothing signed.** A restore lands no set and writes no entry; `KB_ACTOR` is not read. Rests on "no role is needed" and "history ends with the last entry".
5. **The restored database is a store's database as `sqlite_store.make` leaves one**: WAL mode set, `application_id`/`user_version` left as copied (harmless to the adapter). Opening the restored store must be indistinguishable from opening a started one.
6. **The backup's place.** Refused with rule `root` (as `refusals.export_would_overwrite`) when anything is there, a file or a directory, empty or not, or a dangling symlink; checked before the store is opened and again by creating the file exclusively, so nothing is ever written over. A failed backup removes the partial file it made, and only that.
7. **Finding the store.** `kb backup` goes through the client's `_operated` path, as `kb export` does: discovery's faults, `store.directly`'s fault for a connection, then `Operator`'s boundary opening the store (EarlierKb, LaterKb, Unreadable faults from `escapes.py`). The outline's refusal rows compare the backup's stderr, with the command's name swapped, to `kb validate`'s run in the same place.
8. **One moment without the write lock.** The copy runs in a read transaction on a WAL database: it neither takes nor waits on the write lock, so writers are never refused because of it and it is never `busy`. The boundary for backup is not `at_one_moment` (the copy is its own read transaction), and not `writes`: a served store is backed up beside its server (`served.unserved` is not asked).
9. **Restoring a place.** `staging.py` checks the root as `kb.init` does (`starting.refused`: rule `root`, already a store, inside a store, cannot be written), then reads the backup's form (decision 2), then stages: the database copied in from the backup (SQLite backup from the file, not a byte copy, so a backup taken mid-WAL lands whole), the marker written last, one rename into place. The unwritable refusal's message says a store is restored, not started, in a directory kb can write, naming it; the place-refusals' other messages are `kb.init`'s.
10. **Commands.** `kb backup <file>` and `kb restore <file> <root>`; exit 2 on a refusal, 0 otherwise, as every command. `kb --help` lists `{init,validate,export,import,backup,restore,serve}`; the help for each says what it does in the capability's words. Interrupt handling for restore is `cli._interrupted`, as `kb init --seed`'s.

## Review Focus

1. A backup of a store whose WAL holds landed sets not yet checkpointed holds those sets. Owner: Task 1, a plain test (land a set, back up with no checkpoint, restore, read it).
2. A backup's place in a directory that does not exist is refused, not raised. Owner: Task 5, a plain test of the command.
3. Restoring a backup whose file is a kb backup but truncated (damaged) is refused with rule `unreadable` and nothing made, never a traceback. Owner: Task 3, a plain test.
4. A restored store can be changed straight away and served at once (`kb serve` on it). Owner: Task 1, a plain test: create an artifact through `kb_client.connect(root)` after restoring.
5. A backup of a freshly started store (only the type of types) restores to a store that checks clean. Owner: Task 1, a plain test.

---

### Task 1: Slice 149 — back a store up and restore it whole

Review: per-task
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.10.0/scripts

- [ ] **Scenarios** (`@slice-149`, 4 scenarios, 4 collected): operate-a-store / The command line offers setting up, checking, exporting, backing up, restoring and importing, and nothing else that changes what the store holds; The operator backs up a store, and the backup holds it whole; The operator restores a backup in a directory with no store inside it; A restored store's history ends where the backed-up store's did.

- [ ] **Why it is red today** (suite record at a43eaea): every step naming a backup or a restore is undefined; there is no `backup` or `restore` command (`kb --help` lists `{init,validate,export,import,serve}`). The command-line scenario's Then changed wording, so slice 113's `_offers_four_commands` step (tests/test_look_after_a_store.py:128) no longer matches; its `nothing else that changes what the store holds` step still does.

- [ ] **Where the change lands.**
  - New `src/kb/backups.py`: a backup, the one file a store is copied to: made from the store held (through the port, decision 1) at a place nothing is at, and read back as this kb's backup, an earlier kb's, a later kb's or none (decision 2). Its CLAUDE.md row.
  - New `src/kb/sqlite_backup.py`: the SQLite adapter's online copy of a database into a new file and out of one, and the header values it carries. Its CLAUDE.md row. The port (`port.py`) gains one method every adapter answers, the store copied whole to a file at one moment; `SqliteStore` answers it through `sqlite_backup.py`.
  - `src/kb/operating.py`: `Operator.backup`, one call into the domain inside the boundary (decision 8).
  - `src/kb/client.py`: `backup(file)` through `_operated`, as `export` (decision 7).
  - `src/kb/staging.py`: `restored(root, backup)`, decision 9, beside `seeded` and `started`.
  - `src/kb/refusals.py`: the faults of decision 2 and 6, from plain values. If it would cross 250, the backup's faults go in `backups.py`'s own refusals module instead (`backup_refusals.py`), with its row.
  - `src/kb/cli.py`: the two commands, dispatch only (decision 10).
  - New step module under `tests/` for backup and restore steps, imported into `tests/test_look_after_a_store.py`; slice 113's `_offers_four_commands` replaced by the new wording's step.

- [ ] **Steps to reuse.** `a directory that has no store inside it, and nothing names which role the operator is` (no `KB_ACTOR` is passed); `_kb` from conftest (in process); `calls.a_decision_type_and_a_decision`, `calls.define`, `calls.start_a_store`; `nothing else that changes what the store holds`; `there is a store inside that directory` (it asserts exit 0 and empty stderr on `ran`). The snapshot and replace calls from `calls.py` to give the store a replaced decision and a snapshot.

- [ ] **Decisions applied.** 1, 2 (only "this kb's backup" is exercised here), 3, 4, 5, 9, 10. Review Focus 1, 4, 5 land here.

- [ ] **Verify.** `.venv/bin/python -m pytest -q -m slice-149` → 4 passed; then `make test` → at least 687 passed, 24 failed (slices 150-153 still red).

- [ ] **Checkpoint.** `plan status 149 green`; `plan log "Suite: ..."`.

### Task 2: Slice 150 — back up a store while it is written and served

Review: per-task
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.10.0/scripts

- [ ] **Scenarios** (`@slice-150`, 4 scenarios, 4 collected): operate-a-store / A set landing while the operator backs up the store is in the backup whole or not at all; The operator backs up the store while clients are writing to it; The operator backs up the store while another change is being written; The operator backs up a store a server is serving.

- [ ] **Why it is red today:** their Givens (clients writing, a set landing during the backup, another change holding the store, a server serving it) and Whens are undefined. Once Task 1 is green the backup itself exists; what is unknown is whether its one read transaction holds under a writer.

- [ ] **Where the change lands.** Only where the red run shows it: `src/kb/sqlite_backup.py` (one step, a read transaction, never `BEGIN IMMEDIATE`), `src/kb/operating.py` (the boundary flags, decision 8). Steps in the backup step module.

- [ ] **Steps to reuse.** conftest's `_another_change_holds_the_store` (it holds the write lock longer than the store waits; the backup must finish while it is held); `at_once.py` for writers running beside the backup and a set held mid-landing at a gate; `serving.py` to run a real `kb serve` on the store at port 0, and `_answered_at` (tests/test_look_after_a_store.py:217) for "a caller reaching it is answered from that store".

- [ ] **Decisions applied.** 8. "Whole or not at all" is shown by restoring the backup and finding all three decisions of the set, with their history and journal entries, or none (decision 3's comparison).

- [ ] **Verify.** `.venv/bin/python -m pytest -q -m slice-150` → 4 passed; then `make test` → at least 691 passed, 20 failed.

- [ ] **Checkpoint.** `plan status 150 green`; `plan log "Suite: ..."`.

### Task 3: Slice 151 — a restore refuses what it cannot make a store of

Review: batch-end
Model: sonnet
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.10.0/scripts

- [ ] **Scenarios** (`@slice-151`, 6 scenarios, 6 collected): operate-a-store / Restoring a backup where the directory already has a store inside it is refused; Restoring a backup inside a store is refused; Restoring a backup in a directory kb cannot write is refused; Restoring something that is not a backup kb made is refused; Restoring a backup made by an earlier kb is refused; Restoring a backup made by a later kb is refused.

- [ ] **Why it is red today:** each Then (`restoring is rejected because …`) and the Givens for a file that is not a backup, and backups made by an earlier and a later kb, are undefined.

- [ ] **Where the change lands.** `src/kb/staging.py` (`restored` refuses before anything is made, decision 9), `src/kb/backups.py` (decision 2's three readings), the faults where Task 1 put them.

- [ ] **Steps to reuse.** conftest's `_directory_with_a_store_inside`, `_directory_inside_a_store`, `_store_holds_what_it_held` and `before`; slice 146's unwritable-root setup in tests/test_look_after_a_store.py; `held.holds_nothing`/`held.holds_anything_in_the_place` for "nothing made". An earlier or a later kb's backup is made in the step by setting the copy's `user_version` below or above `STORE_FORM` through `backups.py`'s public functions or plain `sqlite3` on the test's own file.

- [ ] **Decisions applied.** 2, 9. Review Focus 3 lands here.

- [ ] **Verify.** `.venv/bin/python -m pytest -q -m slice-151` → 6 passed; then `make test` → at least 697 passed, 14 failed.

- [ ] **Checkpoint.** `plan status 151 green`; `plan log "Suite: ..."`.

### Task 4: Slice 152 — a stopped restore leaves no store

Review: batch-end
Model: sonnet
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.10.0/scripts

- [ ] **Scenarios** (`@slice-152`, 1 scenario, 1 collected): operate-a-store / A restore that was stopped before it finished leaves no store, and the same restore run again restores the backup.

- [ ] **Why it is red today:** the When (`the operator's restore of that backup in that directory is stopped before it finishes`) and `the operator runs the same restore again` are undefined. The step `that directory has no store inside it` exists (the seeded init's stop) and reads `stopped`.

- [ ] **Where the change lands.** `src/kb/staging.py` if the run shows a stopped restore leaves anything a rerun trips on (the staging place is cleared first, as for a seed); `src/kb/cli.py` for SIGINT, through `_interrupted`. `tests/stopping.py` gains the restore beside the seeded init, killed with SIGKILL the moment the directory holds anything and still no store.

- [ ] **Steps to reuse.** `stopping.stopped` (its trigger, and the installed `kb`); `that directory has no store inside it`; `there is a store inside that directory`; Task 1's comparison of the restored store with the backed-up one.

- [ ] **Decisions applied.** 9.

- [ ] **Verify.** `.venv/bin/python -m pytest -q -m slice-152` → 1 passed; then `make test` → at least 698 passed, 13 failed.

- [ ] **Checkpoint.** `plan status 152 green`; `plan log "Suite: ..."`.

### Task 5: Slice 153 — a backup refuses where it cannot be made

Review: batch-end
Model: sonnet
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.10.0/scripts

- [ ] **Scenarios** (`@slice-153`, 3 scenarios, 13 collected): operate-a-store / Backing up a store to a place where anything already is is refused (4 examples); kb backup finds the store as kb validate does, and is refused where kb validate is (8 examples); Backing up where a connection to a server is found and no store is refused.

- [ ] **Why it is red today:** the Whens (`the operator backs up the store to that place`, `the operator runs kb backup there`) and Thens are undefined. Most of the behaviour should already come from Task 1's path (decision 7); the run says which parts do not.

- [ ] **Where the change lands.** `src/kb/backups.py` (decision 6's place check), `src/kb/client.py` only if the run shows `_operated` misses a case. `tests/test_every_call_is_refused_when_the_store_cannot_be_read.py`'s `COMMANDS` gains `backup`, so the table-driven test covers it as every other command (formulating-features: "a line every call must keep").

- [ ] **Steps to reuse.** conftest's `_working_deep_inside`, `_outside_with_kb_root`, `_outside_with_nothing_named`, `_outside_with_kb_root_naming_no_store`, `_inside_one_naming_another`; `a directory holding a store made by an earlier kb` / `… a later kb` / `a directory holding a connection to a server and no store` (tests/test_look_after_a_store.py:348-363) and the damaged-database setup of test_every_call_is_refused_when_the_store_cannot_be_read.py; `serving.py` for "that server serves a store". `_kb_validate` (tests/test_look_after_a_store.py:107) for the comparison run.

- [ ] **Decisions applied.** 6, 7. Review Focus 2 lands here.

- [ ] **Verify.** `.venv/bin/python -m pytest -q -m slice-153` → 13 passed; then `make test` → at least 711 passed, 0 failed.

- [ ] **Checkpoint.** `plan status 153 green`; `plan log "Suite: ..."`.
