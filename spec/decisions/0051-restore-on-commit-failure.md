---
id: design-decision/missingmass.io/shopsystem/kb/restore-on-commit-failure
summary: "On a git failure after files are written, kb restores the files from HEAD and reports the failure; no scenario pins it."
date: 2026-09-23
status: superseded
by: ".shop/records/archive/design-notes/2026-09-23-kb-design.md"
source: decision-argument/missingmass.io/shopsystem/kb/2026-09-23-kb-design
revisit_when: "a failed commit ever leaves a stray file"
---

# restore-on-commit-failure

## Decision
On a git failure after files are written, kb restores the files from HEAD and reports the failure; no scenario pins it.
