# kb batch 32 Implementation Plan: the kb.v2 identity skeleton

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Each task is one slice, implemented under shopsystem-bdd:bdd-red-green. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** the suite collects again, then kb names every artifact and type by an https IRI its client chose, through `kb.v2`, with a v1 store refused, an IRI kept for life, identity carried beside content, and creates in a set naming each other by IRI (slices 154 to 160).

**Architecture:** two enabling slices first: one gets the suite collecting again, and one splits `values.py` so the IRI conversions fit. Then the contract breaks once, in slice 156. `kb.proto` moves to package `kb.v2`, an artifact's id becomes the IRI its create carries, a create names the IRI of its type's version, and the type that describes types moves to `https://missingmass.io/kb/type`. Every step definition and the port's conformance tests move with it. Slices 157 to 160 build on that skeleton. This batch adds no new module. `keys.py` goes in slice 160.

**Tech Stack:** Python 3.11, grpcio/protobuf (`make contract`), SQLite, pytest-bdd 8.1, pytest-xdist.

**Spec:** `spec/index.md` (Constraints carried, Order of building), `spec/capabilities/{name-artifacts-and-items,define-a-type,change-the-store,name-what-is-asked-for,answer-a-damaged-file,hand-over-content,read-an-artifact,make-several-changes-in-one-go,export-and-import-a-store}.md`, `spec/decisions.md` (decision/0022, 0023, 0027, contract-v2, iri-grammar, type-of-types-iri, keys-in-a-set-dropped, pre-v2-stores-not-migrated, v1-store-cannot-be-moved, published-contract-v2, create-echoes-its-iri, removed-iris-may-be-reused, rules-for-iri-refusals). Slices: `docs/superpowers/plans/2026-09-24-kb-slices.md`, slices 154 to 160.

## Global Constraints

- Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.10.0/scripts
- One task per slice, in slice order. The plan holds no code. The implementer writes the steps and the code under bdd-red-green, after the red run.
- Each task has a `Review:` and a `Model:` line, and the controller dispatches by them. `Review: per-task` with `Model: opus` goes to a task that touches concurrency, the published contract, data integrity or moving stored data. `Review: batch-end` with `Model: sonnet` goes to every other task, and gets no task review because the batch's branch review covers it.
- CLAUDE.md's rules hold:
  - No module under `src/kb/` may pass 250 lines, and `servicer.py` (137 lines) must stay under 150.
  - Rule 1: no broad `except` outside `servicer.py`'s wrapper.
  - Rule 2: a request field becomes a value in `values.py` (or `signatures.py`) before anything else sees it.
  - Rule 6: only `names.py` decides what an artifact's or an item's name looks like, including an export file's place.
  - When a task changes what a module owns, it changes that module's row in CLAUDE.md's map too.
- The baseline at 1809133 (plan log) is 434 passed and 63 failed in 19 s, with 9 test modules not collected (ScenarioNotFound). The 28 K1 backup-and-restore runs (`@slice-149` to `@slice-153`) fail here and keep failing all through K2/K3, because K1 is built on another branch. They are not this batch's failures.
- At this batch's end, every scenario tagged `@slice-1` to `@slice-148` or `@slice-156` to `@slice-160` passes. Every failing test is then a scenario tagged `@slice-149` to `@slice-153` or `@slice-161` onward, or the published contract's rule-name test (slice 182, rule `differs`).
- No migration (decision/pre-v2-stores-not-migrated): a kb.v1 store is refused, never converted.

### Binding values, verbatim from the spec

- The constraint carried: "Every artifact, part and type is named by an https IRI: an artifact's is chosen by its client under its type's IRI and kept for life, a part's is its artifact's IRI and its place in it as a fragment, and a type's is any IRI its client chooses. kb never mints an artifact's IRI and holds no prefixes."
- The published contract: "`kb.proto` (package `kb.v2`) … the IRI of the type that describes types (`https://missingmass.io/kb/type`), kb's IRI grammar …"
- The IRI grammar, from name-what-is-asked-for's Implementation: "An IRI matches `https://<host>/<segment>(/<segment>)*`, the host `<name>(.<name>)*` in lower case and each segment `<name>(.<name>)*`, where `<name>` is `[a-z0-9]+(-[a-z0-9]+)*`, at most 512 characters; a type version's IRI is a type's IRI followed by `@<n>`; a part's is an artifact's IRI followed by `#<place>`."
- The rules, from decision/rules-for-iri-refusals: an IRI not of kb's grammar carries `locator`. An IRI not under its type's, or one already held, carries `identity`. A version not held carries `version`.
- The export layout, from export-and-import-a-store's Implementation: "`<dir>/<host>/<segment>/.../<segment>.yaml`, one file per artifact, its place the host and path of its IRI; each held version of a type at the place of the type's IRI followed by `@<n>`, so the type that describes types is at `<dir>/missingmass.io/kb/type@1.yaml`."
- The canonical identity keys, from the same Implementation: "identity keys first, in the order `id` (the IRI), the type version's IRI, `revision`, `title`".

## Decisions this plan takes

Each decision rests on the line or ledger entry named, so that the implementer does not decide it alone.

1. **Wire names (Implementation; decision/contract-style-in-behaviour).**
   - `Locator.id`, `Created.id`, `Artifact.id` and `Stub.id` carry the IRI.
   - `CreateRequest` (and each create of `BatchCreateRequest`) carries `id` (the artifact's IRI) and `type` (the IRI of the type version).
   - `Artifact`, `Stub` and `Entry` replace `kind` and `schema_version` with `type`, the IRI of the version the artifact conforms to.
   - A field a request names a kind by (List, Search, Follow, link `targets`) carries the type's IRI and no version.
   - Removed field numbers are `reserved`.
   - The golden file becomes `tests/contract_v2.golden`, pinned by the descriptor test, which is renamed for v2.
2. **A version's place in the content.** The canonical identity keys are `id`, `type` (the version's IRI), `revision` and `title`, in that order. The settled keys (`settled.py`) are those four, so `schema_version` is gone from content too.
3. **The type that describes types** is the artifact at `https://missingmass.io/kb/type`, its version `https://missingmass.io/kb/type@1`. A new store writes it on start. `names.TYPES`/`schema` and `values.TYPE_KIND` give way to it.
4. **A type's versions in slice 156.** kb holds one version of each type, the one the type stands at. A create names that version's IRI. A create naming any other version, or a type not held, is refused with rule `version`, naming the version back (Implementation: "a version the store does not hold carries rule `version`"). Several held versions and kb's own numbering come in slices 161 to 163. Tagged scenarios that move a type on keep doing it as they do today, through the `next_version` helper in `tests/calls.py`.
5. **A `kb:` reference in slice 156** names a type version's IRI (`kb:<type IRI>@<n>`). It resolves only to the version held. Several versions come in slice 165.
6. **IRIs the steps use.**
   - Types sit at `https://shop.example/kb/<kind>`, with `work-item` for "work item", and so on.
   - An artifact a step creates without stating an IRI sits at `<type IRI>/<the slug its title gave before>`. Scenario text that says "the name the store gave" is unchanged and reads that IRI back.
   - A scenario that quotes an IRI uses it verbatim.
   - The IRIs come from `tests/calls.py` alone. No step module spells an IRI of its own except where a scenario quotes one.
7. **The store's marker** moves to `store: 2` in slice 156, because the database's identity columns change. In slice 157, `store: 1` is answered as an earlier kb's store (decision/v1-store-cannot-be-moved), and any other form stays a later kb's.
8. **A removed IRI's history** (slice 158; decision/removed-iris-may-be-reused). The new artifact starts at revision 1. `History` filtered by the IRI gives both lives' entries in the order they landed, as slice 87's freed name did.
9. **Nested type IRIs** (the QUESTION FOR THE SPEC in the plan log, recommended answer). An IRI belongs to the nearest type it sits under: the longest held type IRI that is a whole-segment prefix of it. A create naming a version of any other type is refused with `identity`. Slice 158 applies this to creates; slice 167 applies it to placeholders.
10. **Duplicate IRIs in a set** (slice 160). Two creates carrying one IRI are refused with rule `identity`, naming the IRI on each create after the first. This sits beside every other fault of the set, as the duplicate key was (decision/rules-for-iri-refusals).

## Review Focus

1. **A create whose IRI carries a fragment or a version** (`…/decision/a#steps/x`, `…/decision/a@2`) is refused with `locator`, because an artifact's IRI holds neither. Owner: Task 3, a plain test of the conversion.
2. **A create at exactly its type's IRI** (`https://shop.example/kb/decision` as a decision) is refused with `identity`, because it does not sit under the type. Owner: Task 5, a plain test through the contract.
3. **A create at an IRI a type is held at** (an artifact at a type's own IRI) is refused with `identity`, as any IRI already held is. Owner: Task 5, a plain test.
4. **A v1 store found through `KB_ROOT`, and found upward**, gives the same refusal. The old outline pinned both and the new scenario finds it one way. Owner: Task 4, a plain test.
5. **A create in a set that links to its own IRI** lands, the link resolving within the set. Owner: Task 7, a plain test.

QUESTION FOR THE SPEC (logged, recommended answer applied as decision 9). When one held type's IRI sits under another's, an IRI under both has two candidate types. Repro: define types at `https://example.com/shop/decision` and `https://example.com/shop/decision/minor`, then create a decision at `https://example.com/shop/decision/minor/a`.

---

### Task 1: Slice 154. The suite collects again and binds every scenario once

Review: batch-end
Model: sonnet
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.10.0/scripts

- [ ] **Check:** `make test` gives no collection error, `tests/test_every_scenario_is_bound.py` passes, and every failing test is a scenario tagged `@slice-149` to `@slice-153` or `@slice-156` onward, or `test_the_rule_names_kb_gives_are_exactly_the_spec_lists`.
- [ ] **Why it is red today** (suite record at 1809133):
  - Nine modules bind titles that the K2 formulation replaced: answer-a-damaged-file, add-an-item-to-a-collection, change-an-artifact, check-the-store, create-an-artifact, export-and-import-a-store, list-artifacts-of-a-kind, read-an-artifact and remove-an-artifact. pytest-bdd raises ScenarioNotFound on the first replaced title in each, for example "The client creates an artifact" and "A name that is not a plain name is refused".
  - In all, 38 titles were removed. The slice plan's log names the run, and `git diff 3d4cb20 1809133 -- features` shows them all.
  - `test_every_scenario_is_bound` fails both ways: titles bound and gone, and new titles unbound.
- [ ] **Where the change lands:** test modules only, nothing under `src/`.
  - Remove each `@scenario` binding of a removed title, and every step definition and helper only those bindings used.
  - Bind each new or retitled scenario once, in the module whose feature and steps it shares, as `scenarios(...)` or `@scenario` as that module does already. It then fails on missing steps until its slice.
- [ ] **Decisions applied:** none. Do not write a step a later slice will write. A binding is all this task adds.
- [ ] **Verify:** `make test` should collect every module. The failures are exactly the K1 runs (28), the scenarios tagged 156 to 185 that are now bound, and the rule-name test.
- [ ] **Checkpoint:** `plan status 154 green`, then `plan log "Suite: ..."` with the counts. That record is the baseline for Task 2.

### Task 2: Slice 155. values.py split before the IRI conversions grow it

Review: batch-end
Model: sonnet
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.10.0/scripts

- [ ] **Check:** `make test` gives the same passed and failed tests as slice 154's record. `wc -l src/kb/values.py` gives at most 200, and no module under `src/kb/` is over 250 lines.
- [ ] **Why it is red today:** `src/kb/values.py` is 241 lines (backlog, 2026-10-01). The IRI, type-version and set conversions that Tasks 3 to 7 add would push it past 250.
- [ ] **Where the change lands:**
  - Move the store-start and operator-directory values (`root`, `directory` and what only they use) into a new module that owns "the values a store's start and the operator's commands take: a root and a directory". `starting.py`, `operating.py`, `staging.py` and `cli.py` import it.
  - Add the module's row to CLAUDE.md's map, and narrow `values.py`'s row to match.
  - Nothing changes behaviour. Plain tests that import these names follow them.
- [ ] **Decisions applied:** none.
- [ ] **Verify:** `make test` gives slice 154's counts, and the `wc -l` above holds.
- [ ] **Checkpoint:** `plan status 155 green`, then `plan log "Suite: ..."`.

### Task 3: Slice 156. The client names its artifacts and types by IRI through kb.v2

Review: per-task
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.10.0/scripts

- [ ] **Scenarios** (`@slice-156`, 6 scenarios, 6 collected):
  - change-the-store / The client creates an artifact, giving its IRI and the IRI of the version of its type it conforms to
  - change-the-store / The client replaces an artifact
  - name-artifacts-and-items / An artifact created at an IRI of the client's choosing under its type's IRI is held at that IRI
  - define-a-type / The client defines a type, giving it an https IRI of kb's grammar
  - define-a-type / A type's IRI need not sit under the IRI of the type that describes types
  - define-a-type / The type that describes types is held at its own IRI
- [ ] **Why it is red today:**
  - The six have no steps.
  - Behind them, kb mints every id from a title. `values.named` and `names.written(kind, slug)` produce `<kind>/<slug>`.
  - `CreateRequest` carries `kind` and no id, and `Artifact`/`Stub`/`Entry` carry `kind` and an integer `schema_version` (kb.proto lines 64 to 230).
  - The type that describes types is `schema/schema`, from `names.TYPES` and `metaschema.py`.
  - Export places a file at `<kind>/<slug>.yaml` (`names.place`/`filed`).
- [ ] **Where the change lands:**
  - **The contract:** `src/kb/contract/kb.proto` moves to package `kb.v2` with decision 1's fields, and `make contract` regenerates the stubs. `tests/contract_v2.golden` and the renamed descriptor test pin it. `test_the_published_contract.py`'s version test reads v2.
  - **`values.py`:** gains the IRI grammar (one conversion each for an artifact's IRI, a type's IRI and a type version's IRI) and a locator whose id is an IRI. This is rule 2, implemented once. It returns `locator` on a fault of the grammar's shape. The full grammar outline is slice 178's (batch 36), but the conversion is this task's.
  - **`names.py`:** owns how an IRI is split into host and segments, the export place (the layout under Binding values, `@<n>` for a type version), and `filed` read back from a place. This is rule 6. Minting from a title stays for items only.
  - **Identity:**
    - `settled.py` takes decision 2's keys.
    - `requests.py` and `changes.py` build a create from the IRI and the version IRI.
    - `drafting.py`/`edits.py` take the create's IRI as its name and the named version (decision 4).
    - `composition.py`/`validation.py` resolve `kb:` references by version IRI (decision 5).
    - `metaschema.py` and `starting.py` write the type that describes types at decision 3's IRI.
    - `store.py` sets `STORE_FORM = 2` (decision 7).
    - The SQLite adapter keeps the IRI and the version IRI in place of kind and version. `sqlite_store.py` is at 221 lines, so if a column change would cross 250, split it first within this task, under the CLAUDE.md rule.
  - **Reads and queries:** `read.py`, `query.py` and `search.py` give `type` and take a kind as a type's IRI.
  - **Export and import:** `export.py`, `offers.py` and `importing.py` place and read files by `names.py`'s IRI layout, so the tagged export, import and seeding scenarios stay green.
  - **Tests:** every step module and `tests/calls.py` move to decision 6's IRIs, and `test_the_storage_port.py`'s conformance tests move to IRIs.
  - Update CLAUDE.md's rows for every module whose ownership changes: `names.py`, `settled.py`, `metaschema.py`, `values.py`, `export.py`, `offers.py`.
- [ ] **Decisions applied:** 1, 2, 3, 4, 5, 6, 7. Review Focus 1 is pinned here by a plain test of the conversion.
- [ ] **Steps to reuse:**
  - "a store holding a decision type whose artifacts require a purpose then a rationale, …" through `tests/calls.py`'s `tagged_decision_type`/`define`/`creating`/`created`, which now take IRIs.
  - `read(client, iri, whole=True)` for "reading it back".
  - The change-the-store revision steps of the old "The client changes an artifact" binding, for "The client replaces an artifact".
- [ ] **Verify:**
  - `.venv/bin/python -m pytest -q -m slice-156` gives 6 passed.
  - `make test` passes every scenario tagged `@slice-1` to `@slice-148` and `@slice-156`, and the plain tests. Every other failure is a scenario of a later slice, a K1 run, or the rule-name test.
- [ ] **Checkpoint:** `plan status 156 green`, then `plan log "Suite: ..."`.

### Task 4: Slice 157. A store made before kb.v2 is refused

Review: per-task
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.10.0/scripts

- [ ] **Scenarios** (`@slice-157`, 1 scenario, 1 collected): answer-a-damaged-file / A store found that was made by a kb before contract v2 refuses every call and command that needs it.
- [ ] **Why it is red today:**
  - The scenario has no steps. The old outline's steps, for "made by an earlier kb in a form this kb cannot read", were bound to the removed title.
  - After Task 3, a marker of `store: 1` is a form this kb does not know, so `store.py` would raise `LaterKb` ("a later version of kb is needed").
  - `refusals.earlier_kb` still advises importing the old store's files, which decision/v1-store-cannot-be-moved supersedes.
- [ ] **Where the change lands:**
  - `src/kb/store.py`: the marker check tells `store: 1` (and the older `contract` marker) apart as `EarlierKb` before anything is opened.
  - `src/kb/refusals.py`: `earlier_kb`'s message says the store was made by an earlier kb that this kb cannot read or move, with no advice to import. The rule stays `unreadable`.
  - Update CLAUDE.md's `store.py` row.
- [ ] **Decisions applied:** 7. Review Focus 4 is pinned here by a plain test, with the store found through `KB_ROOT` and found upward.
- [ ] **Steps to reuse:**
  - The answer-a-damaged-file steps for a store "made by an earlier kb" (write a kb.v1 marker and database beside a store's files).
  - "nothing is written in the store".
  - "what was asked is rejected because …".
- [ ] **Verify:** `.venv/bin/python -m pytest -q -m slice-157` gives 1 passed, and `make test` shows no new failure.
- [ ] **Checkpoint:** `plan status 157 green`, then `plan log "Suite: ..."`.

### Task 5: Slice 158. An artifact's IRI is its own for life

Review: per-task
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.10.0/scripts

- [ ] **Scenarios** (`@slice-158`, 8 scenarios, 8 collected), all name-artifacts-and-items:
  - An artifact created at an IRI not under its type's IRI is refused
  - An artifact created at an IRI the store already holds an artifact at is refused
  - An artifact keeps the IRI it was created with for life
  - After an artifact has been removed, a new artifact may be created at its IRI
  - A title that reads as a date is still a title
  - A title that reads as yes is still a title
  - A title given as the yes-or-no true is still a title
  - A title given as the number 12 is still a title
- [ ] **Why it is red today:**
  - None has steps.
  - After Task 3, a create takes its IRI, but nothing checks the IRI against its type, and the draft cannot hold two artifacts at one IRI. A create at a held IRI would fall to the port's write and fail as `unreadable` or be taken over.
  - The title scenarios lost their "name made from that text" Then lines, so they only need steps on the IRI create.
- [ ] **Where the change lands:**
  - `src/kb/edits.py` (a create's IRI checked to sit under the nearest type, decision 9, and not held in the draft).
  - `src/kb/refusals.py` (the two `identity` faults, naming the IRI).
  - `src/kb/sqlite_store.py`/`sqlite_checks.py`, if a removed IRI's rows block a new artifact there (decision 8).
  - `names.py` alone answers "is this IRI under that type's" (rule 6).
- [ ] **Decisions applied:** 8, 9. Review Focus 2 and 3 are pinned here by plain tests through the contract.
- [ ] **Steps to reuse:**
  - Task 3's "a store holding a decision type at …" and "the decision is held at …".
  - "nothing is written".
  - The remove steps of remove-an-artifact.
  - The old title-coercion steps of slices 1.5, 1.18 and 1.25 in `tests/test_create_an_artifact.py`, less the name assertion.
- [ ] **Verify:** `.venv/bin/python -m pytest -q -m slice-158` gives 8 passed, and `make test` shows no new failure.
- [ ] **Checkpoint:** `plan status 158 green`, then `plan log "Suite: ..."`.

### Task 6: Slice 159. An artifact's identity travels beside its content

Review: per-task
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.10.0/scripts

- [ ] **Scenarios** (`@slice-159`, 3 scenarios, 3 collected):
  - hand-over-content / Content given to a create that carries what travels beside it is refused
  - read-an-artifact / Reading the whole artifact gives its IRI, its type version's IRI, its revision and its title beside its content
  - read-an-artifact / A link filled in comes with its IRI, its type version's IRI, its title and its revision, ahead of its content
- [ ] **Why it is red today:**
  - None has steps.
  - The hand-over scenario now names the IRI, the type version and the revision. The old one named the name and the version.
  - The read scenarios ask for the type version's IRI, which `read.py`'s filled-in target and `Artifact` give as Task 3 left them. That may already hold, so the red run says.
- [ ] **Where the change lands:**
  - `src/kb/values.py`/`settled.py` refuse content carrying `id`, `type` or `revision` (decision 2), each named back, with the rule the old scenario's refusal carried.
  - `src/kb/read.py` gives a filled-in target `id`, `type`, `title` and `revision` ahead of its content, in the canonical order.
- [ ] **Decisions applied:** 2.
- [ ] **Steps to reuse:**
  - The slice 1.6 hand-over steps ("the artifact is rejected because content holds only what the type declares").
  - Slice 88's filled-in link steps in `tests/test_read_an_artifact.py`.
  - The read-an-artifact Background.
- [ ] **Verify:** `.venv/bin/python -m pytest -q -m slice-159` gives 3 passed, and `make test` shows no new failure.
- [ ] **Checkpoint:** `plan status 159 green`, then `plan log "Suite: ..."`.

### Task 7: Slice 160. Creates in a set name each other by their IRIs

Review: per-task
Model: opus
Scripts: /home/vscode/.claude/plugins/cache/shopsystem-bdd/shopsystem-bdd/0.10.0/scripts

- [ ] **Scenarios** (`@slice-160`, 5 scenarios, 7 collected), all make-several-changes-in-one-go:
  - A create in a set points at what another create in it makes, earlier or later (2 examples)
  - A link in a set to the IRI another create in it carries lands on what that create makes (2 examples)
  - Two new artifacts in one set that point at each other by their IRIs land
  - Two creates in one set that carry the same IRI are refused
  - Each create in a set gives back its artifact's IRI and first revision, in the order of the set
- [ ] **Why it is red today:**
  - Their steps are gone: the key steps of slice 121 bound the removed titles.
  - `BatchCreateRequest`'s create still carries `key` (kb.proto line 449), and `keys.py` rewrites `@<key>` links after every create has acted. Under Task 3, creates carry IRIs, so a key adds nothing (decision/keys-in-a-set-dropped).
  - Whether a link to a later create's IRI resolves depends on the draft holding every create before links are checked. `drafting.py` checks against the state the whole set leaves, so the red run will show it.
- [ ] **Where the change lands:**
  - The contract: the create's `key` field is removed and reserved, and the golden file is updated.
  - `src/kb/keys.py` is deleted, with its call in `drafting.py`.
  - `names.KEYED`/`keyed` and `values.key` are deleted.
  - `changes.py`'s duplicate-key check becomes the duplicate-IRI check (decision 10).
  - CLAUDE.md: remove the `keys.py` row, and update `changes.py`'s, `drafting.py`'s and `names.py`'s rows.
- [ ] **Decisions applied:** 1, 10. Review Focus 5 is pinned here by a plain test.
- [ ] **Steps to reuse:**
  - The make-several Background.
  - `create_many`/`created` in `tests/calls.py`, which take an IRI in place of a key.
  - "the store holds none of the changes in the set".
  - "the set is rejected because …".
- [ ] **Verify:**
  - `.venv/bin/python -m pytest -q -m slice-160` gives 7 passed.
  - `make test` passes every scenario tagged `@slice-1` to `@slice-148` and `@slice-156` to `@slice-160`. Every failure is a scenario tagged `@slice-149` to `@slice-153` or `@slice-161` onward, or the rule-name test.
- [ ] **Checkpoint:** `plan status 160 green`, then `plan log "Suite: ..."`.
