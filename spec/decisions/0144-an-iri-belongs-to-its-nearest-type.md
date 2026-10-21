---
id: design-decision/missingmass.io/shopsystem/kb/an-iri-belongs-to-its-nearest-type
summary: "When one type's IRI sits under another's, an IRI under both belongs to the nearest type: the longest type IRI that is a whole-segment prefix of it. A create naming a version of any other type is refused with rule `identity`, and a placeholder at such an IRI takes the nearest type."
date: 2026-10-10
status: accepted
by: "slicing question (K2, slices 158 and 167), answered under the person's delegation of 2026-10-10"
---

# an-iri-belongs-to-its-nearest-type

## Decision
When one type's IRI sits under another's, an IRI under both belongs to the nearest type: the longest type IRI that is a whole-segment prefix of it. A create naming a version of any other type is refused with rule `identity`, and a placeholder at such an IRI takes the nearest type.
