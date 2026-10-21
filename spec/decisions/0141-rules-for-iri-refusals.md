---
id: design-decision/missingmass.io/shopsystem/kb/rules-for-iri-refusals
summary: "An IRI not of kb's grammar carries rule `locator`; an IRI not under its type's, and an IRI already held, carry `identity`; a version not held, or not later than the one an artifact conforms to, carries `version`; an import's artifact differing from the one the store holds carries a new rule, `differs`, which joins kb's published rule names."
date: 2026-10-10
status: accepted
by: "the person's delegation of 2026-10-10"
---

# rules-for-iri-refusals

## Decision
An IRI not of kb's grammar carries rule `locator`; an IRI not under its type's, and an IRI already held, carry `identity`; a version not held, or not later than the one an artifact conforms to, carries `version`; an import's artifact differing from the one the store holds carries a new rule, `differs`, which joins kb's published rule names.
