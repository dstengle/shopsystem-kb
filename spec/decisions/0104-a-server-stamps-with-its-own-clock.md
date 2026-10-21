---
id: design-decision/missingmass.io/shopsystem/kb/a-server-stamps-with-its-own-clock
summary: "A server stamps each change with its own clock: the machine's under `kb serve`, and the one given to `kb.testing.served` when one is given; a client's clock belongs to a client that reaches its store in process, so a change asked of a server by a client readied with one is refused."
date: 2026-10-06
status: accepted
by: ".shop/records/archive/design-notes/2026-10-06-kb-shop-knowledge-requests-design.md; supersedes design-decision/missingmass.io/shopsystem/kb/a-server-found-where-the-store-is (its clause "the clock stays the in-process client's")"
source: decision-argument/missingmass.io/shopsystem/kb/2026-10-06-kb-shop-knowledge-requests-design
supersedes: design-decision/missingmass.io/shopsystem/kb/a-server-found-where-the-store-is
---

# a-server-stamps-with-its-own-clock

## Decision
A server stamps each change with its own clock: the machine's under `kb serve`, and the one given to `kb.testing.served` when one is given; a client's clock belongs to a client that reaches its store in process, so a change asked of a server by a client readied with one is refused.
