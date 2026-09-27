# kb Batch 22 Implementation Plan: slice 102.6.1, the last before 0.3.0

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. One task. It is a capability slice of `docs/superpowers/plans/2026-09-24-kb-slices.md`, built red-green under shopsystem-bdd:bdd-red-green.

**This plan carries no code** (shopsystem-knowledge adrs/0011).

**Goal:** A client or operator running kb with an environment that names another git repository finds every change in the store's own history, and that repository untouched. This happens, for example, when kb runs from a git hook, which sets `GIT_DIR` and its kin. After this batch the tree can be tagged 0.3.0, which is the user's decision.

**Spec:** `docs/superpowers/specs/2026-09-23-kb-design.md`:
- "Finding the store": "nothing is guessed, and a read or write never goes somewhere the user did not expect";
- the write path's commit;
- the journal's "every change leaves an entry".

`CLAUDE.md` is binding. `store.py` owns "files, the git repository, discovery of a store", and `_git` is the one place git is run.

## Global Constraints

- **What may change.** No feature line changes. `kb.proto` does not change. Every rule in CLAUDE.md holds. `src/kb/` modules stay under 250 lines, and `store.py` is at 237.
- **The suite.** Today it gives `253 passed, 12 failed` (run at `be24e7a`); the 12 are this slice's rows. After this task, every scenario passes.
- **Commits.** Use `git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit`, with the model's Co-Authored-By line. Make one commit. The implementer never pushes or tags.
- **Where files go.** Never create a file outside this repository's `.superpowers/`. `/home/vscode` is shared with shop-knowledge, whose suite may be running. Throwaway git repositories for the steps go under each test's `tmp_path`. Probes go under `.superpowers/batch22/`.

## Review Focus

1. **The kb checkout itself** (owner: Task 1). A step or probe that names a git repository must never name the kb checkout or any repository outside the test's `tmp_path`. After the task, `git -C /home/vscode/shopsystem-kb status --porcelain` shows only the task's own changes, and its log shows no stray commit.
2. **A repository-locating variable git adds later** (owner: Task 1). Clearing reads git's own list (`git rev-parse --local-env-vars`) rather than a list kb keeps. If that list cannot be read, the call fails closed and does not run git with the inherited environment. Log how it is read, and at what cost: once per process, not once per call.

---

### Task 1: Slice 102.6.1, a git repository named by the caller's environment never receives the store's history

**Scenarios** (`@slice-102.6.1`, 12 in all):
- `read-the-journal` / A change made while the client's environment names another git repository is recorded in the store's own history (7 rows);
- `start-a-store` / Starting a store while the client's environment names another git repository begins the store's own history (2 rows);
- `look-after-a-store` / The operator sets up a store from a shell whose environment names another git repository;
- `read-an-artifact` / A git repository named by the environment is no way of saying which store is meant (2 rows).

**Why red:** the scenarios fail on `StepDefinitionNotFoundError` today. Once their steps exist, the write and init rows fail on "that git repository is left as it was". `store._git` passes a copy of the caller's environment, so an inherited `GIT_DIR` overrides `git -C <store>`. The batch 21 review reproduced this: Init and Create answer with no fault, the store gets no history, and the other repository receives the commits.

**Where it lands:**
- `store._git`: every call, `init` included, runs with an environment cleared of each variable git lists as locating a repository.
- The existing `env=` a caller passes, the author's identity, keeps its meaning.
- Nothing else knows git.

**Steps:**
- The Givens set `GIT_DIR` and its kin, the set git gives a hook, with `monkeypatch`, pointing at a repository made under `tmp_path`. For the operator's scenario, they go into the environment of the `kb` subprocess.
- The Then "that git repository is left as it was" compares that repository's `git log` and `git status --porcelain` before and after. This step may know git, because the Given made a real git repository.
- The history Then reads through the contract (`Journal`).
- The read rows go with the existing store-finding steps.

**Folded in** (from the batch 21 review):
- `tests/test_the_published_contract.py`'s docstring names the clock keyword it pins.
- `rules.ALL` reads `globals()`.
- `write.py`'s `zip(landings, stamps)` takes `strict=True`.
- `journal.py`'s docstring names no process step. The known gap stays in the plan's log.

**Tasks:**
- [ ] Take the write outline's first row red on its own assertion, then green in `_git`. Then take the other rows and scenarios, each seen red first or credited to the change that made it green.
- [ ] Make the folded-in edits.
- [ ] Run Review Focus 1 and 2.
- [ ] Confirm the suite gives every scenario passing.
- [ ] Write the checkpoint in the slice plan's log, set the status to green, and commit.

## After the batch

- [ ] A whole-branch review on the most capable model. The reviewer runs kb's suite, and shop-knowledge's suite against this checkout's `src`.
- [ ] Push `main`.
- [ ] Then the release commit, `pyproject.toml` to 0.3.0 plus a v0.3.0 line in adrs/0010-tags.md, and the tag. The tag is the user's decision.
