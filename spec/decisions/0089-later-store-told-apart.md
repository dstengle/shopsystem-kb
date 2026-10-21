---
id: design-decision/missingmass.io/shopsystem/kb/later-store-told-apart
summary: "A store whose marker names a form of store this kb does not know, one a later kb made, and a store whose marker cannot be read at all, whatever its bytes, are told apart from a damaged database: every call and command that needs the store, the import included, is refused because the store was made by a later version of kb, which is needed to read it, nothing is written, and the store is not opened; starting a store over one is refused as over any store. The rule is `unreadable`, as for an earlier kb's store, since what the client can do is the same (this kb cannot read the store)."
date: 2026-10-01
status: accepted
by: ".shop/records/archive/design-notes/2026-10-01-kb-batch24-review-answers.md; the controller's answer to the integration's question 1, under the person's delegation"
---

# later-store-told-apart

## Decision
A store whose marker names a form of store this kb does not know, one a later kb made, and a store whose marker cannot be read at all, whatever its bytes, are told apart from a damaged database: every call and command that needs the store, the import included, is refused because the store was made by a later version of kb, which is needed to read it, nothing is written, and the store is not opened; starting a store over one is refused as over any store. The rule is `unreadable`, as for an earlier kb's store, since what the client can do is the same (this kb cannot read the store).
