---
id: design-decision/missingmass.io/shopsystem/kb/input-safety-at-the-boundary
summary: "Every request field becomes a validated value before the domain sees it; names follow a plain-name grammar with no `..` or absolute paths; the boundary fails closed, one wrapper turning refusals into faults with nothing written."
date: 2026-09-24
status: accepted
by: ".shop/records/decision-arguments/0007-input-safety-at-the-boundary.md"
---

# input-safety-at-the-boundary

## Decision
Every request field becomes a validated value before the domain sees it; names follow a plain-name grammar with no `..` or absolute paths; the boundary fails closed, one wrapper turning refusals into faults with nothing written.
