---
id: design-decision/missingmass.io/shopsystem/kb/scale
summary: "One repository, an incremental load cache, batch operations under one lock, and a server when callers are several; no daemon."
date: 2026-09-23
status: superseded
by: ".shop/records/archive/design-notes/2026-09-23-kb-design.md"
revisit_when: "the lock queue grows"
---

# scale

## Decision
One repository, an incremental load cache, batch operations under one lock, and a server when callers are several; no daemon.
