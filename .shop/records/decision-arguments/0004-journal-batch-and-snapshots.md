---
id: decision-argument/missingmass.io/shopsystem/kb/0004-journal-batch-and-snapshots
kind: decision-argument
about: bounded-context/missingmass.io/shopsystem/kb
---
# 0004 The journal carries a batch id; versioning floats with snapshots

2026-09-23. Every journal entry names the set (batch) it landed in and the journal filters by it. Artifacts carry a revision; a piece of work records what it read as a snapshot in the journal rather than pinning versions.
