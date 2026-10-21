---
id: design-decision/missingmass.io/shopsystem/kb/seed-may-be-the-root
summary: "`kb init <root> --seed <root>` is accepted, not refused: the seed is read with kb's staging place passed over, as an import passes over a store's own files, so an operator who copies a seed into the volume a store will live in can seed it from there. Chosen over refusing a seed that is, or holds, the root, which would make the operator keep the seed elsewhere."
date: 2026-10-08
status: accepted
by: "the batch 28 review (B2), lines approved by the controller under the person's delegation of 2026-10-08"
---

# seed-may-be-the-root

## Decision
`kb init <root> --seed <root>` is accepted, not refused: the seed is read with kb's staging place passed over, as an import passes over a store's own files, so an operator who copies a seed into the volume a store will live in can seed it from there. Chosen over refusing a seed that is, or holds, the root, which would make the operator keep the seed elsewhere.
