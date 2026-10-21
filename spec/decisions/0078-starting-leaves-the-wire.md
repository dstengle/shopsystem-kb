---
id: design-decision/missingmass.io/shopsystem/kb/starting-leaves-the-wire
summary: "A store is started by the operator's `kb init` or by a client in its own process calling `kb.init(root, role)`, which takes the same optional clock `connect` takes and raises `kb.NotStarted` carrying the faults when it refuses; there is no `Init` rpc, a served store cannot be started through its server, and starting keeps every behaviour it had, only the way it is asked for changing."
date: 2026-10-01
status: accepted
by: ".shop/records/archive/design-notes/2026-10-01-kb-contract-v1-design.md; the controller's answer to the integration's question 5, under the person's delegation of 2026-10-01"
---

# starting-leaves-the-wire

## Decision
A store is started by the operator's `kb init` or by a client in its own process calling `kb.init(root, role)`, which takes the same optional clock `connect` takes and raises `kb.NotStarted` carrying the faults when it refuses; there is no `Init` rpc, a served store cannot be started through its server, and starting keeps every behaviour it had, only the way it is asked for changing.
