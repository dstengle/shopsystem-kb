# kb Batch 18 Implementation Plan: slice 99, a call from a working directory that has since been removed

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Each task is one slice of `docs/superpowers/plans/2026-09-24-kb-slices.md`. The one task here is a capability slice, written red-green against its scenarios under shopsystem-bdd:bdd-red-green.

**This plan carries no code** (shopsystem-knowledge adrs/0011). The planner plans, and the implementer writes the code in the execution session. The plan says:
- what is red and why;
- where the change lands;
- which decisions are already made;
- what can be reused;
- how to verify it.

It holds no code blocks, file contents, diffs or step-definition bodies, and was not built or replayed. Its counts come from `pytest --collect-only -q -m slice-99` and from a run of this checkout at `2c9e3ee`.

**Goal:** a client call made from a working directory that has since been removed reads through the store `KB_ROOT` names. With none named, it is refused with a fault saying the working directory is gone. Today the call breaks off with the operating system's `FileNotFoundError`. This is requested by shop-knowledge's slice 50.22, which waits for a release carrying it.

**Architecture:** kb is the Python package `kb` in this checkout. `kb.client.InProcessClient` finds a call's store in `_servicer`. With no root given, it calls `store.locate(Path.cwd(), os.environ)`. `store.locate` looks upward from that directory with `find_above` and reads `KB_ROOT`. Each refusal of discovery is a `kb_pb2.Fault` with `rule="store"`, built in `locate`.

**Tech Stack:** Python 3.11, protobuf + grpcio (no `.proto` change), pytest 9 + pytest-bdd 8.

**Spec:** `docs/superpowers/specs/2026-09-23-kb-design.md`. The passages this plan argues from:
- "Finding the store", as amended in 7b35ef2: "A working directory that no longer exists is inside no store: `KB_ROOT` still names one, and with none set the call is refused, saying the working directory is gone."
- "The client and the store": "Any other call that finds no store is refused with a fault, never an exception."

The scenarios, all `@slice-99` in `features/read-an-artifact.feature`:
- the outline "The client names the store from a working directory that has since been removed", two rows: outside any store, and inside a different store's directory;
- the outline "A call from a working directory that has since been removed, with nothing naming a store, is refused", two rows: outside any store, and inside the store's directory;
- "A working directory that has gone is a fault the client is given, never an exception".

`CLAUDE.md` is binding.

## What happens today

`Path.cwd()` raises `FileNotFoundError` when the process's working directory has been removed. It is called in `InProcessClient._servicer` before `store.locate` is reached, so `KB_ROOT` is never read, and the exception escapes the client (it is outside the servicer's fail-closed wrapper). shop-knowledge's probes on 2026-09-27 showed `shop-knol read decision/x` from a removed directory giving the operating system's `No such file or directory`, with and without `KB_ROOT` set. That wording is shop-knowledge's own `OSError` guard catching what kb raised.

All five rows fail today on `StepDefinitionNotFoundError`, each on its Given:
- "the client is working in a directory outside any store, which has since been removed, with KB_ROOT naming this store";
- "... a folder deep inside the directory a different store sits in, which has since been removed, with KB_ROOT naming this store";
- "... a directory outside any store, which has since been removed, and nothing names a store";
- "... a folder deep inside the directory the store sits in, which has since been removed, and nothing names a store";
- "the client is working in a directory that has since been removed, and nothing names a store".

The Thens "the read is rejected because the directory it is working in is gone" and "the client is given that refusal as it is given any other fault, the call never breaking off" are not defined either. "the client is given the decision, from the store KB_ROOT names" and "no content comes back" exist.

## Global Constraints

- Feature files are read-only for the implementer. Any diff under `features/` is a stop condition. The rows are already tagged.
- `kb.proto` does not change.
- Every rule in CLAUDE.md holds, in particular:
  - Rule 1: no module other than the servicer's wrapper catches broad exceptions, so the fix catches nothing broad.
  - Rule 3's spirit: discovery answers with a value or a fault, never an exception.
  - Size: no module over 250 lines, and `servicer.py` under 150.
- Work on `main` in this checkout. Commits use `git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit`, the message ending with the Co-Authored-By line of the model that made the commit. The implementer does not push. The controller pushes after the batch's review.
- Scratch files go under `.superpowers/` (git-ignored), never under `/tmp`.
- Counts:
  - The suite is `220 passed, 5 failed` today (run at `2c9e3ee`).
  - `-m slice-99` selects 5.
  - After the task: `225 passed`.
  - The store-finding scenarios slice 99 must keep green run with `-m "slice-1.3 or slice-1.8 or slice-1.15 or slice-88"`, which selects 13.

## Review Focus

1. **The admin command line** (`kb validate`) from a removed working directory. No scenario covers it (log, 2026-09-27: nothing upstream needs it). After the task, run it once from a removed directory and log what it shows. If it shares discovery with the client, it now gives the same fault. If it does not, that is logged, not fixed.
2. **A relative `KB_ROOT` from a removed directory.** It cannot be resolved, so it is `KB_ROOT` naming no store (log, 2026-09-27). After the task, run a read with `KB_ROOT=relative/path` from a removed directory, and log the fault.
3. **A client given a root** (`kb.client.connect(root)`) from a removed working directory skips discovery. After the task it still reads its store. Log it.

---

### Task 1: Slice 99, a call from a working directory that has since been removed

**Slice plan entry:** capability.
- Scenarios: the five rows above.
- Unknown: whether discovery can tell a working directory that is gone apart from one inside no store before it looks upward, without the client catching what the one fail-closed wrapper should.

**Where the change lands (CLAUDE.md's module map).**
- `store.py` owns "discovery of a store from a root", so the working directory's absence is found there, not in `client.py`. `client.py` is the in-process transport and holds no domain logic.
  - The client stops reading the working directory itself and asks discovery for the store.
  - Discovery reads the working directory, and a directory that no longer exists yields no directory to look up from. It is inside no store, so `KB_ROOT` is read as for any directory inside no store: named and holding a store, it serves; named and holding none, it is its own refusal, as today. With `KB_ROOT` not set, discovery refuses with a `rule="store"` fault saying the working directory is gone, in the same plain voice as the other store faults.
  - How discovery learns that the working directory is gone (the operating system's `FileNotFoundError` from reading it, caught narrowly where it is read) is the implementer's choice, within rule 1: a narrow catch of that one error where the working directory is read is not a broad catch.
- `store.locate`'s signature may change. Its callers are the client and the admin command line (`cli.py`). Both keep working, and Review Focus 1 says what to log.
- The Givens go in `tests/test_read_an_artifact.py`, beside the existing store-finding Givens (`_working_deep_inside_the_store`, `_outside_with_kb_root_naming_this_one`, `_outside_with_nothing_naming_one`, `_inside_one_store_with_kb_root_naming_another`).
  - Each moves the process into its directory with `monkeypatch.chdir`, then removes the directory.
  - Sets or clears `KB_ROOT` with `monkeypatch`.
  - For a row "inside a different store's directory", makes that other store first.

  Reuse those Givens' setup and don't copy it: parametrize them or share a helper. `monkeypatch` restores the working directory after the scenario, so no later test runs from a removed directory. The Then "the read is rejected because the directory it is working in is gone" asserts the one fault's rule and that its message says the working directory is gone. The Then "the client is given that refusal as it is given any other fault, the call never breaking off" asserts the answer is a response carrying a fault, not an exception.

**Decisions already made:** the spec settles both outcomes. The fault's exact wording is the implementer's, in the voice of the other store faults ("no store was found, neither above … nor named outright"), saying the working directory is gone. It names no path, since the directory has none any more.

**Reuse:** the When "the client reads the decision" (`_read_the_decision_from_here`), the Thens "the client is given the decision, from the store KB_ROOT names" and "no content comes back", and the fixtures `root` and `readied`.

- [ ] **Step 1:** Run `.venv/bin/python -m pytest -q -m slice-99` and confirm `5 failed` on `StepDefinitionNotFoundError`. `-m "slice-1.3 or slice-1.8 or slice-1.15 or slice-88"` gives `13 passed`.
- [ ] **Step 2:** Under bdd-red-green, row by row:
  - the refusal outside any store first;
  - then the refusal inside the store's directory;
  - then the never-an-exception scenario;
  - then the two `KB_ROOT` rows.

  Each is seen red on its own assertion (the `FileNotFoundError` escaping) before the change under `src/` that makes it green. A row green as soon as its steps exist is credited to the change that made it so, and logged.
- [ ] **Step 3:** The store-finding scenarios stay green. `.venv/bin/python -m pytest -q` gives `225 passed`. Every module is within its size limit.
- [ ] **Step 4:** Run the Review Focus probes 1 to 3 under `.superpowers/`, and log what each shows.
- [ ] **Step 5:** Checkpoint in the slice plan's log: the red runs, where the absence is found, the fault's wording, the probes and the suite's line. Set slice 99's Status to green, and commit.

## After the batch

- [ ] A whole-branch review on the most capable model, against this plan, CLAUDE.md and the spec. The reviewer runs the suite themselves. Its findings are logged, then fixed or ruled.
- [ ] Push `main`. A release carrying slice 99 is the user's decision (shopsystem-knowledge adrs/0006). Once it is tagged, shop-knowledge pins it and its slice 50.22 goes green.
