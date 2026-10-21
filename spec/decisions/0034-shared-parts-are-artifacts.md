---
id: design-decision/missingmass.io/shopsystem/kb/shared-parts-are-artifacts
summary: "A thing used from more than one artifact, or changing independently of its container, is its own artifact, referenced with bindings by each using artifact; state that belongs to a use lives on the artifact representing the use, never on the thing."
date: 2026-09-23
status: accepted
by: ".shop/records/archive/design-notes/2026-09-23-kb-design.md"
revisit_when: "a use needs state the bindings cannot carry"
---

# shared-parts-are-artifacts

## Decision
A thing used from more than one artifact, or changing independently of its container, is its own artifact, referenced with bindings by each using artifact; state that belongs to a use lives on the artifact representing the use, never on the thing.
