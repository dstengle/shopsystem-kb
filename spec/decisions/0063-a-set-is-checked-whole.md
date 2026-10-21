---
id: design-decision/missingmass.io/shopsystem/kb/a-set-is-checked-whole
summary: "A set is checked once as a whole against the state it leaves, so its changes may point at each other and rely on any other in the set; each separate change is checked against the state the one before it left."
date: 2026-10-01
status: superseded
by: ".shop/records/archive/design-notes/2026-10-01-kb-storage-sqlite-design.md"
source: decision-argument/missingmass.io/shopsystem/kb/2026-10-01-kb-storage-sqlite-design
---

# a-set-is-checked-whole

## Decision
A set is checked once as a whole against the state it leaves, so its changes may point at each other and rely on any other in the set; each separate change is checked against the state the one before it left.
