---
id: design-decision/missingmass.io/shopsystem/kb/published-contract-v1-in-0-6-0
summary: "What a client may depend on is still versioned together by the release tag: `kb.proto` in package `kb.v1`, `kb.init` with its `execution` keyword and `kb.NotStarted`, `kb.client.connect` with its clock and `where()`, `kb.content` with `NotCanonical.path` and its form, `kb.testing.served`, the id `schema/schema`, the connection file's form, and every fault's `rule` name, `connection`, `unreachable` and `served` among them; all of it adds to contract v1 and changes nothing in it, so the package stays `kb.v1` and the release is kb 0.6.0; everything else may change without notice."
date: 2026-10-06
status: superseded
by: ".shop/records/archive/design-notes/2026-10-06-kb-shop-knowledge-requests-design.md"
source: decision-argument/missingmass.io/shopsystem/kb/2026-10-06-kb-shop-knowledge-requests-design
supersedes: design-decision/missingmass.io/shopsystem/kb/published-contract-v1
---

# published-contract-v1-in-0-6-0

## Decision
What a client may depend on is still versioned together by the release tag: `kb.proto` in package `kb.v1`, `kb.init` with its `execution` keyword and `kb.NotStarted`, `kb.client.connect` with its clock and `where()`, `kb.content` with `NotCanonical.path` and its form, `kb.testing.served`, the id `schema/schema`, the connection file's form, and every fault's `rule` name, `connection`, `unreachable` and `served` among them; all of it adds to contract v1 and changes nothing in it, so the package stays `kb.v1` and the release is kb 0.6.0; everything else may change without notice.
