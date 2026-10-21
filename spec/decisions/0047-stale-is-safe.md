---
id: design-decision/missingmass.io/shopsystem/kb/stale-is-safe
summary: "An artifact behind its type's version is reported stale, never failed, and can be read and written until someone updates it."
date: 2026-09-23
status: accepted
by: ".shop/records/archive/design-notes/2026-09-23-kb-design.md"
revisit_when: "a stale artifact causes wrong behaviour"
---

# stale-is-safe

## Decision
An artifact behind its type's version is reported stale, never failed, and can be read and written until someone updates it.
