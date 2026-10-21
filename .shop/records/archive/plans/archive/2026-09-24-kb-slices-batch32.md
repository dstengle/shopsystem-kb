---
id: initiative-archive/missingmass.io/shopsystem/kb/2026-09-24-kb-slices-batch32
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

## Slice 154: The suite collects again and binds every scenario once
- Kind: enabling
- Check: `make test` -> no collection error; test_every_scenario_is_bound passes; every test that fails is a scenario tagged @slice-149 to @slice-153 or @slice-156 onward, or the published contract's rule-name test (slice 182)
- Observable: The suite runs every module again, so each later slice's red is an observation and not a collection error.
- Unknown: none
- Needs: none
- Status: green

## Slice 155: values.py split before the IRI conversions grow it
- Kind: enabling
- Check: `make test` -> the same passed and failed tests as slice 154's record; `wc -l src/kb/values.py` -> at most 200 lines, and no module under src/kb over 250
- Observable: The request conversions have room for kb's IRI grammar without crossing CLAUDE.md's size limit.
- Unknown: none
- Needs: the backlog line of 2026-10-01 (values.py at 241 of 250 lines)
- Status: green

## Slice 156: The client names its artifacts and types by IRI through kb.v2
- Kind: capability
- Scenarios: change-the-store / The client creates an artifact, giving its IRI and the IRI of the version of its type it conforms to; name-artifacts-and-items / An artifact created at an IRI of the client's choosing under its type's IRI is held at that IRI; change-the-store / The client replaces an artifact; define-a-type / The client defines a type, giving it an https IRI of kb's grammar; define-a-type / A type's IRI need not sit under the IRI of the type that describes types; define-a-type / The type that describes types is held at its own IRI
- Observable: A client creates types and artifacts at IRIs it chose, naming the version of the type each conforms to, and reads them back there, over kb.v2.
- Unknown: Whether every artifact, types included, can be held and found by the IRI its client chose, end to end through kb.v2
- Needs: kb.proto moved to package kb.v2 with its golden file; every tagged scenario's steps and the storage port's conformance tests moved to IRIs so they stay green; export and import place files by the path of the IRI so the tagged export, import and seeding scenarios stay green
- Status: green

## Slice 157: A store made before kb.v2 is refused
- Kind: capability
- Scenarios: answer-a-damaged-file / A store found that was made by a kb before contract v2 refuses every call and command that needs it
- Observable: A client or operator pointed at a kb.v1 store is told this kb can neither read nor move it, and nothing is written.
- Unknown: How a store made by a kb of contract kb.v1 is told apart from this kb's before anything is opened
- Needs: none
- Lands: 2 production, 2 test
- Status: green

## Slice 158: An artifact's IRI is its own for life
- Kind: capability
- Scenarios: name-artifacts-and-items / An artifact created at an IRI not under its type's IRI is refused; name-artifacts-and-items / An artifact created at an IRI the store already holds an artifact at is refused; name-artifacts-and-items / An artifact keeps the IRI it was created with for life; name-artifacts-and-items / After an artifact has been removed, a new artifact may be created at its IRI; name-artifacts-and-items / A title that reads as a date is still a title; name-artifacts-and-items / A title that reads as yes is still a title; name-artifacts-and-items / A title given as the yes-or-no true is still a title; name-artifacts-and-items / A title given as the number 12 is still a title
- Observable: A create is refused at an IRI outside its type's or one already held, an artifact keeps its IRI through every change, and a removed artifact's IRI can be taken again at a first revision.
- Unknown: Whether a removed artifact's IRI can start over at its first revision while the removed artifact's history is kept
- Needs: none
- Lands: 4 production, 2 test
- Status: green

## Slice 159: An artifact's identity travels beside its content
- Kind: capability
- Scenarios: hand-over-content / Content given to a create that carries what travels beside it is refused; read-an-artifact / Reading the whole artifact gives its IRI, its type version's IRI, its revision and its title beside its content; read-an-artifact / A link filled in comes with its IRI, its type version's IRI, its title and its revision, ahead of its content
- Observable: A client reads each artifact's IRI, type version IRI, revision and title beside its content, filled-in links included, and content that carries any of them is refused, each named back.
- Unknown: Whether the identity a read gives beside the content is exactly what content may not carry
- Needs: none
- Lands: 2 production, 3 test
- Status: green

## Slice 160: Creates in a set name each other by their IRIs
- Kind: capability
- Scenarios: make-several-changes-in-one-go / A create in a set points at what another create in it makes, earlier or later; make-several-changes-in-one-go / A link in a set to the IRI another create in it carries lands on what that create makes; make-several-changes-in-one-go / Two new artifacts in one set that point at each other by their IRIs land; make-several-changes-in-one-go / Two creates in one set that carry the same IRI are refused; make-several-changes-in-one-go / Each create in a set gives back its artifact's IRI and first revision, in the order of the set
- Observable: A client creates several artifacts in one set that point at each other by the IRIs it chose, with keys gone from the contract, and is given each IRI and first revision in order.
- Unknown: Whether a set's links to the IRIs its own creates carry resolve against the draft once keys are gone
- Needs: none
- Lands: 6 production, 4 test
- Status: green

## Log
- 2026-10-10 Batch batch31 archived to archive/2026-09-24-kb-slices-batch31.md; last 2026-10-10 Suite: 723 passed, 0 failed at b231c9c in 23 s
- 2026-10-10 Suite: 723 passed, 0 failed at b231c9c in 23 s
- 2026-10-10 Suite: 434 passed, 63 failed at 1809133 in 19 s; 9 test modules not collected (ScenarioNotFound: answer-a-damaged-file, add-an-item, change, check-the-store, create, export-and-import, list, read, remove); failing: the 28 operate-a-store backup and restore runs (K1), test_every_scenario_is_bound (2), the published contract's rule names, 14 define-a-type and 16 make-several-changes-in-one-go runs (K2/K3 scenarios with no steps), 2 operator check-the-store runs
- 2026-10-10 K2+K3 (contract kb.v2) sliced into 154 to 185 from the 102 untagged scenarios of 1809133 (151 collected runs): two enabling slices, then the kb.v2 identity skeleton (156), then by risk: type versions, placeholders, export through the contract, check-only sets, names and parts, import into any store. 38 replaced scenarios were removed by the K2 formulation; their bindings and the step definitions only they used go in slice 154.
- 2026-10-10 Batches: batch 32 = slices 154-160 (collect, values.py split, the kb.v2 identity skeleton, pre-v2 store refused, IRI for life, identity beside content, sets by IRI); batch 33 = 161-165 (type versions); batch 34 = 166-170 (placeholders); batch 35 = 171-176 (history position, export through the contract, path selection); batch 36 = 177-181 (check-only sets, IRI grammar, part names, set links to parts and placeholders, import into a store); batch 37 = 182-185 (import differs, placeholders and skips in import, the command line's offer, blocked on K1). The kb.v2 break lands whole in slice 156, so each batch ends with every scenario tagged up to it green and every failure a scenario of a later slice or of K1 (149-153, built on another branch).
- 2026-10-10 QUESTION FOR THE SPEC: when a type's IRI sits under another held type's IRI (https://x/decision and https://x/decision/sub), an IRI under both has two types: which one a create's IRI must sit under, and which type a placeholder at such an IRI has, no line says. Repro: define types at https://example.com/shop/decision and https://example.com/shop/decision/minor, then create a decision at https://example.com/shop/decision/minor/a, or link to it unheld. — recommended: an IRI belongs to the nearest type it sits under (the longest type IRI that is a whole-segment prefix of it); a create naming a version of another type is refused with rule identity, and a placeholder is typed by that nearest type. Applied in slices 158 and 167.
- 2026-10-10 K1 overlap: operate-a-store's 'The command line offers ... importing ...' was reformulated by K2 (import into a store) and lost its @slice-149 tag here; it is slice 185, blocked until K1 merges. Slice 149's Scenarios line still names it for the K1 branch; reconcile the tag when the branches meet.
- 2026-10-10 K1 (batch 31) merged into this branch; slice 185 unblocked
- 2026-10-10 slice 154 green. Someone can now: run the whole suite with every module collected and every formulated scenario bound once, so each later K2/K3 slice goes red on its own scenarios. Surprised by: the worktree venv has pytest-bdd 9.0.0, which no longer sets __scenario__, so test_every_scenario_is_bound read nothing; it now also reads pytest_bdd's scenario_wrapper_template_registry. Open questions: pyproject pins pytest-bdd>=8.1.0, so main's venv (8.1.0) and this one differ. Next: slice 155.
- 2026-10-10 Suite: 660 passed, 143 failed at d3db1a6 in 22 s; failing: the 28 operate-a-store backup and restore runs are NOT among them (K1 merged, they pass); failing are the scenarios tagged slice-156 onward that are now bound and test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-10 Suite: 660 passed, 143 failed at 2005c4d in 24 s; failing: the scenarios tagged slice-156 onward now bound, and test_the_rule_names_kb_gives_are_exactly_the_spec_lists (pytest-bdd pinned <9, 8.1.0 installed)
- 2026-10-10 slice 155 green. Someone can now: add the IRI conversions to values.py (199 lines) with roots.py owning the root, directory and file values. Surprised by: nothing. Open questions: none. Next: slice 156.
- 2026-10-10 Suite: 660 passed, 143 failed at 2441784 in 24 s; failing: the scenarios tagged slice-156 onward now bound, and test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-10 slice 156 green. Someone can now: create an artifact at an IRI they chose under its type's, naming the IRI of the type version it conforms to, define a type at any https IRI of kb's grammar, and read the type that describes types at https://missingmass.io/kb/type, all through kb.v2.
  Surprised by: the contract break moved every step module and the port's conformance tests at once; refusals.py would have crossed 250 lines, so the operator's directory and file faults moved to file_refusals.py (new row in CLAUDE.md); a kb: reference pinned to a version (decision 5) with one version held (decision 4) means a type built on another can no longer follow its base, so the plain test of a base moving under a change lost its built-on cases, and moving a base that another held type refers to leaves that reference naming a version no longer held (a create or relink through it escapes as a store fault); a create naming a version now refuses a create drafted before its type moved, so the concurrency test of a kind's type moving uses a replacement; the slice-158 title scenarios and the slice-179 item-title outline pass already on the migrated steps.
  Open questions: a type change that leaves another type's kb: reference naming a version no longer held is unhandled until several versions are held (slices 161 to 165); a create at an IRI already held is not refused until slice 158 (it escapes as a store fault from the port's conflict); bench/ and docker/ still build kb.v1 requests. Next: slice 157.
- 2026-10-10 Suite: 671 passed, 133 failed at bd159cd in 24 s; failing: the scenarios tagged slice-157 onward, and test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-10 Deferred to slice 165 (the person's ruling): changing a base type leaves a kb: reference to its old version dangling (store: NoSuchResource) while one version is held; slice 165 holds the version, restores the relink tests removed in slice 156, and pins it
- 2026-10-10 Probe: grep for STORE_FORM, EarlierKb, keys/keyed/values.key, identity/version/under, Conflict, Stub/CreateItem in kb.proto and the golden; marker run slices 157-160 (15 failed, 4 passed) -> 157: 2 production, 2 test; 158: 4, 2; 159: 2, 3; 160: 6, 4 (all within the budget)
- 2026-10-10 slice 157 green. Someone can now: point this kb at a store a kb before contract v2 made (marker store: 1, or the older contract marker) and be told, by every call and command, that an earlier version of kb made it and this kb can neither read nor move it, with nothing opened or written.
  Surprised by: EarlierKb no longer carries the directory of the store's files, since the message stopped naming it; refusals.earlier_kb takes the root alone and escapes.py follows.
  Open questions: a marker of store: 0, or any form below 1, is still answered as a later kb's (decision 7 names store: 1 only; no scenario covers another). Next: slice 158.
- 2026-10-10 Suite: 674 passed, 132 failed at 29b1b8c in 23 s; failing: the scenarios tagged slice-158 onward, and test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-10 Probe: six code-scouts over slices 157-185 (notes under .superpowers/scout/2026-10-10-sizing/: grep for version, TYPE_KIND, ids(, NoSuchResource, Replace*, Unlanded, placeholder, export, stream, path, differs, fresh, keys; marker runs of every slice) -> every slice's Lands set; over the budget: 161 (12 production, 4 test), 166 (8 production, 8 test), 175 (7 production, 5 test)
- 2026-10-10 Re-slice: 161 cut as expand, migrate, capability: 160.1 (the store keeps each type's version beside the type), 160.2 (types read through the kept versions), then 161 (writes make versions the store numbers; the client's version rule retired with it), 7 production, 3 test. 175 cut as 174.1 (the contract's path fields) then 175, 6 production, 3 test. 166 blocked until batch 34 is planned. Batch 33 = 160.1, 160.2, 161-165.
- 2026-10-10 RE-FORMULATE: change-the-store / the @slice-108 outline row 'removing the tag | new decision | a link must land on a node of a kind the type allows | neither the tag nor the new decision' is green today and contradicts check-a-change's placeholders (slice 166): with the tag removed and its type held, the new decision's link is to an IRI the store does not hold under a type the link allows. Evidence: .superpowers/scout/2026-10-10-sizing/slices-166-170.md. Recommended: the link lands on a placeholder and the decision is held (a removed IRI is an IRI not held; decision/removed-iris-may-be-reused).
- 2026-10-10 QUESTION FOR THE SPEC: export-and-import-a-store says an import that differs from what the store holds is refused and nothing lands, and that with errors skipped all but the broken files land; which holds for a differing file under --skip-errors no line says. Repro: a store holding a decision, a directory holding it with other content and one other clean file, kb import --skip-errors. — recommended: differing is refused whatever is skipped (it is not a broken file; skipping it would hide a conflict). Applies to slice 182.
- 2026-10-10 QUESTION FOR THE SPEC: with errors skipped, a file linking to an IRI nobody holds under a type whose only version in the directory is broken and skipped: the link's placeholder has no held type to stand under. Repro: slice 184's second row with the work item's link under the skipped type. — recommended: the file is left out with the type (a placeholder needs a held type, decision 0024), reported as skipped by its link's type. Applies to slices 183 and 184.
- 2026-10-10 Planner note for batch 36/37: the import keys files by the unversioned type IRI, so two version files of one type in a directory collide (slices 174, 181, 184); and once links to unheld IRIs are stored, reads of the linking artifact fail closed until slice 169 (order 169's guard with 166).
- 2026-10-10 slice 158 green. Someone can now: create an artifact only at an IRI under the type it names (the nearest held type it sits under) that the store holds nothing at, both refused with identity naming the IRI, and create a new artifact at a removed one's IRI, starting at revision 1.
  Surprised by: a type's own create had to be left out of the under-its-type check (decision/type-iris-are-free) or no type could be defined; "An artifact keeps the IRI it was created with for life" and "After an artifact has been removed, a new artifact may be created at its IRI" went green on their step definitions alone, no production code (decision 8 already held, as the brief guessed).
  Open questions: whether an identity fault should stand alone or beside the create's title and content faults (it stands beside them, as the first; no scenario says); a create at exactly its type's IRI gets both identity faults (not under its type, and already held); whether an artifact may sit under another artifact's IRI (it may today, belonging to the type above; no scenario says); a set with two creates at one IRI is now refused by the draft on the second, before slice 160's own refusal exists. Next: slice 159.
- 2026-10-10 Suite: 703 passed, 128 failed at a0201db in 22 s; failing: the scenarios tagged slice-159 onward, and test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-10 slice 159 green. Someone can now: hand over content and be refused, each named back, when it carries the artifact's IRI, its type version or its revision, and read beside a whole artifact's content, and ahead of a filled-in link's, its IRI, its type version's IRI, its revision and its title.
  Surprised by: all three scenarios went green on their step definitions alone; settled.py already refuses the four identity keys with `identity` and read.py already gives a filled-in target id, type, revision and title first. No production code changed.
  Open questions: the task named Stub gaining `revision` in kb.proto (and the golden); it was not added, because a filled-in link is the target in the content, not a Stub, and no scenario or Behaviour line of read-an-artifact reads a stub's revision, so the published contract would change with nothing red asking for it. The controller decides whether Stub carries one. Next: slice 160.
- 2026-10-10 Suite: 706 passed, 125 failed at 0469ae3 in 22 s; failing: the scenarios tagged slice-160 onward, and test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-10 slice 160 green. Someone can now: land a set of creates that name each other by the IRIs they carry, earlier or later in the set, with no key anywhere in the contract.
  Surprised by: every scenario went green on its step definitions alone, since slice 158's held-in-the-draft check already refuses each create after the first at one IRI, so changes.py got no check of an IRI carried twice; the step's grep still finds six lines of `spot.key` in places.py, edits.py and links.py, the mapping key or index a place's node stands under, there before this task and nothing of a set's key.
  Open questions: a create that does not convert, at an IRI an earlier create of the set carries, gets its conversion fault only and no `identity` (decision 10 read strictly asks for one; no scenario does); the fault for an IRI carried twice in a set says the store already holds one at it, though the set does; README.md line 18 still describes the key (the release slice's). Next: slice 161.
- 2026-10-10 Suite: 714 passed, 118 failed at a63a474 in 23 s; failing: the scenarios tagged slice-161 onward, and test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-10 Suite: 721 passed, 118 failed at 95f0b87 in 23 s; failing: the scenarios tagged slice-161 onward, and test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-10 QUESTION FOR THE SPEC: once kb numbers a type's versions (decision/kb-numbers-type-versions), whether a type's content still carries version, and what a number the client sends means, no line says; the type that describes types requires an integer version in a type's content today. Repro: define a type with version 7 in its content, or change one sending the number it already has. — recommended: content keeps version and kb writes the number it gives there, a client's number neither required nor refused. Applied as decision 4 of batch 33's plan (slice 161).
- 2026-10-10 Batch 33 planned: .shop/records/archive/plans/2026-10-10-kb-batch33-implementation.md (160.1, 160.2, 161-165), from .superpowers/scout/2026-10-10-batch33/research.md
- 2026-10-10 Suite: 727 passed, 118 failed at 0a36085 in 23 s; failing: the scenarios tagged slice-161 onward, and test_the_rule_names_kb_gives_are_exactly_the_spec_lists
