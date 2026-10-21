---
id: design-decision/missingmass.io/shopsystem/kb/a-set-lands-in-one-transaction
summary: "A set lands in one database transaction, so a failure part-way leaves nothing written and nothing to restore."
date: 2026-10-01
status: accepted
by: ".shop/records/archive/design-notes/2026-10-01-kb-storage-sqlite-design.md"
source: decision-argument/missingmass.io/shopsystem/kb/2026-10-01-kb-storage-sqlite-design
supersedes: design-decision/missingmass.io/shopsystem/kb/restore-on-commit-failure
---

# a-set-lands-in-one-transaction

## Decision
A set lands in one database transaction, so a failure part-way leaves nothing written and nothing to restore.
