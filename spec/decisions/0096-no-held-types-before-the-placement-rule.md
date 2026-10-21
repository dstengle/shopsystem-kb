---
id: design-decision/missingmass.io/shopsystem/kb/no-held-types-before-the-placement-rule
summary: "A type the store held before kb read its keywords only where it reads them is not provided for: there are no stores or clients to carry, as everything is new code, so a type is checked against the placement rule whenever it is written and the lines about held types are removed."
date: 2026-10-01
status: accepted
by: "the person, 2026-10-01: "Don't worry about migration. This is all new code so migration is not needed at this point"; supersedes design-decision/missingmass.io/shopsystem/kb/kb-keywords-read-where-written (its clause on a type the store already holds)"
supersedes: design-decision/missingmass.io/shopsystem/kb/kb-keywords-read-where-written
---

# no-held-types-before-the-placement-rule

## Decision
A type the store held before kb read its keywords only where it reads them is not provided for: there are no stores or clients to carry, as everything is new code, so a type is checked against the placement rule whenever it is written and the lines about held types are removed.
