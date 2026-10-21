---
id: design-decision/missingmass.io/shopsystem/kb/an-artifact-keeps-its-version
summary: "A write naming no version keeps the version its artifact conforms to and is checked against it; an artifact moves only to a later version of its own type that a write names, and a write naming an earlier version or another type's is refused; the store's check reads each artifact against the version it conforms to, so one behind its type is a violation only if it does not fit that version."
date: 2026-10-10
status: accepted
by: "the person's delegation of 2026-10-10; supersedes design-decision/missingmass.io/shopsystem/kb/validation-from-composed-schema (its clause that stale artifacts are checked against the current type)"
supersedes: design-decision/missingmass.io/shopsystem/kb/validation-from-composed-schema
---

# an-artifact-keeps-its-version

## Decision
A write naming no version keeps the version its artifact conforms to and is checked against it; an artifact moves only to a later version of its own type that a write names, and a write naming an earlier version or another type's is refused; the store's check reads each artifact against the version it conforms to, so one behind its type is a violation only if it does not fit that version.
