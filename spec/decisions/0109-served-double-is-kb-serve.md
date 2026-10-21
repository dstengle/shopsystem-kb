---
id: design-decision/missingmass.io/shopsystem/kb/served-double-is-kb-serve
summary: "`kb.testing.served(store_root, connection_dir, *, clock=None)` is a published context manager that serves a started store with the server `kb serve` runs, not an imitation, in the test's own process on `127.0.0.1` at a free port, writes the connection under a different directory (a directory never holds both), yields the address and on exit, however the test ended, stops the server and removes the connection; no pytest plugin is loaded on install, a fixture over it being the client's three lines, which the README shows."
date: 2026-10-06
status: accepted
by: ".shop/records/archive/design-notes/2026-10-06-kb-shop-knowledge-requests-design.md"
source: decision-argument/missingmass.io/shopsystem/kb/2026-10-06-kb-shop-knowledge-requests-design
---

# served-double-is-kb-serve

## Decision
`kb.testing.served(store_root, connection_dir, *, clock=None)` is a published context manager that serves a started store with the server `kb serve` runs, not an imitation, in the test's own process on `127.0.0.1` at a free port, writes the connection under a different directory (a directory never holds both), yields the address and on exit, however the test ended, stops the server and removes the connection; no pytest plugin is loaded on install, a fixture over it being the client's three lines, which the README shows.
