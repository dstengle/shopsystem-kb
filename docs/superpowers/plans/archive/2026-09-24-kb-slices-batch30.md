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

## Slice 148: A store seeded from a directory that holds the directory it is started in
- Kind: capability
- Scenarios: features/operate-a-store.feature / The operator sets up a store seeded from a directory that is, or holds, the directory it is started in
- Observable: an operator who keeps a seed in a directory around the store's place runs kb init P/r --seed P and gets a store holding exactly the seed
- Unknown: whether kb's staging place is passed over wherever the root lies inside the seed, with what the seed holds beside it still read
- Needs: none
- Status: green

## Log
- 2026-10-08 Batch batch29 archived to archive/2026-09-24-kb-slices-batch29.md; last 2026-10-08 Suite: 680 passed, 0 failed at 2bdaf29 in 22 s
- 2026-10-08 Suite: 680 passed, 0 failed at 2bdaf29 in 22 s
- 2026-10-08 Suite: 679 passed, 2 failed at ccc8bc5 in 24 s; failing: both examples of the seed-is-or-holds-the-root outline, reformulated from slice 147's scenario (e503ee9)
- 2026-10-08 slice 148 green. Someone can now: run kb init P/r --seed P and get exactly the seed, the staging place passed over wherever the root lies in the seed. Surprised by: the 'is' example passed once its steps existed (batch 29 already covered it); only 'holds' was red, on the Then. Open questions: none. Next: none.
- 2026-10-08 Suite: 684 passed, 0 failed at 9ce198b in 21 s
- 2026-10-08 Batch 30 branch review: ready to merge, no fix-now findings. Suite: 684 passed, 0 failed at 1edad09 in 21 s
