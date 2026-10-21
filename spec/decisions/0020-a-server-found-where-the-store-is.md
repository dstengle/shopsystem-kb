---
id: design-decision/missingmass.io/shopsystem/kb/a-server-found-where-the-store-is
summary: "Several callers reach one store through `kb serve <root> --listen <host:port>`, which takes changes one at a time and owns the store it serves; a caller finds it where it would find the store, `kb/store.yaml` or `kb/server.yaml` and never both; it listens on any interface it is given, with no authentication, its network its boundary; the clock stays the in-process client's; chosen over locking the store for several in-process callers (extends 0008 and 0018)."
date: 2026-09-28
status: superseded
by: ".shop/records/decision-arguments/0020-a-server-found-where-the-store-is.md"
source: decision-argument/missingmass.io/shopsystem/kb/0020-a-server-found-where-the-store-is
---

# a-server-found-where-the-store-is

## Decision
Several callers reach one store through `kb serve <root> --listen <host:port>`, which takes changes one at a time and owns the store it serves; a caller finds it where it would find the store, `kb/store.yaml` or `kb/server.yaml` and never both; it listens on any interface it is given, with no authentication, its network its boundary; the clock stays the in-process client's; chosen over locking the store for several in-process callers (extends 0008 and 0018).
