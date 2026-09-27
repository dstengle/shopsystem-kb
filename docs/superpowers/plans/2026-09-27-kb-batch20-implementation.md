# kb Batch 20 Implementation Plan: slices 100.2 to 100.5, 101 and 102, the published surface for a release

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Each task is one slice of `docs/superpowers/plans/2026-09-24-kb-slices.md`, in slice order. Tasks 1 to 5 are enabling slices, each verified by its check. Task 6 is a capability slice, written red-green under shopsystem-bdd:bdd-red-green.

**This plan carries no code** (shopsystem-knowledge adrs/0011). For each task it says:
- what fails and why;
- where the change lands;
- what is already decided;
- how to verify it.

**Goal:** make kb's published surface (adrs/0018) true and pinned before the release shop-knowledge waits for:
- the rule names, written once, listed and pinned (100.2);
- the contract versioned by the release tag (100.3);
- `kb.content` holding only what is published (100.4);
- a relative-root `Init` from a removed directory refused (100.5);
- no test reaching a store outside its temporary directory (101);
- a clock a client's own tests may give the in-process client (102).

After this batch comes the release, which is the user's decision.

**Spec:** `docs/superpowers/specs/2026-09-23-kb-design.md`, as amended in 7b35ef2, 00710a6, 2b03edd and ae3ed33. The passages that matter here:
- the contract section's "What a client may depend on ...", its rule-name sentence and "The contract is versioned by kb's release tag; clients pin the tag";
- "Finding the store";
- "Transports", with its clock sentence;
- Testing's "No test reaches a store outside its own temporary directory".

The decisions are adrs/0008 and 0018. `CLAUDE.md` is binding. The seventh architecture review's report, `.superpowers/batch20/arch-review-100.1.md` (scratch, outside git), gives R3, R4 and R5 in detail; this plan repeats what each task needs.

## Global Constraints

- **Features and contract.** No feature file changes except Task 6's steps, and its feature lines are read-only. `kb.proto` changes only in Task 2's header comment.
- **Rules.** Every rule in CLAUDE.md holds. `src/kb/` modules stay under 250 lines, and `servicer.py` under 150. Only the servicer's wrapper catches broad exceptions (rule 1).
- **The baseline.** The suite gives `227 passed, 7 failed` today (run at `ae3ed33`). The 7 failures are slice 102's rows.
  - `.venv/bin/python -m pytest -q -rf | grep ^FAILED | sort > .superpowers/batch20/failing-before.txt` records them.
  - Tasks 1 to 5 each leave that list unchanged.
  - After Task 6 the suite gives every scenario passing: `234 passed`, or the count with the tests Tasks 1 and 4 add.
- **Commits.** Commit with `git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit`, ending the message with the model's Co-Authored-By line. Make one commit per task, holding its change and its checkpoint in the slice plan's log, with its status set to green. The implementer never pushes or tags.
- **Scratch.** Probes go under `.superpowers/batch20/`, never `/tmp`.
- **The client.** shop-knowledge pins kb by tag and today uses these names, which must keep working until its slice 50.23 moves off the last two:
  - `kb.client.connect()` and `connect(root)`;
  - `kb.content.loads`, `dumps` and `text`;
  - `kb.canonical.NotCanonical`;
  - `kb.journal.now`, which it replaces from its tests.

## Review Focus

1. **A client's `connect()` calls unchanged** (owner: Task 6). `connect()`, `connect(root)` and a clock left out all behave as today. `kb.journal.now` replaced from outside still stamps every entry when no clock is given. Probe: replace it in a process, make a change, read the journal. Log it.
2. **The rule set against the scenarios** (owner: Task 1). Every rule name a kb scenario's Then asserts is in the pinned set. List any that are not.
3. **The guard never trips on kb's own suite** (owner: Task 5). The guard's check that no store is found from the checkout does not trip on the `kb/` package directory in `src/`, which is not a store. Log it.

---

### Task 1: Slice 100.2, every rule name kb gives is written once, listed in the spec, and pinned

**Check:**
- `grep -nE 'rule="' src/kb/*.py | grep -v '^src/kb/rules.py'` gives none. There are 36 such lines in six modules today: `refusals.py` 15, `store.py` 9, `values.py` 8, `validation.py` 2, `requests.py` 1 and `cli.py` 1.
- The table-built rules are named from the one module too: `values.py`'s `_unsigned` rows (`actor`, `message`) and the content problems' tuples.
- JSON Schema's validator keyword (`validation.py`, `rule=error.validator`) passes through unchanged.
- The spec's contract section lists the set.
- `tests/test_the_published_contract.py` pins the set.
- The failing list is unchanged.

**Where it lands:**
- A new module under `src/kb/` holds the name of every rule a fault of kb's own carries (the review suggests `rules.py`). It gets a CLAUDE.md module-map row: "the name of every rule a fault of kb's own carries, which kb publishes (adrs/0018)"; never holds: faults, messages. Every fault builder uses its names.
- The spec's contract section gains the list, after the sentence "A fault's `rule` is one of kb's own rule names, which this spec lists, ...". List the names in the same order as the module.
- The surface test asserts that the module's set equals the set the spec lists. Reading the spec file from the test is acceptable, since it is kb's own document. It also asserts that at least one scenario's JSON Schema rule is a keyword and not in the set.

**Decided:** `rules.py` is internal. The published list is the spec's. The test keeps the spec and the code together.

- [ ] Record the failing list.
- [ ] Add the module and move every literal to it.
- [ ] Add the spec list and the surface test.
- [ ] Run the check and Review Focus 2.
- [ ] Write the checkpoint and commit.

### Task 2: Slice 100.3, the contract says it is versioned by kb's release tag

**Check:**
- `grep -n "Clients pin\|version 0.1" src/kb/contract/kb.proto src/kb/contract/__init__.py` gives none; there are 2 matches today.
- `make contract`, then `git diff --stat src/kb/contract`, shows `kb.proto` and nothing generated. A comment changes no descriptor.
- `CONTRACT_VERSION` stays as the store marker's value, and its docstring says so, not that clients pin it.
- The failing list is unchanged.

- [ ] Make the change.
- [ ] Run the check.
- [ ] Write the checkpoint and commit.

### Task 3: Slice 100.4, kb.content holds only what kb publishes

**Check:**
- `.venv/bin/python -c "import kb.content as c; assert sorted(c.__all__) == ['NotCanonical', 'dumps', 'loads', 'text']; assert not hasattr(c, 'entries')"` exits 0.
- The published-contract test asserts `__all__`.
- `grep -rn "content import.*entries\|content\.entries" src tests` gives none.
- The failing list is unchanged.

**Where it lands:** `values.content` reads a whole artifact's text through `canonical.entries`, which it already imports. shop-knowledge imports no `entries`.

- [ ] Make the change.
- [ ] Run the check.
- [ ] Write the checkpoint and commit.

### Task 4: Slice 100.5, starting a store at a relative root from a removed working directory is refused, never raised

**Check:**
- A probe from a removed working directory, `Init` with root `.` through `kb.client.connect()`, answers with a `root` fault saying the working directory is gone. Today `FileNotFoundError` escapes from `store.vacant`'s `root.path.resolve()`.
- Root `sub` still gives today's refusal.
- CLAUDE.md's `store.py` row says discovery reads the process's working directory and `KB_ROOT`.
- The failing list is unchanged.
- The probe is kept as a test of the module's public function, or through the client, as CLAUDE.md allows.

**Where it lands:** `store.py`, where a root is resolved. It uses the same narrow reading of the working directory that slice 99 added (`store.working_directory()`), not a second catch.

- [ ] Show the traceback with the probe and log it.
- [ ] Make the change.
- [ ] Run the probe and the check.
- [ ] Write the checkpoint and commit.

### Task 5: Slice 101, no test reaches a store outside its own temporary directory

**Check:**
- The failing list is unchanged.
- A throwaway `kb/store.yaml` made in the checkout's parent directory makes the suite refuse to start, saying why. Log it, then remove it.
- Every test starts in a working directory under its temporary directory.

**Where it lands:** `tests/conftest.py`.
- A session-start guard refuses to run when a store can be found from the checkout or from the system's temporary directory, looking upward as discovery does. It uses `store.find_above`, a public function; kb's tests may use kb's own public functions.
- An autouse fixture moves every test into a directory under its `tmp_path`, restored after, and clears `KB_ROOT` unless the test sets it. The existing store-finding Givens move the working directory themselves, and keep working because they `chdir` after the fixture.

- [ ] Add the guard and show it tripping, then remove the throwaway store.
- [ ] Add the fixture.
- [ ] Run Review Focus 3.
- [ ] Write the checkpoint and commit.

### Task 6: Slice 102, a client may be given a clock its changes are stamped with

**Scenarios (`@slice-102`, 7 rows):**
- `start-a-store` / Starting a store is stamped with the moment the client's clock gives;
- `read-the-journal` / A client given a clock stamps each change it makes with the moment the clock gives, all six rows: creates, changes, adds an item, removes, several in one go, and snapshots.

**Unknown:** whether the moment can reach every place the journal stamps an entry from the client alone, through the servicer, without a module-level clock.

**Why red:** all 7 rows fail on `StepDefinitionNotFoundError`. The Givens "the client was readied with a clock that reads ..." are missing, and so are the Thens "the store's one history entry says it happened at ..." and "every entry that change left in the journal says it happened at ...".

**Where it lands:**
- `kb.client.connect(root=None, clock=None)` takes the clock as a keyword with a default: a callable returning an aware `datetime`.
- `InProcessClient` hands it to the servicer it builds for each call, and to `Init`'s.
- The servicer hands it to the write pipeline, and the write pipeline to `journal.write` and `journal.snapshot`, which read it at each stamp.
- With no clock given, the journal reads `journal.now`, looked up when each entry is stamped, so a replacement made from outside still takes effect. It stays until shop-knowledge's slice 50.23 lands with the pin bump (slice 102's Needs).
- Each module passes the clock on without knowing what it is: `client.py` holds no domain logic, and `servicer.py` stays under 150 lines.

**Steps:**
- The Givens go in `tests/test_read_the_journal.py` and `tests/test_start_a_store.py`, beside their features' steps.
- The existing `today is` step may keep its way of setting the day, or move to the published clock. If it moves, all of `read-the-journal`'s scenarios stay green.

**Decided:**
- The clock is read at each stamp.
- A snapshot is stamped by it.
- An earlier stamp is accepted as given.

These are all from the slice plan's 2026-09-27 log.

- [ ] Take each row red then green under bdd-red-green, `Init`'s first.
- [ ] Run Review Focus 1.
- [ ] Confirm the suite gives every scenario passing.
- [ ] Write the checkpoint and commit.

## After the batch

- [ ] A whole-branch review on the most capable model, over this batch's commits, against this plan, CLAUDE.md, the spec and adrs/0018. The reviewer runs the suite, and shop-knowledge's suite with `PYTHONPATH` pointed at this checkout's `src`, which must give the same answer as against the pinned tag.
- [ ] Push `main`.
- [ ] Then the release: bump `pyproject.toml`, tag and push the tag, which is the user's decision (shopsystem-knowledge adrs/0006).
