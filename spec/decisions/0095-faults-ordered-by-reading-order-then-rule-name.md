---
id: design-decision/missingmass.io/shopsystem/kb/faults-ordered-by-reading-order-then-rule-name
summary: "Faults at different places come in the order the artifact reads back in, which is its type's declared order and the order the store writes it in (a collection's items in their order, sections in their order, a section's inner sections after it), not the order the client wrote it in; faults at one place come by rule name, alphabetically; a type refused as it is written has the places of the type as it reads back; across the changes of a set, the order of the set. This holds for a refused artifact, a type refused as it is written, each change of a set, and each artifact's violations in a check."
date: 2026-10-01
status: superseded
by: "the person's answers under their delegation of 2026-10-01, to the questions on the fault-order lines of check-a-change, check-the-store, make-several-changes-in-one-go and define-a-type"
supersedes: design-decision/missingmass.io/shopsystem/kb/faults-ordered-by-place-then-rule
---

# faults-ordered-by-reading-order-then-rule-name

## Decision
Faults at different places come in the order the artifact reads back in, which is its type's declared order and the order the store writes it in (a collection's items in their order, sections in their order, a section's inner sections after it), not the order the client wrote it in; faults at one place come by rule name, alphabetically; a type refused as it is written has the places of the type as it reads back; across the changes of a set, the order of the set. This holds for a refused artifact, a type refused as it is written, each change of a set, and each artifact's violations in a check.
