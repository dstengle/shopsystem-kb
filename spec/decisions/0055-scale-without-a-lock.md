---
id: design-decision/missingmass.io/shopsystem/kb/scale-without-a-lock
summary: "One repository, an incremental load cache, batch operations, and, when callers are several, a server that takes changes one at a time; there is no lock and no daemon."
date: 2026-09-30
status: superseded
by: "the migration gate; .shop/records/decision-arguments/0020-a-server-found-where-the-store-is.md"
supersedes: design-decision/missingmass.io/shopsystem/kb/scale
revisit_when: "changes wait at the server in growing numbers"
---

# scale-without-a-lock

## Decision
One repository, an incremental load cache, batch operations, and, when callers are several, a server that takes changes one at a time; there is no lock and no daemon.
