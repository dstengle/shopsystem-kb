---
id: design-decision/missingmass.io/shopsystem/kb/summary-read-only-at-the-top
summary: "The fields shown at a glance (`summary`) are read only at the top of a type's schema; one at the top of a collection's items is refused like any misplaced keyword, rule `placement`, because a part's stub carries only its collection, name and title and kb reads `summary` nowhere else; showing item fields in part stubs would change the published contract and no client asks for it."
date: 2026-10-01
status: accepted
by: "the batch 26 review's question, decided by the controller under the person's delegation of 2026-10-01; supersedes design-decision/missingmass.io/shopsystem/kb/kb-keywords-read-where-written (its clause on `summary` at the top of a collection's items)"
supersedes: design-decision/missingmass.io/shopsystem/kb/kb-keywords-read-where-written
---

# summary-read-only-at-the-top

## Decision
The fields shown at a glance (`summary`) are read only at the top of a type's schema; one at the top of a collection's items is refused like any misplaced keyword, rule `placement`, because a part's stub carries only its collection, name and title and kb reads `summary` nowhere else; showing item fields in part stubs would change the published contract and no client asks for it.
