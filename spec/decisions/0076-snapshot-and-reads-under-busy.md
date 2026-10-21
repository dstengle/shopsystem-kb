---
id: design-decision/missingmass.io/shopsystem/kb/snapshot-and-reads-under-busy
summary: "A snapshot writes to the store, so it is a call that changes the store and is refused as `busy` like a change; kb export and kb validate are reads and are never refused as busy; where entries for different artifacts carry the same moment they are given in the order they landed, and a read of one artifact's history keeps landing order even where its moments run the other way."
date: 2026-10-01
status: accepted
by: ".shop/records/archive/design-notes/2026-10-01-kb-pr1-review-answers.md; the person's answers of 2026-10-01 to the integration's questions 5 to 8"
---

# snapshot-and-reads-under-busy

## Decision
A snapshot writes to the store, so it is a call that changes the store and is refused as `busy` like a change; kb export and kb validate are reads and are never refused as busy; where entries for different artifacts carry the same moment they are given in the order they landed, and a read of one artifact's history keeps landing order even where its moments run the other way.
