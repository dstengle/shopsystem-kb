---
id: design-decision/missingmass.io/shopsystem/kb/history-ordered-per-artifact
summary: "Moments order each artifact's history, not the whole store's: one artifact's entries come in the order its changes landed, entries across artifacts in the order of their moments, and a read since a moment gives what is stamped from that moment on as the store holds it when read, so a client following the history reads since a moment a little before the last one it saw and drops the entries it already has."
date: 2026-10-01
status: accepted
by: ".shop/records/archive/design-notes/2026-10-01-kb-pr1-review-answers.md"
source: decision-argument/missingmass.io/shopsystem/kb/2026-10-01-kb-pr1-review-answers
---

# history-ordered-per-artifact

## Decision
Moments order each artifact's history, not the whole store's: one artifact's entries come in the order its changes landed, entries across artifacts in the order of their moments, and a read since a moment gives what is stamped from that moment on as the store holds it when read, so a client following the history reads since a moment a little before the last one it saw and drops the entries it already has.
