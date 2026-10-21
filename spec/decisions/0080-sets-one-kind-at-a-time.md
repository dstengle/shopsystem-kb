---
id: design-decision/missingmass.io/shopsystem/kb/sets-one-kind-at-a-time
summary: "`Apply` and its four operation messages go; a set is one kind of change at a time, `CreateMany`, `ReplaceMany`, `AddMany` or `RemoveMany`, and never mixes kinds, so a create and a replacement are two calls; a set still lands whole or not at all, is checked against the state the whole set leaves, names itself and gives each change's own result."
date: 2026-10-01
status: superseded
by: ".shop/records/archive/design-notes/2026-10-01-kb-contract-v1-design.md"
source: decision-argument/missingmass.io/shopsystem/kb/2026-10-01-kb-contract-v1-design
---

# sets-one-kind-at-a-time

## Decision
`Apply` and its four operation messages go; a set is one kind of change at a time, `CreateMany`, `ReplaceMany`, `AddMany` or `RemoveMany`, and never mixes kinds, so a create and a replacement are two calls; a set still lands whole or not at all, is checked against the state the whole set leaves, names itself and gives each change's own result.
