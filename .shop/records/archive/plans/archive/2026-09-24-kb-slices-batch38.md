---
id: initiative-archive/missingmass.io/shopsystem/kb/2026-09-24-kb-slices-batch38
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

## Slice 176.1: The item names leave names.py
- Kind: enabling
- Check: `make test` -> the same result as the record before it; `wc -l src/kb/names.py` -> at most 160, and no module under src/kb over 250
- Observable: The grammar of item names has a module of its own, with room for names a create gives its parts.
- Unknown: none
- Needs: names.py at 233 of 250 lines before slice 179
- Lands: 4 production, 1 test
- Status: green

## Slice 176.2: Content conversion leaves values.py
- Kind: enabling
- Check: `make test` -> the same result as the record before it; `wc -l src/kb/values.py` -> at most 185, and no module under src/kb over 250
- Observable: The conversion of content trees has a module of its own, and values.py has room for the names slices 178 and 179 convert.
- Unknown: none
- Needs: values.py at 230 of 250 lines before slices 178 and 179
- Lands: 4 production, 1 test
- Status: green

## Slice 177: A set can be checked only
- Kind: capability
- Scenarios: make-several-changes-in-one-go / A set of <changes> asked to be checked only answers as it would land and lands nothing; make-several-changes-in-one-go / A set asked to be checked only that would be refused is refused with every fault; make-several-changes-in-one-go / A replacement in a set asked to be checked only that says a revision its artifact no longer stands at is refused; make-several-changes-in-one-go / A set asked to be checked only while another change is being written is answered, not refused as busy
- Observable: A client asks for a set of creates or replacements to be checked only and is answered as it would land, with nothing written and never refused as busy.
- Unknown: Whether a set can be drafted and checked against one read moment without taking the write lock
- Needs: none
- Lands: 4 production, 3 test
- Status: green

## Slice 178: Every name a call carries is an IRI of kb's grammar
- Kind: capability
- Scenarios: name-what-is-asked-for / A name a call carries is an IRI of kb's grammar; name-what-is-asked-for / A read by a name that is not an IRI of kb's grammar is refused; name-what-is-asked-for / A read by a name that is a path on the disk is refused; name-what-is-asked-for / A change by a name that is not an IRI of kb's grammar writes nothing; name-what-is-asked-for / A create naming a version of a type not shaped as a type's IRI, "@" and a number is refused; name-what-is-asked-for / A read by an IRI under no type the store holds is refused
- Observable: A client's name broken in any one way of kb's grammar, or past 512 characters, is refused for its shape before anything is looked up.
- Unknown: none
- Needs: none
- Lands: 1 production, 3 test
- Status: green

## Slice 179: A create may name its parts
- Kind: capability
- Scenarios: name-artifacts-and-items / A part is named by its artifact's IRI, # and its place in it; name-artifacts-and-items / A part given a name of the client's choosing on create holds that name; name-artifacts-and-items / A part given no name on create is named by the store from its title or its place; name-artifacts-and-items / An artifact created giving two parts of one collection the same name is refused; name-artifacts-and-items / An artifact created giving a part a name that is not a plain name is refused; name-artifacts-and-items / Two items created with the same title in one collection, neither given a name, are given names of their own; name-artifacts-and-items / An item's title with capitals and punctuation gives a plain name; name-artifacts-and-items / An added item's title becomes its name, read as text, refused if it leaves nothing
- Observable: A client names the parts it creates, or leaves the store to name them from title or place, and reads any part by its artifact's IRI, # and its place.
- Unknown: Whether names a create gives its parts and names the store mints can stand together in one collection
- Needs: none
- Lands: 5 production, 3 test
- Status: green

## Slice 180: Links in a set land on parts and placeholders the set makes
- Kind: capability
- Scenarios: make-several-changes-in-one-go / A link in a set into a part a create in it names lands on that part; make-several-changes-in-one-go / A link in a set to an IRI nothing holds, under <type>, lands on a placeholder
- Observable: A client's set links into a part another create in it names, or to an IRI nothing holds under a type the store or the set provides.
- Unknown: none
- Needs: none
- Lands: 0 production, 1 test
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
- 2026-10-11 Batch batch37 archived to archive/2026-09-24-kb-slices-batch37.md; last 2026-10-11 Suite: 1278 passed, 57 expected to fail, 0 unexpectedly passing, 0 failed at 1e406a3 in 25.8 s
- 2026-10-11 Suite: 1278 passed, 57 expected to fail, 0 unexpectedly passing, 0 failed at 1e406a3 in 25.8 s
- 2026-10-11 Batch 38 = 176.1, 176.2 (enabling splits), 177 to 180; researched with a consequence sweep (.superpowers/scout/2026-10-11-batch38/research.md). Batch 39 = the import: 180.2, 181 to 185, with the RELEASE GATE lines.
- 2026-10-11 QUESTION FOR THE SPEC: a set asked to be checked only while a server serves the store (a served store takes changes only through its server; a check writes nothing); and whether a single create or replacement may be checked only. — recommended: a checked-only set is a read: answered directly or through the server, never refused as served or busy; only sets of creates and of replacements carry the flag. Applied as decisions 1 and 3 of batch 38's plan (slice 177).
- 2026-10-11 QUESTION FOR THE SPEC: names a create gives its parts beside names the store mints in one collection; and a read by a part's IRI (<IRI>#<place>) against 'an artifact's name holds no #'. — recommended: given names are taken first and minted names avoid them; a clash between two given names, or a given name that is not a plain name, is refused; a read or a change may name a part by its IRI, a create's own IRI may not carry one. Applied as decisions 4 and 5 of batch 38's plan (slice 179).
- 2026-10-11 slice 176.1 green. Someone can now: add the item-name work of batch 38 to item_names.py without touching the IRI grammar; names.py is 142 lines. Surprised by: nothing; plain stays in names.py as place steps use it too. Open questions: none. Next: slice 176.2.
- 2026-10-11 Suite: 1278 passed, 57 expected to fail, 0 unexpectedly passing, 0 failed at ba58ba2 in 24.9 s
- 2026-10-11 slice 176.2 green. Someone can now: change how content is converted in content_values.py without touching the single-field conversions; values.py is 168 lines. Surprised by: nothing; content_values.py is new rather than content.py, which holds canonical text without faults, kb_pb2 or rules. Open questions: none. Next: task 2.
- 2026-10-11 Suite: 1278 passed, 57 expected to fail, 0 unexpectedly passing, 0 failed at d938da3 in 32.8 s
- 2026-10-11 slice 178 green. Someone can now: send a name of any shape and be refused for it with the name given back, and read the two refusals' reasons in words. Surprised by: the outline's steps had no binding in the read module (it was bound in the create module), so it moved there. Open questions: none. Next: slice 179.
- 2026-10-11 Suite: 1296 passed, 39 expected to fail, 0 unexpectedly passing, 0 failed at 6e760e6 in 29.6 s
- 2026-10-11 slice 179 green. Someone can now: name the parts a create carries (a plain name, one to a collection, else refused at the part's place with nothing written), leave any unnamed for the store to name around the names given, and name a part by its artifact's IRI, # and its place wherever a locator is taken. Surprised by: a read by a locator's place answers with the whole artifact once the place is found to hold something, not the node, so a read by a part's IRI does the same and the scenario's Then asserts the step is in what is given; the step 'the refusal names "..."' already bound in the create module asserts the fault's artifact is the quoted text, so the scenario refusing a name given twice is bound in the add module with a step of its own; a locator's name holding # that is not an IRI and a place of plain steps is refused whole as a name, which slice 178's row for # twice requires. Open questions: should a read by a place, or by a part's IRI, give the node alone (kb.proto says 'a node inside it otherwise'); a locator giving both a part's IRI and a place is refused even when they agree; a type version's IRI followed by # and a place is refused as a name; a change (replace) still checks handed-back names only in the artifact's own collections, not those inside items, and item_names.handed_back raises on a name that is a list; a create's part-name faults stand beside its content's faults against its type but not beside those found as it acts (its IRI, its title, identity keys in its content). Next: slice 180.
- 2026-10-11 Suite: 1346 passed, 31 expected to fail, 0 unexpectedly passing, 0 failed at 0c11cc3 in 25.7 s
- 2026-10-11 QUESTION FOR THE SPEC: a client readied with its own clock, asking a server for a set to be checked only, where a change from such a client is refused with rule clock. — recommended: answered; a check reads no clock and writes nothing. Applied in slice 177.
- 2026-10-11 QUESTION FOR THE SPEC: what a read that names a part (a locator with a place, or a part's IRI) gives: read-an-artifact's Implementation says the response returns node content and the contract's Locator says 'a node inside it otherwise', but no Behaviour line says it, and until slice 179's fix round such a read answered with the whole artifact. — recommended: the part named and nothing else of its artifact, at the level asked. Applied in slice 179's fix round.
- 2026-10-11 QUESTION FOR THE SPEC: a call giving both a part's IRI and a place is refused even when they agree; a type version's place (<type>@1 with place schema) reads while <type>@1#schema is refused; a given part name has no length bound, so a part's IRI can pass 512 characters. — recommended: keep the refusal; one spelling per call; bound a part's name so its IRI stays within 512. For formulation.
- 2026-10-11 Suite: 1375 passed, 31 expected to fail, 0 unexpectedly passing, 0 failed at f668e5d in 27 s
- 2026-10-11 slice 177 green. Someone can now: ask for a set of creates or of replacements to be checked only (check_only on BatchCreateRequest and BatchReplaceRequest) and be given each change's IRI and the revision it would leave, with no name for the set, or every fault landing it would give, with nothing written, while another change is being written and while a server owns the store, directly or through it. Surprised by: whether an rpc writes is now asked of the request in three places (boundary.py, server.py, client.py); a landing's refusal for a part dropped while linked was found only by the adapter, and is now found in the draft for a landing and a check alike, so two refusals changed rank (a failing clock, and a write lock held too long, now come after it). Open questions: a set with a dropped linked part and another fault answers only the other fault. Next: slice 180.
- 2026-10-11 QUESTION FOR THE SPEC: a set with a dropped linked part and another fault answers only the other fault, before and after slice 177, so 'every fault found' was never met for this refusal, while a removal's comes beside other faults. — recommended: it comes beside the set's other faults, as a removal's does; a slice of its own with a Behaviour line.
- 2026-10-11 Suite: 1424 passed, 26 expected to fail, 0 unexpectedly passing, 0 failed at bcb41e1 in 30 s
- 2026-10-11 Suite: 1425 passed, 26 expected to fail, 0 unexpectedly passing, 0 failed at 0e0ad2f in 32 s
- 2026-10-11 slice 180 green. Someone can now: link, in one set of creates, into a part a create of the set names, and to an IRI nothing holds under a type the store holds or the set itself makes, which lands on a placeholder.
  Surprised by: nothing; no production change (decision 7). The work item type's own link is made to allow parts for the 'in its content' example, which the Given says only of tasks.
  Open questions: none. Next: slice 180.1.
- 2026-10-11 Suite: 1429 passed, 22 expected to fail, 0 unexpectedly passing, 0 failed at afa7d4d in 33 s
- 2026-10-11 Suite: 1431 passed, 22 expected to fail, 0 unexpectedly passing, 0 failed at a1454c5 in 31 s
- 2026-10-11 Batch 38 branch review at c06ff5c: ready to merge with fixes; fix wave a1454c5 (a read at a glance of items that carry no title gives stubs with an empty title; kb.proto says what a read naming a part gives). The 26 to 33 s spread of the suite is contention among 32 workers, no new slow test.
- 2026-10-11 QUESTION FOR THE SPEC: slice 179's ruling that a change's rules for item names apply at any depth means a Replace or an Add can no longer give a new name to an item inside an item, which landed before; a name inside an added item is refused item-name while the item's own is identity; no Behaviour line names depth. — recommended: keep it (a name is given at a create, at any depth, and never by a change); a Behaviour line in name-artifacts-and-items with the next formulation.
