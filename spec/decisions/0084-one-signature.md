---
id: design-decision/missingmass.io/shopsystem/kb/one-signature
summary: "Every request that changes the store, and `Snapshot`, carries one `Signature` holding the role, the piece of work and the message, a snapshot's piece of work being its signature's; the rules of signing do not change, only the shape they arrive in."
date: 2026-10-01
status: accepted
by: ".shop/records/archive/design-notes/2026-10-01-kb-contract-v1-design.md"
source: decision-argument/missingmass.io/shopsystem/kb/2026-10-01-kb-contract-v1-design
---

# one-signature

## Decision
Every request that changes the store, and `Snapshot`, carries one `Signature` holding the role, the piece of work and the message, a snapshot's piece of work being its signature's; the rules of signing do not change, only the shape they arrive in.
