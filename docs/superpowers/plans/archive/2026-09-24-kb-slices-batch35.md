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
`docs/superpowers/plans/archive/2026-09-24-kb-slices-batches1-25.md` and slices 124 to 127 in
`docs/superpowers/plans/archive/2026-09-24-kb-slices-batch26.md`, and slices 128 to 137 with 128.1 and 133.1 in
`docs/superpowers/plans/archive/2026-09-24-kb-slices-batch27.md`, all green. No slice is open.

## Slice 165.7: The port lands a link to an IRI not held, under a held type the link allows
- Kind: enabling
- Check: `make test` -> the same passed and failed tests as the record before it, with the storage port's conformance cases of a link to an IRI not held rewritten: it lands when it carries a held type the link allows and is refused otherwise; the domain still refuses every such link
- Observable: The storage port can keep a link to an IRI nothing is held at, vouched for by the held type it sits under, before the domain lets a client write one.
- Unknown: Whether the adapter can check a link to an IRI not held inside the landing transaction without knowing what a type declares
- Needs: expand of slice 166's breaking change: a link to an IRI not held is refused today at the adapter and in the domain
- Lands: 3 production, 1 test
- Status: green

## Slice 166: A link to an IRI not held lands on a placeholder
- Kind: capability
- Scenarios: check-a-change / An artifact pointing at an IRI the store does not hold, under a type it holds that the link allows, lands its link on a placeholder; query-the-store / The client asks for the placeholders; name-what-is-asked-for / A read by an IRI links point at that the store does not hold is refused
- Observable: A client links to something not yet written and finds it again by asking for the placeholders, each with every link into it; reading it is not found.
- Unknown: Whether a link can be kept on an IRI the store does not hold and found again from the link index
- Needs: none
- Lands: 4 production, 3 test
- Status: green

## Slice 166.1: The client asks for the placeholders
- Kind: capability
- Scenarios: query-the-store / The client asks for the placeholders; check-a-change / An artifact pointing at an IRI the store does not hold, under a type it holds that the link allows, lands its link on a placeholder
- Observable: A client links to something not yet written and finds it again by asking for the placeholders, each with every link into it.
- Unknown: Whether the links whose targets are not held can be listed from the link index at one moment
- Needs: a new rpc in the published contract
- Lands: 6 production, 4 test
- Status: green

## Slice 166.2: A type is not removed while a link waits under it
- Kind: capability
- Scenarios: define-a-type / Removing a type while a link waits on an IRI under it is refused
- Observable: A client removing a type that links wait under is refused, each linking artifact named, where today the removal lands and leaves links the store would refuse.
- Unknown: Whether the links waiting on IRIs under a type can be found when it is removed, and held against a link landing at the same moment
- Needs: the storage port's race of a type's removal and a link under it, pinned in both orders
- Lands: 4 production, 3 test
- Status: green

## Slice 166.3: A type is not defined over what already sits under another
- Kind: capability
- Scenarios: define-a-type / Defining a type under another type's IRI, over what already sits there, is refused
- Observable: A client defining a type nested under another type's IRI is refused while artifacts of that other type, or links waiting on them, sit under the new type's IRI, each named.
- Unknown: Whether what sits under a new type's IRI can be found, and held against a create or link landing there at the same moment
- Needs: none
- Lands: 4 production, 2 test
- Status: green

## Slice 167: A placeholder is typed by the type its IRI sits under
- Kind: capability
- Scenarios: check-a-change / An artifact pointing at an IRI under a type the store does not hold is refused; check-a-change / An artifact pointing at an IRI the store does not hold, under a type the link does not allow, is refused; check-a-change / An item pointing at an IRI under a type the store does not hold is refused; check-a-change / An artifact with several faults reports them all
- Observable: A client's link to an IRI not held is refused when no held type holds it or the link field does not allow that type.
- Unknown: Whether a link's targets can be checked against the type an unheld IRI sits under, inside the landing transaction
- Needs: none
- Lands: 0 production, 2 test
- Status: green

## Slice 168: A placeholder is filled by creating what it names
- Kind: capability
- Scenarios: check-a-change / An artifact pointing into a part of an IRI the store does not hold, under a type it holds that the link allows, lands its link on a placeholder; check-a-change / An artifact pointing into a part a held artifact does not have is refused; check-a-change / Creating an artifact at an IRI links already point at fills the placeholder; check-a-change / Creating an artifact without the part a link points into leaves that link on a placeholder
- Observable: A client creates the artifact a link was waiting on and the link lands on it, while a link into a part the new artifact lacks stays a placeholder.
- Unknown: Whether creating an artifact fills the links waiting on its IRI, and on its parts, with no relinking
- Needs: none
- Lands: 0 production, 1 test
- Status: green

## Slice 169: Reads mark a link that lands on nothing held
- Kind: capability
- Scenarios: read-an-artifact / At a glance, the stub of a link to an IRI the store does not hold is marked as not held; read-an-artifact / A link to an IRI the store does not hold comes back marked as landing on nothing held, at any level and following links or not
- Observable: A client reading at any level can tell a link to something not held from one that lands, and nothing is filled in for it.
- Unknown: Whether every read level can mark a link's target as not held without a read per link
- Needs: none
- Lands: 4 production, 3 test
- Status: green

## Slice 170: The check lists placeholders apart from violations
- Kind: capability
- Scenarios: check-the-store / A store holding links to IRIs it does not hold lists each placeholder with what links to it; check-the-store / A store whose only findings are placeholders reports no violation; check-the-store / Every violation is reported; operate-a-store / The operator checks the whole store; operate-a-store / The operator checks a store whose only findings are placeholders
- Observable: A client's check and the operator's kb validate list every placeholder with each link into it, apart from violations and from what is behind, and a store with only placeholders checks clean.
- Unknown: Whether the check's answer and kb validate's report can carry placeholders as a third list
- Needs: none
- Lands: 3 production, 4 test
- Status: green

## Slice 170.1: A link that waits keeps waiting when its artifact changes
- Kind: capability
- Scenarios: check-a-change / Changing an artifact that holds a link waiting on a part its target lacks leaves the link waiting
- Observable: A client changes an artifact that holds a link left waiting on a part its target lacks, and the change lands with the link still waiting, where today every change to it is refused.
- Unknown: Whether the domain and the port can both tell a link that already waits from one a change makes
- Needs: one judgement of whether a link already waits, used by the draft's check, the port's landing check and the store's check
- Lands: 5 production, 3 test
- Status: green

## Slice 170.2: drafting.py, cli.py and edits.py split before batch 36 grows them
- Kind: enabling
- Check: `make test` -> the same passed and failed tests as the record before it; `wc -l` -> src/kb/drafting.py at most 215, src/kb/cli.py at most 200, src/kb/edits.py at most 200, and no module under src/kb over 250
- Observable: The modules the next slices land in (a set checked only, a create naming its parts, the command line's offer) have room for them.
- Unknown: none
- Needs: the batch 35 review's refactors A, B and C: what stands in the way of a type's removal moves to standing.py; the printing of the check's lists and the import's report to a module of its own; a create's identity and naming to a module of its own
- Lands: 6 production, 0 test
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
- 2026-10-11 Batch batch34 archived to archive/2026-09-24-kb-slices-batch34.md; last 2026-10-11 Suite: 878 passed, 91 failed at 1fe51e3 in 25 s; failing: slice-166 onward scenarios, test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-11 Suite: 878 passed, 91 failed at 1fe51e3 in 25 s; failing: slice-166 onward scenarios, test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-11 Re-slice: 166 cut as 165.7 (expand: the port), 166 (the domain, with a guard so the linking artifact still reads) and 166.1 (the placeholders query and rpc); its two scenarios of the listing are retagged slice-166.1 and the re-formulated change-the-store outline (decision/a-link-to-a-removed-artifact-waits-on-a-placeholder, the RE-FORMULATE entry answered under the person's delegation) is slice 166's. Batch 35 = 165.7, 166, 166.1, 167 to 170. From .superpowers/scout/2026-10-10-batch34/research.md.
- 2026-10-11 slice 165.7 green. Someone can now: hand the port a link to an IRI not held that carries the held type it sits under (Link.under, filled by links.handed from composition.nearest_type) and have it land when that type is held and among the link's kinds, while a client still sees every such link refused by the domain.
  Surprised by: an artifact's link to its own type allows the kind of types, and the type of types is always held, so a carried type alone would let an artifact land under a type not held: the adapter refuses an implicit link to an IRI not held whatever it carries, and links.handed gives it none; the suite did not collect at the start (test_remove_an_artifact.py bound the outline by its old title), repaired alone in 5c1471a, so this task's baseline is 877 passed, 92 failed at 5c1471a, not the last record's.
  Open questions: a link drafted while its target was held carries no type, so when a removal lands first the port still refuses it as Unlanded and write.py answers unlanded: slice 166 must draft it again or carry the type for a held target too; a link into a part of an IRI not held lands at the port unchecked (decision 3), with no case of its own here; removing a type while links wait on IRIs under it is not refused by the port, nothing being stored for them. Next: slice 166.
- 2026-10-11 Suite: 893 passed, 92 failed at a028a68 in 24 s; failing: slice-166 onward scenarios (among them the removing-the-tag example of the removal-and-link outline), test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-11 QUESTION FOR THE SPEC: a type may be removed while links wait on IRIs under it (placeholders), since nothing is stored for a placeholder and no artifact of its kind exists; the links then name IRIs under no held type, which a new link could not. Repro (after slice 166): define tag, link a decision to an unheld tag IRI, remove the tag type. — recommended: the removal is refused because something still points at it, naming each linking artifact, as it is while artifacts of its kind exist; to be formulated and cut as a slice inside batch 35.
- 2026-10-11 HAND-BACK slice 166, test tests/test_links_as_the_port_takes_them.py::test_a_link_carries_the_held_type_a_target_not_held_sits_under[held] | test tests/test_a_type_moving_under_a_change.py::test_a_create_naming_an_earlier_version_is_held_to_the_links_that_version_makes | test tests/test_export_and_import_a_store.py::test_a_link_to_nothing_in_a_field_only_the_version_a_file_names_reads_as_a_link_is_reported: an existing test can only stay green by being rewritten, and the task does not list it under "Tests the decisions break" (the first by decision 10, the other two by decisions 1 and 2).
  Evidence: "assert (ArtifactId(decision/a), ArtifactId(https://shop.example/kb/decision)) == (ArtifactId(decision/a), None)" (a link to a held target now carries the held type it sits under); "assert [] == [(\"about\", \"ref\")]" (a note of an earlier version linking to tag/a, not held, under the held tag type its field allows, now lands); "assert (0, []) == (1, [(\"shop.example/kb/note/...yaml\", \"ref\")])" (an import file linking to decision/nothing-by-this-name, not held, under the held decision type, now checks clean).
  Green in this slice: A read by an IRI links point at that the store does not hold is refused; A removal and a new link to the same artifact made at once are each judged against what the other left (both examples). Red: none of the slice; the three tests above, left as they were.
- 2026-10-11 slice 166 green. Someone can now: create or change an artifact whose link names an IRI the store does not hold, under a held type the link field allows (into a part too, where the field may point into one), and have it land and still read at every level and through Follow, the IRI coming back alone, never filled in or walked on from; a link made at once with its target's removal lands on the removed IRI when the removal lands first, and a create at an IRI made at once with a create linking to it lands in either order with the link on what was created.
  Surprised by: three existing tests the brief did not list were broken by the decisions (links.handed's held row by decision 10; the earlier-version create's refusal of a link to a tag not held, and the import check's link to nothing under the held decision type, by decisions 1 and 2), handed back at f723d5d and decided by the plan; the import check, through validation.validate, no longer reports a link to something neither in the directory nor held when it sits under a held allowed type; examining._fit's filter of ref faults at unread files is now largely redundant; the create-at-an-IRI race through the contract passed as written, in both orders, a pin.
  Open questions: Follow narrowed by kind leaves an IRI not held out, it having no kind (slice 167 types a placeholder by the type it sits under and may want it matched); the import no longer reports a link to something neither in the directory nor held under a held allowed type, ahead of slice 183, which owns what the import says of it; a set that removes an artifact and links to it at once now leaves the link waiting on the IRI where it was refused, no test pinning either; reads of an artifact linking into a part of an IRI not held were not probed (slice 168's). Next: slice 166.1.
- 2026-10-11 Suite: 909 passed, 90 failed at 5160fee in 26 s; failing: slice-166.1 onward scenarios, test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-11 Small change (integrating-a-proposal, formulating-features): two Behaviour lines in define-a-type and decision/a-types-place-is-settled-by-what-sits-under-it, from slice 165.7's review (a type removed while links wait under it; a nearer type defined between a link and the create it waits on) and the batch 32 backlog line on a type defined above held artifacts; sliced as 166.2 and 166.3, counts estimated (they add checks beside the removal's and the define's existing ones).
- 2026-10-11 slice 166.1 green. Someone can now: ask a store for its placeholders through the rpc Placeholders, in process or through a server, and be given each IRI (or part) links point at that the store does not hold, with every link into it.
  Surprised by: the step "the decision {how}" in tests/test_check_the_store.py matched the new scenario's "the decision also points at..." and had to be narrowed to the two wordings it reads; the scenario needs a decision with two link fields and a work item whose steps link, so its types are the test's own; the every-rpc row for a damaged database stayed red through step 1, since an rpc that reads nothing does not find the damage.
  Open questions: a link into a part a held artifact lacks is listed by the port and the query (decision 5) with only port cases behind it, its scenario being slice 168's; implicit links are left out by the SQL though the port never lets one land on nothing held, so no case can show that red. Next: slice 167.
- 2026-10-11 Suite: 924 passed, 91 failed at a3c7641 in 31 s; failing: scenarios tagged slice-166.2 onward (among them the three of test_define_a_type.py not bound yet), test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-11 QUESTION FOR THE SPEC: what a read shows for a link into a part of an artifact (held or not); today a read at a glance, a whole read following links, and Follow outward of an artifact holding such a link are refused with locator, for a held target too. Repro: a decision that supersedes https://.../decision/older#options/a, then Read it at a glance. — recommended: at a glance the stub of the artifact the part is in (the bare IRI when not held); following links, the link stays the reference written, not filled in; Follow reaches the artifact the part is in. Applied in slice 166's fix round.
- 2026-10-11 Correction to slice 166's checkpoint: a set that removes an artifact and links to it is refused whole (on_delete), in both orders, and no rpc can make such a set; the link is not left waiting.
- 2026-10-11 Suite: 938 passed, 91 failed at cc829fb in 25 s; failing: scenarios tagged slice-166.2 onward, test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-11 slice 166.2 green. Someone can now: be refused the removal of a type while a link waits on an IRI under it that the store does not hold, each artifact holding such a link named once beside the artifacts of its kind and the types that read it, and that holds when the link and the removal are made at once, in either order.
  Surprised by: nothing new was needed at the port: its read of waiting links (slice 166.1) and its landing check of the type a link carries (slice 165.7) already hold both orders once the removal is drafted under the write lock, as slice 165.1 made every removal of a type; the port still lands such a removal when handed one, pinned by a port case, since it knows nothing of which IRIs sit under which. tests/test_every_scenario_is_bound.py does not fail for slice 166.3's outline, which scenarios() binds.
  Open questions: a set that removes a type and, in the same set, a nearer type under it names the artifact waiting under the nearer one in both removals' refusals (no scenario; the set is refused either way). Next: slice 166.3.
- 2026-10-11 Suite: 947 passed, 90 failed at bf1f0bf in 25 s; failing: scenarios tagged slice-166.3 onward, test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-11 Suite: 948 passed, 90 failed at 30e4261 in 26 s; failing: scenarios tagged slice-166.3 onward, test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-11 slice 166.3 green. Someone can now: define a type under another type's IRI only where nothing held or waited on already belongs to that other type, and be told each IRI that does, whichever of the define and what lands under it lands first.
  Surprised by: both orders of the race were open, and the port compares nothing for either, so every define of a type, every create with an IRI between it and its type's, and every link to an IRI not held with an IRI between it and its type's is now drafted twice, the second time under the write lock (write.py, standing.movable); a new module standing.py holds the read and that question (row in CLAUDE.md); the port and the adapter did not change.
  Open questions: a define under the type of types' own IRI is refused while a type is held under the new one's, by the decision's letter, though a type's IRI is free; a type imported (not defined) under another's is not checked; a held type's change is not in question. Next: slice 167.
- 2026-10-11 Suite: 961 passed, 88 failed at f0a78b7 in 31 s; failing: scenarios tagged slice-167 onward, test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-11 slice 169 green. Someone can now: read an artifact at a glance and see which stubs are of IRIs the store does not hold (`Stub.not_held`, Follow's stubs too), or read it whole, following links or not, and be given beside the content each link of it that lands on nothing held (`Artifact.placeholders`, the Placeholders rpc's message), the link itself left as written.
  Surprised by: the Background's decision type has no second link to a decision, so the Given moves the type on to a version with one (`revisits`) and replaces the decision naming that version; Follow needed no change, its stubs being `read.py`'s; a link into a part its held artifact lacks is marked in a whole read by reading that artifact once for each such link (`places.holds_part`).
  Open questions: at a glance a link into a part its held artifact lacks carries no mark, its stub being of the held artifact, and a summary gives no placeholders; a whole read following links marks only the links of the artifact read, not those of the artifacts filled in (`Linking.artifact` leaves room for them); a section read gives none, a section holding no links. Next: slice 170.
- 2026-10-11 Suite: 977 passed, 83 failed at 34b552f in 26 s; failing: scenarios tagged slice-167, slice-168 and slice-170 onward, test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-11 slice 167 green. Someone can now: see a link to an IRI under a type the store does not hold, or under a held type the link does not allow, refused with rule ref, for an artifact, an item, and beside other faults. Surprised by: nothing; only step definitions were missing. Open questions: none. Next: slice 168.
- 2026-10-11 slice 168 green. Someone can now: link into a part of an IRI the store does not hold and see it listed as a placeholder with its part; create the artifact at that IRI and find the link landing on it; see a link into a part the new artifact lacks stay listed; and see a link into a part a held artifact lacks refused. Surprised by: nothing; step definitions only. Open questions: after a create at a waited-on IRI lacking the part a link names, the whole-store check lists that link as a ref violation (slice 170). Next: slice 170.
- 2026-10-11 Suite: 986 passed, 75 failed at 26b765b in 30 s; failing: scenarios tagged slice-170 onward, test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-11 HAND-BACK slice 170, scenario "A store holding links to IRIs it does not hold lists each placeholder with what links to it" | test tests/test_check_the_store.py::test_a_store_holding_links_to_iris_it_does_not_hold_lists_each_placeholder_with_what: the scenario cannot be made to fail on its Then line, only on its Given, which describes a state the store cannot represent: a link held "from one of its sections" (decision/0011-sections-carry-no-links: a section has exactly title, body and sections; `ref` is read only on a field of a type or of a collection's items).
  Evidence: the Given written as worded, a decision whose purpose holds the link beside its title and body, is refused at the create: `AssertionError: [artifact: "https://shop.example/kb/decision/prices-are-reviewed-daily" place: "sections/0" rule: "additionalProperties" message: "Additional properties are not allowed ('supersedes' was unexpected)"]`. The Then ("the decision and the field, and the decision and the section") was never reached.
  Green in this slice: check-the-store / A store whose only findings are placeholders reports no violation; check-the-store / Every violation is reported. Red: check-the-store / A store holding links to IRIs it does not hold lists each placeholder with what links to it (handed back); operate-a-store / The operator checks the whole store and operate-a-store / The operator checks a store whose only findings are placeholders (step 2, not started).
- 2026-10-11 RE-FORMULATE answered (slice 170's hand-back at c35a777): check-the-store / 'A store holding links to IRIs it does not hold lists each placeholder with what links to it' asked for a link held in a section, which no store can hold (decision/0011-sections-carry-no-links); its Behaviour line names no place. The Given and Then now say one of its items where they said one of its sections; no line changed. Under the person's delegation.
- 2026-10-11 slice 170 green. Someone can now: check a store, through the client or with kb validate, and be given every placeholder with each link into it, listed apart from the violations and from what is behind its type, a store whose only findings are placeholders checking clean.
  Surprised by: the first formulation asked for a link held in a section, which no store can hold (handed back, re-formulated to an item); a link into a part its held artifact lacks is a ref fault to validation, so the check leaves that fault out for each link that waits; operate-a-store's 'checks clean' scenario went green on its step definitions alone, kb validate having always failed only on a violation.
  Open questions: kb validate prints a placeholder's IRI, the linking artifact and the link's place, never the part a link names, no scenario asking for it; a link that waits and that validation would also refuse for another reason (a type its field does not allow) would be in both lists, a state no write reaches (a nearer type is refused with identity, a type linked under cannot be removed, a narrowed type leaves the artifact on its version). Next: slice 171.
- 2026-10-11 Suite: 993 passed, 70 failed at fa6729e in 26 s; failing: scenarios tagged slice-171 onward, test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-11 QUESTION FOR THE SPEC: when a type is defined under the IRI of the type that describes types, does a type already held under the new IRI stand in the way (slice 166.3 refuses it, against decision/type-iris-are-free)? — recommended: no; types do not belong to the type of types by where they sit; a link waiting there still stands in the way. Applied in slice 166.3's fix round.
- 2026-10-11 Suite: 1001 passed, 70 failed at 6f32754 in 28 s; failing: scenarios tagged slice-171 onward, test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-11 Suite: 1007 passed, 70 failed at 773b781 in 27 s; failing: scenarios tagged slice-171 onward, test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-11 Suite: 1012 passed, 70 failed at ce380e0 in 26 s; failing: scenarios tagged slice-171 onward, test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-11 QUESTION FOR THE SPEC: kb validate's line for a placeholder: whether it shows the part a link names. — recommended: yes, the IRI, # and the part, so a link into a part and one to the whole of an IRI print apart. Applied in slice 170's fix round.
- 2026-10-11 QUESTION FOR THE SPEC: define-a-type refuses a type defined over what sits 'under' it; whether a link waiting on the new type's own IRI stands in the way too. Repro: a decision superseding decision/ghost (not held), then a type defined at decision/ghost lands and the check reports ref on the untouched decision. — recommended: yes, the IRI itself counts; the define is refused naming it. Applied in batch 35's fix wave.
- 2026-10-11 QUESTION FOR THE SPEC: a set removing a type and a nearer held type under it names a waiting artifact in both refusals (decision 11 of batch 35's plan does not say). — recommended: keep it; each removal says what stands in its own way.
- 2026-10-11 Batch 35 branch review at 7410e63: 1012 passed, 70 failed (expected only); with fixes. Fix now: a type may be defined at the very IRI a link waits on (standing.under); write.py spells IRI#part itself; a published comment's wording. A slice with its line (170.1): an artifact holding a link into a part its filled target lacks cannot be changed at all. Enabling splits before batch 36: drafting.py, cli.py, edits.py. The export of a store in that lacking-part state cannot be imported: backlog, RELEASE GATE, with slice 183.
- 2026-10-11 Suite: 1018 passed, 70 failed at 4917dcd in 31 s; failing: scenarios tagged slice-171 onward, test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-11 slice 170.1 green. Someone can now: change an artifact that holds a link waiting on a part its target was created without (replace it whole, a section, an item, add or drop an item, alone or in a set) and the link still waits, listed as a placeholder, while a link the change adds or alters into a lacking part is still refused ref.
  Surprised by: it landed in 9 production modules and 4 test, over the budget of 8, so the Lands line is left as planned (the plan script refuses 9): beside the six the task names, draft.py (the links that waited before the draft), sqlite_reads.py (the port's waiting read narrowed to one artifact, so a write reads only its own artifact's rows) and sqlite_store.py (two lines, the waiting links read before any of the set is written, or a set that drops the part and keeps the link would pass as waiting); the mark is the store's own account (the link was held landing on nothing held), so a change drafted while the target was not held still lands after a create there without the part; removing the target of such a link is refused on_delete as before, so the removal race cannot arise through the contract.
  Open questions: a waiting link inside an item of a collection changes place when an earlier item is removed, and is then judged as new and refused (the decision says same field and place); the decision's last sentence (an import lets such a link wait) is not done here, examining.py passes no waiting links; read.py keeps its own copy of whether a link lands (backlog). Next: slice 170.2.
- 2026-10-11 Suite: 1056 passed, 70 failed at 9aaf196 in 28 s; failing: scenarios tagged slice-171 onward, test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-11 Slice 170.1 landed in 9 production and 4 test modules against its estimate of 5 and 3, one production module over the budget (the plan script refuses to record the count): the one judgement had to be handed through the draft, the port's read and the adapter's landing check. Not re-cut after the fact; recorded for the sizing of slices that hand a new fact to the port.
- 2026-10-11 slice 170.2 green. Someone can now: grow drafting.py and edits.py in batch 36 with room under the limits; drafting.py 215, edits.py 194, new reports.py and naming.py. Surprised by: cli.py stops at 215, not 200 (the parser and dispatch in main are what is left). Open questions: move the argument parser out of cli.py to meet 200? Next: slice 171.
- 2026-10-11 Suite: 1056 passed, 70 failed at f136ec4 in 29 s; failing: slice-171 onward scenarios and test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-11 QUESTION FOR THE SPEC: check-a-change's line lets a change land that 'leaves that link as it is'; whether a waiting link is still that link when an earlier item of its collection, or an earlier link of its field, is removed or reordered (its place by index moves). — recommended: yes; the link is the same when it has the same target and part in the same field of the same artifact or named item, wherever it stands in a list. Applied in slice 170.1's fix round (batch 35 plan, decision 14).
- 2026-10-11 Suite: 1077 passed, 70 failed at be68fc8 in 31 s; failing: scenarios tagged slice-171 onward, test_the_rule_names_kb_gives_are_exactly_the_spec_lists
- 2026-10-11 QUESTION FOR THE SPEC: an import or seed of a file whose item has no id lands the item unnamed, where a write names every item; kb import --check calls it clean. — recommended: the import names items as a write does (or the check reports an item with no name); decide with the import slices (181 onward).
- 2026-10-11 HAND-BACK slice 170.1 (fix round 2), test tests/test_a_link_that_waits_keeps_waiting.py::test_a_change_that_leaves_a_link_waiting_in_an_item_with_no_name_lands_and_the_link_still_waits[imported], [seeded]: going green needs work the ruling does not name. An item with no name told by where it stands (links.py) makes the check clean again, but every write names its artifact's unnamed items (naming.py through names.items), so in any change the link is held by `options/second` where the store held it by `options/1`, and it is refused as new.
  Evidence: assert not changed.faults: rule: "ref", place: "options/1/replaces", message: "a link must land on a node of a kind the type allows; 'https://shop.example/kb/decision/prices-are-reviewed-monthly#options/rollback' does not".
  Green in this slice: the slice-170.1 scenario; test_a_link_that_waits_in_an_item_with_no_name_still_waits_once_its_target_is_created_without_the_part[imported], [seeded]; the links.py pin of an unnamed item's holder. Red: the two cases named.
- 2026-10-11 Suite: 1079 passed, 72 failed at e4792f8 in 28 s; failing: scenarios tagged slice-171 onward, test_the_rule_names_kb_gives_are_exactly_the_spec_lists, test_a_change_that_leaves_a_link_waiting_in_an_item_with_no_name_lands_and_the_link_still_waits[imported], [seeded]
- 2026-10-11 Suite: 1079 passed, 70 failed, 2 skipped at 155a51e in 26.5 s; failing: the scenarios of slices 171 onward and test_the_rule_names_kb_gives_are_exactly_the_spec_lists; skipped: the two cases of a change to an artifact whose imported item has no name (slice 180.2)
