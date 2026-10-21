---
id: design-decision/missingmass.io/shopsystem/kb/an-import-is-held-as-a-change-is
summary: "An import that goes into a store already holding artifacts is a change to that store like any other: asked while a server serves the store it is refused because the store is served, and each file is held to the place its type gives it as a create is, a file whose IRI does not sit under its type, or sits under a nearer held type, being an error of the check."
date: 2026-10-11
status: accepted
by: "research findings (K3, slice 181: an import landed under a running server, and a file filed under another type's IRI landed), answered under the person's delegation of 2026-10-10"
---

# an-import-is-held-as-a-change-is

## Decision
An import that goes into a store already holding artifacts is a change to that store like any other: asked while a server serves the store it is refused because the store is served, and each file is held to the place its type gives it as a create is, a file whose IRI does not sit under its type, or sits under a nearer held type, being an error of the check.
