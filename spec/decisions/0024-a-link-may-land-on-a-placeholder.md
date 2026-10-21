---
id: design-decision/missingmass.io/shopsystem/kb/a-link-may-land-on-a-placeholder
summary: "A link to an IRI the store does not hold, under a type it does hold, lands on a placeholder: the IRI, typed by its place under its type, checked against the link's targets, and filled by creating an artifact at that IRI; the same over the contract and in import; a placeholder is nothing stored; reads mark a link's target as not held and one query lists the placeholders with what links to each; an IRI under a type the store does not hold is still refused; so that artifacts linking to each other can arrive in any order."
date: 2026-10-10
status: accepted
by: ".shop/records/decision-arguments/0024-a-link-may-land-on-a-placeholder.md"
---

# a-link-may-land-on-a-placeholder

## Decision
A link to an IRI the store does not hold, under a type it does hold, lands on a placeholder: the IRI, typed by its place under its type, checked against the link's targets, and filled by creating an artifact at that IRI; the same over the contract and in import; a placeholder is nothing stored; reads mark a link's target as not held and one query lists the placeholders with what links to each; an IRI under a type the store does not hold is still refused; so that artifacts linking to each other can arrive in any order.
