# kb batch 24 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The eleventh architecture review's refactors, then the PR #1 review answers (slices 115 to 118) and the two fixes the review found.

**Architecture:** kb's rules above the storage port, SQLite below it (CLAUDE.md's module map). Every task is a slice of `docs/superpowers/plans/2026-09-24-kb-slices.md`, built red-green under shopsystem-bdd:bdd-red-green against its scenarios, or, for an enabling slice, against its check.

**Tech Stack:** Python 3.11, SQLite (WAL), protobuf, pytest-bdd.

**Spec:** `spec/` (capabilities and `spec/decisions.md`); the review at `/home/vscode/kb-reviews/eleventh-review.md`.

## Global Constraints

- CLAUDE.md's rules hold for every task: no module over 250 lines, `servicer.py` under 150; split first when a change would cross.
- A fault's `rule` is one of the names `spec/index.md` lists; `busy` is new in this batch (its rule name test is red until slice 115).
- No behaviour no scenario asks for; a refactor is checked by the suite giving the same answer plus its structural check.
- Paths are relative to the checkout. `make test` runs the suite.
- Baseline at the start of this batch: `make test` gives 371 passed, 6 failed (the six ids listed in the slices plan's log of 2026-10-01).

## Review Focus

1. A read while a writer holds the lock must never wait or fail (WAL readers); a test that holds the lock must release it even when the test fails.
2. A refusal for a lock that ran out must be told apart by SQLite's error code (`sqlite_errorcode`, SQLITE_BUSY and its extended codes), never by the message text.
3. A block opened by `at_one_moment` must never enclose `exclusive` or `land` (a deferred BEGIN cannot nest).
4. The marker's new value must not make a store this kb starts read as an earlier kb's, nor the other way round.
5. A read-only store must be refused before anything is written beside it (no `-wal` or `-shm` file made).

---

### Task 1: Slice 114.3.1 — every scenario formulated in `features/` is bound by a test module (review S5)

- Check: a test lists every scenario title in `features/` and fails for one no test module binds; after binding, `make test` fails only on the six baseline ids plus the newly bound, not yet built scenarios, each with `StepDefinitionNotFoundError`, and every other id gives the same answer.
- Why it is needed: several test modules bind scenarios by title (`@scenario(...)`), so ten newly formulated scenarios (answer-a-damaged-file 2 outlines, change-the-store 2, export-and-import-a-store 2, keep-the-history 4) are run by nothing.
- Where it lands: `tests/` only. Prefer binding each feature with `scenarios(...)` where its module already defines every step, or bind the missing titles by name in the module that owns the feature; add one guard test (e.g. in `tests/test_the_published_contract.py` or a new `tests/test_every_scenario_is_bound.py`) that collects scenario titles from `features/*.feature` and the bound ones from pytest-bdd's collected items.
- Checkpoint: log the new failing ids and count.

### Task 2: Slice 114.3.2 — every read, and a snapshot's reading, sees the store at one moment (review S1, Must)

- Check: `grep -n "at_one_moment" src/kb/servicer.py src/kb/operating.py src/kb/write.py` shows the read rpcs' wrapping (Read, Validate, Journal, Search, Refs, List), the operator's import check, and `record`; `query.snapshotted` reads each artifact once; a test in `tests/` racing Read and Snapshot of one artifact against a create/remove loop gets no `store` fault; the suite gives the same answer.
- Where it lands: `servicer.py` (the boundary opens the read block for the read rpcs, which the rpc's definition says), `operating.py` (the import check), `write.record` (read inside one moment, land outside it), `query.snapshotted`.
- Decision: a block from `at_one_moment` never encloses `exclusive` or `land`.

### Task 3: Slice 114.3.3 — only `servicer.py` catches broad exceptions (review S4)

- Check: `grep -nE "except (BaseException|Exception)\b|except:" src/kb/*.py` finds only `servicer.py`; `tests/test_the_storage_port.py` and the race tests give the same answer; the suite gives the same answer.
- Where it lands: `sqlite_store.exclusive` and `_saved` commit on the normal path and roll back in `finally` when they have not committed. CLAUDE.md's `sqlite_store.py` row stops naming the checks `sqlite_checks.py` owns.

### Task 4: Slice 114.3.4 — export and offers make their faults in `refusals.py` (review S2)

- Check: `grep -n "kb_pb2" src/kb/export.py src/kb/offers.py` finds nothing; the suite gives the same answer.

### Task 5: Slice 114.3.5 — the place a name takes in the export layout is decided in `names.py` (review S3)

- Check: `grep -nE 'slug\}\.yaml|\.slug' src/kb/export.py` finds nothing; `grep -n "def place\|def filed" src/kb/names.py` finds both; the suite gives the same answer.

### Task 6: Slice 114.3.6 — the adapter writes the search rows `search.py` gives, under row ids kb chooses (review S6, S7)

- Check: `grep -nE '"(sections|body|title)"' src/kb/sqlite_search.py` finds nothing; `grep -n "lastrowid" src/kb/sqlite_search.py` finds nothing; a conformance case in `tests/test_the_storage_port.py` shows an artifact changed and then removed leaves no row matching its words; the suite gives the same answer.
- Where it lands: `search.searchable(content)` yields `(what, label, text)` for each section and field `search.rank` reads; `sqlite_search.py` writes those rows, inserting into `searched` first and giving `search` its rowid explicitly. The SQLite adapter is handed the rows with the change, or calls `search.searchable` itself: the adapter must not import kb's rules, so hand the rows down through the port's `Change` (a field of rows) if `search.py` would otherwise be imported by the adapter. Decide by the module map (`sqlite_search.py` never holds content shape; `search.py` holds ranking prose and fields).

### Task 7: Slice 114.3.7 — code no scenario can reach goes (review S8)

- Check: `grep -n "_refusal_behind\|Unresolvable" src/kb/*.py` finds nothing; `grep -n "holds(type_id)" src/kb/export.py` finds nothing; the suite gives the same answer.

### Task 8: Slice 115 — a change that waits too long for the write lock is refused as busy

- Scenarios (7, `pytest --collect-only -q -m slice-115`): change-the-store / A change that waits longer than the store waits for another change is refused as busy; change-the-store / A read while another change is being written is not refused as busy; make-several-changes-in-one-go / A set that waits longer …; snapshot-what-work-read / A snapshot that waits longer …; operate-a-store / The operator checks the store while another change is being written; export-and-import-a-store / An import that waits longer …; export-and-import-a-store / The operator exports the store while another change is being written. Also red today: `tests/test_the_published_contract.py::test_the_rule_names_kb_gives_are_exactly_the_spec_lists` (rules lack `busy`).
- Why red: no steps yet; and a lock wait that runs out raises `sqlite3.OperationalError` ("database is locked"), which `sqlite_store.opened` turns into `Unreadable` (rule `unreadable`).
- Where it lands: `rules.py` gains `busy`; the port gains a refusal for a lock that ran out (e.g. `Busy`), raised by the adapter when `sqlite_errorcode`'s primary code is `SQLITE_BUSY`; `servicer._escaped` maps it to rule `busy` with a message saying the store was busy with another change and the change may be made again. The import (`importing.py`) checks the store is fresh, drafts and lands inside one `held.exclusive()` block, so the freshness is held through the landing (review Not met 8), with a pytest race test.
- Test seam: a step "another change is being written and holds the store longer than the store waits" holds the write lock on its own connection (in `tests/held.py`, the one module that knows how the store is kept) and shortens the store's wait (`sqlite_store.BUSY`, set for the test through `monkeypatch`); the lock is released at the end of the test whatever happens.
- Decisions: reads never take the write lock, so a read, a check and an export are not refused (WAL); "the same change may be made again" is checked by making it again once the lock is let go and seeing it land.

### Task 9: Slice 116 — the history gives one artifact's entries in the order they landed

- Scenarios (5, `-m slice-116`), keep-the-history: The client reads the journal since a time (reworded Then); The history of one artifact comes in the order its changes landed; The history across artifacts comes in the order of the moments; Entries for different artifacts at the same moment come in the order they landed; An entry stamped before a moment that lands after a read since it is not given by a later read.
- Why red: the history is ordered by moment then seq for every read (`sqlite_reads.history`), so one artifact's entries follow their moments, and ties between sets follow minted seq, not landing.
- Where it lands: `sqlite_reads.history` orders a read narrowed to one artifact by landing order (the `entries` table's insertion order), and every other read by moment then landing order; the port's `history` docstring says so. `tests/test_read_the_journal.py`'s step `_only_todays_change` is rewritten for the reworded Then (review: dead step).
- Decision: a read narrowed to one artifact keeps landing order whatever other filter it carries (the line says "the history of an artifact").

### Task 10: Slice 117 — a store made by an earlier kb is told apart and told how to move

- Scenarios (35 with outline rows, `-m slice-117`): start-a-store / Starting a store in a directory that already has one made by an earlier kb is refused; answer-a-damaged-file / A store found that was made by an earlier kb, in a form this kb cannot read, refuses every call and command that needs it (both ways of finding it).
- Why red: the marker this kb writes (`{"contract": "0.1"}`) is the one 0.3.0 wrote, so a 0.3.0 store reads as one whose database is missing.
- Where it lands: `store.py` writes a new marker value that names this form of store (e.g. `{"store": 1}` beside nothing else) and, when it opens a store whose marker holds the old form, refuses with a refusal of its own that `servicer._escaped` turns into rule `unreadable` with a message saying the store was made by an earlier version of kb: start a new store and import the old one's files. The step that makes an earlier kb's store writes 0.3.0's layout (the marker `contract: "0.1"`, files under `kb/<kind>/<slug>.yaml`, no database) in `tests/held.py`.
- Decision: a marker that is neither form is the earlier-kb refusal too only if it holds `contract`; anything else unreadable as a damaged marker is not this slice's.

### Task 11: Slice 118 — a store on a read-only filesystem is refused as unreadable

- Scenarios (34 rows, `-m slice-118`): answer-a-damaged-file / A store whose database cannot be opened for writing … (a read-only directory, a read-only file).
- Why red: `mode=rw` on a read-only file opens it read-only without a word, and reads may succeed.
- Where it lands: `sqlite_store.opened` refuses with `Unreadable`, naming the database and saying it cannot be opened for writing, when the database file or its directory cannot be written, before any statement; nothing is made beside it.
- Test seam: steps make the directory or the file read-only with `chmod` and restore it at teardown; skip-free (the suite does not run as root).
