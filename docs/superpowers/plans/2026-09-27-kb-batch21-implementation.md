# kb Batch 21 Implementation Plan: slices 102.2 to 102.6, the last before 0.3.0

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Each task is one slice of `docs/superpowers/plans/2026-09-24-kb-slices.md`, taken in slice order. Tasks 2 and 3 are capability slices, built red-green under shopsystem-bdd:bdd-red-green. Tasks 1, 4 and 5 are enabling slices, each verified by its check.

**This plan carries no code** (shopsystem-knowledge adrs/0011). For each task it says what fails and why, where the change lands, what is already decided, and how to verify it.

**Goal:** make kb's history keep every change, whatever the clock a client gives, and make the published surface complete, so that 0.3.0 can be tagged. The slices, in order:
- **102.2:** the signature's conversions get a module of their own, which frees `values.py`.
- **102.3:** changes stamped at the same moment each leave an entry, and every stamp is read before a set's first write.
- **102.4:** a clock's moment in another zone, or in none, is kept in UTC.
- **102.5:** the contract test pins the clock and the rule set.
- **102.6:** the store marker's value leaves `kb.contract`.

**Spec:** `docs/superpowers/specs/2026-09-23-kb-design.md`, in particular:
- the Transports clock sentence;
- the journal entry's fields;
- the write path ("Write one journal file per operation");
- "refused with a fault, never an exception";
- the contract section.

The decisions are adrs/0008 and 0018. `kb.proto`'s comment "`at` is ISO 8601 in UTC" is published contract. `CLAUDE.md` is binding, in particular rule 4 (draft, validate, write: nothing is written until every part of the change is settled) and the module map. The reviews this plan rests on are kept as scratch notes outside git:
- the eighth architecture review, `.superpowers/batch21/arch-review-8.md`;
- the seventh, `.superpowers/batch20/arch-review-100.1.md`, whose section 4 R1 this batch takes up;
- batch 20's whole-branch review, logged in the slice plan on 2026-09-27.

## Global Constraints

- **Features.** No feature file changes except the steps, and the feature lines stay read-only.
- **Contract.** `kb.proto` does not change.
- **Rules.** Every rule in CLAUDE.md holds:
  - modules under `src/kb/` stay under 250 lines, and `servicer.py` under 150;
  - only the servicer's wrapper catches broad exceptions.
- **The baseline.** The suite gives `239 passed, 13 failed` today (run at `e1430d5`). The 13 are the scenarios of 102.3 (5) and 102.4 (8).
  - Record the list with `.venv/bin/python -m pytest -q -rf | grep ^FAILED | sort > .superpowers/batch21/failing-before.txt`.
  - Enabling tasks leave that list unchanged.
  - After Task 2, 8 are left; after Task 3, none.
- **Commits.** Commit with `git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit`, ending the message with the model's Co-Authored-By line. Make one commit per task, holding its change and its checkpoint in the slice plan's log, with its status set to green. The implementer never pushes or tags.
- **Scratch.** Scratch files and probes go under `.superpowers/batch21/`. Never create a file outside this repository's `.superpowers/`: the parent `/home/vscode` is shared with shop-knowledge, whose suite may be running, and a store there breaks it.
- **The client.** shop-knowledge, pinning kb by tag, uses `connect()` and `connect(root)`, `kb.content`, `kb.canonical.NotCanonical`, and `kb.journal.now`, which its tests replace. All of these keep working in this batch; `kb.journal.now` goes only in slice 102.8.

## Review Focus

1. **A clock that raises, or returns something that is not a moment** (owner: Task 2). The clock is read on Init, on a single change, on an Apply of several, and on a Snapshot. Each leaves nothing written: `git status --porcelain` is clean inside the store, and a later Init where Init was refused behaves as before. Log what the client is given. If the exception still escapes the client as an exception, log it for the ninth review; the servicer wrapper's scope, CLAUDE.md rule 1 against `servicer.py:21`, is routed there (batch 20 review M3).
2. **The journal's order with moments in mixed zones** (owner: Task 3). Journal entries are returned oldest first by their UTC moment. Log it.
3. **The replaced `kb.journal.now`** (owner: Tasks 2 and 3). With no clock given, a replacement made from outside still stamps every entry. Log the probe.

---

### Task 1: Slice 102.2, who signs a change is converted in a module of its own

**Check:**
- `wc -l src/kb/values.py` gives 210 or fewer; it is 250 today.
- `grep -nE "def (signed|reader|starter|_unsigned)|class (Actor|Signed)" src/kb/values.py` gives none.
- The new module has a CLAUDE.md row, as the seventh review's R1 words it: "who makes a change and why: the actor, the signature, and the conversions of a writer's, a reader's and a starter's; refuses one that does not sign"; never holds: I/O, other request values.
- Each refusal's text appears once: `grep -c "every entry in the history" src/kb/*.py` names one file.
- No line in the new module is over 120 characters.
- The failing list is unchanged.

**Where it lands:** `Actor`, `Signed`, `actor`, `_unsigned`, `signed`, `reader` and `starter` move out of `values.py` into the new module. Its callers import from it.

- [ ] Make the move.
- [ ] Run the check.
- [ ] Write the checkpoint and commit.

### Task 2: Slice 102.3, changes stamped with the same moment each leave an entry of their own

**Scenarios (`@slice-102.3`, 5 scenarios):**
- `read-the-journal` / Changes stamped with the same moment each leave an entry of their own (3 rows);
- `read-the-journal` / Sets of changes made at the same moment are told apart;
- `start-a-store` / Starting a store and the first change after it keep separate entries at the same moment.

**Unknown:** whether every entry of a set can be given a free id before the set's first write, as rule 4 requires, with `journal.py` deciding whether a journal id is free.

**Why red:** the scenarios fail on `StepDefinitionNotFoundError` today. Once their steps exist, they fail because an entry's id is `<stamp>-<seq>`, where `seq` restarts at 1 for each set, so two sets stamped with the same moment write one file. The batch 20 review's probe showed five changes leaving one entry, and each single change's set is its first entry's id.

**Where it lands:**
- `journal.py` owns "journal entries, their files" (the module map), so it decides whether an id is free and holds the one function that forms an id. The eighth review found the id's shape written twice there.
- `write.py` settles every stamp and id of a set before the set's first write. That covers `Init`'s entry, a single change's, each of an Apply's, and a Snapshot's. So a clock that raises leaves nothing written (Needs; Review Focus 1).
- The stamp is the clock's moment unchanged. kb may not move it on to make an id unique (the formulator's coverage table), so uniqueness comes from the id, not the time.
- How an id is made unique among ids already in the journal and ids settled earlier in the same set is the implementer's choice within the module map. An entry keeps its `batch` meaning: an Apply's minted id, or a single operation's own id.

**Steps:**
- The Givens and Thens go in the two features' test modules, beside their steps.
- The clock Given already exists in both modules. Move it to `tests/conftest.py`, written once, as the batch 20 review asked for 102.4 (fold it here if Task 2 needs it first).

- [ ] Take each scenario red then green, the collision outline's first row first.
- [ ] Run Review Focus 1 and 3.
- [ ] Write the checkpoint and commit.

### Task 3: Slice 102.4, a clock's moment in another zone, or in none, is kept in UTC

**Scenarios (`@slice-102.4`, 8 scenarios):**
- `read-the-journal` / A moment the clock gives in another zone is kept as the same moment;
- `read-the-journal` / A moment the clock gives with no zone is recorded as that moment in UTC;
- `read-the-journal` / The history read since a time answers plainly whatever zone the clock gave (6 rows).

**Why red:** `journal._stamp` writes the moment as given. A zone-less moment then makes `Journal(since=...)` raise `TypeError` out of the client, at `query.py:80`'s comparison. A moment in another zone gets an id ending in `Z` that is false, is filed under the local date, and sorts out of order.

**Where it lands:**
- `journal._stamp` reads a zone-less moment as UTC and turns every moment into UTC, before the id and the entry are formed.
- The one reading of "UTC unless it says otherwise" is shared with `values.since`, which Task 1's move gives room for, rather than written twice.
- `(clock or now)()` becomes a test for `None`, so a clock object that tests false is still used (batch 20 review M1).
- The spec's Transports clock sentence and `connect`'s docstring say what a clock returns: a `datetime`, read as UTC when it has no zone (M4).

**Decided (from the slice plan's log, settled by `kb.proto`):**
- A zone-less moment is read as UTC.
- `at` is given in UTC.

- [ ] Take each scenario red then green.
- [ ] Run Review Focus 2.
- [ ] Write the checkpoint and commit.

### Task 4: Slice 102.5, the published-contract test pins connect's clock

**Check:**
- `tests/test_the_published_contract.py` asserts that `inspect.signature(kb.client.connect).parameters["clock"]` is keyword-only, with default `None`.
- `rules.ALL` is built from the module's upper-case constants, or the test checks that the two agree, so a rule added but not listed goes red (batch 20 review M2).
- The suite gives every scenario passing.

- [ ] Make the change.
- [ ] Show the guard works: a throwaway rule constant left out of `ALL` turns the test red. Log it, then revert.
- [ ] Write the checkpoint and commit.

### Task 5: Slice 102.6, the store marker's value is the store's own, outside the published contract package

**Check:**
- `grep -rn "CONTRACT_VERSION" src/kb/contract` gives none.
- The marker's value lives in `store.py`, beside where `store.yaml` is written.
- A new store's `store.yaml` is byte for byte what it was.
- An existing store still opens.
- The suite gives every scenario passing.

**Where it lands:** the constant and its docstring move to `store.py`, and every reader imports it from there.

- [ ] Make the move.
- [ ] Compare a new store's `store.yaml` bytes before and after, and log it.
- [ ] Write the checkpoint and commit.

## After the batch

- [ ] A whole-branch review on the most capable model, against this plan, CLAUDE.md, the spec and adrs/0018. The reviewer runs kb's suite, and shop-knowledge's suite against this checkout's `src`.
- [ ] Push `main`.
- [ ] Then the release, 0.3.0: bump `pyproject.toml`, tag `v0.3.0` and push the tag. This is the user's decision (shopsystem-knowledge adrs/0006).
