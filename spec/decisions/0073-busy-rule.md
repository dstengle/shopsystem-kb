---
id: design-decision/missingmass.io/shopsystem/kb/busy-rule
summary: "A change, a set or the operator's import that waits for the write lock longer than the store waits is refused with a rule of its own, `busy`, which joins kb's published rule names, nothing written and the same change free to be made again; not `unreadable`, whose advice (the store is damaged or missing) is wrong for it; reads never wait for the lock, so none is refused as busy."
date: 2026-10-01
status: accepted
by: ".shop/records/archive/design-notes/2026-10-01-kb-pr1-review-answers.md"
---

# busy-rule

## Decision
A change, a set or the operator's import that waits for the write lock longer than the store waits is refused with a rule of its own, `busy`, which joins kb's published rule names, nothing written and the same change free to be made again; not `unreadable`, whose advice (the store is damaged or missing) is wrong for it; reads never wait for the lock, so none is refused as busy.
