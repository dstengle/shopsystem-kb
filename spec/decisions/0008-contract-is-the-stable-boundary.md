---
id: design-decision/missingmass.io/shopsystem/kb/contract-is-the-stable-boundary
summary: "`kb.proto` with the in-process transport first is the interface clients depend on and git-first storage may change behind it; types are data and special outputs are client code; no MCP hop; scenario status is a future ledger, not a work-item field."
date: 2026-09-23
status: accepted
by: ".shop/records/decision-arguments/0008-contract-is-the-stable-boundary.md"
source: decision-argument/missingmass.io/shopsystem/kb/0008-contract-is-the-stable-boundary
---

# contract-is-the-stable-boundary

## Decision
`kb.proto` with the in-process transport first is the interface clients depend on and git-first storage may change behind it; types are data and special outputs are client code; no MCP hop; scenario status is a future ledger, not a work-item field.
