---
id: design-decision/missingmass.io/shopsystem/kb/files-are-an-export
summary: "Reviewable files are the operator's output, written on demand by `kb export` as canonical YAML; files on disk enter a store only through `kb import`, which checks them first and lands only in a freshly started store, one holding no artifact besides the type that describes types."
date: 2026-10-01
status: superseded
by: ".shop/records/archive/design-notes/2026-10-01-kb-storage-sqlite-design.md"
revisit_when: "someone needs to combine stores"
---

# files-are-an-export

## Decision
Reviewable files are the operator's output, written on demand by `kb export` as canonical YAML; files on disk enter a store only through `kb import`, which checks them first and lands only in a freshly started store, one holding no artifact besides the type that describes types.
