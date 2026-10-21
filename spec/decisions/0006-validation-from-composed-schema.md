---
id: design-decision/missingmass.io/shopsystem/kb/validation-from-composed-schema
summary: "Required fields and structural rules are JSON Schema 2020-12 fragments composed into one effective schema per type with kb's keywords; hand-written checks cover only what JSON Schema cannot express; stale artifacts are checked against the current type and a failing write to one is refused."
date: 2026-09-24
status: superseded
by: ".shop/records/decision-arguments/0006-validation-from-composed-schema.md"
source: decision-argument/missingmass.io/shopsystem/kb/0006-validation-from-composed-schema
---

# validation-from-composed-schema

## Decision
Required fields and structural rules are JSON Schema 2020-12 fragments composed into one effective schema per type with kb's keywords; hand-written checks cover only what JSON Schema cannot express; stale artifacts are checked against the current type and a failing write to one is refused.
