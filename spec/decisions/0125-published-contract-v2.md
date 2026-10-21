---
id: design-decision/missingmass.io/shopsystem/kb/published-contract-v2
summary: "What a client may depend on is still versioned together by the release tag, as design-decision/missingmass.io/shopsystem/kb/published-contract-v1-in-0-7-0 lists it, except that `kb.proto` is in package `kb.v2`, the type that describes types is published as `https://missingmass.io/kb/type` in place of `schema/schema`, and kb's IRI grammar is published as the rule a client names artifacts, parts and types by."
date: 2026-10-10
status: accepted
by: ".shop/records/archive/requests/2026-10-10-requests-to-kb-portable-knowledge.md; the person's delegation of 2026-10-10"
supersedes: design-decision/missingmass.io/shopsystem/kb/published-contract-v1-in-0-7-0
---

# published-contract-v2

## Decision
What a client may depend on is still versioned together by the release tag, as decision/published-contract-v1-in-0-7-0 lists it, except that `kb.proto` is in package `kb.v2`, the type that describes types is published as `https://missingmass.io/kb/type` in place of `schema/schema`, and kb's IRI grammar is published as the rule a client names artifacts, parts and types by.
