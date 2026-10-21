---
id: design-decision/missingmass.io/shopsystem/kb/result-or-refusal
summary: "Every response is either the call's result or a refusal holding every fault, never both: a refusal carries no half-filled result and a result carries no faults; `Check`'s result is the violations and the stale, the violations being what the store holds, not a refusal."
date: 2026-10-01
status: accepted
by: ".shop/records/archive/design-notes/2026-10-01-kb-contract-v1-design.md"
---

# result-or-refusal

## Decision
Every response is either the call's result or a refusal holding every fault, never both: a refusal carries no half-filled result and a result carries no faults; `Check`'s result is the violations and the stale, the violations being what the store holds, not a refusal.
