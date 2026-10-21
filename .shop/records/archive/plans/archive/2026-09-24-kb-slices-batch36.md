---
id: initiative-archive/missingmass.io/shopsystem/kb/2026-09-24-kb-slices-batch36
kind: initiative-archive
about: bounded-context/missingmass.io/shopsystem/kb
---
# kb slices

kb's own living plan, split on 2026-09-24 from the plan the two
repositories shared until kb 0.1, shop-knowledge's
`docs/superpowers/plans/2026-09-23-shop-knowledge-slices.md`, as both
specs' "Order of building" say. It holds every slice made only of kb
scenarios, with the number, the `@slice-<n>` tags, the status, and the log
entries it had there. The numbers skip those of the slices left in
shop-knowledge's plan; a number is never reused across the two, and a
slice in the other plan is named with its repository, as in
"shop-knowledge slice 22".

Slices 0 and 1 mix the two repositories and stay in shop-knowledge's plan.
They appear below only as notes that this plan waits on them there; both
are green.

kb 0.1 is tagged `v0.1.0`, and shop-knowledge pins it. From here each
repository plans alone. shop-knowledge's scenarios remain the demand signal
for kb: a kb change shop-knowledge needs arrives as a request to bump the
pin, and the kb slice that meets it is placed here by its unknown like any
other.

Slices 1.1 to 1.26 are numbered under slice 1 because they finished what
slice 1 began, deciding what kb 0.1 writes to disk or refuses on Init,
Create, or Read. Slices 2 onward are ordered as they were in the shared
plan: those that each settle one unknown, ordered by the size of it, then
those with none, bundled by feature and step definitions and ordered by
value.

The order of the sections in this file is the order of the work, and the
numbers read in that order. A slice placed after the plan was cut takes
its place among the slices not yet begun and a dotted number under the
slice before it (8.1 runs after 8 and before 9), so existing numbers and
tags stay valid. Whole numbers are renumbered, and tags rewritten, only
when whole slices change order, within this repository only.

Slices 0 to 123 are in
`.shop/records/archive/plans/archive/2026-09-24-kb-slices-batches1-25.md` and slices 124 to 127 in
`.shop/records/archive/plans/archive/2026-09-24-kb-slices-batch26.md`, and slices 128 to 137 with 128.1 and 133.1 in
`.shop/records/archive/plans/archive/2026-09-24-kb-slices-batch27.md`, all green. No slice is open.

## Slice 170.3: A store's database is made in one transaction
- Kind: enabling
- Check: `make test` -> the same passed and failed tests as the record before it, in at most 20 s (26 to 31 s today); a plain test that starting a store commits its schema once (no more than a handful of syncs: the count measured before and after is in the report); a store, a backup and a restore made after the change open and answer as before
- Observable: Starting a store, in the suite and for an operator, no longer pays a disk sync for every statement of the schema.
- Unknown: Whether the schema, the search tables and the type versions table can all be made inside one transaction in WAL mode
- Needs: the test-efficiency analysis of 2026-10-11: one kb.init makes 65 fdatasync calls, 104 ms on disk against 6 ms in memory
- Lands: 2 production, 1 test
- Status: green

## Slice 170.4: The suite is green between slices
- Kind: enabling
- Check: `make test` -> 0 failed: every scenario tagged to a slice the living plan does not yet show green, and the rule-names test (slice 182), is an expected failure; a test of the marking itself shows a scenario of a planned slice is expected to fail and one of a slice no longer in the plan runs for real; the summary line gives passed, expected-to-fail and unexpectedly-passing counts
- Observable: A regression is the only red in the suite, so nobody compares lists of failing names, and a scenario that starts passing before its slice shows in the summary.
- Unknown: Whether the plan's slice statuses can be read at collection cheaply and safely enough to mark tests by them
- Needs: the test-efficiency analysis and the request to shopsystem-bdd of 2026-10-11 (C: the suite is green between slices)
- Lands: 0 production, 2 test
- Status: green

## Slice 170.5: A map of which tests execute which code
- Kind: enabling
- Check: `make coverage-map` -> writes a per-test coverage database outside the fast suite; `make covered-by WHAT=src/kb/examining.py:150` (or the form the slice settles) lists the tests that execute that line; `make test` is unchanged in time and result
- Observable: A planner or scout asks which tests execute a function, and which code no passing test executes, instead of searching for names.
- Unknown: Whether per-test contexts work with pytest-xdist and the in-process operator commands at a cost a separate target can bear
- Needs: coverage as a development dependency; the request to shopsystem-bdd of 2026-10-11 (A: tools)
- Lands: 0 production, 2 test
- Status: green

## Log
- 2026-10-10 QUESTION FOR THE SPEC: when a type's IRI sits under another held type's IRI (https://x/decision and https://x/decision/sub), an IRI under both has two types: which one a create's IRI must sit under, and which type a placeholder at such an IRI has, no line says. Repro: define types at https://example.com/shop/decision and https://example.com/shop/decision/minor, then create a decision at https://example.com/shop/decision/minor/a, or link to it unheld. — recommended: an IRI belongs to the nearest type it sits under (the longest type IRI that is a whole-segment prefix of it); a create naming a version of another type is refused with rule identity, and a placeholder is typed by that nearest type. Applied in slices 158 and 167.
- 2026-10-10 RE-FORMULATE: change-the-store / the @slice-108 outline row 'removing the tag | new decision | a link must land on a node of a kind the type allows | neither the tag nor the new decision' is green today and contradicts check-a-change's placeholders (slice 166): with the tag removed and its type held, the new decision's link is to an IRI the store does not hold under a type the link allows. Evidence: .superpowers/scout/2026-10-10-sizing/slices-166-170.md. Recommended: the link lands on a placeholder and the decision is held (a removed IRI is an IRI not held; decision/removed-iris-may-be-reused).
- 2026-10-10 QUESTION FOR THE SPEC: export-and-import-a-store says an import that differs from what the store holds is refused and nothing lands, and that with errors skipped all but the broken files land; which holds for a differing file under --skip-errors no line says. Repro: a store holding a decision, a directory holding it with other content and one other clean file, kb import --skip-errors. — recommended: differing is refused whatever is skipped (it is not a broken file; skipping it would hide a conflict). Applies to slice 182.
- 2026-10-10 QUESTION FOR THE SPEC: with errors skipped, a file linking to an IRI nobody holds under a type whose only version in the directory is broken and skipped: the link's placeholder has no held type to stand under. Repro: slice 184's second row with the work item's link under the skipped type. — recommended: the file is left out with the type (a placeholder needs a held type, decision 0024), reported as skipped by its link's type. Applies to slices 183 and 184.
- 2026-10-10 QUESTION FOR THE SPEC: once kb numbers a type's versions (decision/kb-numbers-type-versions), whether a type's content still carries version, and what a number the client sends means, no line says; the type that describes types requires an integer version in a type's content today. Repro: define a type with version 7 in its content, or change one sending the number it already has. — recommended: content keeps version and kb writes the number it gives there, a client's number neither required nor refused. Applied as decision 4 of batch 33's plan (slice 161).
- 2026-10-10 QUESTION FOR THE SPEC: when a type is removed, whether its versions go with it no line says; today their rows stay, and a type defined again at that IRI would read the old type's later versions as its own. Repro: define a type, change it, remove it, define another there, read <IRI>@2. — recommended: removing a type removes every version of it, and a type defined there again starts at version 1. Applied as decision 11 of batch 33's plan (slice 161).
- 2026-10-10 QUESTION FOR THE SPEC: an export orders each artifact's entries by its type's latest version (export.py; tests/test_export_and_import_a_store.py asserts it for an artifact written before its type reordered its fields), and the import check reads a file against its kind's latest version; decision/an-artifact-is-read-through-its-version says everything kb reads of an artifact goes through its own version, and the export capability names no version. — recommended: export and import follow the decision (the artifact's own version); applied when slices 174 and 181 are planned.
- 2026-10-10 QUESTION FOR THE SPEC: a replacement of one section or item that names a later version of its artifact's type moves and checks the whole artifact; no line says a part's replacement may name a version. Repro: replace one section of a decision at version 1 naming version 2. — recommended: only a replacement of the whole artifact may name a version; one of a part naming one is refused with rule version.
- 2026-10-10 QUESTION FOR THE SPEC: a type's own replacement naming a version goes through the artifact's rule against the versions of the type that describes types; no line covers it. Repro: replace a type naming https://missingmass.io/kb/type@1. — recommended: as any artifact (it names the version of the type of types it conforms to); no change.
- 2026-10-11 QUESTION FOR THE SPEC: a type removed and defined again in one set is refused while another type's version reads it (slice 165.1), and the removed type's versions go with it though define-a-type's Purpose says the capability removes no version. — recommended: reword the Purpose to 'removes no version of a type it holds' and leave the refusal; route with the next formulation.
- 2026-10-11 QUESTION FOR THE SPEC: an import of a directory holding version 2 of a type and no version 1: whether it lands, and what an artifact conforming to the missing version gets. — recommended: the import keeps the numbers its files give; a version file alone lands; an artifact conforming to a version neither the directory nor the store holds is an error of the check (it claims a type version nobody holds). Applied as batch 34's decision for slice 165.6.
- 2026-10-11 QUESTION FOR THE SPEC: the history gains 'one import entry for each artifact that lands': whether each version file of a type is an artifact of its own for that count. — recommended: one entry per file that lands, a type's version files included.
- 2026-10-11 QUESTION FOR THE SPEC: an export selecting a type (slice 176): whether that type's version files are among 'that type's artifacts'. — recommended: yes, the type's version files and the artifacts conforming to any version of it. Needed before slice 176.
- 2026-10-11 QUESTION FOR THE SPEC: a file naming a version of its type neither the directory nor the store holds is reported with rule version and its own message (file_refusals.no_version_offered); with errors skipped that file is left out and the rest lands; no line states the rule or the wording. — recommended: keep both; add a Behaviour line and scenario with slice 184's formulation.
- 2026-10-11 QUESTION FOR THE SPEC: a type may be removed while links wait on IRIs under it (placeholders), since nothing is stored for a placeholder and no artifact of its kind exists; the links then name IRIs under no held type, which a new link could not. Repro (after slice 166): define tag, link a decision to an unheld tag IRI, remove the tag type. — recommended: the removal is refused because something still points at it, naming each linking artifact, as it is while artifacts of its kind exist; to be formulated and cut as a slice inside batch 35.
- 2026-10-11 QUESTION FOR THE SPEC: what a read shows for a link into a part of an artifact (held or not); today a read at a glance, a whole read following links, and Follow outward of an artifact holding such a link are refused with locator, for a held target too. Repro: a decision that supersedes https://.../decision/older#options/a, then Read it at a glance. — recommended: at a glance the stub of the artifact the part is in (the bare IRI when not held); following links, the link stays the reference written, not filled in; Follow reaches the artifact the part is in. Applied in slice 166's fix round.
- 2026-10-11 RE-FORMULATE answered (slice 170's hand-back at c35a777): check-the-store / 'A store holding links to IRIs it does not hold lists each placeholder with what links to it' asked for a link held in a section, which no store can hold (decision/0011-sections-carry-no-links); its Behaviour line names no place. The Given and Then now say one of its items where they said one of its sections; no line changed. Under the person's delegation.
- 2026-10-11 QUESTION FOR THE SPEC: when a type is defined under the IRI of the type that describes types, does a type already held under the new IRI stand in the way (slice 166.3 refuses it, against decision/type-iris-are-free)? — recommended: no; types do not belong to the type of types by where they sit; a link waiting there still stands in the way. Applied in slice 166.3's fix round.
- 2026-10-11 QUESTION FOR THE SPEC: kb validate's line for a placeholder: whether it shows the part a link names. — recommended: yes, the IRI, # and the part, so a link into a part and one to the whole of an IRI print apart. Applied in slice 170's fix round.
- 2026-10-11 QUESTION FOR THE SPEC: define-a-type refuses a type defined over what sits 'under' it; whether a link waiting on the new type's own IRI stands in the way too. Repro: a decision superseding decision/ghost (not held), then a type defined at decision/ghost lands and the check reports ref on the untouched decision. — recommended: yes, the IRI itself counts; the define is refused naming it. Applied in batch 35's fix wave.
- 2026-10-11 QUESTION FOR THE SPEC: a set removing a type and a nearer held type under it names a waiting artifact in both refusals (decision 11 of batch 35's plan does not say). — recommended: keep it; each removal says what stands in its own way.
- 2026-10-11 QUESTION FOR THE SPEC: check-a-change's line lets a change land that 'leaves that link as it is'; whether a waiting link is still that link when an earlier item of its collection, or an earlier link of its field, is removed or reordered (its place by index moves). — recommended: yes; the link is the same when it has the same target and part in the same field of the same artifact or named item, wherever it stands in a list. Applied in slice 170.1's fix round (batch 35 plan, decision 14).
- 2026-10-11 QUESTION FOR THE SPEC: an import or seed of a file whose item has no id lands the item unnamed, where a write names every item; kb import --check calls it clean. — recommended: the import names items as a write does (or the check reports an item with no name); decide with the import slices (181 onward).
- 2026-10-11 Batch batch35 archived to archive/2026-09-24-kb-slices-batch35.md; last 2026-10-11 Suite: 1079 passed, 70 failed, 2 skipped at 155a51e in 26.5 s; failing: the scenarios of slices 171 onward and test_the_rule_names_kb_gives_are_exactly_the_spec_lists; skipped: the two cases of a change to an artifact whose imported item has no name (slice 180.2)
- 2026-10-11 Suite: 1079 passed, 70 failed, 2 skipped at 155a51e in 26.5 s; failing: the scenarios of slices 171 onward and test_the_rule_names_kb_gives_are_exactly_the_spec_lists; skipped: the two cases of a change to an artifact whose imported item has no name (slice 180.2)
- 2026-10-11 Batch 36 (tooling), from the efficiency analyses and the request to shopsystem-bdd of 2026-10-11: 170.3 (the schema in one transaction), 170.4 (the suite green between slices), 170.5 (a per-test coverage map). Store invariants as property tests are not cut yet: they need the invariants stated first. Then batch 37 = 171 to 176.
- 2026-10-11 slice 170.3 green. Someone can now: start a store with its database's whole schema committed once (sqlite_store.make runs it between one BEGIN and COMMIT, then sets WAL), 13 fdatasync a start where there were 65, about 20 ms where there were about 81, the suite about 23 s where it was about 29 s; tests/test_a_database_is_made_in_one_transaction.py pins it through SQLite's trace.
  Surprised by: the schema of sqlite_types.py is already part of sqlite_store.SCHEMA and the search tables are in it, so one line changed; a restore's copy (sqlite_backup.copied_out) already takes 8 syncs and 9 ms and is untouched; the 5 syncs a start still makes beyond the making are its first landing and are not this slice's.
  Open questions: no test holds a making that fails partway through its schema (the one test of a failed start replaces make whole); the marker is still written last, and a schema cut short is now rolled back, leaving an empty file where it left some tables. Next: slice 170.4.
- 2026-10-11 Suite: 1080 passed, 70 failed, 2 skipped at 6812dde in 23.3 s; failing: the scenarios of slices 171 onward and test_the_rule_names_kb_gives_are_exactly_the_spec_lists; skipped: the two cases of a change to an artifact whose imported item has no name (slice 180.2)
- 2026-10-11 slice 170.4 green. Someone can now: run `make test` and read any failure as a regression, since a test of a slice the plan holds as not green is expected to fail (xfailed, reason "slice <n> not built") and one passing early is counted as xpassed.
  Surprised by: 6 cases pass before their slice, so the xpassed count stands at 6, not 0: three Examples rows of "An added item's title becomes its name, read as text, refused if it leaves nothing" (@slice-179) and three of "Each error is reported by file and reason" (@slice-183), outlines tagged to a later slice whose older rows already pass; they were among the passed before. Red on a scenario's own assertion needs `--runxfail` beside `-m slice-N`; without it the failure is counted and its traceback not shown.
  Open questions: a regression in one of the 6 rows that pass early would show only as xpassed falling from 6 and xfailed rising, not as a failure, until slices 179 and 183 are green; whether those rows keep their slice tag is slicing's. Next: slice 170.5.
- 2026-10-11 Suite: 1083 passed, 72 expected to fail, 6 unexpectedly passing, 0 failed at 44a4368 in 23.5 s; unexpectedly passing: 3 rows of "An added item's title becomes its name, read as text, refused if it leaves nothing" (slice 179), 3 rows of "Each error is reported by file and reason" (slice 183)
- 2026-10-11 Suite: 1096 passed, 72 expected to fail, 0 unexpectedly passing, 0 failed at 5986b47 in 25 s
- 2026-10-11 slice 170.5 green. Someone can now: ask which passing tests execute a file, line or function of src/kb, and which function-body lines no passing test executes (make coverage-map, then make coverage-ask). Surprised by: the module's top level runs at import, before any test context and (under xdist) before coverage starts, so it is not asked after; the map holds expected-failure tests too, so a list of passing tests (.coverage-map.passed) filters them. Open questions: none. Next: batch end.
- 2026-10-11 Suite: 1100 passed, 72 expected to fail, 0 unexpectedly passing, 0 failed at 81f62d4 in 23.3 s
- 2026-10-11 Suite: 1129 passed, 72 expected to fail, 0 unexpectedly passing, 0 failed at 59fd536 in 23.1 s
