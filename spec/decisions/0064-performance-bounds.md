---
id: design-decision/missingmass.io/shopsystem/kb/performance-bounds
summary: "At 30,000 artifacts a summary read and a three-step traversal take under 100 ms each, a single change under 50 ms and a set of 100 changes under 1 s, checked by a benchmark kept in the repository rather than by scenarios; a release that misses one does not ship."
date: 2026-10-01
status: accepted
by: ".shop/records/archive/design-notes/2026-10-01-kb-storage-sqlite-design.md"
revisit_when: "the scale targets are set"
---

# performance-bounds

## Decision
At 30,000 artifacts a summary read and a three-step traversal take under 100 ms each, a single change under 50 ms and a set of 100 changes under 1 s, checked by a benchmark kept in the repository rather than by scenarios; a release that misses one does not ship.
