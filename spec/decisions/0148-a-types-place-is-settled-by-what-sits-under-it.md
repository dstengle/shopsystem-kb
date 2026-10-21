---
id: design-decision/missingmass.io/shopsystem/kb/a-types-place-is-settled-by-what-sits-under-it
summary: "An IRI belongs to the nearest held type it sits under, and what already sits under a type fixes that: a type is not removed while a link waits on an IRI under it that the store does not hold, as it is not while artifacts of its kind exist; and a type is not defined at an IRI under another type's while an artifact of that other type is held under the new type's IRI or a link waits on an IRI there, since the define would move what is held or waited on to a type it was not checked against. Each refusal names what stands in the way."
date: 2026-10-11
status: accepted
by: "review questions (slice 165.7: a type removed while links wait under it leaves links the store would refuse; a nearer type defined between a link and the create it waits on lets any kind land there; and the batch 32 review's type defined above held artifacts), answered under the person's delegation of 2026-10-10"
---

# a-types-place-is-settled-by-what-sits-under-it

## Decision
An IRI belongs to the nearest held type it sits under, and what already sits under a type fixes that: a type is not removed while a link waits on an IRI under it that the store does not hold, as it is not while artifacts of its kind exist; and a type is not defined at an IRI under another type's while an artifact of that other type is held under the new type's IRI or a link waits on an IRI there, since the define would move what is held or waited on to a type it was not checked against. Each refusal names what stands in the way.
