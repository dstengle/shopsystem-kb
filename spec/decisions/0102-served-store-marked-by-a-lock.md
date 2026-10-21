---
id: design-decision/missingmass.io/shopsystem/kb/served-store-marked-by-a-lock
summary: "While it serves, the server holds a lock of the operating system on a file of the store's own inside `kb/` that says the address it serves at, so a client that finds the store directly reads it and is refused a change, naming that address; the lock goes when the server's process does, so a server that stopped, however it stopped, leaves no store marked as served."
date: 2026-10-06
status: accepted
by: ".shop/records/archive/design-notes/2026-10-06-kb-shop-knowledge-requests-design.md"
source: decision-argument/missingmass.io/shopsystem/kb/2026-10-06-kb-shop-knowledge-requests-design
---

# served-store-marked-by-a-lock

## Decision
While it serves, the server holds a lock of the operating system on a file of the store's own inside `kb/` that says the address it serves at, so a client that finds the store directly reads it and is refused a change, naming that address; the lock goes when the server's process does, so a server that stopped, however it stopped, leaves no store marked as served.
