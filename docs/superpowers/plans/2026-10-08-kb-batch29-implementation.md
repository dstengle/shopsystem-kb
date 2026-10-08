# kb batch 29 Implementation Plan: a root kb cannot write, and a seed that is the root

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Each task is one slice, implemented under shopsystem-bdd:bdd-red-green. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** a root kb cannot write is refused with rule `root`, naming it, before anything is made, by `kb init`, `kb init --seed` and `kb serve --start` alike (146); `kb init R --seed R` lands exactly the seed, kb's staging place passed over (147). Closes the batch 28 review's B1 and B2.

**Architecture:** both are small changes to existing modules. 146: one more refusal in `store.vacant`, which `kb.init`, `staging.started` and `staging.seeded` already ask before anything is made. 147: the staging place's name moves to `store.py` (it owns the store's layout), and `offers.py` passes it over at the directory's top as it passes over a store's history. No new module.

**Tech Stack:** Python 3.11, `os.access`, pytest-bdd 8.1, pytest-xdist.

**Spec:** `spec/capabilities/operate-a-store.md` (the two Behaviour lines and the Implementation line added in d42df01), `spec/decisions.md` decision/seed-may-be-the-root, decision/unwritable-root-refused. Slices: `docs/superpowers/plans/2026-09-24-kb-slices.md`, slices 146 and 147.

## Global Constraints

- Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.10.0/scripts
- One task per slice, in slice order. The plan holds no code: the implementer writes steps and code under bdd-red-green, after the red run.
- Both tasks are `Review: batch-end`, `Model: sonnet`: neither touches concurrency, the published contract's shape, or moving stored data; the batch's branch review covers them.
- CLAUDE.md holds: no module under `src/kb/` over 250 lines (`store.py` is at 234, `refusals.py` 223); `values.py` (241) must not grow. A module's row in CLAUDE.md's map changes in the task that changes what it owns (`store.py`: the staging place's name and a root kb cannot write; `offers.py`: kb's staging place passed over).
- Rule 1: no broad `except` anywhere new.
- The refusal's rule is `rules.ROOT`; no rule name is added (decision/unwritable-root-refused).
- No scenario or step definition names the staging directory (`.kb-starting`) (spec Testing). A plain test of a module's public functions may.
- The suite runs as uid 1000, so a directory made `0o555` is one kb cannot write; a test that makes one restores its mode when it ends, passed or failed, so the temporary directory can be removed.
- Baseline at 725633f (plan log): **676 passed, 4 failed** in 21 s: the 4 collected operate-a-store scenarios of slices 146 and 147.

### Binding values, verbatim from the spec

- Behaviour: "If the directory a store would be started in cannot be written, kb init, with a seed directory or without, and kb serve with `--start` are refused because a store can only be started in a directory kb can write, naming the directory; nothing is served, and nothing is made in it."
- Behaviour: "When the operator runs kb init with a seed directory that is the directory the store is started in, saying which role they are, there is a store inside that directory holding the files it held, as kb import lands them into a freshly started store, and nothing kb made while starting it is among them."
- Implementation: "A seed directory that is the root itself is read with kb's staging place passed over, as an import passes over a store's own files. A root kb cannot write is refused with rule `root`, naming the root, before anything is made, the way `kb.init` refuses a root it cannot start a store in."

## Decisions this plan takes

1. **Where writability is checked:** in `store.vacant`, after every refusal it gives today (a root that is not there, not a directory, already has a store, holds something in the store's place, sits inside a store), so a root that is both unwritable and already refused for another reason keeps today's answer. Writable means `os.access(path, os.W_OK | os.X_OK)`. The message reads `a store is started in a directory kb can write, and {named} is not one`, with `named` as `vacant` already quotes it. Because `kb.init` (`write.start`), `staging.started` and `staging.seeded` (`_vacant`) all ask `vacant` first, the three commands refuse alike before anything is made, and `kb serve --start` serves nothing.
2. **The staging place's name** becomes `store.STAGING` (`".kb-starting"`); `staging.py` uses it, and so does `tests/test_seeding_a_store.py`, which names it today.
3. **What is passed over:** `offers._files` passes over every file under `store.STAGING` at the offered directory's top, as it passes over `HISTORY`. Nothing else changes in what an import reads: a seed that is the root and holds other things (say, a `kb/` it already had) is refused before staging by `vacant` as today.

---

### Task 1: Slice 146 — a store started in a directory kb cannot write is refused naming it

Review: batch-end
Model: sonnet
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.10.0/scripts

- [ ] **Scenarios** (`@slice-146`, 1 scenario outline, 3 collected): operate-a-store / Starting a store in a directory kb cannot write is refused (kb init; kb init with a seed directory; kb serve with --start, giving an address).

- [ ] **Why it is red today**: no step for "a directory that has no store inside it and that kb cannot write"; behind it, `store.vacant` accepts such a root, and the start fails later as rule `store` naming `<root>/.kb-starting` (seeded, serve --start) or as `unreadable`/`store` from the database (plain init).

- [ ] **Where the change lands.** `src/kb/store.py` `vacant` (decision 1); its docstring and CLAUDE.md's `store.py` row. Steps in the module binding operate-a-store's outline.

- [ ] **Steps to reuse.** `a directory that has no store inside it` (tests/test_look_after_a_store.py) and `nothing is served` (tests/conftest.py since batch 28); `_kb` for each command with `KB_ACTOR` set; a seed that checks clean as slice 138's steps write one; "giving an address": `serving.closed_port` or as slice 143's steps do. "Nothing made in it": the directory's listing is empty afterwards. "The directory is named": stderr holds the rule `root` and the directory's path.

- [ ] **Decisions applied.** 1.

- [ ] **Verify.** `.venv/bin/python -m pytest -q -m slice-146` → 3 passed.

- [ ] **Checkpoint.** `plan status 146 green`.

### Task 2: Slice 147 — a store seeded from the directory it is started in

Review: batch-end
Model: sonnet
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.10.0/scripts

- [ ] **Scenarios** (`@slice-147`, 1 scenario, 1 collected): operate-a-store / The operator sets up a store seeded from the directory it is started in.

- [ ] **Why it is red today**: no step for "a directory that has no store inside it, holding files that check clean: a type for decisions and a decision"; behind it, the import reads the staged store's own files (`.kb-starting/kb/...`) as offered files and refuses them as errors (batch 28 review B2).

- [ ] **Where the change lands.** `src/kb/store.py` gains `STAGING` (decision 2); `src/kb/staging.py` uses it; `src/kb/offers.py` `_files` passes it over (decision 3), its module docstring says so; `tests/test_seeding_a_store.py` uses `store.STAGING`. CLAUDE.md's `offers.py` row names kb's staging place among what is passed over.

- [ ] **Steps to reuse.** slice 138's: the seed written as an export writes it, and "as kb import lands them into a freshly started store" compared against a second store started under the same role with `kb import` of the same files (decision 3 of batch 28: artifacts, names, titles, revisions, type versions; histories' roles, messages and sets, not moments or ids). "And nothing else": the seeded store holds no artifact the comparison store does not.

- [ ] **Decisions applied.** 2, 3.

- [ ] **Verify.** `.venv/bin/python -m pytest -q -m slice-147` → 1 passed; then `make test` → 680 passed, 0 failed.

- [ ] **Checkpoint.** `plan status 147 green`; `plan log "Suite: ..."`.
