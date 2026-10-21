---
id: initiative-archive/missingmass.io/shopsystem/kb/2026-09-24-kb-slices-batch34
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

## Slice 165.2: The tests' view of an export lists every version's file
- Kind: enabling
- Check: `make test` -> the same passed and failed tests as the record before it; `grep -n "held.names(root)" tests/test_export_and_import_a_store.py` finds no comparison of an export with one file per type
- Observable: The tests that compare an export with what a store holds can name a file for every held version of a type, before any store they compare holds two.
- Unknown: none
- Needs: migrate of the export layout's change: the test helpers that expect one file per type
- Lands: 0 production, 2 test
- Status: green

## Slice 165.3: The operator's export gives every version of a type, each artifact as its version declares
- Kind: capability
- Scenarios: export-and-import-a-store / The operator exports the store to a directory that is empty or does not exist; export-and-import-a-store / An artifact that conforms to an earlier version of its type is exported in the order that version declares
- Observable: The operator's kb export writes one file for each held version of a type, with the revision and title it was made with, and each artifact's content in the order the version it conforms to declares.
- Unknown: How every held version of a type is written as a file of its own from one read moment
- Needs: one existing plain test that asserts export in the latest version's order is rewritten
- Lands: 2 production, 2 test
- Status: green

## Slice 165.4: importing.py split before the import of versions grows it
- Kind: enabling
- Check: `make test` -> the same passed and failed tests as the record before it; `wc -l src/kb/importing.py` -> at most 180, and no module under src/kb over 250
- Observable: The import's examination of a directory and its landing each have room for version files.
- Unknown: none
- Needs: slice 180.1's work, brought forward (importing.py at 237 of 250 lines)
- Lands: 2 production, 0 test
- Status: green

## Slice 165.5: An import tells the versions of one type apart
- Kind: enabling
- Check: `make test` -> the same passed and failed tests as the record before it; a plain test offers a directory holding two version files of one type and finds both, each named by its own version
- Observable: A directory holding two versions of one type offers both for import, where today one overwrites the other before anything is checked.
- Unknown: none
- Needs: migrate of the import's keying of files by name
- Lands: 2 production, 1 test
- Status: green

## Slice 165.6: A store with an artifact behind its type comes back from its export
- Kind: capability
- Scenarios: export-and-import-a-store / A store holding an artifact behind its type comes back from its export as it was
- Observable: The operator imports the export of a store holding an artifact left at an earlier version of its type into a fresh store, and the artifact is read, listed, checked and replaced there as it was, every version of its type held.
- Unknown: Whether one imported set can land several versions of one type, each as its file gives it, with every artifact checked and linked through the version it names
- Needs: closes the RELEASE GATE backlog line of batch 33
- Lands: 7 production, 3 test
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
- 2026-10-11 Batch batch33 archived to archive/2026-09-24-kb-slices-batch33.md; last 2026-10-11 Suite: 843 passed, 93 failed at 503c507 in 24 s; failing: slice-166 onward scenarios and test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-11 Suite: 843 passed, 93 failed at 503c507 in 24 s; failing: slice-166 onward scenarios and test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-11 Re-slice (the RELEASE GATE of batch 33): batch 34 = 165.2 to 165.6, an export and its import carrying every version of a type, ahead of placeholders (batch 35 = 166 to 170). Slice 174 keeps only its client scenario (export-through-the-contract), its operator scenario now slice 165.3's; slice 181 keeps import into a store already holding artifacts; slice 184 keeps the skip analysis. The port's read of a type's held versions landed with slice 165.1. From .superpowers/scout/2026-10-10-batch34/export-import-versions.md.
- 2026-10-11 Small change (integrating-a-proposal, formulating-features): two Behaviour lines in export-and-import-a-store (export in the order an artifact's version declares; a store with an artifact behind its type comes back from its export as it was), resting on decision/an-artifact-is-read-through-its-version; approved under the person's delegation.
- 2026-10-11 QUESTION FOR THE SPEC: an import of a directory holding version 2 of a type and no version 1: whether it lands, and what an artifact conforming to the missing version gets. — recommended: the import keeps the numbers its files give; a version file alone lands; an artifact conforming to a version neither the directory nor the store holds is an error of the check (it claims a type version nobody holds). Applied as batch 34's decision for slice 165.6.
- 2026-10-11 QUESTION FOR THE SPEC: the history gains 'one import entry for each artifact that lands': whether each version file of a type is an artifact of its own for that count. — recommended: one entry per file that lands, a type's version files included.
- 2026-10-11 QUESTION FOR THE SPEC: an export selecting a type (slice 176): whether that type's version files are among 'that type's artifacts'. — recommended: yes, the type's version files and the artifacts conforming to any version of it. Needed before slice 176.
- 2026-10-11 slice 165.2 green. Someone can now: compare an export with a store holding a type at several versions through held.versions and _held_files. Surprised by: test_export_and_import_find_the_store_as_validate_does already holds a type at two versions, so its comparison stays on the standing version's file until the export writes every version (Task 2). Open questions: none. Next: slice 165.3.
- 2026-10-11 Suite: 842 passed, 94 failed at c4308c7 in 25 s; failing: as at 503c507 plus the unbound scenarios of slice-165.3, slice-165.6, slice-166 onward and the rule names
- 2026-10-11 HAND-BACK slice 165.3, test tests/test_export_and_import_a_store.py::test_an_artifact_left_at_its_version_when_its_type_reordered_its_fields_exports_in_the_order_that_version_declares (was ..._exports_in_the_order_its_type_now_declares): an existing test can only stay green by being loosened, beyond what the task lists. The task lists it as rewritten to the export order of the version conformed to, and that part is done and passes; the same test then checks and imports its export, which now holds two versions of the note type, and the task leaves the import of such an export to slice 165.6.
  Evidence: assert (checked.faults, list(checked.errors), list(checked.skipped)) == ([], [], []) fails with errors [artifact: "shop.example/kb/note/x.yaml" rule: "content" message: "it is not in canonical form: its text is not the text kb writes"].
  Green in this slice: The operator exports the store to a directory that is empty or does not exist (both examples); An artifact that conforms to an earlier version of its type is exported in the order that version declares. Red: none of the slice; the test named above.
- 2026-10-11 slice 165.3 green. Someone can now: export every held version of a type, each artifact in the order its own version declares. Surprised by: a type's title cannot change through Replace, so the outline's two versions share a title; a version file's type comes from the content the version was made with; the import half of the reordered-fields test had to be split off and skipped until 165.6. Open questions: none. Next: slice 165.4.
- 2026-10-11 Suite: 846 passed, 92 failed, 1 skipped at a3f1f6f in 24 s; failing: scenarios tagged slice-166 onward, test_the_rule_names_kb_gives_are_exactly_the_spec_lists, test_every_scenario_is_bound (slice-165.6's unbound scenario)
- 2026-10-11 slice 165.4 green. Someone can now: grow the import of versions in importing.py (56 lines) beside examining.py (190), the examination of a directory. Surprised by: Checked is the examination's answer too, so it lives in examining.py and client, operating and staging moved to it (no shim). Open questions: none. Next: slice 165.5.
- 2026-10-11 Suite: 846 passed, 92 failed at 29f6bd2 in 25 s; failing: the slice-166-onward scenarios, test_the_rule_names_kb_gives_are_exactly_the_spec_lists, tests/test_every_scenario_is_bound.py
- 2026-10-11 slice 165.5 green. Someone can now: offer and examine the version files of one type apart, each under its own version's IRI. Surprised by: nothing. Open questions: none. Next: landing two versions of a type (task 5).
- 2026-10-11 Suite: 847 passed, 92 failed at 3d7444e in 27 s; failing: slice-166 onward scenarios, test_the_rule_names_kb_gives_are_exactly_the_spec_lists, tests/test_every_scenario_is_bound.py
- 2026-10-11 slice 165.6 green. Someone can now: export a store holding an artifact behind its type and import that directory into a fresh store, where every version of the type lands as its file gives it and the artifact is read, listed, checked (behind, no violation) and replaced as it was. The RELEASE GATE backlog line of batch 33 is closed: the review's reproduction (define a note type, create a note at its first version, change the type, export, import --check clean, import, read at a glance and whole, list, check, replace) now passes, as the scenario and as one plain test for each call, with the second export byte for byte the first and kb init --seed landing both versions.
  Surprised by: the port and the adapter needed nothing for a set landing two versions of one type; the import's own check read every artifact through its kind's latest, so the work was in examining.py, drafting.py and links.py (its default to the latest gone, composition.latest_schema removed). A file naming a version of its type nobody holds is a new fault of the check, rule version (file_refusals.no_version_offered); drafting.py now puts a set's imports of one type in the order of their numbers itself.
  Open questions: the rule and message of a file naming a version nobody holds were chosen here (rule version, as a create naming one), no scenario states them; the skip analysis still takes an artifact as read through every version file of its type the directory brings, so an error in a version the artifact does not conform to still holds it back (slice 184's). Next: slice 166.
- 2026-10-11 Suite: 874 passed, 91 failed at d745fb4 in 26 s; failing: slice-166 onward scenarios, test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-11 QUESTION FOR THE SPEC: a file naming a version of its type neither the directory nor the store holds is reported with rule version and its own message (file_refusals.no_version_offered); with errors skipped that file is left out and the rest lands; no line states the rule or the wording. — recommended: keep both; add a Behaviour line and scenario with slice 184's formulation.
- 2026-10-11 Batch 34 branch review at 781a959: 874 passed, 91 failed (expected only); the release gate is closed; one issue to fix now: slice 165.5 broke the skip analysis (a file no longer leads to its type's files), which no passing test covers because every skip scenario is slice 184's and unbound.
- 2026-10-11 Suite: 878 passed, 91 failed at 1fe51e3 in 25 s; failing: slice-166 onward scenarios, test_the_rule_names_kb_gives_are_exactly_the_spec_lists
