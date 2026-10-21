---
id: design-decision/missingmass.io/shopsystem/kb/write-lock-on-one-machine
summary: "On one machine the database's write lock serialises writers across threads and processes, each change's revision compared inside the transaction and, on a mismatch, the change re-drafted against the new state and landed, so no client sees a conflict; readers never wait; across containers callers share a store through a server (0020), because SQLite over a network filesystem is not safe; there is no daemon."
date: 2026-10-01
status: superseded
by: ".shop/records/archive/design-notes/2026-10-01-kb-storage-sqlite-design.md"
source: decision-argument/missingmass.io/shopsystem/kb/2026-10-01-kb-storage-sqlite-design
supersedes: design-decision/missingmass.io/shopsystem/kb/scale-without-a-lock
---

# write-lock-on-one-machine

## Decision
On one machine the database's write lock serialises writers across threads and processes, each change's revision compared inside the transaction and, on a mismatch, the change re-drafted against the new state and landed, so no client sees a conflict; readers never wait; across containers callers share a store through a server (0020), because SQLite over a network filesystem is not safe; there is no daemon.
