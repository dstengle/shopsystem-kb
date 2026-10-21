---
id: design-decision/missingmass.io/shopsystem/kb/damaged-database-one-fault
summary: "A database that cannot be opened or read refuses every call and every command with one fault, rule `unreadable`, naming the database, and writes nothing; damage to files is found by the import check, not by the store."
date: 2026-10-01
status: accepted
by: ".shop/records/archive/design-notes/2026-10-01-kb-storage-sqlite-design.md"
source: decision-argument/missingmass.io/shopsystem/kb/2026-10-01-kb-storage-sqlite-design
---

# damaged-database-one-fault

## Decision
A database that cannot be opened or read refuses every call and every command with one fault, rule `unreadable`, naming the database, and writes nothing; damage to files is found by the import check, not by the store.
