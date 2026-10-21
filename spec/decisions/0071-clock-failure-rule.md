---
id: design-decision/missingmass.io/shopsystem/kb/clock-failure-rule
summary: "A clock that fails during a change gives the client a fault with rule `clock`, no artifact and no path, and `clock` joins kb's published rule names, since no existing name fits and the list is closed."
date: 2026-10-01
status: accepted
by: ".shop/records/archive/design-notes/2026-10-01-kb-storage-sqlite-design.md; the controller's answer of 2026-10-01"
---

# clock-failure-rule

## Decision
A clock that fails during a change gives the client a fault with rule `clock`, no artifact and no path, and `clock` joins kb's published rule names, since no existing name fits and the list is closed.
