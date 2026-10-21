---
id: design-decision/missingmass.io/shopsystem/kb/type-of-types-id-published
summary: "The type that describes types is `schema/schema`, and that id is published, so a client tells a store that holds nothing but kb's own type by listing the kind `schema` and finding that id alone; no call is added."
date: 2026-10-06
status: superseded
by: ".shop/records/archive/design-notes/2026-10-06-kb-shop-knowledge-requests-design.md"
source: decision-argument/missingmass.io/shopsystem/kb/2026-10-06-kb-shop-knowledge-requests-design
---

# type-of-types-id-published

## Decision
The type that describes types is `schema/schema`, and that id is published, so a client tells a store that holds nothing but kb's own type by listing the kind `schema` and finding that id alone; no call is added.
