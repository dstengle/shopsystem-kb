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

## Slice 146: A store started in a directory kb cannot write is refused naming it
- Kind: capability
- Scenarios: features/operate-a-store.feature / Starting a store in a directory kb cannot write is refused
- Observable: an operator whose /data is a root-owned bind mount is told the directory cannot be written, naming it, instead of a store that could not answer naming kb's staging place
- Unknown: where a root's writability is checked so that kb.init, kb init --seed and kb serve --start refuse it alike, with rule root, before anything is made
- Needs: none
- Status: green

## Slice 147: A store seeded from the directory it is started in
- Kind: capability
- Scenarios: features/operate-a-store.feature / The operator sets up a store seeded from the directory it is started in
- Observable: an operator who copied a seed into /data runs kb init /data --seed /data and gets a store holding exactly the seed
- Unknown: whether passing over kb's staging place in the offered files is enough, with the seed's own files read while the staged store sits beside them
- Needs: none
- Status: green

## Log
- 2026-10-08 Batch batch28 archived to archive/2026-09-24-kb-slices-batch28.md; last 2026-10-08 Suite: 676 passed, 0 failed at 7c6a066 in 21 s
- 2026-10-08 Suite: 676 passed, 0 failed at 7c6a066 in 21 s
- 2026-10-08 Suite: 676 passed, 4 failed at 725633f in 21 s; failing: the 4 collected operate-a-store scenarios formulated from d42df01 (a seed directory that is the root; starting a store in a directory kb cannot write, 3 examples)
- 2026-10-08 slice 146 green. Someone can now: be told, by kb init, kb init --seed and kb serve --start alike, that a directory kb cannot write is no place for a store, with nothing made in it. Surprised by: nothing. Open questions: none. Next: slice 147.
- 2026-10-08 Suite: 679 passed, 1 failed at 889acc8 in 21 s; failing: the seed-is-the-root scenario of slice 147
- 2026-10-08 slice 147 green. Someone can now: set up a store seeded from the very directory it is started in. Surprised by: the import message names the seed directory, so the comparison normalises it. Open questions: none. Next: none.
- 2026-10-08 Suite: 680 passed, 0 failed at 2bdaf29 in 22 s
- 2026-10-08 Batch 29 branch review: ready to merge, no fix-now findings. Suite: 680 passed, 0 failed at 20ef344 in 22 s
