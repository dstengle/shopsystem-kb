---
id: design-decision/missingmass.io/shopsystem/kb/published-contract-v1-in-0-7-0
summary: "What a client may depend on is still versioned together by the release tag: `kb.proto` in package `kb.v1`, `kb.init` with its `execution` keyword and `kb.NotStarted`, `kb.client.connect` with its clock and `where()`, `kb.content` with `NotCanonical.path` and its form, `kb.testing.served`, the id `schema/schema`, the connection file's form, every fault's `rule` name, and kb's image's store directory (`/data`), its port (50051), its entry point (`kb`) and its default command (`serve /data --listen 0.0.0.0:50051 --start`), the Dockerfile's insides not among them; with `kb init --seed` and `kb serve --start` this adds to contract v1 and changes nothing in it, so the package stays `kb.v1` and the release is kb 0.7.0; everything else may change without notice."
date: 2026-10-07
status: superseded
by: ".shop/records/archive/design-notes/2026-10-07-kb-docker-design.md"
source: decision-argument/missingmass.io/shopsystem/kb/2026-10-07-kb-docker-design
supersedes: design-decision/missingmass.io/shopsystem/kb/published-contract-v1-in-0-6-0
---

# published-contract-v1-in-0-7-0

## Decision
What a client may depend on is still versioned together by the release tag: `kb.proto` in package `kb.v1`, `kb.init` with its `execution` keyword and `kb.NotStarted`, `kb.client.connect` with its clock and `where()`, `kb.content` with `NotCanonical.path` and its form, `kb.testing.served`, the id `schema/schema`, the connection file's form, every fault's `rule` name, and kb's image's store directory (`/data`), its port (50051), its entry point (`kb`) and its default command (`serve /data --listen 0.0.0.0:50051 --start`), the Dockerfile's insides not among them; with `kb init --seed` and `kb serve --start` this adds to contract v1 and changes nothing in it, so the package stays `kb.v1` and the release is kb 0.7.0; everything else may change without notice.
