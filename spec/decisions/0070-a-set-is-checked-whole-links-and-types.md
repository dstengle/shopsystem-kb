---
id: design-decision/missingmass.io/shopsystem/kb/a-set-is-checked-whole-links-and-types
summary: "A set's links and types are checked once against the state the whole set leaves, so its changes may point at each other, earlier or later, while each change acts on the store as the changes before it in the set left it; each separate change is checked against the state the one before it left."
date: 2026-10-01
status: accepted
by: ".shop/records/archive/design-notes/2026-10-01-kb-storage-sqlite-design.md; the formulation question on make-several-changes-in-one-go #9, answered 2026-10-01"
source: decision-argument/missingmass.io/shopsystem/kb/2026-10-01-kb-storage-sqlite-design
supersedes: design-decision/missingmass.io/shopsystem/kb/a-set-is-checked-whole
---

# a-set-is-checked-whole-links-and-types

## Decision
A set's links and types are checked once against the state the whole set leaves, so its changes may point at each other, earlier or later, while each change acts on the store as the changes before it in the set left it; each separate change is checked against the state the one before it left.
