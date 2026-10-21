---
id: design-decision/missingmass.io/shopsystem/kb/references-inside-a-set
summary: "A create in `CreateMany` may carry a key of the client's choosing, unique in the set, and a link written `@<key>` anywhere in the set names the artifact that create makes, kb putting the minted name in its place before anything is checked; a reference names a whole artifact, never a part; a key no create carries, a key two creates carry, and a key with a place are refused with rule `ref`."
date: 2026-10-01
status: superseded
by: ".shop/records/archive/design-notes/2026-10-01-kb-contract-v1-design.md; the controller's answers to the integration's questions 1, 2 and 8, under the person's delegation of 2026-10-01"
---

# references-inside-a-set

## Decision
A create in `CreateMany` may carry a key of the client's choosing, unique in the set, and a link written `@<key>` anywhere in the set names the artifact that create makes, kb putting the minted name in its place before anything is checked; a reference names a whole artifact, never a part; a key no create carries, a key two creates carry, and a key with a place are refused with rule `ref`.
