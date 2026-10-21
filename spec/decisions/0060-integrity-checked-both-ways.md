---
id: design-decision/missingmass.io/shopsystem/kb/integrity-checked-both-ways
summary: "A change is checked for the links into what it changes as well as the links it carries: dropping an item, or removing an artifact or a type, that anything outside the set links into is refused with the published rule `on_delete` (`linked` is only the port's internal name), every artifact carrying one implicit link to its type, and the adapter re-checks this inside its write transaction so a concurrent change cannot slip between the check and the write."
date: 2026-10-01
status: accepted
by: ".shop/records/archive/design-notes/2026-10-01-kb-storage-sqlite-design.md"
---

# integrity-checked-both-ways

## Decision
A change is checked for the links into what it changes as well as the links it carries: dropping an item, or removing an artifact or a type, that anything outside the set links into is refused with the published rule `on_delete` (`linked` is only the port's internal name), every artifact carrying one implicit link to its type, and the adapter re-checks this inside its write transaction so a concurrent change cannot slip between the check and the write.
