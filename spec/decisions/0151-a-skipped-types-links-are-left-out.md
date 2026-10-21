---
id: design-decision/missingmass.io/shopsystem/kb/a-skipped-types-links-are-left-out
summary: "A link waits on a placeholder only under a held type (design-decision/missingmass.io/shopsystem/kb/a-link-may-land-on-a-placeholder), so with errors skipped a file carrying a link to an IRI under a type no version of which lands is left out with that type and reported as skipped by it; a link to a file left out under a type that does land waits on a placeholder."
date: 2026-10-11
status: accepted
by: "slicing question (K3, slices 183 and 184: a link under a type whose only version is broken), answered under the person's delegation of 2026-10-10"
---

# a-skipped-types-links-are-left-out

## Decision
A link waits on a placeholder only under a held type (decision/0024-a-link-may-land-on-a-placeholder), so with errors skipped a file carrying a link to an IRI under a type no version of which lands is left out with that type and reported as skipped by it; a link to a file left out under a type that does land waits on a placeholder.
