---
id: design-decision/missingmass.io/shopsystem/kb/composition-covers-common-fields
summary: "Types share fields only by `allOf` with `$ref`, kb's keywords composing base first; no type hierarchy."
date: 2026-09-23
status: accepted
by: ".shop/records/archive/design-notes/2026-09-23-kb-design.md"
revisit_when: "a type needs to override or mix in"
---

# composition-covers-common-fields

## Decision
Types share fields only by `allOf` with `$ref`, kb's keywords composing base first; no type hierarchy.
