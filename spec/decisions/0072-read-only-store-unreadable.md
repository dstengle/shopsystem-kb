---
id: design-decision/missingmass.io/shopsystem/kb/read-only-store-unreadable
summary: "A store whose database cannot be opened for writing, because the directory, the file or the mount it is on is read-only, is a database that cannot be read, refused with rule `unreadable` and nothing written, as a damaged or missing one is; kb does not read a read-only store until what one means is defined (whether it may be read while nothing may change it, what its history says, how a served store relates to it)."
date: 2026-10-01
status: accepted
by: ".shop/records/archive/design-notes/2026-10-01-kb-pr1-review-answers.md"
source: decision-argument/missingmass.io/shopsystem/kb/2026-10-01-kb-pr1-review-answers
---

# read-only-store-unreadable

## Decision
A store whose database cannot be opened for writing, because the directory, the file or the mount it is on is read-only, is a database that cannot be read, refused with rule `unreadable` and nothing written, as a damaged or missing one is; kb does not read a read-only store until what one means is defined (whether it may be read while nothing may change it, what its history says, how a served store relates to it).
