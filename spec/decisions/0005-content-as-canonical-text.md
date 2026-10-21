---
id: design-decision/missingmass.io/shopsystem/kb/content-as-canonical-text
summary: "Artifact content crosses the protobuf contract as canonical YAML text, not a Struct, so key order and integers survive; identity keys are typed fields."
date: 2026-09-24
status: accepted
by: ".shop/records/decision-arguments/0005-content-as-canonical-text.md"
---

# content-as-canonical-text

## Decision
Artifact content crosses the protobuf contract as canonical YAML text, not a Struct, so key order and integers survive; identity keys are typed fields.
