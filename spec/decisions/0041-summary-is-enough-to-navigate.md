---
id: design-decision/missingmass.io/shopsystem/kb/summary-is-enough-to-navigate
summary: "A summary read carries stubs of what an artifact points at and counts of what points at it, enough to move through the graph without whole reads."
date: 2026-09-23
status: accepted
by: ".shop/records/archive/design-notes/2026-09-23-kb-design.md"
revisit_when: "clients routinely follow a summary with a whole read of the same artifact"
---

# summary-is-enough-to-navigate

## Decision
A summary read carries stubs of what an artifact points at and counts of what points at it, enough to move through the graph without whole reads.
