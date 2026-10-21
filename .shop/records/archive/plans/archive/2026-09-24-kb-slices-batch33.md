---
id: initiative-archive/missingmass.io/shopsystem/kb/2026-09-24-kb-slices-batch33
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

## Slice 160.1: The store keeps each type's version beside the type
- Kind: enabling
- Check: `make test` -> the same passed and failed tests as the record before it, and the storage port's conformance tests of a type version read by its IRI pass; nothing outside the port and its adapter reads the versions yet
- Observable: The storage port holds the version each type stands at as a thing of its own, read by its IRI, ready for a second version to stand beside it.
- Unknown: Whether a type's versions can be kept beside the artifacts without the store's listings counting them
- Needs: expand of slice 161's breaking change: a stored layout existing code reads
- Lands: 6 production, 1 test
- Status: green

## Slice 160.2: Types are read through the versions the store keeps
- Kind: enabling
- Check: `make test` -> the same passed and failed tests as the record before it; a plain test reads the version a type stands at by that version's IRI; `grep` shows a type's schema is read for checking only through the kept versions
- Observable: Every check reads a type through the version kept for it, so a second version can be held without changing how anything is checked.
- Unknown: none
- Needs: migrate of slice 161's breaking change
- Lands: 4 production, 1 test
- Status: green

## Slice 161: Every version of a type is held, numbered by the store
- Kind: capability
- Scenarios: define-a-type / The client changes a type; define-a-type / The client changes a type and the store numbers the new version; define-a-type / While an artifact conforms to a version of a type, the store holds that version; define-a-type / When no artifact conforms to a version of a type any longer, the store still holds that version
- Observable: A client changes a type and finds each earlier version still held, as it was made, at its own IRI, the new one numbered next by the store.
- Unknown: Whether every version of a type can be held beside the others, fixed once made, each read through its own IRI
- Needs: none
- Lands: 7 production, 3 test
- Status: green

## Slice 162: A create names the version of its type it conforms to
- Kind: capability
- Scenarios: check-a-change / An artifact created naming a version of its type is checked against that version; name-what-is-asked-for / A create naming a type version the store does not hold is refused
- Observable: A client creates an artifact against an earlier version of its type and is held to that version; an unheld version is refused, named back.
- Unknown: Whether a create can be drafted and checked against the version it names rather than the type's latest
- Needs: none
- Lands: 4 production, 1 test
- Status: green

## Slice 163: An artifact keeps its version until a write names a later one
- Kind: capability
- Scenarios: change-the-store / A change naming no version of its type keeps the artifact at the version it conforms to; change-the-store / A replacement naming a later version of the artifact's type moves the artifact to it; change-the-store / A replacement naming an earlier version of the artifact's type, or a version of another type, is refused; check-a-change / Changing an artifact that is behind its type naming no version keeps it at the version it conforms to; check-a-change / Changing an artifact that is behind its type naming the latest version, with content that fits it, brings it up to date; check-a-change / Changing an artifact that is behind its type naming a later version, with content that does not fit it, is refused
- Observable: A client's changes leave an artifact at its own version unless one names a later version of its own type, which it is then held to.
- Unknown: Whether every change is checked against the version its artifact conforms to, moving only forward within its own type
- Needs: none
- Lands: 5 production, 3 test
- Status: green

## Slice 163.1: An artifact is read through the version it conforms to
- Kind: capability
- Scenarios: read-an-artifact / An artifact that conforms to an earlier version of its type is read as that version declares
- Observable: A client reading an artifact left at an earlier version of its type, at a glance, whole or following links, is given it as that version declares, where today the read goes through the latest version and can be refused.
- Unknown: Whether every read level can take each artifact's own version rather than one schema for its kind
- Needs: none
- Lands: 4 production, 2 test
- Status: green

## Slice 163.2: A type's change restates none of its artifacts' links
- Kind: capability
- Scenarios: define-a-type / A type is changed and the links of an artifact conforming to its earlier version stay as that version declares
- Observable: A client changing a type finds the links of artifacts left at its earlier version as that version declares them: what they point at still cannot be removed, and a field only the new version makes a link is not one for them.
- Unknown: Whether a set that changes a type lands soundly with no held artifact's links restated
- Needs: four existing plain tests that assert the restating are rewritten
- Lands: 3 production, 3 test
- Status: green

## Slice 163.3: The restating of links leaves the port
- Kind: enabling
- Check: `make test` -> the same passed and failed tests as the record before it; `grep -rnE "Relink|relinks|reread|_restated|kinds=" src/kb tests` finds nothing
- Observable: The storage port and its adapter no longer carry restated links or the kinds a set reads anew, which nothing asks for once a type's change restates nothing.
- Unknown: none
- Needs: contract of slice 163.2's change: the machinery it leaves unused is removed, with three port conformance cases that test only it
- Lands: 4 production, 1 test
- Status: green

## Slice 164: The store's check reads each artifact against its own version
- Kind: capability
- Scenarios: check-the-store / An artifact that conforms to a version of its type a later version has followed is listed as behind its type; check-the-store / An artifact behind its type is checked against the version of its type it conforms to; define-a-type / A type is changed so that artifacts the store holds would no longer fit it
- Observable: A client checking the store sees an artifact behind its type listed as behind, and a violation only where it does not fit the version it conforms to.
- Unknown: Whether the whole-store check can read every artifact through the version it conforms to in one view
- Needs: none
- Lands: 2 production, 2 test
- Status: green

## Slice 165: Links and references name a type or a version of one
- Kind: capability
- Scenarios: define-a-type / A link field naming a kind by its type's IRI may point at an artifact of any version of that type; define-a-type / A type refers to a shape another type defines, naming the version it reads; define-a-type / A type that could never check an artifact is refused when it is written
- Observable: A client's link fields reach artifacts of any version of a type, its kb: references read the version they name, and a type naming a version not held is refused, the fault named.
- Unknown: Whether kb: references resolve through a registry of every held type version by its IRI
- Needs: none
- Lands: 3 production, 2 test
- Status: green

## Slice 165.1: A type another type's version reads is not removed
- Kind: capability
- Scenarios: define-a-type / Removing a type while a version of another type reads one of its versions is refused
- Observable: A client removing a type that a held version of another type refers to, or is built on, is refused, each referring type named, where today the removal lands and the store's check then fails as the store's own fault.
- Unknown: Whether every held version of every type can be asked which types' versions it reads when a type is removed
- Needs: tests/test_a_type_moving_under_a_change.py's case that removes a referred type is rewritten to the refusal
- Lands: 3 production, 2 test
- Status: green

## Log
- 2026-10-10 QUESTION FOR THE SPEC: when a type's IRI sits under another held type's IRI (https://x/decision and https://x/decision/sub), an IRI under both has two types: which one a create's IRI must sit under, and which type a placeholder at such an IRI has, no line says. Repro: define types at https://example.com/shop/decision and https://example.com/shop/decision/minor, then create a decision at https://example.com/shop/decision/minor/a, or link to it unheld. — recommended: an IRI belongs to the nearest type it sits under (the longest type IRI that is a whole-segment prefix of it); a create naming a version of another type is refused with rule identity, and a placeholder is typed by that nearest type. Applied in slices 158 and 167.
- 2026-10-10 RE-FORMULATE: change-the-store / the @slice-108 outline row 'removing the tag | new decision | a link must land on a node of a kind the type allows | neither the tag nor the new decision' is green today and contradicts check-a-change's placeholders (slice 166): with the tag removed and its type held, the new decision's link is to an IRI the store does not hold under a type the link allows. Evidence: .superpowers/scout/2026-10-10-sizing/slices-166-170.md. Recommended: the link lands on a placeholder and the decision is held (a removed IRI is an IRI not held; decision/removed-iris-may-be-reused).
- 2026-10-10 QUESTION FOR THE SPEC: export-and-import-a-store says an import that differs from what the store holds is refused and nothing lands, and that with errors skipped all but the broken files land; which holds for a differing file under --skip-errors no line says. Repro: a store holding a decision, a directory holding it with other content and one other clean file, kb import --skip-errors. — recommended: differing is refused whatever is skipped (it is not a broken file; skipping it would hide a conflict). Applies to slice 182.
- 2026-10-10 QUESTION FOR THE SPEC: with errors skipped, a file linking to an IRI nobody holds under a type whose only version in the directory is broken and skipped: the link's placeholder has no held type to stand under. Repro: slice 184's second row with the work item's link under the skipped type. — recommended: the file is left out with the type (a placeholder needs a held type, decision 0024), reported as skipped by its link's type. Applies to slices 183 and 184.
- 2026-10-10 QUESTION FOR THE SPEC: once kb numbers a type's versions (decision/kb-numbers-type-versions), whether a type's content still carries version, and what a number the client sends means, no line says; the type that describes types requires an integer version in a type's content today. Repro: define a type with version 7 in its content, or change one sending the number it already has. — recommended: content keeps version and kb writes the number it gives there, a client's number neither required nor refused. Applied as decision 4 of batch 33's plan (slice 161).
- 2026-10-10 Batch batch32 archived to archive/2026-09-24-kb-slices-batch32.md; last 2026-10-10 Suite: 727 passed, 118 failed at 0a36085 in 23 s; failing: the scenarios tagged slice-161 onward, and test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-10 Suite: 727 passed, 118 failed at 0a36085 in 23 s; failing: the scenarios tagged slice-161 onward, and test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-10 slice 160.1 green. Someone can now: read a version of a type by its IRI through the storage port (type_version), kept in its own table beside artifacts from a store's start, with nothing in the domain reading it yet.
  Surprised by: the adapter knows nothing of types, so it cannot tell a type's change or its number from the change as it was; the change now carries the version it leaves the type standing at (port.Versioned), handed by drafting.py and by write.start, two production files the task did not name. sqlite_reads.py imports the new module, so sqlite_types.py takes and gives content as stored text.
  Open questions: a removed type's version row stays and still reads by its IRI (Review Focus 4, Task 3's); a client's version number that is not a whole number above 0 (0, -1, 1.0) is keyed as names.versioned writes it, as drafting already does for an artifact's type; a store file made before this batch has no type_versions table and nothing is done for it (no stored database fixture is checked in under tests/ or features/). Next: slice 160.2.
- 2026-10-10 Suite: 734 passed, 118 failed at 88f6a88 in 24 s; failing: the scenarios tagged slice-161 onward, and test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-10 slice 160.2 green. Someone can now: read a type's schema for every check through the version the store keeps, and read a version at its IRI <type IRI>@<n>. Surprised by: a read of a version needed requests.py (the locator conversion refused '@') beside the brief's three files. Open questions: none. Next: slice 160.3.
- 2026-10-10 Suite: 736 passed, 118 failed at b8dde10 in 22 s; failing: the scenarios tagged slice-161 onward, and test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-10 HAND-BACK slice 161 step 1 at edc5708: three port conformance cases slice 160.1 wrote assert the earlier version is gone once a type changes; the task's Tests the decisions break did not list them. Planner: listed, rewritten to assert the earlier version still held as made (batch 33 plan, Task 3, step 1.1).
- 2026-10-10 QUESTION FOR THE SPEC: when a type is removed, whether its versions go with it no line says; today their rows stay, and a type defined again at that IRI would read the old type's later versions as its own. Repro: define a type, change it, remove it, define another there, read <IRI>@2. — recommended: removing a type removes every version of it, and a type defined there again starts at version 1. Applied as decision 11 of batch 33's plan (slice 161).
- 2026-10-10 slice 161 green. Someone can now: change a type without sending a number and have the store make the next version beside the earlier ones, each read at `<type IRI>@<n>` as it was made, kept while an artifact conforms to it and after none does.
  Surprised by: the scenarios went green on their step definitions alone, steps 1 to 2 having built the behaviour; a draft that changed a type answered only the version it left it at, so a set changing a type and a type that refers to its earlier version was refused with `shape` where the two changes made one by one land (draft.py now reads an earlier version as the store keeps it, pinned by a plain test); CLAUDE.md's row and docstrings of composition.py still say a reference is held only at the version its type stands at, which is no longer so (slice 165's module, left).
  Open questions: a type removed and defined again in one set is unpinned, and no rpc can ask it (a set is of one kind), only a caller of write.land; a `version` in a type's content that is not a number is still refused with rule `type`; an import still keeps the number its file gives (slices 174, 181). Next: slice 162.
- 2026-10-10 Suite: 756 passed, 114 failed at 8d6b776 in 23 s; failing: the scenarios tagged slice-162 onward, and test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-10 slice 162 green. Someone can now: create an artifact naming an earlier version of its type that the store holds, and have it checked, content and links, against that version and land conforming to it, whatever the type stands at or moves to while the create is written.
  Surprised by: before this slice a create naming an earlier held version was not refused but checked against, and stamped with, the latest version; the unheld-version refusal already existed, so the outline's two rows went green on their steps, and the leftover step 'that fault stands on its own' still asserted rule kind from the scenario's earlier form (no other feature line uses it) and now asserts version. The link rows a create hands the port were read through the latest version; a plain test showed it, and links.handed now takes the type a create was checked against.
  Open questions: (1) a summary read of an artifact behind its type still reads its links through the latest version (read.py, query.py), and is refused with locator when a field the latest makes a link holds plain text; no slice-162 line covers reads. (2) a later change to the type still restates the links of every held artifact of the kind through the latest version (Draft.stale, drafting._relinked), so a create's links are the named version's only until its type next changes; tests/test_a_type_moving_under_a_change.py's existing cases assert that restating. (3) a replacement, an addition and the check of the store still move or read an artifact at the latest version (slices 163, 164). Next: slice 163.
- 2026-10-10 Suite: 763 passed, 111 failed at 1cfffe3 in 25 s; failing: the scenarios tagged slice-163 onward, and test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-10 HAND-BACK slice 163 step 2 at 0ddd2fe: three existing tests expect a replacement naming no version to be held to its type's latest version (two in test_add_an_item_to_a_collection.py, one in test_a_type_moving_under_a_change.py); the task did not list them. Planner: listed in batch 33's Task 5; two setups name the later version, one is rewritten to the links the artifact's own version makes.
- 2026-10-10 slice 163 green. Someone can now: change an artifact and have it stay at the version of its type it conforms to, held to that version's rules, and move it to a later version of its own type only by naming that version on a replacement, which is then checked against it; an earlier version or another type's is refused with `version`.
  Surprised by: three existing tests relied on a replacement naming no version moving its artifact to the latest version (step 2's hand-back; the plan now lists them). Every scenario went green on its step definitions alone, the rule having been built in step 2 against plain tests. A listing by kind gives nothing in this batch's state (a later slice's), so the step for 'the store holds the decision at the IRI it had before' asks what the store holds, not the listing.
  Open questions: a replacement naming the very version its artifact conforms to is kept, not refused (the controller's ruling; no scenario covers it). A replacement of one section or item that names a version moves the whole artifact; no scenario covers it. A type's own replacement goes through the same rule. Reads, the whole-store check and the links of artifacts a set leaves untouched still go through the latest version (slice 164 and later). Next: slice 164.
- 2026-10-10 Suite: 796 passed, 103 failed at 5f46bfb in 25 s; failing: the scenarios tagged slice-164 onward, and test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-10 Small change (integrating-a-proposal, formulating-features): two Behaviour lines and decision/an-artifact-is-read-through-its-version, from slice 162's review (reads of an artifact behind its type refused with locator; a type's change restating earlier-version artifacts' links, dropping a refuse link). Sliced as 163.1, 163.2, 163.3 from .superpowers/scout/2026-10-10-batch33/versions-read-and-links.md.
- 2026-10-10 Probe: grep for artifact_schema, kind_schema, reread, stale, Relink, relinks, kinds in src and tests; read of read.py, query.py, drafting.py, draft.py, port.py, sqlite_checks.py -> 163.1: 4 production, 2 test; 163.2: 3 production, 3 test; 163.3: 4 production, 1 test
- 2026-10-10 QUESTION FOR THE SPEC: an export orders each artifact's entries by its type's latest version (export.py; tests/test_export_and_import_a_store.py asserts it for an artifact written before its type reordered its fields), and the import check reads a file against its kind's latest version; decision/an-artifact-is-read-through-its-version says everything kb reads of an artifact goes through its own version, and the export capability names no version. — recommended: export and import follow the decision (the artifact's own version); applied when slices 174 and 181 are planned.
- 2026-10-10 slice 163.1 green. Someone can now: read an artifact left at an earlier version of its type as that version declares, at a glance and whole. Surprised by: the whole row at depth 0 already passed before any code (a plain whole read never consults the schema); links.handed left on the latest, as no scenario asks. Open questions: none. Next: slice 163.2.
- 2026-10-10 Suite: 799 passed, 104 failed at 6ad96c5 in 24.6 s; failing: slice-164 onward scenarios and test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-10 slice 163.2 green. Someone can now: change a type and find every artifact left at its earlier version linking exactly as that version declares, a link it declares still guarding its target and a field only the new version makes a link not one.
  Surprised by: the draft read the links of an artifact a set puts through the latest version of its kind, so a create naming an earlier version beside a removal in one set was refused for a link its version does not make; draft.py now reads them through the artifact's own version (a plain test in tests/test_the_link_index.py pins it). links.handed's default (latest) is left for importing.py, its one remaining caller (decision 14). Drafted lost its relinks and kinds fields and drafting.py its _relinked; write.py hands the port changes and entries only.
  Open questions: none. Next: slice 163.3, which removes what is now unused: Draft.reread, Draft.stale and Draft._changed/_note, composition.reading, port.Relink, the port's and adapter's relinks and kinds parameters, sqlite_checks._restated.
- 2026-10-10 Suite: 802 passed, 103 failed at 1b395c7 in 23.6 s; failing: slice-164 onward scenarios and test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-10 Correction to slice 163's checkpoint: a listing by kind does return the decision; a test helper reads the stubs of a names-only listing, empty since slice 29, so three assertions (tests/test_change_an_artifact.py:541, tests/conftest.py:145, tests/test_make_several_changes_in_one_go.py:292) check nothing; fixed in batch 33's fix wave.
- 2026-10-10 QUESTION FOR THE SPEC: a replacement of one section or item that names a later version of its artifact's type moves and checks the whole artifact; no line says a part's replacement may name a version. Repro: replace one section of a decision at version 1 naming version 2. — recommended: only a replacement of the whole artifact may name a version; one of a part naming one is refused with rule version.
- 2026-10-10 QUESTION FOR THE SPEC: a type's own replacement naming a version goes through the artifact's rule against the versions of the type that describes types; no line covers it. Repro: replace a type naming https://missingmass.io/kb/type@1. — recommended: as any artifact (it names the version of the type of types it conforms to); no change.
- 2026-10-10 slice 163.3 green. Someone can now: read the storage port and its SQLite adapter and find only what a change itself is checked for (the revision it read, the revisions of the types it was read through, links landing, links into what a set removes or drops, entry ids held once); the suite passes what it passed less the three deleted port cases, and the search for Relink, relinks, reread, _restated and kinds= in src/kb and tests finds nothing.
  Surprised by: nothing. No test beyond the three listed handed relinks or kinds to land, so no other test changed. Draft.remove no longer reads the artifact it removes (it did only to note a removed type as changed).
  Open questions: spec/capabilities/check-a-change.md's 'Implementation, may change' lines still describe relinks (the controller's to route); links.handed's default to the latest version is used only by importing.py. Next: slice 164.
- 2026-10-10 Suite: 799 passed, 103 failed at effd7c9 in 23.7 s; failing: slice-164 onward scenarios and test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-10 slice 164 green. Someone can now: run the store's check and have each artifact judged by the version of its type it conforms to, listed as behind when its type has moved on. Surprised by: nothing; composition needed no change. Open questions: none. Next: slice 165.
- 2026-10-10 Suite: 803 passed, 99 failed at a3bad6f in 26 s; failing: slice-165 onward scenarios and test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-10 slice 165 green. Someone can now: define a type that reads a shape from, or is built on, a named version of another type and have its artifacts checked against that version whatever the other type moves on to, and point a link at artifacts of any version of a kind.
  Surprised by: both the link-field and the named-version scenarios, and two of the four could-never-check rows, went green on their steps alone (Tasks 2 and 3 already held and resolved versions); the only red on a Then was the shape refusal's message, which said a type and now says a type version. composition.read_through followed each kb: reference through the latest version of the type named, and started from the latest version of the kind's type: it now follows the version the change was checked against and each reference at the version it names (two plain tests in tests/test_a_type_moving_under_a_change.py, red first).
  Open questions: (1) a type a kept version of another type refers to can be removed, its versions with it, leaving the reference dangling: a later write of an artifact read through it is refused with rule store (Unresolvable), no line says whether the removal should be refused; (2) the port still compares a type read through by the type's revision, so a change read through kb:<T>@1 is drafted again when T merely moves on to version 2, though what @1 reads cannot change; the exact comparison is that the version is still kept as made, which needs the port to take versions in Change.through. Next: slice 166.
- 2026-10-10 Suite: 814 passed, 93 failed at 56d9253 in 24 s; failing: slice-166 onward scenarios and test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-10 Batch 33 branch review at 9c8cd74: 814 passed, 93 failed (expected only); ready to merge with fixes. Fix now: a set changing a type twice checks only its last change as a type; vacuous listing assertions; a request's version converted in values.py; documents out of line; dead steps. Slice 165.1 from slice 165's review (a referred type is not removed). The export and import round trip of an artifact behind its type is broken until the slices cut next (backlog, RELEASE GATE).
- 2026-10-10 slice 165.1 green. Someone can now: rely on a type staying held, with every version of it, while any held version of another type refers to a shape of it or is built on it; its removal is refused on_delete naming each such type once, beside the artifacts of its kind.
  Surprised by: the port could not say which versions of a type are held (an import keeps the number its file gives, so 1..n is not it), so it gained one read, versions, answered by the draft too for what a set makes; and a removal drafted before a referring type was defined landed after it, which the port compares nothing of, so a set that removes a type is now drafted and landed only inside the port's exclusive block (write.py, drafted twice). The refusal is made in drafting.py against what the whole set leaves, not in edits.py as the task named.
  Open questions: a type removed and defined again in one set is refused as a removal is while another type reads it (no line says); a set's intermediate version of a type (changed twice in one set) is now read by the draft, which a kb: reference in the same set can therefore name. Next: slice 166.
- 2026-10-10 Suite: 828 passed, 93 failed at b95d130 in 24 s; failing: slice-166 onward scenarios and test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-10 Suite: 832 passed, 93 failed at 2f53623 in 26 s; failing: slice-166 onward scenarios and test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-11 Correction to slice 165.1's checkpoint: its Surprised-by said the order 'referring type drafted, removal lands first' was already covered, the referring change carrying the referred type among the types it was read through. It was not: a type's own define or change handed none of the types its schema refers to or is built on, so both landed and a create then answered with the store's own fault. Closed in 503c507: every change that leaves a type is read through the types the version it makes reads, a removed one is the port's conflict, and the redraft under the write lock refuses it with shape. Still open: the referred type removed and defined again between the draft and the landing stands at revision 1 again and is not seen (true of any change read through a type); and, no race needed, a reference to a shape a held version does not define is accepted when the type is written.
- 2026-10-11 Suite: 843 passed, 93 failed at 503c507 in 24 s; failing: slice-166 onward scenarios and test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-11 QUESTION FOR THE SPEC: a type removed and defined again in one set is refused while another type's version reads it (slice 165.1), and the removed type's versions go with it though define-a-type's Purpose says the capability removes no version. — recommended: reword the Purpose to 'removes no version of a type it holds' and leave the refusal; route with the next formulation.
