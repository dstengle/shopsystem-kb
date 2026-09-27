# kb Batch 19 Implementation Plan: slice 100, kb.content publishes the refusal of text kb cannot keep

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. One task, an enabling slice of `docs/superpowers/plans/2026-09-24-kb-slices.md`, verified by its check.

**This plan carries no code** (shopsystem-knowledge adrs/0011). It says what fails and why, where the change lands, and how to verify it.

**Goal:** everything kb publishes about content can be imported from `kb.content`, including `NotCanonical`, the refusal of text kb cannot keep, with the place it names (`path`). That gives a client (shop-knowledge, its slice 50.23) no reason to import `kb.canonical` (adrs/0018).

**Spec:** `docs/superpowers/specs/2026-09-23-kb-design.md`, the contract section as amended in 00710a6: "What a client may depend on is published and versioned with the contract: `kb.proto` and its messages, the in-process client's `connect`, `kb.content` (content as canonical text, and `NotCanonical`, the refusal of text kb cannot keep), and each fault's `rule` name." The decision is `adrs/0018-the-published-contract.md`. `CLAUDE.md` is binding.

## Global Constraints

- No feature file changes. `kb.proto` does not change. No behaviour changes.
- The suite gives `225 passed, 7 failed` today (run at `ac7c6dd`). The 7 failures are slice 102's rows, planned later. After the task the result is the same, plus the new surface test passing.
- Every rule in CLAUDE.md holds, and every module is within its size limit.
- Commit with `git -c user.name="David Stenglein" -c user.email=dave@missingmass.io commit`, ending the message with the model's Co-Authored-By line. The implementer does not push or tag.
- Scratch files go under `.superpowers/`.

---

### Task 1: Slice 100, kb.content publishes the refusal of text kb cannot keep

**Check** (from the slice plan):
- `.venv/bin/python -c "from kb.content import loads, dumps, text, NotCanonical; import kb.canonical; assert NotCanonical is kb.canonical.NotCanonical"` exits 0;
- a test of the published surface is in the suite and passes;
- CLAUDE.md's module map row for `content.py` names `NotCanonical`;
- the suite gives the same answer, with that test added.

**Why it fails today:**
- `kb.content` imports `canonical`, but it does not offer `NotCanonical` as a name of its own.
- Its docstrings say `loads` "Raises canonical.NotCanonical".
- No test pins what kb publishes.

**Where the change lands:**
- `src/kb/content.py` publishes `NotCanonical` as its own name. It stays the one class defined in `canonical.py`, not a copy, so `except kb.content.NotCanonical` catches what `canonical` raises.
- The docstrings of `loads` and `dumps` say what they raise under their published name. `dumps` raises it for content kb cannot keep, such as prose with a line ending in a space before its last.
- The surface test lives in the one test module that tests the published surface. Add one if none exists, named for what it pins. CLAUDE.md says tests use "the contract or the module's public functions", and this test is exactly that. It pins:
  - `kb.content`'s `loads`, `dumps`, `text` and `NotCanonical`;
  - that `NotCanonical` has `path`;
  - `kb.client.connect`;
  - `kb.contract.kb_pb2`'s being importable.

  It does not pin the wording of any fault.
- In CLAUDE.md's module map, the `content.py` row reads "artifact content crossing the contract as canonical text, and `NotCanonical`, the refusal of text kb cannot keep: what kb publishes about content (adrs/0018)".

**Steps:**
- [ ] **Step 1:** Run the check's `python -c`, and see it fail on the import. Log it.
- [ ] **Step 2:** Make the change and add the surface test. Run `python -c` again, and the new test, both passing.
- [ ] **Step 3:** Run the suite and get `226 passed, 7 failed` (or the count with the new test), with the same 7 failing. Run the size check.
- [ ] **Step 4:** Checkpoint in the slice plan's log, set slice 100's Status to green, and commit.
