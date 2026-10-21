---
id: design-decision/missingmass.io/shopsystem/kb/links-read-only-where-kb-reads-them-today
summary: "A link field is read only directly among the fields of a type, of a base it is built on, or of the items of any of its collections at any depth; one in a named shape another field uses is refused like any other misplaced link field, because kb has never read links there and reading them would be new behaviour the type-language note does not ask for."
date: 2026-10-01
status: accepted
by: "the batch 26 planning question, decided by the controller under the person's delegation of 2026-10-01; supersedes design-decision/missingmass.io/shopsystem/kb/kb-keywords-read-where-written (its clause on a named shape another field uses)"
supersedes: design-decision/missingmass.io/shopsystem/kb/kb-keywords-read-where-written
---

# links-read-only-where-kb-reads-them-today

## Decision
A link field is read only directly among the fields of a type, of a base it is built on, or of the items of any of its collections at any depth; one in a named shape another field uses is refused like any other misplaced link field, because kb has never read links there and reading them would be new behaviour the type-language note does not ask for.
