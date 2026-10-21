---
id: design-decision/missingmass.io/shopsystem/kb/kb-git-owns-its-store
summary: "Every git call kb makes clears the variables git lists as locating a repository, and `GIT_CONFIG_PARAMETERS` and `GIT_CONFIG_COUNT`, so a caller's `GIT_DIR`, its kin and its `-c` settings never redirect or change the store's history; kb's own `-c` settings stay in force."
date: 2026-09-27
status: superseded
by: ".shop/records/decision-arguments/0019-kb-git-owns-its-store.md"
source: decision-argument/missingmass.io/shopsystem/kb/0019-kb-git-owns-its-store
---

# kb-git-owns-its-store

## Decision
Every git call kb makes clears the variables git lists as locating a repository, and `GIT_CONFIG_PARAMETERS` and `GIT_CONFIG_COUNT`, so a caller's `GIT_DIR`, its kin and its `-c` settings never redirect or change the store's history; kb's own `-c` settings stay in force.
