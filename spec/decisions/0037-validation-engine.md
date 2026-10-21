---
id: design-decision/missingmass.io/shopsystem/kb/validation-engine
summary: "Validation uses python-jsonschema with the `referencing` library, extended with kb keywords, so the JSON Schema side is checked natively in one pass and code checks only what the schema language cannot express."
date: 2026-09-23
status: accepted
by: ".shop/records/archive/design-notes/2026-09-23-kb-design.md"
---

# validation-engine

## Decision
Validation uses python-jsonschema with the `referencing` library, extended with kb keywords, so the JSON Schema side is checked natively in one pass and code checks only what the schema language cannot express.
