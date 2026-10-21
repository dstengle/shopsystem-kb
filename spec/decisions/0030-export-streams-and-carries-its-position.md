---
id: design-decision/missingmass.io/shopsystem/kb/export-streams-and-carries-its-position
summary: "The contract's export answers as a stream, one file to a message, selected by the path below each type and by type, and says the journal position it reflects, so that a store larger than one message exports and an export of what changed since a position can be added later as an optional field without breaking the contract."
date: 2026-10-10
status: accepted
by: ".shop/records/decision-arguments/0030-export-streams-and-carries-its-position.md"
revisit_when: "a store needs an export of only what changed since a position"
---

# export-streams-and-carries-its-position

## Decision
The contract's export answers as a stream, one file to a message, selected by the path below each type and by type, and says the journal position it reflects, so that a store larger than one message exports and an export of what changed since a position can be added later as an optional field without breaking the contract.
