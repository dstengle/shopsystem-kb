# kb batch 30 Implementation Plan: a seed that holds the root

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Each task is one slice, implemented under shopsystem-bdd:bdd-red-green. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `kb init P/r --seed P` lands exactly the seed, kb's staging place passed over wherever the root lies inside the seed (148).

**Architecture:** a seeded start tells the import the one place it made (`<root>/.kb-starting`), and the offered files pass over everything under that place, wherever it lies below the seed. Today only a `.kb-starting` at the seed's top is passed over (batch 29), so a root below the seed has its staged store read as offered files. No new module.

**Tech Stack:** Python 3.11, pytest-bdd 8.1, pytest-xdist.

**Spec:** `spec/capabilities/operate-a-store.md` (the Behaviour line and the Implementation line changed in e503ee9), `spec/decisions.md` decision/seed-may-be-the-root. Slices: `docs/superpowers/plans/2026-09-24-kb-slices.md`, slice 148.

## Global Constraints

- Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.10.0/scripts
- One task per slice. The plan holds no code: the implementer writes steps and code under bdd-red-green, after the red run.
- The task is `Review: batch-end`, `Model: sonnet`: it touches no concurrency, published contract or stored data; the batch's branch review covers it.
- CLAUDE.md holds: no module under `src/kb/` over 250 lines; `values.py` (241) must not grow, and the place passed over is not a request field, so it is not a `values.py` conversion. Rule 1: no broad `except`. A module's row in CLAUDE.md's map changes in the task that changes what it owns.
- No scenario or step definition names the staging directory (`.kb-starting`) (spec Testing). A plain test of a module's public functions may.
- Baseline at ccc8bc5 (plan log): **679 passed, 2 failed** in 24 s: both examples of the reformulated outline.

### Binding values, verbatim from the spec

- Behaviour: "When the operator runs kb init with a seed directory that is the directory the store is started in, or holds it, saying which role they are, there is a store inside that directory holding the files the seed directory held, as kb import lands them into a freshly started store, and nothing kb made while starting it is among them."
- Implementation: "A seed directory that is the root itself, or holds it, is read with kb's staging place passed over wherever the root lies inside it, as an import passes over a store's own files."

## Decisions this plan takes

1. **What is passed over:** exactly the staging place this run made, `<root>/.kb-starting` resolved, and every file under it, when it lies inside the seed directory; nothing else of the root. A file named `.kb-starting` elsewhere in a seed, not this run's place, is read as any other file. The seed's other files, the root's own included, are read as the seed.
2. **How the import learns it:** the operator's import request (`operating.Importing`) carries an optional place to pass over, given only by `staging.seeded`; `kb import` gives none. It reaches `offers.py` beside the directory, not as a `values.py` conversion.
3. **The top-level pass-over stays:** `offers.HISTORY` keeps `store.STAGING` (batch 29), so `kb import` of a directory holding a stopped run's leftover at its top is unchanged.
4. **"As kb import lands them"**, compared as slice 147 compares it (batch 28 decision 3: artifacts, names, titles, revisions, type versions; histories' roles, message form and sets, with the seed path normalised), against a second store started under the same role into which `kb import` lands the same seed.

## Review Focus

1. A seed that holds the root two or more levels down (`kb init P/a/b --seed P`) lands the seed. Owner: Task 1, a plain test of the import's offered files or the command.
2. A seed holding the root where the root already holds other files besides the staging place: those files are read as part of the seed (errors when they are not in the export layout), as decision 1 says. Owner: Task 1, a plain test.

---

### Task 1: Slice 148 — a store seeded from a directory that holds the directory it is started in

Review: batch-end
Model: sonnet
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.10.0/scripts

- [ ] **Scenarios** (`@slice-148`, 1 scenario outline, 2 collected): operate-a-store / The operator sets up a store seeded from a directory that is, or holds, the directory it is started in (`is`, `holds`).

- [ ] **Why it is red today** (suite record at ccc8bc5): the outline's steps changed wording (`a seed directory that <relation> that directory, holding files that check clean: ...`; `kb init with that seed directory against the directory`), so both examples miss step definitions; slice 147's old steps in tests/test_look_after_a_store.py (around line 410) no longer match any scenario. Behind the `holds` example, the import reads `r/.kb-starting/kb/...` as offered files and refuses them (4 errors), because `offers._files` passes `store.STAGING` over only at the seed's top.

- [ ] **Where the change lands.** `src/kb/operating.py` (`Importing` gains the place passed over; the import hands it on), `src/kb/importing.py` and `src/kb/offers.py` (`offered` passes over files under that place), `src/kb/staging.py` (`seeded` gives its staging place). CLAUDE.md's `offers.py` and `staging.py` rows as their ownership changes. Replace slice 147's old steps with the outline's; remove those no scenario uses.

- [ ] **Steps to reuse.** `a directory that has no store inside it`; slice 147's seed writing and `_holds_the_seed_as_imported(..., seeded_from=...)` comparison; for `holds`, the seed is a directory with the root made inside it (the root empty), for `is`, the seed is the root.

- [ ] **Decisions applied.** 1, 2, 3, 4. Review Focus 1 and 2 land here.

- [ ] **Verify.** `.venv/bin/python -m pytest -q -m slice-148` → 2 passed; then `make test` → 681 passed, 0 failed.

- [ ] **Checkpoint.** `plan status 148 green`; `plan log "Suite: ..."`.
