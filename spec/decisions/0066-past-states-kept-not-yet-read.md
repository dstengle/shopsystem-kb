---
id: design-decision/missingmass.io/shopsystem/kb/past-states-kept-not-yet-read
summary: "The contract has no historical read; the store keeps each artifact's content at every revision, which the contract's next version will read."
date: 2026-10-01
status: accepted
by: ".shop/records/archive/design-notes/2026-10-01-kb-storage-sqlite-design.md"
supersedes: design-decision/missingmass.io/shopsystem/kb/git-serves-time-travel
revisit_when: "a client needs a past state through the contract"
---

# past-states-kept-not-yet-read

## Decision
The contract has no historical read; the store keeps each artifact's content at every revision, which the contract's next version will read.
