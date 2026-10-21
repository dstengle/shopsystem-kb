---
id: design-decision/missingmass.io/shopsystem/kb/type-language-stays-json-schema
summary: "kb keeps JSON Schema 2020-12, with its own keywords, as the language types are written in, not a smaller structural model of kb's own: the one client's eight types use about ten JSON Schema keywords and fit inside it; a replacement would break contract v1 (a fault's rule is the JSON Schema keyword it breaks) and every type a store holds, with no migration to carry them; and kb would rebuild the validator, its errors and the type of types that the library gives it today."
date: 2026-10-01
status: accepted
by: ".shop/records/archive/design-notes/2026-10-01-kb-type-language-design.md; the controller's recommendation under the person's delegation of 2026-10-01"
revisit_when: "a client needs a type JSON Schema cannot state, or types must migrate between versions"
---

# type-language-stays-json-schema

## Decision
kb keeps JSON Schema 2020-12, with its own keywords, as the language types are written in, not a smaller structural model of kb's own: the one client's eight types use about ten JSON Schema keywords and fit inside it; a replacement would break contract v1 (a fault's rule is the JSON Schema keyword it breaks) and every type a store holds, with no migration to carry them; and kb would rebuild the validator, its errors and the type of types that the library gives it today.
