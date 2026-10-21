---
id: design-decision/missingmass.io/shopsystem/kb/an-artifact-is-read-through-its-version
summary: "Everything kb reads of an artifact it reads through the version of its type the artifact conforms to, its links included: a read gives it as that version declares, at every level, and a change to its type restates none of its links, which stay as its version declares them until a write moves the artifact to a later version."
date: 2026-10-10
status: accepted
by: "review questions (slice 162: reads of an artifact behind its type, and links restated when a type changes), answered under the person's delegation of 2026-10-10"
---

# an-artifact-is-read-through-its-version

## Decision
Everything kb reads of an artifact it reads through the version of its type the artifact conforms to, its links included: a read gives it as that version declares, at every level, and a change to its type restates none of its links, which stay as its version declares them until a write moves the artifact to a later version.
