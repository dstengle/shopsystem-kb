---
id: design-decision/missingmass.io/shopsystem/kb/kb-runs-no-git
summary: "Git is no longer kb's store and kb runs no git at all: starting a store makes no repository, the history is rows in the store's database, and committing exported files to git is the operator's choice."
date: 2026-10-01
status: accepted
by: ".shop/records/archive/design-notes/2026-10-01-kb-storage-sqlite-design.md"
source: decision-argument/missingmass.io/shopsystem/kb/2026-10-01-kb-storage-sqlite-design
supersedes: design-decision/missingmass.io/shopsystem/kb/kb-git-owns-its-store
---

# kb-runs-no-git

## Decision
Git is no longer kb's store and kb runs no git at all: starting a store makes no repository, the history is rows in the store's database, and committing exported files to git is the operator's choice.
