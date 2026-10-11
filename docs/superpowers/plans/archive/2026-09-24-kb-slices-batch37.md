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

## Slice 170.6: The one wrapper leaves servicer.py
- Kind: enabling
- Check: `make test` -> the same result as the record before it; `wc -l src/kb/servicer.py` -> at most 100, and no module under src/kb over 250
- Observable: The rpc adapter has room for a streamed rpc, and the one fail-closed wrapper is a module of its own.
- Unknown: none
- Needs: servicer.py at 141 of 150 lines before slice 172 adds a streamed boundary
- Lands: 4 production, 0 test
- Status: green

## Slice 170.7: The port's values leave port.py
- Kind: enabling
- Check: `make test` -> the same result as the record before it; `wc -l src/kb/port.py` -> at most 180, and no module under src/kb over 250
- Observable: The storage port has room for the reads slices 172 and 175 add.
- Unknown: none
- Needs: port.py at 246 of 250 lines; every importer of its values moves with them
- Lands: 8 production, 2 test
- Status: green

## Slice 171: Each history entry gives its position
- Kind: capability
- Scenarios: keep-the-history / Each entry read from the history gives its position in the history
- Observable: A client reading the history holds a position for each entry it is given.
- Unknown: none
- Needs: none
- Lands: 0 production, 1 test
- Status: green

## Slice 172: The client exports the store through the contract
- Kind: capability
- Scenarios: export-through-the-contract / The client exports the store; export-through-the-contract / The client exports the store, and is told the position of the last history entry landed at that moment
- Observable: A client takes every canonical file of the store, one at a time and at its place, from one moment, and is told the history position they reflect.
- Unknown: Whether the store can be streamed as canonical files from one read moment, with the position of the last entry landed then
- Needs: none
- Lands: 8 production, 4 test
- Status: green

## Slice 173: An export is a read, served or not
- Kind: capability
- Scenarios: export-through-the-contract / While a server serves the store, the client exports through it; export-through-the-contract / While another change is being written to the store, the client exports it
- Observable: A client exports through a server exactly as in process, and while another change holds the store.
- Unknown: Whether a server-streamed rpc passes through the server and the network transport unchanged without waiting on the write lock
- Needs: none
- Lands: 2 production, 1 test
- Status: green

## Slice 174: Each version of a type is exported as a file of its own
- Kind: capability
- Scenarios: export-through-the-contract / The client exports a store holding several versions of a type; export-and-import-a-store / The operator exports the store to a directory that is empty or does not exist
- Observable: A client's export and the operator's kb export give one file per held type version, at the type's place, @ and its number, each with its own revision and title.
- Unknown: How every held version of a type is written as a file of its own with the revision and title it was made with
- Needs: none
- Lands: 0 production, 1 test
- Status: green

## Slice 174.1: List and Follow requests carry a path
- Kind: enabling
- Check: `make test` -> the same passed and failed tests as the record before it; the contract's descriptor test passes against the golden file with `path` on the List and Follow requests and List's kind optional
- Observable: The contract has the fields a client selects by path with, before anything reads them.
- Unknown: none
- Needs: expand of slice 175, which was one test module over the budget
- Lands: 1 production, 2 test
- Status: green

## Slice 175: Lists and follows select by the path below the type
- Kind: capability
- Scenarios: query-the-store / The client lists by a path below the type; query-the-store / The client follows links narrowed to a path below the type
- Observable: A client lists, or follows links, by where artifacts sit below their type across every type, whole segments only.
- Unknown: Whether a path below the type can select by whole segments across every type from the store's rows
- Needs: none
- Lands: 6 production, 3 test
- Status: green

## Slice 176: An export selects by path and by type
- Kind: capability
- Scenarios: export-through-the-contract / The client exports selecting a path below the type; export-through-the-contract / The client exports selecting a type; export-through-the-contract / The client exports selecting a path below the type and a type together; name-what-is-asked-for / Listing, searching, following links or exporting by a kind the store holds no type for is refused
- Observable: A client exports only a path, a type, or both together, and an export by a kind not held is refused as a list is.
- Unknown: none
- Needs: none
- Lands: 4 production, 4 test
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
- 2026-10-11 Batch batch36 archived to archive/2026-09-24-kb-slices-batch36.md; last 2026-10-11 Suite: 1129 passed, 72 expected to fail, 0 unexpectedly passing, 0 failed at 59fd536 in 23.1 s
- 2026-10-11 Suite: 1129 passed, 72 expected to fail, 0 unexpectedly passing, 0 failed at 59fd536 in 23.1 s
- 2026-10-11 Batch 37 = 170.6, 170.7 (enabling splits), 171 to 176; researched with a consequence sweep (.superpowers/scout/2026-10-11-batch37/research.md), whose four unowned rows are decisions 6 to 9 of the batch plan.
- 2026-10-11 QUESTION FOR THE SPEC: an export selecting a path: whether it gives any type's files, and with a type and a path together whether the type's version files come with the artifacts. — recommended: a path alone gives artifacts only; a type gives its version files and its artifacts; both together give the type's version files and its artifacts at or under the path. Applied as decision 5 of batch 37's plan (slice 176).
- 2026-10-11 QUESTION FOR THE SPEC: whether kb promises an order between two history positions (ids sort by moment, entries land in another order when a clock goes back), and whether the operator's kb export, Search, History, Snapshot and Placeholders gain selection by path. — recommended: a position names an entry and promises no order; an export's position is the entry landed last; none of those gains a path. Applied as decisions 3, 6 and 7 of batch 37's plan.
- 2026-10-11 slice 170.6 green. Someone can now: read the one fail-closed wrapper in boundary.py, with servicer.py (90 lines) left as the rpc adapter. Surprised by: nothing. Open questions: none. Next: slice 170.7.
- 2026-10-11 Suite: 1129 passed, 72 expected to fail, 0 unexpectedly passing, 0 failed at 4a40255 in 27 s
- 2026-10-11 slice 170.7 green. Someone can now: read the port's interface and refusals in port.py (118 lines) apart from the values it takes and gives in port_values.py. Surprised by: nothing. Open questions: none. Next: slice 170.8.
- 2026-10-11 Suite: 1129 passed, 72 expected to fail, 0 unexpectedly passing, 0 failed at c9497af in 24 s
- 2026-10-11 slice 171 green. Someone can now: read the history and hold each entry's id as its position. Surprised by: nothing. Open questions: none. Next: slice 174.1.
- 2026-10-11 Suite: 1130 passed, 71 expected to fail, 0 unexpectedly passing, 0 failed at 9509066 in 23.6 s
- 2026-10-11 slice 174.1 green. Someone can now: send a path with a List or a Follow (ListRequest.path = 4, FollowRequest.path = 6); nothing reads them yet. Surprised by: nothing. Open questions: none. Next: slice 174.2.
- 2026-10-11 Suite: 1130 passed, 71 expected to fail, 0 unexpectedly passing, 0 failed at b522c00 in 24.9 s
- 2026-10-11 slice 172 green. Someone can now: call Export on a client over a store in its own process and iterate the store's canonical files, one to a message, each at its place, all from one read moment, ending with the position, the id of the entry landed last.
  Surprised by: the contract's own response rule fits a stream unchanged, each message an ExportResponse of result (Exported: a file or the end) or refusal; a refusal after files were sent takes the end's place, so only a stream ending in the end is whole; names.py gained placing (a place as one path) and the golden's renderer now marks a streamed rpc.
  Open questions: where the client finds the connection to a server, Export has no branch yet and answers from the connection's directory in process, refused as unreadable with the later-kb message (slice 173 replaces it); the stream's store handle is SQLite's, bound to the thread that reads it, which slice 173 must hold to when grpc ends a stream. Next: slice 173.
- 2026-10-11 Suite: 1153 passed, 69 expected to fail, 0 unexpectedly passing, 0 failed at 391b2f6 in 23.5 s
- 2026-10-11 slice 173 green. Someone can now: export a store through the server that serves it, given the same files and position as in process, and export while another change holds the store or the server is writing one.
  Surprised by: closing a grpc channel with a stream still open, from a generator finalized as the program ends, waits for ever on grpc's daemon thread, so network.py leaves the channel to the process then (a program that ends with an export unread now ends); grpc iterates and lets go of the servicer's generator on one worker thread, so the store handle's thread never changes on the server and boundary.py and server.py needed nothing; how far a server reads ahead of a slow client is the connection's affair (0.5 to 1 MB), so the one-moment test holds the server's reading itself.
  Open questions: a stream read or closed in process from a thread other than the one that first read it fails (a refusal with rule unreadable naming SQLite's thread check; close raises RuntimeError, generator ignored GeneratorExit, the store held until the stream is collected), slice 172's code, no scenario; a server stopping cuts an export off after its grace period with unreachable as the last message, which no capability line states. Next: slice 174.
- 2026-10-11 Suite: 1166 passed, 67 expected to fail, 0 unexpectedly passing, 0 failed at a2955a2 in 23.4 s
- 2026-10-11 Suite: 1172 passed, 67 expected to fail, 0 unexpectedly passing, 0 failed at e87ede1 in 23.8 s
- 2026-10-11 slice 174 green. Someone can now: export a store through the contract and be given each held version of a type as a file of its own at the type's place, @ and the version's number. Surprised by: nothing; the scenario was green once its steps existed. Open questions: none. Next: slice 175.
- 2026-10-11 Suite: 1173 passed, 66 expected to fail, 0 unexpectedly passing, 0 failed at 1eeda3a in 28.4 s
- 2026-10-11 slice 175 green. Someone can now: list by a path below the type across every type (or within a kind), and narrow a follow to one, matched by whole segments, so plan gives plan and plan/a and never planning.
  Surprised by: read.stubs kept what a type shows by the version's number alone, so a list across types gave a work item's stub through the decision type's fields; it now keeps it by the version's IRI (read.py, not named by the task). The adapter leaves the kind of types out of a kindless listing by values.TYPE_KIND, the first thing it knows of types. The path value (values.Below) and names.below/selects landed in step 1, since the port takes them.
  Open questions: a follow narrowed by a path does not walk on through a step the path leaves out, as a kind's narrowing does not (no scenario says); a follow narrowed by a path keeps a type that sits under the IRI of the type of types, which a kindless list leaves out; a list by the kind of types and a path gives such types; a malformed path is refused with rule locator, by analogy with a kind's. Next: slice 176.
- 2026-10-11 Suite: 1230 passed, 64 expected to fail, 0 unexpectedly passing, 0 failed at 612e6e5 in 26.7 s
- 2026-10-11 slice 176 green. Someone can now: export through the contract only what a path below the type selects (whole segments, across every type), only a kind's artifacts, or both together (ExportRequest.path = 1, kind = 2), each file byte for byte the whole export's and the position the store's; an export by a kind the store holds no type for is refused as a list is, the stream's one message.
  Surprised by: the scenarios' Then lines give no other file than the artifacts', so a kind selects no version file of its type, where decision 5 of batch 37's plan said it would; the Then lines were followed. The outline's three older rows had never run (their Given was bound only in another module) and their Then still looked for 'invoice' where a kind is now given back as its type's IRI; the step now looks for the IRI. The scenario selecting both went green on its When alone, the code of the two before it being all it needs (shown by mutation).
  Open questions: an export by the kind of types gives every type's version files, and with a path beside it only the types under the IRI of the type of types that the path selects, as the port's ids gives them (no scenario says); a selection that selects nothing is a whole export of no file, ending with the position. Next: slice 177.
- 2026-10-11 Suite: 1278 passed, 57 expected to fail, 0 unexpectedly passing, 0 failed at f1707bb in 27.0 s
- 2026-10-11 Correction to the QUESTION FOR THE SPEC on an export's selection: the scenarios' Then lines decide it, not batch 37's decision 5: selecting a type, alone or with a path, gives the files of that type's artifacts and no other file, so no version file of the type; slice 176 is built so. An export by the kind of types gives every type's version files (unpinned).
- 2026-10-11 Suite: 1278 passed, 57 expected to fail, 0 unexpectedly passing, 0 failed at ea5c879 in 30 s
- 2026-10-11 Suite: 1278 passed, 57 expected to fail, 0 unexpectedly passing, 0 failed at 1e91f8c in 26 s
- 2026-10-11 Batch 37 branch review at 6bb06bb: make test 1278 passed, 57 expected to fail, 0 failed; ready to merge with fixes, all of them published or rule text (kb.proto's comments on ExportResponse, ExportRequest, ListRequest and ListResponse; CLAUDE.md's store.py row; Client.Export's docstring). A client's export written to disk imports and seeds a fresh store and re-exports byte for byte. The RELEASE GATE on unread exports is confirmed and stays open.
- 2026-10-11 Suite: 1278 passed, 57 expected to fail, 0 unexpectedly passing, 0 failed at 1e406a3 in 25.8 s
