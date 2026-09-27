# kb Batch 16 Implementation Plan: slice 97, a set holding no changes is refused

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Each task is one slice of `docs/superpowers/plans/2026-09-24-kb-slices.md`. The one task here is a capability slice, written red-green against its scenario under shopsystem-bdd:bdd-red-green.

**This plan carries no code.** From 2026-09-27 the planner plans and the implementer writes the code in the execution session. The plan says what is red and why, where the change lands, which decisions are already made, what can be reused and how to verify it. It holds no code blocks, file contents, diffs or step-definition bodies. It was not built or replayed. Its counts come from `pytest --collect-only -q -m slice-N` and from runs of this checkout at `a9bdadf` (slice 97 cut and tagged, slice 96 still planned).

**Runs after batch 15.** Slice 97 stands on slice 96: the order of its faults beside a missing role or message (Decision 2) only means something once `values.signed` refuses those. Do not start this task until slice 96's checkpoint is logged green in the slice plan.

**Goal:** An Apply holding no operations is refused because a set must hold at least one change, with nothing written and nothing in the history, instead of breaking off with an error from git.

**Architecture:** kb is the Python package `kb` in this checkout. A protobuf contract (`kb.contract`) sits in front of `KbServicer` (`src/kb/servicer.py`). Each rpc runs inside one boundary that turns `values.Refused` into that rpc's faults. All five changing rpcs reach the domain through `servicer._land`, which today converts the operations (`requests.operations`, which never raises and keeps a failed operation as a `Refusal` in its place), then the signature (`values.signed`, which slice 96 makes refuse a missing role or message), then calls `write.land`. Create, Write, Append and Delete always hand `_land` a list of one operation; only Apply can hand it none.

**Tech Stack:** Python 3.11, protobuf + grpcio (no `.proto` change in this batch), ruamel.yaml 0.19 (YAML 1.2), git via subprocess, pytest 9 + pytest-bdd 8.

**Spec:** `docs/superpowers/specs/2026-09-23-kb-design.md`. The passages this plan argues from:
- The rpc table: "`Apply` | ordered list of Create/Write/Append/Delete, actor, message | batch id, minted by kb; per-operation results; one commit".
- "Errors are a typed list of `{ artifact, path, rule, message }`. Every mutating rpc returns all errors found, not the first."
- The write pipeline's step 6: "`git add` every written file by name, one commit, message from the request, author from the actor."

The scenario: `features/make-several-changes-in-one-go.feature`, "A set holding no changes at all is refused", tagged `@slice-97`.

The decisions are `adrs/0013-empty-set-refused.md`, `adrs/0014-signature-refused-before-operations.md` and `adrs/0016-empty-set-fault.md`. `CLAUDE.md` is binding.

## What happens today

The probe `.superpowers/probes/batch16-empty.py` (see Probe below) ran on 2026-09-27 at `a9bdadf`. Its output is kept as `.superpowers/probes/batch16-before.txt`:
- `empty set` (the client's role, a message): `raised CalledProcessError` from `git commit`; nothing uncommitted, HEAD unmoved, journal `4->4`.
- `empty set, no role` and `empty set, no message`: the same. Once slice 96 is green these answer the role's or the message's fault instead.
- `one unset operation` (an Apply of one `Operation` with nothing set): answers `('', '', 'locator', "... '' is not")`, nothing written. Out of this slice (Review Focus 2).

Why it raises: `write.land` drafts nothing, serialises nothing, and `write._written` saves no file and writes no journal entry, so it calls `store.commit` with no paths. `git add --` stages nothing and `git commit` exits 1 with nothing to commit. `subprocess.CalledProcessError` is not a `Refused`, so it escapes the boundary to the client. Unlike slice 96's case, nothing is left on disk; the defect is that the call breaks off instead of being refused.

The fix is to refuse the set before the domain sees it. That is CLAUDE.md's rule 2: an empty set is a request that does not convert. It is not a repair in `write.py` or `store.py` (for example, skipping the commit when there are no paths), which would answer an empty set with an empty success, against decision 0013.

## Global Constraints

- Feature files are read-only for the implementer. Any diff under `features/` is a stop condition. The `@slice-97` tag is already committed.
- Red-green, one scenario at a time, adding no behaviour that no scenario asks for. Nothing changes the answer to an Apply of one unset operation (Review Focus 2).
- CLAUDE.md's rules are each implemented once:
  - `grep -c "try:" src/kb/servicer.py` stays `1`.
  - `grep -nE "except (Exception|BaseException)|except:" src/kb/*.py` prints nothing.
  - The refusal text appears once in `src/kb/`: `grep -rc "a set must hold at least one change" src/kb/*.py | grep -v ":0"` gives `src/kb/requests.py:1`.
- Size: no module over 250 lines, and `servicer.py` under 150. Today `requests.py` is 177 and `servicer.py` 101.
- Tests use the contract, through `tests/calls.py`, or a module's public functions. They never use private helpers.
- `make test` runs `.venv/bin/python -m pytest -q`. While any scenario is red, its last line is make's own `Error 1`, so read pytest's summary line above it. The summary lines quoted below leave out `, N warnings in Xs`.
- The contract's version stays `0.1`, `pyproject.toml` stays `0.2.0`, and `kb.proto` is not touched (Decision 5).
- Work on `main` in this checkout. Commit with `git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit`, the message ending with the Co-Authored-By line of the model that made the commit.
- Counts. At `a9bdadf`: the suite gives `12 failed, 196 passed` (208 collected). The failures are slice 96's ten rows, slice 93's fourth row and this scenario. After batch 15, the expected baseline for this task is `1 failed, 207 passed`, the one failure being this scenario. `pytest --collect-only -q -m slice-97` gives `1/208 tests collected`.

## Decisions this plan makes

Each decision rests on a spec or plan passage, so the implementer does not have to choose.

1. **The fault.** One fault: rule `operations`, no artifact, no path, message "a set must hold at least one change", taken from the scenario's reason. The response carries no set name (`batch` empty) and no results. The rule names the request field (`ApplyRequest.operations`), as `root`, `since`, `title` and slice 96's `message` do. Recorded as `adrs/0016`.
2. **The signature comes first, and alone.** An empty set with no role or no message answers the role's and message's faults only, in decision 0014's order, and nothing about the set. This follows 0014 ("its operations are not checked") and slice 93. The spec's "all errors found, not the first" pulls the other way; this is the question the slice plan already logs for slice 96 (2026-09-27), and this slice does not add a new one. Recorded in `adrs/0016`.
3. **Where it lands: `requests.py`, converting a change request as a whole.** `requests.py` owns "each rpc's request as the values its one domain call takes ... refuses a request that does not convert". An empty set is a property of the whole request, not of one field, so it belongs in `requests.py`, not `values.py`. One conversion in `requests.py`, in the manner of `requests.starting`, takes a change's operations and its actor and message. It converts the signature first (`values.signed`), then refuses an empty set, then converts each operation as `requests.operations` does today. `servicer._land` makes that one call and hands what it returns to `write.land`. Do not put the emptiness check inside `requests.operations` and leave `_land` as it is: `_land` evaluates its arguments left to right, so the operations would be converted before the signature and an empty set with no role would answer `[operations]`, against Decision 2. The conversion's name is the implementer's; its docstring says the order.
4. **Nothing else in `src/kb/` changes.** `write.py`, `store.py`, `edits.py` and `values.py` are not touched. `git diff --stat src/kb` after the task shows `requests.py` and `servicer.py` alone. The check can never fire for Create, Write, Append or Delete, since each hands over one operation; it is shared, not special-cased per rpc.
5. **`kb.proto` is not touched.** `ApplyResponse`'s comment ("With faults, a refusal: every fault of every operation, and nothing was written") does not mention a whole-set fault, just as it does not mention slice 96's signature faults; batch 15 left the comments as they are (its Decision 6), and so does this batch.
6. **The steps.**
   - The When "the client asks, in one go, for a set holding no changes at all, saying which role and why" goes in `tests/test_make_several_changes_in_one_go.py`. It records what the shared Thens need from before the call (Decision 7), then sends `calls.apply` with an empty list, the client's role and a message, and returns the response and those before-values as the fixture `attempt`.
   - The Then "the set is rejected because a set must hold at least one change" goes in the same module and uses `_refused_with(attempt, [("", "", "operations")])`, which already asserts empty `batch` and no results. It asserts that the message returned starts with the reason. It is a plain string step, like the module's other three rejection Thens; its text does not collide with them.
7. **The two last Thens are shared with slice 96, not written twice.** Slice 96 adds "the store holds no artifact it did not hold before" and "the store's history holds no entry for it" to `tests/test_change_an_artifact.py`. Step definitions in a test module are visible only to that module in pytest-bdd 8, so this scenario cannot use them where they are. Move both into `tests/conftest.py`, which already holds shared steps ("the store that is there holds what it held before"), and have this module's When record the same before-values under the same keys of `attempt` that slice 96's When records. Read slice 96's steps first to learn those keys. Nothing in the steps' assertions changes. `tests/test_change_an_artifact.py` must stay green unchanged in behaviour: `-m slice-96` still gives `10 passed`. If a lifted body turns out to depend on something only change-an-artifact's Background holds, stop and write a HAND-BACK in the slice plan's log; do not write a second copy.

## Review Focus

Most likely to bite first. None of these gets code in this plan.

1. **Empty set with no role or no message.** Per Decision 2 it answers `[actor]` or `[message]` alone, nothing about the set. No scenario pins it. Reproduction: `.superpowers/probes/batch16-empty.py`, lines `empty set, no role` and `empty set, no message`. At `a9bdadf` both raise `CalledProcessError`; after batch 15 they answer the signature's fault; after this task, unchanged from batch 15. If either answers `operations`, the conversion order in Decision 3 is wrong.
2. **A set of one operation with nothing set.** Today it is read as a Write with no locator and refused as a `locator` fault naming `''`. It is not empty, so this task leaves it alone. Logged as a QUESTION FOR THE SPEC in the slice plan (2026-09-27). Reproduction: the same probe, line `one unset operation`. Expected after this task: unchanged.
3. **The other changing rpcs.** Create, Write, Append and Delete go through the same conversion with one operation, so they must not change. The full suite covers them; the probe's `batch15-*` scripts from batch 15 can be rerun to show no difference.
4. **Git failures other than an empty commit.** The spec's step 6 restore is still unbuilt, and a role or message of spaces still reaches git and fails (slice plan's question of 2026-09-27). This task does not touch `store.commit`; do not add a guard there.
5. **A set's name.** The refused response has `batch` empty. Nothing mints a set name for an empty set and nothing is journalled, so `journal(client, batch=...)` has nothing to find.

---

### Task 1: Slice 97, a set holding no changes is refused

**Slice plan entry:** slice 97, capability.
- Scenario: kb / make-several-changes-in-one-go / A set holding no changes at all is refused (`@slice-97`).
- Observable: a client that asks, in one go, for a set holding no changes is refused because a set must hold at least one change, and the store, its files and its history are as they were, where today the call breaks off with an error from git.
- Unknown it settles: whether a set can be refused for being empty as a request that does not convert, before the domain sees it, while a set with no role or no message still answers those faults alone. Expected answer: yes, with the one conversion in Decision 3.

**Why the scenario is red today** (run at `a9bdadf`):
- It stops at `StepDefinitionNotFoundError` on its When: nothing matches "the client asks, in one go, for a set holding no changes at all, saying which role and why".
- Behind the step, the Apply raises `subprocess.CalledProcessError` from `store.commit` ("What happens today"). So once the steps exist it stays red at its When with that error until `requests.py` refuses the set.
- The two Thens it shares with slice 96 are in `tests/test_change_an_artifact.py` and not visible to this module (Decision 7), so they would also fail as not found until they are moved.

**Where it lands (CLAUDE.md's module map):**
- `src/kb/requests.py`: the conversion of a change request (Decision 3). This implements rule 2 once for a whole request: an empty set is refused before the domain sees it. Rule 4 follows, since `write.land` is never called. Rule 1 needs nothing new: `values.Refused` raised in `requests.py` already becomes the Apply response's faults at the boundary.
- `src/kb/servicer.py`: `_land` makes that one call instead of its two conversions. Nothing else changes there.
- Test side:
  - `tests/test_make_several_changes_in_one_go.py`: the new When and the rejection Then.
  - `tests/conftest.py`: the two Thens moved from `tests/test_change_an_artifact.py`.
  - `tests/test_change_an_artifact.py`: those two Thens removed.

**Reuse:**
- `tests/test_make_several_changes_in_one_go.py`:
  - Background Given "a store holding a decision type and a work item" (`_store_with_a_decision_type_and_a_work_item`).
  - `_refused_with(attempt, faults)`, which asserts `batch` empty, no results, and the faults' artifact, path and rule, and returns the first message.
  - `_everything_under(directory)` and `_journal(root)`, if the shared Thens' before-values need them; otherwise `calls.everything_under` and `calls.journal`.
- `tests/calls.py`: `CLIENT`, `apply` (with the `actor` parameter slice 96 adds; default the client's role), `journal`, `listing`, `everything_under`.
- `tests/conftest.py`: the `root` fixture.
- From slice 96, moved as they are: "the store holds no artifact it did not hold before" and "the store's history holds no entry for it".

**Probe** (throwaway, run from the checkout root, kept outside git under `.superpowers/`):
- `.venv/bin/python .superpowers/probes/batch16-empty.py` starts a fresh store in a temporary directory for each line, holding the decision and work-item types and one work item. It sends an Apply and prints the outcome (faults as artifact, path, rule and message, the set name and the number of results, or the exception), `git status --porcelain` of the store, whether HEAD moved, and the journal count before -> after.
- Its output at `a9bdadf` is `.superpowers/probes/batch16-before.txt`.

- [ ] **Step 1: Confirm the baseline** (after batch 15).
  - The slice plan shows slice 96 `green`.
  - `.venv/bin/python -m pytest -q` gives `1 failed, 207 passed`. The failure is `tests/test_make_several_changes_in_one_go.py::test_a_set_holding_no_changes_at_all_is_refused`.
  - `.venv/bin/python -m pytest --collect-only -q -m slice-97` gives `1/208 tests collected`.
  - `.venv/bin/python -m pytest -q -m slice-97` gives `1 failed`, at `StepDefinitionNotFoundError` on the When.
  - `.venv/bin/python -m pytest -q -m slice-96` gives `10 passed`.
  - Rerun the probe and save it as `.superpowers/probes/batch16-after-96.txt`. Expected: `empty set` still raises `CalledProcessError`; `empty set, no role` answers `[('', '', 'actor', 'every entry in the history names the role that made it')]`; `empty set, no message` answers `[('', '', 'message', 'every entry in the history says why it was made')]`; `one unset operation` unchanged. If `empty set` does anything other than raise, stop: batch 15 went beyond its plan, and this plan's red reason no longer holds.
- [ ] **Step 2: Move the two shared Thens** into `tests/conftest.py` (Decision 7). `.venv/bin/python -m pytest -q tests/test_change_an_artifact.py -m slice-96` gives `10 passed`, and the suite is still `1 failed, 207 passed`.
- [ ] **Step 3: Write the When and the rejection Then** (Decision 6).
- [ ] **Step 4: See it red for the right reason.** `.venv/bin/python -m pytest -q -m slice-97` gives `1 failed`, failing in its When with `subprocess.CalledProcessError` (git with nothing to commit), not `StepDefinitionNotFoundError`. The suite gives `1 failed, 207 passed`.
- [ ] **Step 5: Make it green** in `requests.py` and `servicer._land` (Decisions 1 to 4).
  - `.venv/bin/python -m pytest -q -m slice-97` gives `1 passed`.
  - `.venv/bin/python -m pytest -q tests/test_make_several_changes_in_one_go.py` gives `8 passed`.
- [ ] **Step 6: The whole suite and the structural checks.**
  - `.venv/bin/python -m pytest -q` gives `208 passed`.
  - `git diff --stat src/kb` lists `src/kb/requests.py` and `src/kb/servicer.py` only.
  - `wc -l src/kb/requests.py src/kb/servicer.py`: 250 or fewer, and under 150.
  - `grep -c "try:" src/kb/servicer.py` gives `1`.
  - `grep -nE "except (Exception|BaseException)|except:" src/kb/*.py` prints nothing.
  - The refusal text appears once, in `requests.py` (Global Constraints).
  - `git diff --stat features` prints nothing.
- [ ] **Step 7: Probe after.** Rerun the probe and diff against `batch16-after-96.txt`. Expected, and only this line changed: `empty set: answered faults=[('', '', 'operations', 'a set must hold at least one change')] batch='' results=0; uncommitted=[]; head moved=False; journal 4->4`. `empty set, no role`, `empty set, no message` and `one unset operation` are unchanged (Review Focus 1 and 2).
- [ ] **Step 8: Log the checkpoint and commit.** In `docs/superpowers/plans/2026-09-24-kb-slices.md`, set slice 97's Status to `green` and append, dated:
  - a `slice 97 green` entry in the shape of slice 89.2's: what someone can now rely on; "Surprised by"; "Red and green" with the counts above; the probe lines before and after; the greps and the line counts of `requests.py` and `servicer.py`; "Open questions", naming the QUESTION FOR THE SPEC on an unset operation logged on 2026-09-27;
  - `batch 16 checkpoint: slice 97 green; suite 208 passed; every slice in the plan is green, leaving the questions for the spec`.

  Commit the tests, `src/kb/requests.py`, `src/kb/servicer.py` and the slice plan together.
