---
id: design-decision/missingmass.io/shopsystem/kb/sqlite-canonical
summary: "The store is one SQLite database, `kb/store.sqlite3` in WAL mode beside its marker `kb/store.yaml`, and canonical YAML 1.2, read and written by kb alone, is its export and wire form rather than its storage; chosen after a spike in which SQLite met every criterion fixed beforehand at 30,000 documents (reads and three-step traversals in about 0.02 ms, search in 4 ms, every race closed by its write lock and a revision compare-and-set), while TerminusDB 12.0.7 met two outright and the rest only with adapter code working around it."
date: 2026-10-01
status: accepted
by: ".shop/records/archive/design-notes/2026-10-01-kb-storage-sqlite-design.md"
supersedes: design-decision/missingmass.io/shopsystem/kb/yaml-1-2-git-canonical
---

# sqlite-canonical

## Decision
The store is one SQLite database, `kb/store.sqlite3` in WAL mode beside its marker `kb/store.yaml`, and canonical YAML 1.2, read and written by kb alone, is its export and wire form rather than its storage; chosen after a spike in which SQLite met every criterion fixed beforehand at 30,000 documents (reads and three-step traversals in about 0.02 ms, search in 4 ms, every race closed by its write lock and a revision compare-and-set), while TerminusDB 12.0.7 met two outright and the rest only with adapter code working around it.
