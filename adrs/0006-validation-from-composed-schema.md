# 0006 Validation is schema-driven from composed fragments

2026-09-24. Required fields and structural rules live in JSON Schema 2020-12 fragments composed into one effective schema per type, plus the kb keywords (ref, parts, sections, summary). Hand-written checks cover only what JSON Schema cannot express. Stale artifacts are checked against the current schema; a failing write to one is refused.
