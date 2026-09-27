# kb Batch 17 Implementation Plan: slice 98, a role or a reason of only blank space counts as none

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Each task is one slice of `docs/superpowers/plans/2026-09-24-kb-slices.md`. The one task here is a capability slice, written red-green against its scenarios under shopsystem-bdd:bdd-red-green.

**This plan carries no code.** From 2026-09-27 the planner plans and the implementer writes the code in the execution session. The plan says what is red and why, where the change lands, which decisions are already made, what can be reused and how to verify it. It holds no code blocks, file contents, diffs or step-definition bodies. It was not built or replayed. Its counts come from `pytest --collect-only -q -m ...` and from runs of this checkout at `85a64f3` (the twelve rows added, slice 98 not yet cut).

**Goal:** A Create, Write, Append, Delete, Apply or Snapshot under a role, or with a message, of blank space alone is refused exactly as one with none is, with nothing written and nothing in the history, instead of breaking off with an error from git and leaving the change on disk.

**Architecture:** kb is the Python package `kb` in this checkout. A protobuf contract (`kb.contract`) sits in front of `KbServicer` (`src/kb/servicer.py`). Each rpc runs inside one boundary that turns `values.Refused` into that rpc's faults. Every changing rpc converts its role and message once, before anything is drafted: Create, Write, Append, Delete and Apply through `requests.change`, which calls `values.signed`; Snapshot through `values.reader`. Both build their faults in `values._unsigned`, which today counts a role or a message as missing only when it is empty.

**Tech Stack:** Python 3.11, protobuf + grpcio (no `.proto` change), ruamel.yaml 0.19 (YAML 1.2), git via subprocess, pytest 9 + pytest-bdd 8.

**Spec:** `docs/superpowers/specs/2026-09-23-kb-design.md`. The passages this plan argues from:
- The bet "every-change-is-attributable. Actor, execution, message, and a fingerprint per operation are what history needs."
- The write pipeline's step 6: "`git add` every written file by name, one commit, message from the request, author from the actor."
- The rpc table's rows for Create, Write, Append, Delete and Apply, each taking "actor, message".

The scenarios: the rows of `features/change-an-artifact.feature`'s outline "A change that does not say which role made it, or why, is refused" (`@slice-96`) whose saying is "saying why but giving a role that is only blank space" or "saying which role it is but giving as its reason only blank space" (ten rows), and the rows of `features/snapshot-what-a-piece-of-work-read.feature`'s outline "Every way a snapshot can be asked for wrongly is refused" (`@slice-93`) "the decision and the process giving a role that is only blank space" and "the decision and the process giving as its reason only blank space" (two rows). They keep their outlines' tags; slice 98 is run with `-m "slice-96 or slice-93"`.

The decisions are `adrs/0012-writes-need-role-and-message.md`, `adrs/0014-signature-refused-before-operations.md`, `adrs/0015-missing-message-rule.md` and `adrs/0017-blank-role-or-message.md`. `CLAUDE.md` is binding.

## What happens today

The probe `.superpowers/probes/batch17-blank.py` (see Probe below) ran on 2026-09-27 at `85a64f3`. Its output is kept as `.superpowers/probes/batch17-before.txt`:
- `snapshot, role of spaces` and `snapshot, message of spaces`: `raised CalledProcessError`; a journal entry left staged and uncommitted, journal `3->4`.
- `write, role of a tab and a newline`: `raised CalledProcessError`; the decision's file modified and a journal entry added, both uncommitted; a Read answers revision 2.
- `write, message of a no-break space`: answered no faults and committed, the commit message a no-break space.
- `write, padded role and message` (`" agent "`, `"  Say why  "`): answered no faults and committed.
- `snapshot, work of spaces`: answered no faults and recorded the snapshot (Review Focus 3).
- `init, role '  '`: `raised CalledProcessError`, the store's directory left behind (Review Focus 2).

The earlier probe `.superpowers/probes/batch15-edges.py`, rerun at `85a64f3`, gives the same for `write, role of spaces` and `write, message of spaces`.

Why it raises: `values._unsigned` tests `not request.role` and `not message`, so a string of spaces passes. The change is drafted, validated, written and journalled. Then git strips the author name and the commit message of blank space, finds nothing, and `git commit` exits non-zero. `subprocess.CalledProcessError` is not a `Refused`, so it escapes the boundary with the files already on disk (the spec's restore on git failure is unbuilt). A no-break space is not stripped by git, so it commits.

The fix is to count blank space alone as nothing where the role and message are converted, once, in `values._unsigned`. That is CLAUDE.md's rule 2: a request field becomes a checked value before anything else sees it. It is not a guard in `store.commit` or `write.py`.

## Global Constraints

- Feature files are read-only for the implementer. Any diff under `features/` is a stop condition. The rows are already tagged.
- Red-green, one row at a time where the steps allow, adding no behaviour that no scenario asks for. Nothing changes the answer to Init or to a snapshot's piece of work (Review Focus 2 and 3).
- CLAUDE.md's rules are each implemented once:
  - `grep -c "try:" src/kb/servicer.py` stays `1`.
  - `grep -nE "except (Exception|BaseException)|except:" src/kb/*.py` prints nothing.
  - Each refusal text appears once in `src/kb/`: `grep -rc "names the role that made it" src/kb/*.py | grep -v ":0"` and `grep -rc "says why it was made" src/kb/*.py | grep -v ":0"` each give one file, with count `1`.
- Size: no module over 250 lines, and `servicer.py` under 150. Today `values.py` is 249 lines and `servicer.py` 101. See Decision 3 for what happens if `values.py` would pass 250.
- Tests use the contract, through `tests/calls.py`, or a module's public functions. They never use private helpers.
- `make test` runs `.venv/bin/python -m pytest -q`. While any scenario is red, its last line is make's own `Error 1`, so read pytest's summary line above it. The summary lines quoted below leave out `, N warnings in Xs`.
- The contract's version stays `0.1`, `pyproject.toml` stays as it is, and `kb.proto` is not touched.
- Work on `main` in this checkout. Commit with `git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit`, the message ending with the Co-Authored-By line of the model that made the commit.
- Counts, from `pytest --collect-only -q`:
  - The suite: `220 tests collected`. At `85a64f3` it gives `12 failed, 208 passed`, the twelve being slice 98's rows.
  - `-m slice-96`: `20/220`; at `85a64f3` `10 failed, 10 passed`.
  - `-m slice-93`: `6/220`; at `85a64f3` `2 failed, 4 passed`.
  - `-m "slice-96 or slice-93"`: `26/220`; at `85a64f3` `12 failed, 14 passed`.

## Decisions this plan makes

Each decision rests on a spec or plan passage, so the implementer does not have to choose.

1. **What blank space is.** A role or a message counts as none when nothing is left once blank space is taken from both ends, blank space being every character `str.isspace` counts: spaces, tabs, line breaks, a no-break space. Rests on the rows' words "only blank space" and on "every-change-is-attributable": a role or reason a reader of the history cannot see says nothing. Git's own stripping is narrower (it keeps a no-break space) and is not the measure. Recorded as `adrs/0017`.
2. **A role or message with text is kept exactly as given.** `" agent "` and `"  Say why  "` are taken as they are and are not trimmed before they reach the journal or the commit. No scenario asks for trimming, and the spec says "message from the request, author from the actor". Recorded in `adrs/0017`. (Git will still trim them in the commit itself, as it does today.)
3. **Where it lands: `values._unsigned`, once.** `values.py` owns "conversion of single request fields into validated values", and `_unsigned` is the one place both `values.signed` (every write) and `values.reader` (a snapshot) build the role's and the message's faults. Change only its two tests of missing-ness; the faults, their rules (`actor`, `message`), their messages and their order (decision 0014: role first, then message, then a snapshot's piece of work) stay as they are. `values.starter` (Init) and the piece-of-work check in `values.reader` are not touched (Review Focus 2, 3). The change is expected to leave `values.py` at 249 lines. **If it would take `values.py` past 250 lines**, the task first splits the signature conversions (`Actor`, `Signed`, `actor`, `_unsigned`, `signed`, `reader`, `starter`) into a module of their own as an enabling step, as the last architecture review suggested: the suite green at `12 failed, 208 passed` with no behaviour changed, the new module added to CLAUDE.md's module map (owns: who makes a change and why; never holds: anything else), the callers in `requests.py` and `servicer.py` repointed, and committed on its own before the rule is made. It then makes the rule there.
4. **Nothing else in `src/kb/` changes.** `write.py`, `store.py`, `requests.py` and `servicer.py` are not touched (unless Decision 3's split applies). `git diff --stat src/kb` after the task shows `values.py` alone.
5. **The steps extend two tables; no new step is written.**
   - In `tests/test_change_an_artifact.py`, the When "the client {call}, {saying}" (`_change_unsigned`) picks its actor and message from the table `SAYING`. Add its two new sayings: "saying why but giving a role that is only blank space" (an actor whose role is blank space, with a message) and "saying which role it is but giving as its reason only blank space" (`CLIENT`, with a message of blank space). The regex is built from the table's keys, so the When matches once they are there.
   - In `tests/test_snapshot_what_a_piece_of_work_read.py`, the When "the client snapshots {request}" (`_snapshot_wrongly`) picks from the table `WRONGLY`. Add its two new requests, each with `EXECUTION`, the decision and the process: one with a role of blank space and `SAID`, one with the role `"agent"` and a message of blank space.
   - The blank space the tables send is a space, a tab and a space (`" \t "`), for both role and message, so the rows pin more than the space git strips; one constant in each module, named once.
   - The Thens are unchanged: `_rejected_for_its_signature` and `_snapshot_rejected` already key on the reason, and the shared Thens in `tests/conftest.py` ("the store holds no artifact it did not hold before", "the store's history holds no entry for it") and "reading the decision gives what it held before, at the version it held before" already read the before-values `_change_unsigned` records.

## Review Focus

Most likely to bite first. None of these gets code in this plan.

1. **A role or message with text around blank space.** Per Decision 2, `" agent "` and `"  Say why  "` still commit, unchanged. Reproduction: `.superpowers/probes/batch17-blank.py`, line `write, padded role and message`. Expected after this task: unchanged from before. If it answers a fault, the check is testing more than "nothing left".
2. **Init under a role of blank space.** Raises `CalledProcessError` today and leaves the store's directory behind. Logged as a QUESTION FOR THE SPEC in the slice plan (2026-09-27). Reproduction: the same probe, line `init, role '  '`. Expected after this task: unchanged; do not touch `values.starter`.
3. **A snapshot for a piece of work of blank space.** Recorded today. Logged as a QUESTION FOR THE SPEC (2026-09-27). Reproduction: the same probe, line `snapshot, work of spaces`. Expected after this task: unchanged.
4. **A no-break space.** Git commits it today; after this task it is refused with rule `message` (Decision 1). Reproduction: the same probe, line `write, message of a no-break space`. This is the one line where Decision 1 differs from git's own stripping.
5. **Faults beside the signature.** A write with bad content under a blank role answers the role's fault alone, as decision 0014 orders for an empty one (slice plan's question of 2026-09-27 on reporting every fault). Reproduction: `.superpowers/probes/batch15-edges.py`, line `write, bad content, no role`, run with the role changed to blank space if checked by hand. Expected: `[actor]`.

---

### Task 1: Slice 98, a role or a reason of only blank space counts as none

**Slice plan entry:** slice 98, capability.
- Scenarios: the ten new rows of kb / change-an-artifact / A change that does not say which role made it, or why, is refused; the two new rows of kb / snapshot-what-a-piece-of-work-read / Every way a snapshot can be asked for wrongly is refused.
- Observable: a client that creates, replaces, adds an item to, removes, asks in one go for several changes to, or snapshots an artifact under a role, or with a reason, that is only blank space is refused with the same reason as when it gives none, and the store, its files and its history hold nothing of it, where today the call breaks off with an error from git and leaves the change on disk.
- Unknown it settles: whether the one conversion of a change's role and message, counting blank space alone as nothing, refuses every call that changes the store without passing the size limit of the module that holds it. Expected answer: yes, in `values._unsigned`, with `values.py` staying at 249 lines.

**Why the rows are red today** (run at `85a64f3`):
- All twelve stop at `StepDefinitionNotFoundError` on their When: the new sayings are not keys of `SAYING`, and the new requests are not keys of `WRONGLY`, so no regex matches.
- Behind the steps, each call raises `subprocess.CalledProcessError` from `store.commit` (What happens today), so once the table entries exist they stay red in their When with that error until `values._unsigned` counts blank space as none.

**Where it lands (CLAUDE.md's module map):**
- `src/kb/values.py`: `_unsigned` (Decision 3). This implements rule 2 once for every call that changes the store: a blank role or message is refused before anything is drafted. Rule 4 follows, since `write.land` is never reached. Rule 1 needs nothing new: `values.Refused` already becomes each rpc's faults at the boundary.
- Test side: the two tables in `tests/test_change_an_artifact.py` and `tests/test_snapshot_what_a_piece_of_work_read.py` (Decision 5).

**Reuse:**
- `tests/test_change_an_artifact.py`: the Given "the decision carries two options", the When `_change_unsigned` with its tables `UNSIGNED` and `SAYING`, the Then `_rejected_for_its_signature` with `UNSIGNED_REASONS`, the constants `ANOTHER`, `SECTIONS`, `DECISION`.
- `tests/test_snapshot_what_a_piece_of_work_read.py`: the Background Given, the When `_snapshot_wrongly` with `WRONGLY`, the Then `_snapshot_rejected` with `REASONS`, "the journal holds no entry for it" (`_no_entry_for_it`), the constants `EXECUTION`, `DECISION`, `PROCESS`, `SAID`.
- `tests/conftest.py`: "the store holds no artifact it did not hold before", "the store's history holds no entry for it".
- `tests/calls.py`: `CLIENT`, `snapshot`, `write`, `append`, `remove`, `apply`, `request`.

**Probe** (throwaway, run from the checkout root, kept outside git under `.superpowers/`):
- `.venv/bin/python .superpowers/probes/batch17-blank.py` starts a fresh store in a temporary directory for each line, holding the decision type and one decision, sends one call, and prints the faults (rule and message) or the exception, `git status --porcelain` of the store, the journal count before -> after, and the last commit's author and message. Its last line starts a store under a role of spaces.
- Its output at `85a64f3` is `.superpowers/probes/batch17-before.txt`.

- [ ] **Step 1: Confirm the baseline.**
  - `.venv/bin/python -m pytest -q` gives `12 failed, 208 passed`, the twelve being slice 98's rows.
  - `.venv/bin/python -m pytest --collect-only -q -m "slice-96 or slice-93"` gives `26/220 tests collected`.
  - `.venv/bin/python -m pytest -q -m "slice-96 or slice-93"` gives `12 failed, 14 passed`, each failure at `StepDefinitionNotFoundError`.
  - `wc -l src/kb/values.py` gives `249`.
- [ ] **Step 2: Add the two sayings to `SAYING`** (Decision 5). `-m slice-96` gives `10 failed, 10 passed`, each failure now `subprocess.CalledProcessError` in the When, not `StepDefinitionNotFoundError`.
- [ ] **Step 3: Add the two requests to `WRONGLY`** (Decision 5). `-m slice-93` gives `2 failed, 4 passed`, each failure `subprocess.CalledProcessError` in the When.
- [ ] **Step 4: Make it green** in `values._unsigned` (Decisions 1 to 4). First check whether the change leaves `values.py` at 250 lines or fewer; if not, do Decision 3's split first, as its own commit, the suite at `12 failed, 208 passed` before and after it.
  - `.venv/bin/python -m pytest -q -m "slice-96 or slice-93"` gives `26 passed`.
- [ ] **Step 5: The whole suite and the structural checks.**
  - `.venv/bin/python -m pytest -q` gives `220 passed`.
  - `git diff --stat src/kb` lists `src/kb/values.py` only (or, after a split, only the split's files).
  - `wc -l src/kb/values.py src/kb/servicer.py`: 250 or fewer, and under 150.
  - `grep -c "try:" src/kb/servicer.py` gives `1`.
  - `grep -nE "except (Exception|BaseException)|except:" src/kb/*.py` prints nothing.
  - Each refusal text appears once (Global Constraints).
  - `git diff --stat features` prints nothing.
- [ ] **Step 6: Probe after.** Rerun the probe, save it as `.superpowers/probes/batch17-after.txt`, and diff against `batch17-before.txt`. Expected changed lines, each with `uncommitted=[]` and the journal `3->3`: `snapshot, role of spaces` and `write, role of a tab and a newline` answer `[('actor', 'every entry in the history names the role that made it')]`; `snapshot, message of spaces` and `write, message of a no-break space` answer `[('message', 'every entry in the history says why it was made')]`. Unchanged: `snapshot, work of spaces`, `write, padded role and message` and `init, role '  '` (Review Focus 1 to 3). Only the timestamps in journal file names differ on the unchanged lines.
- [ ] **Step 7: Log the checkpoint and commit.** In `docs/superpowers/plans/2026-09-24-kb-slices.md`, set slice 98's Status to `green` and append, dated:
  - a `slice 98 green` entry in the shape of slice 97's: what someone can now rely on; "Surprised by"; "Red and green" with the counts above (`-m "slice-96 or slice-93"` before, with the steps, after; the suite before and after); the probe lines before and after; the greps and the line count of `values.py`; "Open questions", naming the two QUESTIONS FOR THE SPEC logged when slice 98 was cut (Init under a blank role, a snapshot's blank piece of work) and the one of 2026-09-27 on a change refused for its signature not reporting its operations' faults;
  - `batch 17 checkpoint: slice 98 green; suite 220 passed; every slice in the plan is green, leaving the questions for the spec`.

  Commit the tests, `src/kb/values.py` and the slice plan together.
