---
id: design-decision/missingmass.io/shopsystem/kb/earlier-store-told-apart
summary: "The store's marker says which form of store it marks, so a store made by an earlier kb in a form this kb cannot read is told apart: it counts as a store when one is started and when it is found, and every call and command that needs it, the import included, is refused, saying to start a new store and import the old one's files, an earlier kb's store being only ever an import's source; its rule is `unreadable`, since what the client can do about it is the same (this kb cannot read the store), and only the reason differs."
date: 2026-10-01
status: superseded
by: ".shop/records/archive/design-notes/2026-10-01-kb-pr1-review-answers.md; the person's answers of 2026-10-01 to the integration's questions 3 and 9"
---

# earlier-store-told-apart

## Decision
The store's marker says which form of store it marks, so a store made by an earlier kb in a form this kb cannot read is told apart: it counts as a store when one is started and when it is found, and every call and command that needs it, the import included, is refused, saying to start a new store and import the old one's files, an earlier kb's store being only ever an import's source; its rule is `unreadable`, since what the client can do about it is the same (this kb cannot read the store), and only the reason differs.
