---
id: initiative-archive/missingmass.io/shopsystem/kb/2026-09-24-kb-slices-batch31
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

## Slice 149: Back a store up and restore it whole
- Kind: capability
- Scenarios: operate-a-store / The command line offers setting up, checking, exporting, backing up, restoring and importing, and nothing else that changes what the store holds; operate-a-store / The operator backs up a store, and the backup holds it whole; operate-a-store / The operator restores a backup in a directory with no store inside it; operate-a-store / A restored store's history ends where the backed-up store's did
- Observable: The operator backs a store up to one file and restores it in an empty directory as the same store, its history and journal included, with no role named.
- Unknown: What a backup is, such that restoring it gives back the store exactly
- Needs: none
- Status: green

## Slice 150: Back up a store while it is written and served
- Kind: capability
- Scenarios: operate-a-store / A set landing while the operator backs up the store is in the backup whole or not at all; operate-a-store / The operator backs up the store while clients are writing to it; operate-a-store / The operator backs up the store while another change is being written; operate-a-store / The operator backs up a store a server is serving
- Observable: The operator backs up a running store, served or written to directly, and gets it at one moment, while writers and the server carry on unrefused.
- Unknown: Whether the backup reads the store at one moment without taking or waiting on the write lock
- Needs: none
- Status: green

## Slice 151: A restore refuses what it cannot make a store of
- Kind: capability
- Scenarios: operate-a-store / Restoring a backup where the directory already has a store inside it is refused; operate-a-store / Restoring a backup inside a store is refused; operate-a-store / Restoring a backup in a directory kb cannot write is refused; operate-a-store / Restoring something that is not a backup kb made is refused; operate-a-store / Restoring a backup made by an earlier kb is refused; operate-a-store / Restoring a backup made by a later kb is refused
- Observable: The operator is told why a restore cannot be made, whether of the place or of the file, and nothing is made.
- Unknown: How a file is told to be a backup of this kb's, an earlier kb's or a later kb's before anything is made
- Needs: none
- Status: green

## Slice 152: A stopped restore leaves no store
- Kind: capability
- Scenarios: operate-a-store / A restore that was stopped before it finished leaves no store, and the same restore run again restores the backup
- Observable: An interrupted restore leaves the directory with no store, and running it again restores the backup.
- Unknown: Whether a restore stages and places its store as a seeded start does
- Needs: none
- Status: green

## Slice 153: A backup refuses where it cannot be made
- Kind: capability
- Scenarios: operate-a-store / Backing up a store to a place where anything already is is refused; operate-a-store / kb backup finds the store as kb validate does, and is refused where kb validate is; operate-a-store / Backing up where a connection to a server is found and no store is refused
- Observable: The operator's backup finds its store as kb validate does, refuses what kb validate refuses and a connection, and never writes over anything.
- Unknown: Whether kb backup's refusals all come from the operator's existing path to a store's files
- Needs: none
- Status: green

## Log
- 2026-10-08 Batch batch30 archived to archive/2026-09-24-kb-slices-batch30.md; last 2026-10-08 Suite: 684 passed, 0 failed at 9ce198b in 21 s
- 2026-10-08 Suite: 684 passed, 0 failed at 9ce198b in 21 s
- 2026-10-10 Suite: 683 passed, 28 failed at a43eaea in 21 s; failing: the 18 operate-a-store backup and restore scenarios (K1), outlines expanded
- 2026-10-10 slice 149 green. Someone can now: back a store up whole to one file with kb backup <file> and restore it with kb restore <file> <root>, no role needed, its artifacts, each decision's history and the whole journal, snapshot included, as they were. Surprised by: SQLite's backup copies the source's WAL flag into the copy's header, so a backup is switched to rollback-journal mode to stay one file that reading leaves nothing beside; values.py would have crossed 250 with a File value of its own, so Directory became Named (a directory or a file the operator names) and values.file was added beside values.directory; store.start takes how its database is made (a backup's copy) so the marker stays store.py's, written last; the restore code landed with the backup scenario, whose Then reads the backup by restoring it (decision 3), so the two restore scenarios were red only on their undefined steps. Open questions: none. Next: slice 150.
- 2026-10-10 Suite: 690 passed, 24 failed at 14937d6 in 21 s; failing: the 14 backup and restore scenarios of slices 150-153 (K1), outlines expanded
- 2026-10-10 slice 150 green. Someone can now: back up a store while clients write to it, while another change holds its write lock, and while a server serves it, the backup holding a set landing meanwhile whole or not at all.
  Surprised by: no production change was needed; Task 1's one-step online copy in a read transaction already held under writers, the held write lock and a server. The four scenarios went from undefined steps to green on step definitions alone; a probe taking the write lock in sqlite_backup.copied turned 'backup while another change is being written' red with rule busy. _answered_at moved from tests/test_look_after_a_store.py into tests/serving.py (answered_at) so the backup steps share it.
  Open questions: none. Next: slice 151.
- 2026-10-10 Suite: 694 passed, 20 failed at 2752853 in 21 s; failing: the 20 backup and restore scenarios of slices 151-153 (K1), outlines expanded
- 2026-10-10 Suite: 694 passed, 20 failed at db68506 in 23 s; failing: the 20 backup and restore scenarios of slices 151-153 (K1), outlines expanded
- 2026-10-10 slice 151 green. Someone can now: restore a backup knowing it is refused, with nothing made, in a directory with or inside a store, one kb cannot write, or for a file that is not a backup or was made by an earlier or later kb. Surprised by: the six scenarios' two place-refusals passed as soon as their steps existed (staging.restored already checked the root); the unwritable message needed a verb threaded through store.vacant. Open questions: a backup file that does not exist is refused as not a backup (no scenario names it). Next: slice 152.
- 2026-10-10 Suite: 701 passed, 14 failed at c8c6a23 in 21 s; failing: the 14 backup and restore scenarios of slices 152-153 and the backup command's outline rows (K1)
- 2026-10-10 slice 152 green. Someone can now: stop a restore partway and run it again to restore the backup. Surprised by: the scenario passed with no staging change (the staging place is cleared first already); the Given 'a backup ... and a decision' and the closing Then were also undefined, and kb restore needed the SIGINT handler through _interrupted. Open questions: none. Next: slice 153.
- 2026-10-10 Suite: 703 passed, 13 failed at 956adc1 in 21 s; failing: the backup command's outline rows (K1)
- 2026-10-10 slice 153 green. Someone can now: back a store up knowing it never writes over anything, is refused where kb validate is, and names its own place when that fails. Surprised by: the finding-the-store scenarios and the table row were green once their steps existed (Task 1's path), only the place check and the place-failure attribution needed code. Open questions: none. Next: batch-end review.
- 2026-10-10 Suite: 721 passed, 0 failed at e56adfd in 23 s
- 2026-10-10 Batch 31 fix wave (b231c9c): a backup's copy checked whole before it is marked, a damaged store refused as kb validate refuses it; a backup damaged inside refused before a restore makes anything; sqlite_backup raises port.Unreadable; restore over a store says restored; the form set before the mark. Open questions: none.
- 2026-10-10 Suite: 723 passed, 0 failed at b231c9c in 23 s
