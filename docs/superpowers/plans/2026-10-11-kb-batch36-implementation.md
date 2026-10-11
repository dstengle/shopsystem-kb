# kb batch 36 Implementation Plan: tooling for a faster, greener suite

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Each task is one slice, implemented under shopsystem-bdd:bdd-red-green.

**Goal:** three enabling slices from the efficiency analyses of 2026-10-11 (`.superpowers/analysis/2026-10-11-test-efficiency.md`) and the request made upstream to shopsystem-bdd (`shopsystem-bdd/docs/superpowers/requests/2026-10-11-predictable-batches-and-analysis-tools.md`): a store's database made in one transaction (170.3), the suite green between slices (170.4), a per-test coverage map (170.5).

**Tech Stack:** Python 3.11, SQLite (WAL), pytest 8, pytest-bdd 8.1, pytest-xdist, coverage.

## Global Constraints

- Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts
- One task per slice. The plan holds no code.
- CLAUDE.md's rules hold: no module under `src/kb/` over 250 lines; rule 1; rule 3 (a database that cannot be read is one fault); when a task changes what a module owns or how the suite is run, it changes CLAUDE.md's rows and its "Working here" section.
- No migration; the store's form stays `store: 2`.
- An implementer may change an existing test's setup with no assertion changed where its task requires it; changing what any existing test asserts is a `BLOCKED` reply naming it.
- Last suite record before this batch: 1079 passed, 70 failed, 2 skipped; the failures are scenarios tagged `@slice-171` onward and `test_the_rule_names_kb_gives_are_exactly_the_spec_lists`; the two skips name slice 180.2.

### Execution rules

- **Paths in, short replies out.** The controller dispatches with paths and reads replies, `plan show` and `git log --oneline`.
- **By step.** A task with Steps is dispatched one step at a time; none here has Steps.
- **One review per `Review: per-task` task;** a `Review: batch-end` task is covered by the batch's branch review.
- **Fresh fixes.** Findings go to a fresh implementer as a fix round, then to a scoped re-review.
- **Lanes.** None here: the three tasks are small and run in order.

---

### Task 1: Slice 170.3. A store's database is made in one transaction

Review: per-task
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Check:** `make test` gives the same passed and failed tests as the record before it, faster; a plain test pins that making a store's database commits its schema once; stores, backups and restores made after the change open and answer as before.
- [ ] **Why it fails today:** the analysis measured one `kb.init` at 65 `fdatasync` calls (104 ms on disk, 6 ms in memory): the SQLite adapter makes its schema one statement per transaction (84.5 ms as written, 10.9 ms in one).
- [ ] **Where the change lands** (2 production, 1 test): `src/kb/sqlite_store.py` (making the database) and whichever adapter module holds a schema of its own that is made with it (`sqlite_types.py`, `sqlite_search.py`); one test module for the pin. `sqlite_backup.py` only if a restore's new database is made the same slow way.
- [ ] **Decisions:** durability is not weakened: the database still ends in WAL mode with the synchronous setting it has today, and a store start that fails partway leaves no database a later open would take for a store (`store.py` writes the marker last; that stays). Only the number of transactions the schema takes changes. No `PRAGMA synchronous` change, no in-memory database in tests.
- [ ] **Tests the decisions break:** none expected. A test that asserts on the database file's bytes, size or journal at a point inside the making is a `BLOCKED` reply naming it.
- [ ] **Verify:** the pin passes; `make test` fails no test that passed before; the report gives the sync count and the time of one store start before and after, and the suite's wall-clock before and after (three runs each).
- [ ] **Checkpoint:** `plan status 170.3 green`, then `plan log "Suite: ..."`.

### Task 2: Slice 170.4. The suite is green between slices

Review: batch-end
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Check:** `make test` gives 0 failed; every test whose scenario is tagged to a slice the living plan still holds as not green, and the rule-names test (slice 182), is reported as expected to fail; a regression fails as before.
- [ ] **Why it fails today:** about 70 tests fail by design (scenarios of slices 171 onward whose steps are not written, and the published contract's rule-names test, waiting on slice 182's rule `differs`); "no new failure" is checked by comparing lists of names.
- [ ] **Where the change lands** (0 production, 2 test): `tests/conftest.py` (or a small helper module beside it) marks, at collection, each test carrying a `slice-<n>` marker whose slice the living plan (`docs/superpowers/plans/2026-09-24-kb-slices.md`) lists with a Status other than `green`, as an expected failure with the reason "slice <n> not built"; a slice no longer in the living plan (archived, so green) is not marked. The rule-names test gets the same marking by an explicit marker naming slice 182. One test module tests the marking through pytest's own machinery (`pytester` or a subprocess run of a tiny tree): a planned slice's scenario is expected to fail; an archived slice's runs for real and its failure is a failure.
- [ ] **Decisions:**
  - Not strict: a scenario that passes before its slice is reported as unexpectedly passing (pytest's XPASS) in the summary, not as a failure, because an implementer building slice n must be able to run `-m slice-n` to green before the plan says green. The suite record's line carries the count.
  - The plan is read once per run, by its slice headings and Status lines only; if the plan file is missing or unreadable the suite fails loudly at collection (a suite silently treating everything as built would hide regressions).
  - The two skips for slice 180.2 become expected failures of that slice by the same marking, if their test carries the tag; otherwise they stay skips.
  - `make test`'s command and its parallelism are unchanged. CLAUDE.md's "Working here" says the suite is green and what an expected failure means; bdd-red-green's suite record for this repository becomes "N passed, M expected to fail, K unexpectedly passing, 0 failed".
- [ ] **Tests the decisions break:** none: no test's assertion changes; `tests/test_every_scenario_is_bound.py` must still fail for a scenario with no binding at all (an unbound scenario has no test to mark): say what it does today for the 171-onward scenarios and keep that.
- [ ] **Verify:** `make test` gives 0 failed with the expected-failure count equal to the failures of the record before it (70) and 0 unexpectedly passing; breaking one production line makes the suite fail; the marking's own tests pass.
- [ ] **Checkpoint:** `plan status 170.4 green`, then `plan log "Suite: ..."` in the new form.

### Task 3: Slice 170.5. A map of which tests execute which code

Review: batch-end
Model: sonnet
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.11.0/scripts

- [ ] **Check:** `make coverage-map` writes a per-test coverage database (not under version control) without changing `make test`; a second target or a small script answers "which tests execute this file, function or line" and "which lines of `src/kb` does no passing test execute".
- [ ] **Why it fails today:** no coverage tool is installed; "which tests does this decision break" and "is this behaviour held by any passing test" are answered by search.
- [ ] **Where the change lands** (0 production, 2 to 3 files): `pyproject.toml` (coverage, and pytest-cov if it is the simplest way to record per-test contexts, as development dependencies), `Makefile` (the targets), a small script under `tests/` or `scripts/` for the two questions, `.gitignore`; CLAUDE.md's "Working here" gains the two commands.
- [ ] **Decisions:** contexts are per test (`dynamic_context = test_function` or pytest-cov's `--cov-context=test`); the operator's commands run in-process, so they are covered without subprocess tracing; the one test that runs the installed `kb` and the tests that start another program (`at_once.InAnotherProgram`, `tests/serving.py`) may be left out of the map if tracing them costs more than a line of configuration: say which are. The map may run serially if xdist and contexts do not combine; its run time goes in the report and in CLAUDE.md.
- [ ] **Tests the decisions break:** none.
- [ ] **Verify:** `make coverage-map` completes; the script, asked for `src/kb/examining.py`, names tests of the import's check; asked for unexecuted lines, gives a list; `make test`'s time and result are as before.
- [ ] **Checkpoint:** `plan status 170.5 green`, then `plan log "Suite: ..."`.
