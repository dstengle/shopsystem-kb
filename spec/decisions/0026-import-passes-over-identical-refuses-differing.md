---
id: design-decision/missingmass.io/shopsystem/kb/import-passes-over-identical-refuses-differing
summary: "Import goes into any store: an artifact the store already holds at the same IRI, with the same content and type version, is passed over; one that differs refuses the whole import, naming each IRI, and nothing lands; replacing content stays a change through the contract."
date: 2026-10-10
status: accepted
by: ".shop/records/decision-arguments/0026-import-passes-over-identical-refuses-differing.md; supersedes design-decision/missingmass.io/shopsystem/kb/files-are-an-export (its clause that import lands only in a freshly started store)"
source: decision-argument/missingmass.io/shopsystem/kb/0026-import-passes-over-identical-refuses-differing
supersedes: design-decision/missingmass.io/shopsystem/kb/files-are-an-export
---

# import-passes-over-identical-refuses-differing

## Decision
Import goes into any store: an artifact the store already holds at the same IRI, with the same content and type version, is passed over; one that differs refuses the whole import, naming each IRI, and nothing lands; replacing content stays a change through the contract.
