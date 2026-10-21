---
id: design-decision/missingmass.io/shopsystem/kb/one-method-per-action
summary: "Every rpc is one action named in the spec's words (`Create`, `Replace`, `Add`, `Remove`, `Read`, `List`, `Follow`, `Search`, `History`, `Snapshot`, `Check`) with a request and a response message of its own, no message shared between two requests except the small values every call names things with (a locator, a signature, a fault, a stub); a kind is called a kind and a place a place, never a type or a path, wherever a request or a response names one."
date: 2026-10-01
status: accepted
by: ".shop/records/archive/design-notes/2026-10-01-kb-contract-v1-design.md"
source: decision-argument/missingmass.io/shopsystem/kb/2026-10-01-kb-contract-v1-design
---

# one-method-per-action

## Decision
Every rpc is one action named in the spec's words (`Create`, `Replace`, `Add`, `Remove`, `Read`, `List`, `Follow`, `Search`, `History`, `Snapshot`, `Check`) with a request and a response message of its own, no message shared between two requests except the small values every call names things with (a locator, a signature, a fault, a stub); a kind is called a kind and a place a place, never a type or a path, wherever a request or a response names one.
