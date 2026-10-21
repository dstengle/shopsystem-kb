---
id: design-decision/missingmass.io/shopsystem/kb/serialization-yaml
summary: "Serialization is YAML, read with a standard parser and emitted canonically by kb alone, which never needs round-trip preservation because it is the only writer."
date: 2026-09-23
status: superseded
by: ".shop/records/archive/design-notes/2026-09-23-kb-design.md"
---

# serialization-yaml

## Decision
Serialization is YAML, read with a standard parser and emitted canonically by kb alone, which never needs round-trip preservation because it is the only writer.
