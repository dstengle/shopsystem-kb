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

## Slice 180.1.1: The part read leaves read.py and the place walk has one home
- Kind: enabling
- Check: `make test` -> 1431 passed, 22 expected to fail, 0 failed; `wc -l src/kb/read.py` -> at most 200; `grep -n '\[::2\]\|\[:-1:2\]' src/kb/read.py src/kb/edits.py` -> prints nothing
- Observable: What a place's node's type declares has one home, and the read of a part has a module of its own, so read.py has room for its next change.
- Unknown: none
- Needs: none
- Lands: 5 production, 0 test
- Status: green

## Slice 180.1.2: Each change as the port takes it leaves drafting.py
- Kind: enabling
- Check: `make test` -> what the last record passes; `wc -l src/kb/drafting.py` -> at most 180
- Observable: The half of drafting.py that makes each change as the port takes it has a module of its own, so the import slices have room in drafting.py.
- Unknown: none
- Needs: none
- Lands: 2 production, 0 test
- Status: green

## Slice 180.2: An import names every item as a write does
- Kind: capability
- Scenarios: export-and-import-a-store / (to be formulated with the import batch: a file whose item carries no name is imported with the item named as a write names it)
- Observable: The operator imports a hand-written file whose item has no name and the store holds the item named, as every item a write makes is, so everything that tells items by name works for it.
- Unknown: Whether naming items on import keeps an export of a kb-written store importing byte for byte
- Needs: its Behaviour line and scenario (QUESTION FOR THE SPEC of 2026-10-11, recommended yes); brings back the two tests skipped at slice 170.1's close
- Lands: 2 production, 2 test
- Status: green

## Slice 181: An import lands in a store already holding artifacts
- Kind: capability
- Scenarios: export-and-import-a-store / The operator imports a directory that checks clean into a store, saying which role they are; export-and-import-a-store / The operator imports a directory that checks clean, and the history shows each type landing before its artifacts; export-and-import-a-store / The operator imports a directory holding an artifact the store already holds at the same IRI, with the same content and the same type version
- Observable: The operator imports into a store that already holds artifacts; what it holds identically is passed over and the rest lands.
- Unknown: Whether an import drafted over a store holding artifacts lands only what the store does not hold already
- Needs: none
- Lands: 4 production, 2 test
- Status: green

## Slice 181.1: An import into a served store is refused
- Kind: capability
- Scenarios: export-and-import-a-store / Importing into a store a server serves is refused
- Observable: The operator who imports into a store a server is serving is refused and told the server's address; nothing lands beside the server.
- Unknown: Whether the operator's import can ask after the server as a change asked directly does
- Needs: none
- Lands: 2 production, 1 test
- Status: green

## Slice 181.2: The skip analysis leaves examining.py
- Kind: enabling
- Check: `make test` -> what the last record passes; `wc -l src/kb/examining.py` -> at most 170; no module under src/kb over 250
- Observable: The import check's skip analysis has a module of its own, so examining.py has room for the errors slices 182.1 and 183 add.
- Unknown: none
- Needs: none
- Lands: 3 production, 0 test
- Status: green

## Slice 182: An import that differs from what the store holds is refused
- Kind: capability
- Scenarios: export-and-import-a-store / The operator checks a directory for import holding an artifact the store holds at the same IRI with other content or another type version; export-and-import-a-store / Importing a directory holding an artifact the store already holds at the same IRI with other content or another type version is refused
- Observable: The operator's check and import name every IRI whose file differs from what the store holds, with rule differs, and nothing lands.
- Unknown: How an import's artifact is compared with the one the store holds at its IRI, by content and type version and not revision
- Needs: the published rule names gain differs (the published contract's rule-name test)
- Lands: 4 production, 2 test
- Status: green

## Slice 182.1: An import holds each file to its type's place
- Kind: capability
- Scenarios: export-and-import-a-store / The operator checks a directory for import holding a file whose IRI does not sit under its type
- Observable: The operator's check reports a file filed under another type's IRI, or under none, as an error, so an import lands nothing a create would be refused.
- Unknown: Whether the checks a create's IRI is held to can be asked of a directory's files and the store together
- Needs: none
- Lands: 3 production, 1 test
- Status: green

## Slice 183: An import's links wait on placeholders
- Kind: capability
- Scenarios: export-and-import-a-store / The operator checks a directory for import and each error is reported by file and reason; export-and-import-a-store / The operator imports a directory holding a link to an IRI neither the directory nor the store holds, under a type one of them holds that the link field allows
- Observable: The operator's import lands a link to an IRI nobody holds on a placeholder, and the check reports a file only for a type nobody holds.
- Unknown: Whether the import check reads an unheld IRI's type from the directory and the store together
- Needs: none
- Lands: 6 production, 3 test
- Status: green

## Slice 184: Only a broken type version's reach is skipped
- Kind: capability
- Scenarios: export-and-import-a-store / The operator checks a directory for import that holds a type version's file with an error; export-and-import-a-store / The operator imports with errors skipped
- Observable: The operator sees and skips only the broken files, the type versions built on a broken one and what conforms to them; links to what was left out wait on placeholders.
- Unknown: Whether the skip analysis can follow type versions and kb: references alone, a link to an artifact's file no longer followed
- Needs: none
- Lands: 2 production, 1 test
- Status: green

## Slice 185: The command line offers import into a store
- Kind: capability
- Scenarios: operate-a-store / The command line offers setting up, checking, exporting, backing up, restoring and importing, and nothing else that changes what the store holds
- Observable: The operator's kb help offers import into a store beside setting up, checking, exporting, backing up and restoring.
- Unknown: none
- Needs: K1's backup and restore commands (slices 149 to 153, built on another branch) merged into this branch
- Lands: 1 production, 1 test
- Status: green

## Slice 186: bench, docker and README speak kb.v2
- Kind: enabling
- Check: `make bench` -> every bound met at the size bench/ states; `make image-check` -> passes; `grep -rn "kb\.v1\|kind=\|schema/schema\|v0\.7\.0" README.md bench docker` -> prints nothing; `make test` -> what the last record passes
- Observable: A client reading README.md, the bench and the image's check sees kb.v2: IRIs, types by version, the import into a store, backup and restore; the bounds and the image check run green.
- Unknown: Whether the bounds still hold at kb.v2's shapes (every type version held, placeholders, the import's two comparisons)
- Needs: docker for make image-check; lands in README.md, bench/ and docker/ only
- Lands: 0 production, 0 test
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
- 2026-10-11 QUESTION FOR THE SPEC: an export selecting a path: whether it gives any type's files, and with a type and a path together whether the type's version files come with the artifacts. — recommended: a path alone gives artifacts only; a type gives its version files and its artifacts; both together give the type's version files and its artifacts at or under the path. Applied as decision 5 of batch 37's plan (slice 176).
- 2026-10-11 QUESTION FOR THE SPEC: whether kb promises an order between two history positions (ids sort by moment, entries land in another order when a clock goes back), and whether the operator's kb export, Search, History, Snapshot and Placeholders gain selection by path. — recommended: a position names an entry and promises no order; an export's position is the entry landed last; none of those gains a path. Applied as decisions 3, 6 and 7 of batch 37's plan.
- 2026-10-11 QUESTION FOR THE SPEC: a set asked to be checked only while a server serves the store (a served store takes changes only through its server; a check writes nothing); and whether a single create or replacement may be checked only. — recommended: a checked-only set is a read: answered directly or through the server, never refused as served or busy; only sets of creates and of replacements carry the flag. Applied as decisions 1 and 3 of batch 38's plan (slice 177).
- 2026-10-11 QUESTION FOR THE SPEC: names a create gives its parts beside names the store mints in one collection; and a read by a part's IRI (<IRI>#<place>) against 'an artifact's name holds no #'. — recommended: given names are taken first and minted names avoid them; a clash between two given names, or a given name that is not a plain name, is refused; a read or a change may name a part by its IRI, a create's own IRI may not carry one. Applied as decisions 4 and 5 of batch 38's plan (slice 179).
- 2026-10-11 QUESTION FOR THE SPEC: a client readied with its own clock, asking a server for a set to be checked only, where a change from such a client is refused with rule clock. — recommended: answered; a check reads no clock and writes nothing. Applied in slice 177.
- 2026-10-11 QUESTION FOR THE SPEC: what a read that names a part (a locator with a place, or a part's IRI) gives: read-an-artifact's Implementation says the response returns node content and the contract's Locator says 'a node inside it otherwise', but no Behaviour line says it, and until slice 179's fix round such a read answered with the whole artifact. — recommended: the part named and nothing else of its artifact, at the level asked. Applied in slice 179's fix round.
- 2026-10-11 QUESTION FOR THE SPEC: a call giving both a part's IRI and a place is refused even when they agree; a type version's place (<type>@1 with place schema) reads while <type>@1#schema is refused; a given part name has no length bound, so a part's IRI can pass 512 characters. — recommended: keep the refusal; one spelling per call; bound a part's name so its IRI stays within 512. For formulation.
- 2026-10-11 QUESTION FOR THE SPEC: a set with a dropped linked part and another fault answers only the other fault, before and after slice 177, so 'every fault found' was never met for this refusal, while a removal's comes beside other faults. — recommended: it comes beside the set's other faults, as a removal's does; a slice of its own with a Behaviour line.
- 2026-10-11 QUESTION FOR THE SPEC: slice 179's ruling that a change's rules for item names apply at any depth means a Replace or an Add can no longer give a new name to an item inside an item, which landed before; a name inside an added item is refused item-name while the item's own is identity; no Behaviour line names depth. — recommended: keep it (a name is given at a create, at any depth, and never by a change); a Behaviour line in name-artifacts-and-items with the next formulation.
- 2026-10-11 Batch batch38 archived to archive/2026-09-24-kb-slices-batch38.md; last 2026-10-11 Suite: 1431 passed, 22 expected to fail, 0 unexpectedly passing, 0 failed at a1454c5 in 31 s
- 2026-10-11 Suite: 1431 passed, 22 expected to fail, 0 unexpectedly passing, 0 failed at a1454c5 in 31 s
- 2026-10-11 Batch 39 spec merged (a2b50fd): the import names items; a link into a lacking part waits; a difference is never skipped; a skipped type's links are left out; one history entry per file; a version nobody holds is a check error. New scenarios tagged slice-180.2 (an item that carries no name) and slice-183 (a link into a part the artifact lacks); changed rows in slices 181 to 184's scenarios. Slice 180.2's scenario is 'The operator imports a file holding an item that carries no name'.
- 2026-10-11 Suite: 1431 passed, 29 expected to fail, 0 unexpectedly passing, 0 failed at 44e78c8 in 27 s
- 2026-10-11 Probe: batch 39's research (.superpowers/scout/2026-10-11-batch39/research.md) -> 180.1.1 5 production (read.py needs the type version read out too, to reach 200 lines); 180.1.2 2; 180.2 2 and 2; 181 4 and 2 (not 'remove the fresh check': identical files and a new version of a held type meet a Conflict); 182 4 and 2; 183 6 and 3 (the lacking part reaches the port); 184 2 and 1; 185 1 and 1
- 2026-10-11 Batch 39 = 180.1.1, 180.1.2, 180.2, 181, 181.1, 182, 182.1, 183, 184, 185. Slices 181.1 (an import into a served store is refused) and 182.1 (a file held to its type's place) come from two defects the research found that slice 181 makes reachable on a store in use; lines and scenarios added under decision/an-import-is-held-as-a-change-is.
- 2026-10-11 QUESTION FOR THE SPEC: whether a name a file gives an item is checked as a create's is (plain, not repeated in its collection). — recommended: yes, an error of the check with rule item-name. Applied as decision 2 of batch 39's plan (slice 180.2).
- 2026-10-11 QUESTION FOR THE SPEC: whether a file's title is compared with the held artifact's when an import decides identical or differing (the capability names content and type version). — recommended: yes, everything the file gives but its revision. Applied as decision 7 of batch 39's plan (slices 181, 182).
- 2026-10-11 QUESTION FOR THE SPEC: an import bringing a type version numbered below the version the store's type stands at, which the store does not keep (a gap). — recommended: an error of the check (the store's type has moved past it); not built in batch 39, no scenario reaches it; a backlog line.
- 2026-10-11 QUESTION FOR THE SPEC: every imported link into a part its target lacks waits, not only one the exporting store held waiting (a file cannot tell them apart), so a hand-written directory with a mistyped part imports clean and lists a placeholder. — recommended: yes, as the Behaviour line says without condition; kb validate lists it. Applied as decision 11 of batch 39's plan (slice 183).
- 2026-10-11 QUESTION FOR THE SPEC: which chain a file skipped for its link shows when several versions of the link's type are broken. — recommended: the broken version file with the lowest number. Applied as decision 13 of batch 39's plan (slice 184).
- 2026-10-11 slice 180.1.2 green. Someone can now: change what a change is handed to the port (handing.py) without touching drafting.py. Surprised by: nothing; typed became public and a local of handed had to be renamed. Open questions: none. Next: 180.1.1/180.2/181.
- 2026-10-11 Suite: 1431 passed, 32 expected to fail, 0 unexpectedly passing, 0 failed at a6bc2e8 in 31 s
- 2026-10-11 slice 180.2 green. Someone can now: import or seed a file whose items carry no name and find every item named as a write names it, a name the file gives kept, the check and the landing agreeing and a bad or repeated name an error of the check (rule item-name). Surprised by: the scenario's Given names a store holding the type, but an import still goes only into a fresh store (slice 181), so the Given starts the store and the directory brings the type; the slice marker also gated the two brought-back tests, which lost it. Open questions: none. Next: slice 181.
- 2026-10-11 Suite: 1437 passed, 29 expected to fail, 0 unexpectedly passing, 0 failed at 1bc986f in 27 s
- 2026-10-11 Slice 180.1.1 green (lane A merged): the read of a part is parts.py, a type version read as an artifact is versions.py, the place walk's one home is composition.declared_at; read.py 182 lines
- 2026-10-11 Suite: 1437 passed, 29 expected to fail, 0 unexpectedly passing, 0 failed at 249f17a in 27 s
- 2026-10-11 slice 181 green. Someone can now: import a directory into a store that already holds artifacts, what the store holds identically (an artifact, or a version of a type at its number, revision not compared) passed over with no history entry and the rest landed as one signed set, a held type gaining the versions above the one it stands at.
  Surprised by: an import whose every file is passed over had to stop being refused as 'nothing would land' (now refused so only when no file is taken at all); a type version read at the store's revision would, for a version below the store's that it does not keep, have landed and left the type standing at the lower version, so only a version above the one the type stands at is read so.
  Open questions: QUESTION FOR THE SPEC: with errors skipped, a directory whose only files without errors are all held identically lands nothing and is answered with the report and no fault (not 'nothing would land'); is that the wanted answer. Until slice 182 a file that differs from what the store holds, a type version that differs from the one kept at its number, and a type version below the store's that it does not keep check clean and are refused whole by the import with an escaped Conflict (rule store), nothing landing. Next: slice 181.1.
- 2026-10-11 Suite: 1445 passed, 26 expected to fail, 0 unexpectedly passing, 0 failed at 31d1baf in 27 s
- 2026-10-11 slice 184 green. Someone can now: import with errors skipped and lose only the broken files, the type versions built on a broken version, the artifacts written against them and the artifacts linking under a type no version of which lands, a link to any other file left out waiting on a placeholder, and see the same list from the check first.
  Surprised by: five of the nine runs went green on their steps alone (the skip by type version and kb: reference was built in batch 34); one change, no longer following a link to an artifact's file and leading a link under a lost type to that type's version files, turned the other four. The merge over slice 181 needed no change to src: slice 181's three tests failed only for the test helper _decision, which the lane had taken out; it is back, and a plain test now shows a link under a type only the store holds landing on a placeholder with errors skipped.
  Open questions: a type's only version file that cannot be read as YAML makes a file linking under it an error (ref), not a skip; a type all of whose versions are skipped but none broken is counted as not landing, the chain running through the skipped version. Next: slice 185.
- 2026-10-11 Suite: 1466 passed, 17 expected to fail, 0 unexpectedly passing, 0 failed at 39a01cb in 29 s
- 2026-10-11 QUESTION FOR THE SPEC: a type's only version file that cannot be read as YAML makes a file linking under it an error (ref), not a skip with a chain; the check and the import agree. Repro: export a decision type, a work item type and a work item linking to decision/nowhere; overwrite decision@1.yaml with unreadable YAML; kb import D --check. — recommended: a skip with the chain to the unreadable file, as for a broken version; a backlog line.
- 2026-10-11 QUESTION FOR THE SPEC: with errors skipped, a directory holding one broken file and otherwise only files the store holds identically exits 0 and lands nothing. — recommended: keep; 'nothing would land' is refused only when no sound file is in the directory at all, so a store's own export imports again. Applied in slice 181.
- 2026-10-11 Slice 184: a type whose versions are all skipped by a kb: reference, none broken itself, counts as not landing; files linking under it are skipped with the chain through the skipped version (ruling; no scenario).
- 2026-10-11 Slice 181.2 green. Someone can now: add errors of a file to examining.py (155 of 250 lines); the skip analysis is skipping.py. Surprised by: beneath and held_back are shared by the check and the skip analysis, so they moved with it. Open questions: none.
- 2026-10-11 Suite: 1466 passed, 17 expected to fail, 0 unexpectedly passing, 0 failed at 715dd82 in 28 s
- 2026-10-11 Slice 181.1 green. Someone can now: be told by kb import that a store is served, and at what address, instead of writing under a running server. Surprised by: Operator needed a _hosted of False for the boundary's served check; the scenario's xfail left once the slice was green. Open questions: none.
- 2026-10-11 Suite: 1469 passed, 16 expected to fail, 0 unexpectedly passing, 0 failed at be66aa8 in 28 s
- 2026-10-11 Slice 182.1 green. Someone can now: check a directory for import and see a file filed under another type's IRI, or a type's file over what belongs to another type, reported as an identity error. Surprised by: a create's identity check holds the draft's own entry as already held, so naming.placed asks the place only. Open questions: none. Next: slice 182.2.
- 2026-10-11 Suite: 1473 passed, 14 expected to fail, 0 unexpectedly passing, 0 failed at 9e9a1fd in 29 s
- 2026-10-11 slice 182 green (with the fix round of slice 181's review). Someone can now: check a directory against a store that holds artifacts and be told, file by file with rule differs, every IRI at which it differs from the store, and see the import refused naming each such IRI, errors skipped or not, with nothing landed.
  Surprised by: identical had to become the canonical text of each side without its revision (Python equality passed over a mapping in another order, 1 for true, 1.0 for 1); a file written against a version only the directory brings, of an artifact the store holds, is a difference too; overriding decision 9, a type version below the one the store's type stands at that it does not keep, and one above it whose revision is not above the type's, are differences.
  Open questions: a copy of the type that describes types that differs from the store's is still rule content and is skipped with errors skipped, not rule differs; a directory holding only the type that describes types checks clean and its import is refused 'nothing in the directory would land', while a directory the store holds whole lands nothing and exits 0; a gap in a held type's versions can still be made by import (versions 1 and 3). Next: slice 183.
- 2026-10-11 Suite: 1491 passed, 8 expected to fail, 0 unexpectedly passing, 0 failed at bcaf9c7 in 28 s
- 2026-10-11 slice 183 green. Someone can now: import a directory whose link names an IRI neither it nor the store holds under a held type, or a part the artifact at its IRI lacks, and have the link land and wait on a placeholder, the check calling the directory clean as the import lands it.
  Surprised by: the six rows of the check outline and the two of the unheld-IRI outline needed no production code once slice 181 was in; the mark is set in handing.py, so links.py is unchanged (six production files of the seven named); a store's own export holding such a link was an error of the check even against the store it came from, and now is passed over.
  Open questions: QUESTION FOR THE SPEC (decision 11, already logged): every imported link into a part its held target lacks waits, whether or not the exporting store held it waiting, so a hand-written file can bring a link a create would be refused for. Next: slice 184.
- 2026-10-11 Suite: 1510 passed, 1 expected to fail, 0 unexpectedly passing, 0 failed at 85198a8 in 30 s
- 2026-10-11 slice 185 green. Someone can now: see in the command line's help that kb import goes into a store, fresh or already holding artifacts. Surprised by: nothing; CLAUDE.md's row already said so. Open questions: none. Next: none, batch 39's last slice.
- 2026-10-11 Suite: 1511 passed, 0 expected to fail, 0 unexpectedly passing, 0 failed at e6ccd62 in 28.5 s
- 2026-10-11 Suite: 1516 passed, 0 expected to fail, 0 unexpectedly passing, 0 failed at 0da8375 in 32 s
- 2026-10-11 Every slice of the plan is green at 0da8375 (batch 39's reviews of slices 181, 182 and 183 done, fix rounds in); the batch's whole-branch review follows.
- 2026-10-11 Slice 182 as built: identical means the canonical text of a file's artifact as it would land equals that of what the store holds, each without its revision; a type version's file below the store's version that the store does not keep, and one above it whose revision is not above the type's, are differs (overriding batch 39's decision 9); a file both broken and differing refuses the import even with errors skipped; a differing type of types stays rule content.
- 2026-10-11 QUESTION FOR THE SPEC: an empty directory checks clean and its import is refused 'nothing would land', with and without errors skipped; the capability's line names the refusal only with errors skipped. — recommended: keep the refusal for a directory with no sound file, and say so in the line.
- 2026-10-11 QUESTION FOR THE SPEC: a file that is both broken and differing refuses the import with errors skipped. — recommended: keep; a difference is never skipped (decision/an-import-never-skips-a-difference). Applied in slice 182.
- 2026-10-11 QUESTION FOR THE SPEC: a differing copy of the type that describes types is an error with rule content and is skipped with errors skipped, where the capability's Implementation says it is compared 'the same way' as any artifact. — recommended: keep rule content (the store's copy is always kept); reword the Implementation line.
- 2026-10-11 QUESTION FOR THE SPEC: the wording of the two differs messages (a file that differs; a version the store does not keep) is the implementer's. — recommended: keep; published text to be read by the person.
- 2026-10-11 Suite: 1516 passed, 0 expected to fail, 0 unexpectedly passing, 0 failed at 09c003d in 28 s
- 2026-10-11 Batch 39 branch review at 09c003d: with fixes. About 10,900 store and directory trials: no escaped exception, nothing landed on any refusal, every clean check landed (but the empty directory), every differs refused in both modes; one disagreement (55 trials, one cause): with errors skipped, a link to a file that does not land under a type no version of which lands is not foreseen by the check and the landing refuses the whole import with ref. Fix wave: that, three untrue map rows, formatting.
- 2026-10-11 Slice 186 green (lane merged): README.md, bench/ and docker/ speak kb.v2; make bench at 30000 held every bound (summary read 2.95 ms of 100; traversal 6.65 ms of 100; single change 9.36 ms of 50; set of 100 changes 146.90 ms of 1000); make image-check passed in 22 s leaving nothing behind; no version number is written in README, bench or docker (pyproject.toml's 0.7.0 is the one place to bump; tag v0.7.0 exists and is kb.v1)
- 2026-10-11 Batch 39 fix wave (fb050b9, b6031b0, 49914fc): the check judges a file's links against what would land, so its errors and skips are what an import with errors skipped leaves out; a link value that names nothing is an error of its file (ref or type, as a create's), never the store's fault; map rows true
- 2026-10-11 Suite: 1594 passed, 0 expected to fail, 0 unexpectedly passing, 0 failed at 6de2b4b in 30 s
- 2026-10-11 Batch 39 fix wave rounds 2 and 3 (e7e922e..7647567): the check reports a file's link beside its other errors; a type's place is judged without the directory's own links, so a valid store's export always checks clean; every type file whose place is refused is an identity error, none shielding another; a file linking under a nested type that does not land is skipped; the link judgement is judging.py; the image check requires one refusal line for an unwritable /data, naming it and the cause
- 2026-10-11 Suite: 1603 passed, 0 expected to fail, 0 unexpectedly passing, 0 failed at 7647567 in 30 s
- 2026-10-11 QUESTION FOR THE SPEC, formulation: the import check's behaviours fixed in batch 39's fix wave are held by plain tests only: a link error reported beside a file's other errors; a type under another type's IRI with a link waiting under it; nested type files whose place is refused; a link under a nested type that does not land. — recommended: one Behaviour line that the check's errors and skips are exactly what an import with errors skipped leaves out, with a scenario, and the cases stay plain tests.
- 2026-10-11 Batch 39 closed: fix wave round 3 approved at 7647567 (5,008 trials with three nested types into eight stores: 0 disagreements between the check and the import, 0 store faults, 0 landings on a refusal, 0 stores kb validate faults, 0 of 1,409 landed stores whose own export failed to import). Every slice of K2 and K3 is green.
