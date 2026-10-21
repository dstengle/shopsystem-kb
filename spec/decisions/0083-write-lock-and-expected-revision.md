---
id: design-decision/missingmass.io/shopsystem/kb/write-lock-and-expected-revision
summary: "On one machine the database's write lock serialises writers across threads and processes, each change's revision compared inside the transaction; on a mismatch a change that says no expected revision is re-drafted against the new state and landed, so its client sees no conflict, and one that says an expected revision is refused with rule `revision`; readers never wait; across containers callers share a store through a server (0020), because SQLite over a network filesystem is not safe; there is no daemon."
date: 2026-10-01
status: accepted
by: ".shop/records/archive/design-notes/2026-10-01-kb-contract-v1-design.md"
supersedes: design-decision/missingmass.io/shopsystem/kb/write-lock-on-one-machine
---

# write-lock-and-expected-revision

## Decision
On one machine the database's write lock serialises writers across threads and processes, each change's revision compared inside the transaction; on a mismatch a change that says no expected revision is re-drafted against the new state and landed, so its client sees no conflict, and one that says an expected revision is refused with rule `revision`; readers never wait; across containers callers share a store through a server (0020), because SQLite over a network filesystem is not safe; there is no daemon.
