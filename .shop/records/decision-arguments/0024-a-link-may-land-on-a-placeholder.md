---
id: decision-argument/missingmass.io/shopsystem/kb/0024-a-link-may-land-on-a-placeholder
kind: decision-argument
about: bounded-context/missingmass.io/shopsystem/kb
---
# 0024 A link may land on a placeholder

2026-10-10. A link to an IRI that the store does not hold, under a type it does hold, lands on a placeholder: the IRI, typed by its place under its type, checked against the link's targets, and filled by creating an artifact at that IRI. The rule is the same over the contract and in import. A placeholder is nothing stored, only an IRI linked to and not held; reads mark a link's target as not held, and one query lists the placeholders with what links to each. An IRI under a type the store does not hold is still refused. Rests on 0023. The user's decision, so that contexts linking to each other, and a product's lead shop, can arrive in any order.
