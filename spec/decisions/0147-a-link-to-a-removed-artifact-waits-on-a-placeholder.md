---
id: design-decision/missingmass.io/shopsystem/kb/a-link-to-a-removed-artifact-waits-on-a-placeholder
summary: "A removed artifact's IRI is an IRI the store does not hold: a link made to it after the removal lands on a placeholder like a link to any IRI not held under a held type that the link field allows, so a removal and a new link made at once may both land when the removal lands first; the removal landing second is still refused."
date: 2026-10-10
status: accepted
by: "slicing question (K2, slice 166: the scenario of a removal and a new link made at once against design-decision/missingmass.io/shopsystem/kb/a-link-may-land-on-a-placeholder), answered under the person's delegation of 2026-10-10"
---

# a-link-to-a-removed-artifact-waits-on-a-placeholder

## Decision
A removed artifact's IRI is an IRI the store does not hold: a link made to it after the removal lands on a placeholder like a link to any IRI not held under a held type that the link field allows, so a removal and a new link made at once may both land when the removal lands first; the removal landing second is still refused.
