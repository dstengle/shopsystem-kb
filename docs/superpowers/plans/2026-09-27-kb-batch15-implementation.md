# kb Batch 15 Implementation Plan: slice 96, a change says which role made it, and why

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Each task is one slice of `docs/superpowers/plans/2026-09-24-kb-slices.md`. The one task here is a capability slice, written red-green against its scenarios under shopsystem-bdd:bdd-red-green.

**This plan carries no code.** From 2026-09-27 the planner plans and the implementer writes the code in the execution session. The plan says what is red and why, where the change lands, which decisions are already made, what can be reused and how to verify it. It holds no code blocks, file contents, diffs or step-definition bodies. It was not built or replayed. Its counts come from `pytest --collect-only -q -m slice-N` and from runs of this checkout as it stands at `fbf3747` with slice 96's tag added.

**Goal:** A Create, Write, Append, Delete or Apply without a role or without a message is refused before anything is written. A Snapshot without a message is refused the same way (slice 93's new row, made green by the same rule).

**Architecture:** kb is the Python package `kb` in this checkout. A protobuf contract (`kb.contract`) sits in front of `KbServicer` (`src/kb/servicer.py`). Each rpc runs inside one boundary that turns `values.Refused` into that rpc's faults. Every change reaches the domain through `servicer._land`, which converts the operations (`requests.operations`, which never raises and keeps a failed operation as a `Refusal` in its place) and then the signature (`values.signed(request.actor, request.message)`). It then calls `write.land`. A snapshot converts its signature with `values.reader`. Today `values.signed` wraps the role and message without checking them. `values.reader` checks the role and the piece of work, but not the message.

**Tech Stack:** Python 3.11, protobuf + grpcio (no `.proto` change in this batch), ruamel.yaml 0.19 (YAML 1.2), git via subprocess, pytest 9 + pytest-bdd 8.

**Spec:** `docs/superpowers/specs/2026-09-23-kb-design.md`. The passages this plan argues from:
- "every-change-is-attributable. Actor, execution, message, and a fingerprint per operation are what history needs."
- The rpc table: every mutating rpc takes an actor and a message.
- "Every mutating rpc returns all errors found, not the first."
- The write pipeline's step 6: "one commit, message from the request, author from the actor. On git failure restore the files from HEAD and report."

The scenarios:
- `features/change-an-artifact.feature`, the outline "A change that does not say which role made it, or why, is refused", tagged `@slice-96`.
- `features/snapshot-what-a-piece-of-work-read.feature`, the row "the decision and the process without saying why" in slice 93's outline.

The decisions are `adrs/0012-writes-need-role-and-message.md`, `adrs/0014-signature-refused-before-operations.md` and `adrs/0015-missing-message-rule.md`. `CLAUDE.md` is binding.

## Why today's behaviour is worse than a crash

A crash that leaves the store untouched loses only the call. This one does not. Every call in the outline passes every check, drafts, and reaches `write._written`. That function saves the artifact's file and writes one journal entry per operation. Only after that does it call `store.commit`, and git refuses the commit: empty author name, or empty message. `subprocess.CalledProcessError` escapes the boundary. The new version stays on disk, staged but uncommitted, and it can be read. After a refused Write, a Read answers revision 2 and the Journal lists the entry, even though the change never landed.

The probe `.superpowers/probes/batch15-actor.py` (see Probe below) showed this on 2026-09-27, for all five calls under both missing parts:
- Create: `A decision/another.yaml`, and `decision/another` reads at revision 1.
- Write and Append: `M` the decision, which reads at revision 2.
- Delete: `D` the decision, which is refused as `not-found` from then on.
- Apply: both files and two journal entries, journal 3 -> 5.

A Snapshot with no message leaves its journal entry added and uncommitted.

The spec's step 6 restore ("on git failure restore the files from HEAD") was never built. This task therefore has to refuse before anything is written. It does not repair after the fact. That is CLAUDE.md's rule 2: the role and the message become validated values in `values.py` before the domain sees them. It is also rule 4: nothing is written until everything is checked, and the signature is part of what is checked.

## Global Constraints

- Feature files are read-only for the implementer. Any diff under `features/` is a stop condition. The `@slice-96` tag is already committed with this plan.
- Red-green, one scenario outline at a time, adding no behaviour that no row asks for. Nothing refuses a role or message made only of spaces (Review Focus 1).
- CLAUDE.md's rules are each implemented once:
  - `grep -c "try:" src/kb/servicer.py` stays `1`.
  - `grep -nE "except (Exception|BaseException)|except:" src/kb/*.py` prints nothing.
  - Each refusal text appears once in `src/kb/`: `grep -rc "names the role that made it" src/kb/*.py | grep -v ":0"` gives `src/kb/values.py:1`, and likewise for "says why it was made".
- Size: no module over 250 lines, and `servicer.py` under 150. `values.py` is 241 today, so the task has 9 lines of room (see Decision 5).
- Tests use the contract, through `tests/calls.py`, or a module's public functions. They never use private helpers.
- `make test` runs `.venv/bin/python -m pytest -q`. While any scenario is red, its last line is make's own `Error 1`, so read pytest's summary line above it. The summary lines quoted below leave out `, N warnings in Xs`; the `PytestRemovedIn10Warning`s are the baseline.
- The contract's version stays `0.1`, `pyproject.toml` stays `0.2.0`, and `kb.proto` is not touched (Decision 6).
- Work on `main` in this checkout. Commit with `git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit`, the message ending with the Co-Authored-By line of the model that made the commit.
- Baseline at `fbf3747` plus the tag: `.venv/bin/python -m pytest -q` gives `11 failed, 196 passed`. The failures are the ten `@slice-96` rows and slice 93's fourth row, each `StepDefinitionNotFoundError` on its When.

## Decisions this plan makes

Each decision rests on a spec or plan passage, so the implementer does not have to choose.

1. **The signature is refused before the operations, with its faults alone.** A change or snapshot with no role, no message, or neither is refused with those faults only: role first, then message, then (for a snapshot) the piece of work. Its operations and names are not checked. This follows slice 93, which already refuses a snapshot for its actor before its names. Because `servicer._land` converts the operations without raising and then converts the signature, raising in `values.signed` gives this order unchanged. The spec's "returns all errors found, not the first" pulls the other way, so this is logged as a QUESTION FOR THE SPEC in the slice plan and recorded as `adrs/0014`.
2. **The faults.**
   - No role: rule `actor`, no artifact, no path, message "every entry in the history names the role that made it". This is the same text slice 93 gives, from the scenario's reason.
   - No message: rule `message`, no artifact, no path, message "every entry in the history says why it was made". The rule names the request field, as `root`, `since` and `title` do. Recorded as `adrs/0015`.
3. **The conversion lives in `values.py`, once.** `values.signed` refuses a missing role or message. `values.reader` is the same conversion plus the piece of work, so it builds on it; it does not check the role a second time. Its faults keep the order in Decision 1: slice 93's existing rows still answer `[actor]` each, and a snapshot missing all three answers role, message, piece of work. `values.starter` (Init) keeps its own role check and its own message ("a store can only be started under a role"), because Init's message is fixed by kb ("initialise store").
4. **Nothing else in `src/kb/` changes.** `servicer.py`, `requests.py`, `write.py` and `store.py` are not touched: the servicer already converts the signature before calling the domain. `write.start` builds its `Signed` directly with kb's own message and stays as it is. `git diff --stat src/kb` after the task shows `values.py` alone.
5. **If it will not fit in 250 lines, hand back.** Review 6 proposed splitting the actor conversions out of `values.py` "first". The user's brief for this batch puts the conversion in `values.py`, and one conversion shared by `signed` and `reader` is expected to add only about three lines. If the change would still push `values.py` past 250, stop and write a HAND-BACK to the slice plan's log naming the count. Do not choose a split alone.
6. **`kb.proto` is not touched.** The response comments already say "With faults, a refusal". The Snapshot response's list of refusals was already out of date after slice 93 and stays as it is; no rpc gains a field.
7. **The steps.**
   - `calls.apply` gains `actor=CLIENT`, sent as the request's actor, as `write`, `append` and `remove` already have it. Every existing caller sends what it sends today.
   - The new Then for the reason matches only this outline's two reasons, with a `parsers.re` alternation over escaped strings, as `_aim_at_a_wrong_place` does. A generic `parse("the change is rejected because {reason}")` would compete with the file's specific rejection steps.
   - The snapshot row extends `WRONGLY` so that each entry carries its message. `_snapshot_wrongly` sends that message instead of the fixed "Read before restocking", and existing rows keep that message.
   - The message check in `_snapshot_rejected` covers rule `message` as well as `actor`.
8. **What each row sends.** Valid content, so that before the change the row fails at git and not at a type check:
   - "creates another decision": a Create of a decision titled "Another", with both sections, through `calls.request`. `calls.create` cannot be used, because it asserts there are no faults.
   - "replaces the decision": a Write of the decision with both sections and no options. The probe found this valid: it landed at revision 2 before git refused.
   - "adds an option to the decision": an Append to `options` of an item with a title.
   - "removes the decision": a Delete of the decision.
   - "asks, in one go, …": an Apply of the Create above and the Write above.
   - "saying why but not which role it is": `kb_pb2.Actor(role="")` with a message.
   - "saying which role it is but not why": `CLIENT` with the message `""`.

## Review Focus

Most likely to bite first. None of these gets code in this plan; 1 and 2 are logged as QUESTIONS FOR THE SPEC in the slice plan's log.

1. **A role or message of spaces alone.** It is not empty, so after this task it still passes. Git strips a message of spaces to nothing and refuses the commit, leaving the change on disk as today. Reproduction: `.superpowers/probes/batch15-edges.py`, lines `write, role of spaces` and `write, message of spaces`. Both raise `CalledProcessError` with `M` the decision and a journal entry added, and the decision reads at revision 2. Expected after this task: unchanged. Question for the spec.
2. **A change wrong in its signature and its content at once.** Per Decision 1 it answers only the signature's faults. The spec asks for all errors. Reproduction: the same probe, line `write, bad content, no role`. Today it answers the two `sections` faults, and after this task it should answer `[actor]`. Question for the spec.
3. **Both parts missing.** A change answers `[actor, message]`, role first. A snapshot missing role, message and piece of work answers `actor`, `message`, `actor`, in that order. Today the edges probe line `snapshot, no role, no message, no work` answers the role and piece-of-work faults and nothing of the message. Pin it with the probe after the change; no scenario asks for it.
4. **Init is untouched.** `values.starter` still refuses a missing role with its own message. Slice 94's and start-a-store's scenarios stay green in the full run.
5. **A role with a newline is accepted and committed.** The edges probe line `write, role with a newline` answers no faults and revision 2. This task leaves it alone. It is noted here only so that nobody widens the role check without a scenario.

---

### Task 1: Slice 96, a change says which role made it, and why, or nothing is written

**Slice plan entry:** slice 96, capability.
- Scenarios: kb / change-an-artifact / A change that does not say which role made it, or why, is refused (ten rows, `@slice-96`), and in the same work kb / snapshot-what-a-piece-of-work-read / Every way a snapshot can be asked for wrongly is refused, row "the decision and the process without saying why" (keeps `@slice-93`).
- Observable: a client that creates, replaces, adds an item to, removes, or asks in one set for several changes to an artifact without giving a role, or without a message, is refused with the reason, and the store, its files and its history hold nothing of the change.
- Unknown it settles: whether one conversion of a change's role and message, made before any operation is drafted, refuses every call that changes the store, a single change and a set alike. Expected answer: yes, because every change goes through `servicer._land` (Architecture).

**Why each scenario is red today** (run at `fbf3747`):
- All eleven stop at `StepDefinitionNotFoundError` on their When. No step handles "the client <call>, <saying>", and `WRONGLY` has no "without saying why" entry.
- Behind the steps, every call raises `subprocess.CalledProcessError` from `store.commit` and leaves its files written ("Why today's behaviour is worse than a crash"). So once the steps exist, each row stays red at its When with that error until `values.py` changes.
- Nothing in `values.signed` checks the role or message. `values.reader` checks the role and the piece of work only.

**Where it lands (CLAUDE.md's module map):**
- `src/kb/values.py`, which owns conversion of single request fields into validated values. This is rule 2, implemented once, and rule 4 follows from it: a refused signature never reaches `write.land`.
- Test side:
  - `tests/test_change_an_artifact.py`: new When and Thens.
  - `tests/calls.py`: `apply` gains `actor`.
  - `tests/test_snapshot_what_a_piece_of_work_read.py`: `WRONGLY` carries a message, and `REASONS` gains the new reason.

**Reuse:**
- `tests/test_change_an_artifact.py`:
  - Given "the decision carries two options" (`_two_options`), over the Background `_store_with_a_decision`.
  - Then "reading the decision gives what it held before, at the version it held before" (`_as_it_was`), which needs the When's fixture `attempt` to carry the decision file's bytes under `"before"`.
  - `DECISION`, `SECTIONS`, `OPTIONS`.
- `tests/calls.py`: `CLIENT`, `request` (a Create that returns its faults), `write`, `append`, `remove`, `apply`, `creation`, `replacement`, `journal`, `listing`, `everything_under`.
- `tests/test_snapshot_what_a_piece_of_work_read.py`: `_snapshot_wrongly`, `_snapshot_rejected`, `_no_entry_for_it`, `WRONGLY`, `REASONS`, `EXECUTION`, `DECISION`, `PROCESS`.
- New steps, three Thens and one When:
  - "the change is rejected because <reason>", for this outline's two reasons only (Decision 7). It asserts one fault with the rule from Decision 2, empty artifact and path, the message starting with the reason, and revision 0 where the response has one.
  - "the store holds no artifact it did not hold before". It asserts that List of `decision` names, and `everything_under` the store's `kb/`, are the same as the When recorded before the call.
  - "the store's history holds no entry for it". It asserts that `journal(client)` holds as many entries as before the call.
  - The When records all three before-values and the decision file's bytes, then makes the call.

**Probe** (throwaway, run from the checkout root, kept outside git under `.superpowers/`):
- `.venv/bin/python .superpowers/probes/batch15-actor.py` runs every call of the outline under no role and under no message, each on a fresh store in a temporary directory. For each it prints the outcome, `git status --porcelain` of the store, the journal count before -> after, the decision's revision and the revision of `decision/another`.
- Today every line reads `raised CalledProcessError` with files listed as uncommitted.
- `.venv/bin/python .superpowers/probes/batch15-edges.py` covers Review Focus 1 to 3 and 5.

- [ ] **Step 1: Confirm the baseline.**
  - `.venv/bin/python -m pytest -q` gives `11 failed, 196 passed`.
  - `.venv/bin/python -m pytest --collect-only -q -m slice-96` gives `10/207 tests collected`.
  - `.venv/bin/python -m pytest -q -m slice-96` gives `10 failed`.
  - `.venv/bin/python -m pytest --collect-only -q -m slice-93` gives `4/207 tests collected`.
  - `.venv/bin/python -m pytest -q -m slice-93` gives `1 failed, 3 passed`.
  - Run both probes and keep their output as `.superpowers/probes/batch15-before.txt`.
- [ ] **Step 2: Write the steps for the outline** (Reuse, Decisions 7 and 8), and give `calls.apply` its `actor`.
- [ ] **Step 3: See it red for the right reason.** `.venv/bin/python -m pytest -q -m slice-96` gives `10 failed`, each failing in its When with `subprocess.CalledProcessError` (git refusing the commit), not `StepDefinitionNotFoundError`. `.venv/bin/python -m pytest -q` gives `11 failed, 196 passed`. If any row fails on a content fault instead, its content is wrong (Decision 8); fix the step, not the code.
- [ ] **Step 4: Write the snapshot row's step change** (Decision 7). `.venv/bin/python -m pytest -q -m slice-93` gives `1 failed, 3 passed`, the fourth row failing at `CalledProcessError`.
- [ ] **Step 5: Make it green in `values.py`** (Decisions 1 to 3 and 5).
  - `.venv/bin/python -m pytest -q -m slice-96` gives `10 passed`.
  - `.venv/bin/python -m pytest -q -m slice-93` gives `4 passed`.
- [ ] **Step 6: The whole suite and the structural checks.**
  - `.venv/bin/python -m pytest -q` gives `207 passed`.
  - `git diff --stat src/kb` lists `src/kb/values.py` only.
  - `wc -l src/kb/values.py` is 250 or fewer.
  - `grep -c "try:" src/kb/servicer.py` gives `1`.
  - `grep -nE "except (Exception|BaseException)|except:" src/kb/*.py` prints nothing.
  - The two refusal texts appear once each, in `values.py` (Global Constraints).
  - `git diff --stat features` prints nothing.
- [ ] **Step 7: Probe after.** Rerun both probes and diff against `batch15-before.txt`. Expected from `batch15-actor.py`, every line:
  - `answered faults=[('actor', 'every entry in the history names the role that made it')]` (no role) or `[('message', 'every entry in the history says why it was made')]` (no message);
  - `uncommitted=[]`, journal `3->3`, the decision at `rev=1` with no faults, `another rev=0`.

  Expected from `batch15-edges.py`:
  - `snapshot, no message`: `[('message', …)]`, nothing uncommitted.
  - `snapshot, no role, no message, no work`: faults `actor`, `message`, `actor`, in that order.
  - `write, no role, no message`: `actor` then `message`.
  - `write, bad content, no role`: `[actor]` only.
  - `write, role of spaces` and `write, message of spaces`: unchanged, still raising (Review Focus 1).
  - `write, role with a newline`: unchanged.
- [ ] **Step 8: Log the checkpoint and commit.** In `docs/superpowers/plans/2026-09-24-kb-slices.md`, set slice 96's Status to `green` and append, dated:
  - a `slice 96 green` entry in the shape of slice 89.2's: what someone can now rely on; "Surprised by"; "Check, before and after" with the counts above, the probe lines before and after, the greps and `values.py`'s line count; "Open questions", naming the two QUESTIONS FOR THE SPEC logged on 2026-09-27;
  - a line saying slice 93's fourth row is green with it;
  - `batch 15 checkpoint: slice 96 green; suite 207 passed; every slice in the plan is green, leaving the questions for the spec`.

  Commit the tests, `src/kb/values.py` and the slice plan together.
