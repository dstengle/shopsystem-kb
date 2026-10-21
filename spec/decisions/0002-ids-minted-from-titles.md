---
id: design-decision/missingmass.io/shopsystem/kb/ids-minted-from-titles
summary: "An artifact's id is `kind/name`, the name made from its title by kb's grammar with -2, -3 on collision; parts are named from their title or position, once; a client hands existing ids back on a write and never chooses one."
date: 2026-09-23
status: superseded
by: ".shop/records/decision-arguments/0002-ids-minted-from-titles.md"
source: decision-argument/missingmass.io/shopsystem/kb/0002-ids-minted-from-titles
---

# ids-minted-from-titles

## Decision
An artifact's id is `kind/name`, the name made from its title by kb's grammar with -2, -3 on collision; parts are named from their title or position, once; a client hands existing ids back on a write and never chooses one.
