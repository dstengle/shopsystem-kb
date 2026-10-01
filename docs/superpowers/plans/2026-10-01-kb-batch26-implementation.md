# kb batch 26 Implementation Plan: the type language narrowed to where kb reads it

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Each task is one slice, implemented under shopsystem-bdd:bdd-red-green. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** kb's own keywords (`ref`, `parts`, `sections`, `summary`) are accepted in a type only where kb reads them, and a `ref` states its whole shape (slice 125); every refusal and every check gives its faults in kb's order, as the artifact reads back and then by rule name (slice 126); the type of types resolves the 2020-12 metaschema through a registry kb builds itself (slice 127). Slice 124 (answer-a-damaged-file collapsed, the boundary table) is already green and is reviewed with this batch; it has no task.

**Architecture:** a type is still checked once, as it is written, in `definitions.py`, called from `drafting.py` for the last change a set makes to a type and from `importing.py` for a type file. The walk that finds where kb's keywords stand in a type is a new concern and gets a new module. Fault order is a new concern and gets a new module, which takes its positions from `settled.py`'s order, so the order an artifact reads back in and the order its faults come in cannot drift apart. The metaschema registry stays in `validation.py`, which already builds the registry types resolve through.

**Tech Stack:** Python 3.11, jsonschema 4.26 with referencing 0.37 and jsonschema-specifications 2025.9.1 (installed, not yet declared), pytest-bdd 8.1, pytest-xdist.

**Spec:** `spec/capabilities/define-a-type.md`, `check-a-change.md`, `check-the-store.md`, `make-several-changes-in-one-go.md`; `spec/index.md`; `spec/decisions.md` decision/type-language-stays-json-schema, decision/kb-keywords-read-where-written, decision/metaschema-from-a-registry-of-kbs-own, decision/faults-ordered-by-reading-order-then-rule-name (which supersedes decision/faults-ordered-by-place-then-rule), decision/no-held-types-before-the-placement-rule (266b48e: no held types to carry; a type is checked against the placement rule whenever it is written), decision/links-read-only-where-kb-reads-them-today (a link field in a named shape is refused), decision/a-types-faults-in-the-order-it-was-written (a type's faults in the order it was written); note `docs/superpowers/specs/2026-10-01-kb-type-language-design.md`. Slices: `docs/superpowers/plans/2026-09-24-kb-slices.md`, slices 125, 126, 127.

## Global Constraints

- One task per slice, in slice order. The plan holds no code: the implementer writes steps and code under bdd-red-green, after the red run.
- The controller dispatches each task by its `Review:` and `Model:` lines: 125 is reviewed per task on opus (it adds a published rule name); 126 and 127 are reviewed at batch end on sonnet.
- CLAUDE.md holds: no module under `src/kb/` over 250 lines, `servicer.py` under 150; a change that would cross a limit splits first, inside the task. `values.py` is at 241 lines and must not grow (backlog: shrink it before anything adds to it); nothing in this batch needs it. A new module gets its row in CLAUDE.md's module map in the same task.
- Rule 1 (fail-closed boundary) is untouched: no new module catches broad exceptions. Rule 6 is untouched: no new module decides a name.
- Verification in every task: the slice's marker during red-green; `make test` (parallel) once before the slice's last commit.
- Baseline: at HEAD 36f9b5b `make test` gave **496 passed, 19 failed**; at HEAD 266b48e (define-a-type's two held-type scenarios removed) it gives **496 passed, 17 failed**. The 19 were:
  - 14 slice-125 scenarios in `tests/test_define_a_type.py`, each failing on `StepDefinitionNotFoundError`: A link field declared where kb does not read one is refused; Collections ...; Required sections ...; Fields shown at a glance ...; A link field that leaves out part of what it must say is refused (3 examples); A link field whose removal rule is not refuse is refused; A link field that points at neither one artifact nor several is refused; A type may use any keyword that is not kb's own (3 examples: enum, pattern, format); A held type that carries a keyword where kb does not read it stays as it is; Changing a held type that still carries a keyword where kb does not read it is refused. The last two are removed from the spec and the feature at 266b48e, leaving 12 of these, and 17 failures.
  - 3 slice-126 scenarios with no steps: define-a-type's A type refused with several faults ...; make-several-changes-in-one-go's A change in a set refused with several faults ... and Faults of several refused changes in a set come in the order of the set.
  - `tests/test_every_scenario_is_bound.py::test_every_scenario_formulated_in_the_features_is_bound_by_a_test_module`: check-a-change's and check-the-store's slice-126 scenarios are bound by no test module.
  - `tests/test_the_published_contract.py::test_the_rule_names_kb_gives_are_exactly_the_spec_lists`: `spec/index.md` lists `placement`, `rules.ALL` does not.

### Binding values, verbatim from the spec

- kb's own rule names (`spec/index.md`): `not-found`, `kind`, `locator`, `collection`, `identity`, `on_delete`, `unreadable`, `item-name`, `shape`, `built-on`, `targets`, `version`, `content`, `sections`, `ref`, `actor`, `message`, `operations`, `since`, `title`, `root`, `store`, `clock`, `busy`, `revision`, `placement`.
- Where kb reads its keywords (define-a-type, Implementation): "kb reads `ref` only on a field directly under `properties` of the type's own schema, of a base it is built on, or of the `items` of any of its collections at any depth; `parts` and `summary` only at the top of a type's schema or at the top of a collection's `items`; `sections` only at the top of a type's schema. Anywhere else each is refused, naming the place. The `parts` inside a `ref` is the ref's own and is never refused as a misplaced collection."
- A `ref`'s four keys (define-a-type, Implementation): "A `ref` carries all four of `targets` (a list of kinds), `cardinality` (`one` or `many`), `parts` (yes or no) and `on_delete` (`refuse`, the one rule kb knows), or the type is refused."
- A named shape (decision/links-read-only-where-kb-reads-them-today): a link field "in a named shape another field uses is refused like any other misplaced link field".
- Rules of these refusals (define-a-type, Implementation): "a misplaced `ref`, a `ref` missing part of its shape, and a `ref` whose `cardinality` or `on_delete` kb does not know carry `ref`; a `ref` without `targets` keeps `targets`; a misplaced `parts`, `sections` or `summary` carries `placement`."
- No held type is provided for (decision/no-held-types-before-the-placement-rule): "a type is checked against the placement rule whenever it is written".
- The fault order (`spec/index.md`): "Errors are a typed list of `{ artifact, place, rule, message }`, each artifact's faults in the order of their places in it as it reads back (the order its type declares), then, at one place, by the alphabetical order of their rules' names." Across a set (decision/faults-ordered-by-reading-order-then-rule-name): "across the changes of a set, the order of the set." A type (define-a-type): "they are given in the order its places stand in the type as it reads back, which is the order the client wrote it in, and faults at one place come in the alphabetical order of the names of the rules they break."

## Decisions this plan takes (the Behaviour leaves them open)

1. **The place of a misplaced keyword is the keyword itself**, written as definitions.py writes places today: `schema/` then the path of keys and indices, e.g. `schema/properties/when/sections`, `schema/parts/options/items/sections`, `schema/oneOf/0/properties/about/ref`. Rests on the existing `$ref` faults, which name the keyword (`schema/allOf/0/$ref`, `schema/properties/bindings/items/$ref`).
2. **The place of a `ref` that leaves out or misstates part of its shape is the field**, `schema/properties/<name>` (or the item field's path), as the `targets` fault is today (`schema/properties/relates_to`, slice 68). So a field breaking two link rules has two faults at one place, which is what define-a-type's slice-126 scenario orders.
3. **"The top of a schema" is the schema and each of its `allOf` members, recursively**, as `composition.composition` reads them; "the top of a collection's items" is `parts/<c>/items` and its `allOf` members. Rests on define-a-type's Implementation, "A type built on a base is written `allOf: [{ $ref: kb:schema/<base> }, { ...its own fields }]`", and on kb reading `properties`, `parts` and `summary` through that composition today. `oneOf`, `anyOf`, `not`, `if`/`then`/`else`, `$defs` (decision 4), `items` of an array field, `additionalProperties`, `patternProperties`, `dependentSchemas`, `prefixItems`, `contains` and a field's own nested `properties` are not a top: a kb keyword there is refused.
4. **A named shape is not a place kb reads.** A `ref` anywhere under `$defs`, at any depth, is a misplaced link field: rule `ref`, at the keyword's place (e.g. `schema/$defs/binding/properties/d/ref`). Rests on decision/links-read-only-where-kb-reads-them-today.
5. **Only schema positions are walked.** A kb keyword is found only as a key of a mapping that stands where JSON Schema 2020-12 puts a schema (or of a collection's `items`). A field *named* `ref`, `parts`, `sections` or `summary` (a key of `properties`, `$defs` or `patternProperties`), and anything inside a value keyword (`enum`, `const`, `default`, `examples`, `required`, a `sections` tree, a `summary` list, a `ref` mapping, an unknown keyword's value) is never a kb keyword. Rests on "A type may use any keyword of JSON Schema 2020-12 that is not one of kb's own, anywhere in its schema".
6. **A misplaced `ref` is refused for its place alone**: its shape is not checked, since kb does not read it. A placed `ref` that is not a mapping, or has no `targets`, keeps today's single `targets` fault (slice 68 unchanged). A placed `ref` with `targets` gives one `ref` fault naming every one of `cardinality`, `parts`, `on_delete` it leaves out; one `ref` fault when `cardinality` is present and not `one` or `many`; one `ref` fault when `on_delete` is present and not `refuse`. A `parts` present and not true or false is "not saying whether it may point into a part" (the leave-out fault).
7. **Rules and message openings.** Misplaced `ref`: rule `ref`, message opening "kb does not read a link field there". Misplaced `parts`, `sections`, `summary`: rule `placement`, message opening "kb does not read" and naming the keyword and its place (the scenarios' "kb does not read them there" is read as that opening plus rule `placement`). Leave-out: rule `ref`, opening "a link field says which kinds it may point at, whether it points at one artifact or several, whether it may point into a part and what a removal does". Removal rule: rule `ref`, opening "refuse is the one removal rule kb knows". Cardinality: rule `ref`, opening "a link field points at one artifact or several". The `targets` fault keeps "a link field says which kinds it may point at" (the leave-out opening shares this prefix; slice 68's step asserts the rule too, so they stay apart).
8. **The placement rule checks the type's own document only**, each time it is written. A base is a type of its own, checked when it is written, so a type built on it is not walked into it. A collection's items given by a whole `$ref` to a type are not walked into that type either. Rests on "a type is checked against the placement rule whenever it is written" (decision/no-held-types-before-the-placement-rule).
9. **Every path that writes a type checks it**: a `Create`, a `Replace` (the last change a set makes to a type, as `drafting._faults` checks it today) and a type file offered for import (`importing._faults`). No test sets up a type carrying a misplaced keyword behind the store's back (no line asks for one).
10. **`check.py` does not check types against the placement rule**: every type in a store was checked when it was written.
11. **Order of places.** A place's position is its position in the artifact as `settled.py` orders it to be written: identity keys, fields in the order the type declares them (bases first), other fields as written, `sections`, collections in declared order; an item's `id`, then its fields in its item schema's order, then the rest; a section's `title`, `body`, then its `sections`. A list's entries by their index as a number (`options/2` before `options/10`). The whole artifact (place `""`) comes first, and a node comes before the places inside it (`sections` before `sections/0`, a section before its inner sections). A place naming an entry the artifact lacks stands where the type would put that entry; one the type does not declare stands after the entries present at its level, by its name. Rests on "the order its type declares, which is the order the store writes it in" (check-a-change, Implementation).
12. **A type's places stand in the order the type was written in**, which is how it reads back: `title`, `version`, `schema` as the type of types declares them, and inside `schema` every mapping and list in the order the client wrote it. No declared order is imposed inside `schema`. Rests on decision/a-types-faults-in-the-order-it-was-written.
13. **Rule order at one place is case-insensitive alphabetical**, ties broken by the name as written, then by message text, so faults with one rule at one place are still in a fixed order. Rests on "the alphabetical order of the names of the rules they break" (`maxLength` before `pattern`; `minimum` before `minLength`).
14. **The order is applied per artifact, never across the refusal**: to each change's faults in `drafting.py` before the set is refused (so the set's order holds between changes), and to each artifact's violations in `check.py`. Faults made by converting a request (`changes.py`, `requests.py`, `signatures.py`) are not reordered. The import report keeps its order (no line names it).
15. **The metaschema registry** is the nine 2020-12 resources of `jsonschema_specifications` (the 2020-12 schema and its eight vocabulary metaschemas: applicator, content, core, format-annotation, format-assertion, meta-data, unevaluated, validation), put into the registry kb hands the validator beside its `kb:` retrieval. `jsonschema-specifications>=2025.9.1` is declared in `pyproject.toml`. "The library's own retrieval turned off" is shown in the test by replacing `jsonschema.validators.SPECIFICATIONS` with an empty registry for the test, since the validator otherwise combines it with any registry it is given.

## Questions for the spec

None open. The two raised while planning are decided (decision/links-read-only-where-kb-reads-them-today; decision/a-types-faults-in-the-order-it-was-written) and are folded into decisions 4 and 12.

## Review Focus

Five input classes the spec implies, no scenario exercises, and most likely to bite. Each line names the task that owns the code and the test that pins it, as an intent.

1. **kb's keyword names as data.** A field named `summary`, `parts`, `sections` or `ref` in a nested object; `enum: [ref, parts]`; a `default` or `examples` value holding a mapping with a `ref` key; a `ref`'s own `parts`; a `sections` tree's inner `sections`. None is refused. Owner: Task 1. Test intent: a type carrying each of these in a nested field is accepted and an artifact of it can be created.
2. **`allOf` against the other branches.** `ref`, `parts`, `summary` under a top `allOf` member (the spec's own form for a type built on a base, `allOf: [{ $ref: kb:schema/<base> }, { ...its own fields }]`) are accepted and read as links, collections and stub fields; the same under `oneOf`, `anyOf`, `not`, `if`/`then`/`else`, a nested field's `allOf`, or `$defs` of a nested field are refused at the keyword's place; `sections` under a collection's items, or under its items' `allOf`, is refused. Owner: Task 1. Test intent: a table of (where the keyword stands, accepted or the expected place and rule), one row per position, including `ref` under `$defs/<shape>/properties` of the type and of a collection's items (refused, rule `ref`), through `Create` of a type; for each accepted `ref` row, an artifact whose link there points at nothing is refused with `ref`, proving kb reads it.
3. **Collections at depth.** `ref` and `summary` at the top of the items of a collection inside a collection's items (`parts/a/items/parts/b/items/...`) are accepted and read; `sections` there is refused; a collection's items given by a whole `$ref` to a type are not walked into (decision 8); the `items` of an ordinary array field is not a collection's items, so a `ref` under `properties/tags/items` is refused. Owner: Task 1. Test intent: one type with two levels of collections, accepted, and an item two levels down whose link points at nothing refused with `ref` at `a/0/b/0/<field>`; one type with `ref` under an array field's `items`, refused at `schema/properties/tags/items/ref`.
4. **Places inside items, nested sections, and absent places.** `options/10/title` after `options/2/title` (numbers, not text); `sections/0/sections/1` after `sections/0/body` and before `sections/1`; a fault at `""` (a missing required field, an extra field under `additionalProperties: false`) first; a missing section at `sections` when the artifact has no `sections` key but has options; an added item's faults inside its artifact. Owner: Task 2. Test intent: one artifact, written in reverse order, with faults at each of these places, refused through `Create` and reported by `Check`, its faults equal to the expected list in order.
5. **A `ref` that is both misplaced and malformed, and slice 68 unchanged.** A nested `ref` with no `targets` and `cardinality: two` gives exactly one fault, `ref` at the keyword (decision 6), not `targets`; a placed `ref` with no `targets` still gives exactly one `targets` fault at the field; a placed `ref` with neither `targets` nor `cardinality` gives `ref` then `targets` at the field. Owner: Task 1 (faults), Task 2 (their order). Test intent: three type definitions, each refused with the exact list of (place, rule).

---

### Task 1: Slice 125 — kb's keywords are read only where kb reads them, and a link field states its whole shape

Review: per-task
Model: opus

- [ ] **Scenarios** (define-a-type, `@slice-125`, 12 collected at 266b48e): A link field declared where kb does not read one is refused; Collections declared where kb does not read them are refused; Required sections declared where kb does not read them are refused; Fields shown at a glance declared where kb does not read them are refused; A link field that leaves out part of what it must say is refused (whether it points at one artifact or several; whether it may point into a part; what a removal does); A link field whose removal rule is not refuse is refused; A link field that points at neither one artifact nor several is refused; A type may use any keyword that is not kb's own, anywhere in its schema (enum, pattern, format). The slice's two held-type scenarios were removed from the spec and the feature at 266b48e and are not part of this task. Needs: the published-contract test's rule list gains `placement`.

- [ ] **Why each is red today** (run: `.venv/bin/pytest -q -m slice-125`, 12 failed, all `StepDefinitionNotFoundError`). Probed at HEAD with the steps' intended types:
  - The four misplacement scenarios: `definitions.faults` checks only `$ref` targets and that a `ref` has `targets`; it has no notion of where a keyword stands. A type with `ref`, `parts`, `sections` or `summary` inside a field's nested schema, or `sections` in a collection's items, is accepted.
  - The three leave-out scenarios, removal rule and cardinality: `definitions._link_fields` checks only that `ref` is a mapping holding `targets`. A `ref` with `cardinality: two`, `on_delete: cascade` and no `parts` is accepted.
  - Any keyword not kb's own: accepted today; red only for missing steps, and stays green only if the placement walk respects decision 5.
  - `rules.py` has no `PLACEMENT`, so the published-contract test fails.

- [ ] **Where the change lands.**
  - Split first: `refusals.py` is 222 lines and this task adds five refusals of a type (about 40 lines). Move the refusals of a type as it is written (`no_such_shape`, `built_on_itself`, `no_targets`, `version_kept`) into a new module that owns them, its CLAUDE.md row added; suite green before anything is added. The new refusals go there.
  - `rules.py`: `PLACEMENT = "placement"` (`rules.ALL` picks it up).
  - New module for where kb reads its keywords in a type: the walk of schema positions (decisions 3, 4, 5) that gives each place a kb keyword stands at and whether kb reads it there. CLAUDE.md row: "where kb reads its keywords in a type, and every place one of them stands; never checks, faults or file access". It reads no store and takes plain dicts.
  - `definitions.py` (69 lines): calls the walk; a misplaced keyword becomes its fault; a placed `ref` is checked for its four keys (decision 6); `_link_fields` (every depth) is replaced by the walk's placed `ref`s. It stays the one place a type is checked as written; `drafting.py` and `importing.py` are unchanged.
  - Rules implemented once: rule 4 (draft, validate, land) as it stands, since the refusal comes from the draft before the port; the published-contract rule list.
  - Tests: steps in `tests/test_define_a_type.py`; the Review Focus tests owned by this task (1, 2, 3, and 5's faults) in a new test module using `calls` helpers.

- [ ] **Decisions this task applies:** 1, 2, 3, 4, 5, 6, 7, 8, 9, 10.

- [ ] **Steps and fixtures to reuse** (`tests/test_define_a_type.py`, `tests/calls.py`, `tests/held.py`, `tests/conftest.py`):
  - Background "a store" (conftest, fixture `client`).
  - The When pattern of `_define_a_type_never_checkable`: return the dict `{"response", "before", "after"}` built with `held.holds(root)`, so `_nothing_written` ("nothing is written anywhere in the store") is reused unchanged; `_type_rejected(attempt, rule, path, message)` for each single-fault Then.
  - "artifacts of that type can be created" (`_create_a_note`) creates a `note` with `NOTE_TYPE`'s content: the "any keyword" When defines `NOTE_TYPE` with one extra optional nested object field using the keyword, so the existing Then holds.
  - `calls.request`, `calls.define`, `calls.read`, `calls.DECISION_TYPE`, `NOTE_TYPE`, `LINK`.
  - New: "the refusal names the place" (one step reading the expected place from the When's fixture), the five "the type is rejected because ..." Thens, and "the type is accepted".

- [ ] **Verification.**
  - Red: `.venv/bin/pytest --collect-only -q -m slice-125` gives 12; `.venv/bin/pytest -q -m slice-125` gives 12 failed before steps, then each red for the reason above once its steps exist.
  - Green: `.venv/bin/pytest -q -m slice-125` gives 12 passed; `.venv/bin/pytest -q -m slice-68` still passes (the `targets` fault unchanged).
  - Once before the last commit: `make test` gives 4 failed (the 3 slice-126 scenarios without steps and the bound-scenario guard), every other test passing: 509 passed plus this task's new tests (513 collected at 266b48e). `wc -l src/kb/*.py` shows nothing over 250.

- [ ] **Checkpoint** (append to the slices plan's Log, and set slice 125's Status to green): "- 2026-10-01 slice 125 green. Someone can now: define a type and be told, naming the place, when one of kb's keywords stands where kb would never read it or a link field leaves out part of its shape; the published rule names gain `placement`. Surprised by: <...>. Open questions: none. Next: slice 126." Set slice 125's Scenarios line to the 12 scenarios the feature now holds.

---

### Task 2: Slice 126 — Faults come in kb's order: as the artifact reads back, then by rule name

Review: batch-end
Model: sonnet

- [ ] **Scenarios** (`@slice-126`, 5 once bound): check-a-change / An artifact refused with several faults has them given in the order its places stand when it reads back; check-the-store / An artifact's violations are given in the order its places stand when it reads back; make-several-changes-in-one-go / A change in a set refused with several faults has them given in the order its places stand when its artifact reads back; Faults of several refused changes in a set come in the order of the set; define-a-type / A type refused with several faults has them given in the order its places stand when it reads back. Needs: Task 1's refusals of a type.

- [ ] **Bind first.** check-a-change and check-the-store bind scenarios one by one: add an `@scenario` for check-a-change's in `tests/test_create_an_artifact.py` (beside the other check-a-change bindings) and for check-the-store's in `tests/test_check_the_store.py`. define-a-type and make-several-changes-in-one-go use `scenarios(...)` and are bound already. The bound-scenario guard then passes.

- [ ] **Why each is red today** (run: `.venv/bin/pytest -q -m slice-126`, 3 collected and failed on missing steps before binding). Probed at HEAD with a decision type whose `status` field is written `pattern` then `maxLength`, and a decision written options, sections, then fields, with `status: Not-Lower-Case`, option 2's title a number and no Rationale:
  - check-a-change: faults come as `status pattern`, `status maxLength`, `options/1/title type`, `sections sections`: the library's order (schema keyword order), then kb's section faults, then links (`validation.validate`'s order). Both the place order (options before sections) and the rule order (pattern before maxLength) are wrong.
  - check-the-store: the same order for a planted decision; `check.everything` returns `validation.validate`'s list as it is.
  - A change in a set: the same order, inside `drafting._drafted`, which joins each change's faults in set order without reordering them.
  - Faults of several refused changes in a set: already in set order today (`decision/a` then `decision/b`); red only for missing steps. It must stay green: the order is applied per change, never across the refusal (decision 14).
  - define-a-type: the faults come in `definitions.faults`' walk order (its keyword walk, then its link-field checks), not the order the type was written in; the step writes the type so the two differ (e.g. the field with nested sections before the link field, and the collection last), and expects the written order, then `ref` before `targets` at the link field.

- [ ] **Where the change lands.**
  - New module owning the order faults are given in: the position of a place in an artifact (decision 11), and an artifact's faults sorted by position then rule name (decision 13). CLAUDE.md row: "the order an artifact's faults are given in: as it reads back, then by rule name; never makes or checks faults". Positions come from `settled.py`'s order of an artifact's entries; if `settled.py` must expose that order for a place without the identity keys present, the function goes in `settled.py` (84 lines), which owns "the order its entries are written in as its type declares".
  - `drafting.py` (150 lines): each change's faults put in order before the set is refused, read through the type the change is checked against (for a type, the type of types). `check.py` (22 lines): each artifact's violations put in order.
  - Rules implemented once: the fault order, in the one new module, used by both callers.
  - Tests: steps in `tests/test_create_an_artifact.py`, `tests/test_check_the_store.py`, `tests/test_make_several_changes_in_one_go.py`, `tests/test_define_a_type.py`; Review Focus test 4 and the order part of test 5.

- [ ] **Decisions this task applies:** 11, 12, 13, 14. The decision type of the first three scenarios is one constant in `tests/calls.py` beside `DECISION_TYPE`: `DECISION_TYPE`'s fields, sections and options in that order, plus a field whose two constraints are written in reverse alphabetical order (e.g. `pattern` then `maxLength`), so the library's order and kb's differ. The "declares its fields first ..." Givens move the decision type on to it with `next_version`'s pattern (check-a-change, make-several) or define it (check-the-store).

- [ ] **Steps and fixtures to reuse.**
  - check-a-change: `_store_with_decision_type` (the Background-like Given), `_store_unchanged` ("the store is unchanged", fixture `attempt` with `before`/`after` from `held.holds`).
  - check-the-store: `_store_with_a_decision`, conftest's "the client checks the store" (fixture `checked`), `held.plant` and `held.artifact` to store the decision in the written order behind the store's back, as `_store_with_two_faults` does.
  - make-several: Background "a store holding a decision type and a work item"; `_ask_for_the_set` ("the client asks for the set, saying which role and why", fixture `bad_set`); `_set_rejected` ("the set is rejected because a change in it does not fit its type") hard-codes the slice-121 scenario's refused artifact: make it read the expected refused artifacts from the `bad_set` fixture (its meaning unchanged), so all three scenarios share it.
  - define-a-type: `_nothing_written`; the When returns the same `attempt` dict as Task 1's Whens.

- [ ] **Verification.**
  - Red: after binding, `.venv/bin/pytest --collect-only -q -m slice-126` gives 5; each red for the reason above once its steps exist (the set-order scenario passes once its steps exist: log it as already satisfied).
  - Green: `.venv/bin/pytest -q -m slice-126` gives 5 passed; `.venv/bin/pytest -q tests/test_every_scenario_is_bound.py` passes.
  - Once before the last commit: `make test` gives 0 failed: 515 scenario and test items (the 513 collected at 266b48e plus the two bindings), plus Tasks 1 and 2's new tests, all passing.

- [ ] **Checkpoint:** "- 2026-10-01 slice 126 green. Someone can now: read a refusal, or a check, with its faults in the order the artifact reads back and, at one place, by rule name, the same from one attempt to the next whatever order the artifact was written in. Surprised by: <...>. Open questions: none. Next: slice 127."

---

### Task 3: Slice 127 — The type of types resolves its metaschema through a registry of kb's own

Review: batch-end
Model: sonnet

- [ ] **Check** (from the slice): a test builds the type of types' checker with the library's own retrieval turned off and resolves every 2020-12 metaschema and vocabulary it names from kb's registry, which is built from the declared specifications dependency; starting a store and defining a type then work with the network unreachable; `make test` gives no failure. Needs: the specifications package declared as a direct dependency.

- [ ] **Why it is red today** (probed: `jsonschema.validators.SPECIFICATIONS` replaced by an empty registry and `socket.socket.connect` refusing): starting a store works (the type of types is written, not checked), but defining a type is refused with rule `store`, "the store could not answer, and nothing was written: _WrappedReferencingError: Unresolvable: https://json-schema.org/draft/2020-12/schema". `validation.registry` retrieves only `kb:` URIs; the 2020-12 metaschema reaches the validator only because jsonschema combines its bundled `SPECIFICATIONS` with any registry it is given. `pyproject.toml` does not declare `jsonschema-specifications`. The unknown is answered: the installed 2025.9.1 holds all nine 2020-12 resources (decision 15).

- [ ] **Where the change lands.** `validation.py` (141 lines; it owns the registry types resolve through): the registry it builds holds the nine 2020-12 resources from `jsonschema_specifications` beside its `kb:` retrieval. `metaschema.py` is unchanged (it never holds logic). `pyproject.toml` declares `jsonschema-specifications>=2025.9.1`; `make dev` reinstalls. No new module; no CLAUDE.md row changes (validation.py's row already owns the composed schema's resolution; add "and the 2020-12 metaschemas it resolves through" to its row).

- [ ] **Decisions this task applies:** 15. The test lives in a new test module (e.g. `tests/test_the_metaschema_registry.py`), uses `monkeypatch` for both the library's registry and the network, so it is safe under `-n auto`, and reaches kb only through `kb.init`, the in-process client and `validation`'s public functions.

- [ ] **Steps and fixtures to reuse:** `calls.start_a_store`, `calls.define`, `calls.DECISION_TYPE`, `kb.client.connect`; the pytest `monkeypatch` and `tmp_path` fixtures. No scenario, no step.

- [ ] **Verification.**
  - `.venv/bin/pytest --collect-only -q -m slice-127` gives 0 (an enabling slice: no scenario carries the tag); run the new module by path: `.venv/bin/pytest -q tests/test_the_metaschema_registry.py`, red before the change (the Unresolvable refusal), green after.
  - Once before the last commit: `make test` gives 0 failed.

- [ ] **Checkpoint:** "- 2026-10-01 slice 127 green. Someone can now: check a type without depending on what the validator happens to bundle or fetch; kb's registry holds the nine 2020-12 metaschemas from the declared specifications package. Surprised by: <...>. Open questions: none. Next: batch 26 branch review (slices 124 to 127)."
