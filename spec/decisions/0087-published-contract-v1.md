---
id: design-decision/missingmass.io/shopsystem/kb/published-contract-v1
summary: "What a client may depend on is still versioned together by the release tag: `kb.proto` in package `kb.v1`, `kb.init` and `kb.NotStarted`, `kb.client.connect` with its clock, `kb.content`, the connection file's form, and every fault's `rule` name; everything else may change without notice."
date: 2026-10-01
status: superseded
by: ".shop/records/archive/design-notes/2026-10-01-kb-contract-v1-design.md"
source: decision-argument/missingmass.io/shopsystem/kb/2026-10-01-kb-contract-v1-design
supersedes: design-decision/missingmass.io/shopsystem/kb/the-published-contract
---

# published-contract-v1

## Decision
What a client may depend on is still versioned together by the release tag: `kb.proto` in package `kb.v1`, `kb.init` and `kb.NotStarted`, `kb.client.connect` with its clock, `kb.content`, the connection file's form, and every fault's `rule` name; everything else may change without notice.
