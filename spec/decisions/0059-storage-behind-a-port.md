---
id: design-decision/missingmass.io/shopsystem/kb/storage-behind-a-port
summary: "kb's own rules (names, content checks, sections and items, signatures, faults, the contract) stay above a kb-internal, unpublished port and an adapter keeps the graph below it; SQLite is the first adapter, any other is gated by the same conformance tests, and the public contract, its rule names included, does not change with it."
date: 2026-10-01
status: accepted
by: ".shop/records/archive/design-notes/2026-10-01-kb-storage-sqlite-design.md"
source: decision-argument/missingmass.io/shopsystem/kb/2026-10-01-kb-storage-sqlite-design
revisit_when: "a workload needs queries the port cannot answer within its bounds, such as transitive or pattern queries over transcripts and work state"
---

# storage-behind-a-port

## Decision
kb's own rules (names, content checks, sections and items, signatures, faults, the contract) stay above a kb-internal, unpublished port and an adapter keeps the graph below it; SQLite is the first adapter, any other is gated by the same conformance tests, and the public contract, its rule names included, does not change with it.
