---
id: design-decision/missingmass.io/shopsystem/kb/served-store-rules
summary: "Reaching a served store is refused under three new rules of kb's own, which join the published names: `connection` (the connection cannot be read or names no address; the fault names the connection), `unreachable` (the server cannot be reached or stops answering; the fault names the address and the call comes back with its answer) and `served` (a change asked of a served store by a client that found it directly; the fault names the server's address); a change asked of a server by a client readied with a clock keeps kb's rule `clock`, and that client's reads are answered."
date: 2026-10-06
status: accepted
by: ".shop/records/archive/design-notes/2026-10-06-kb-shop-knowledge-requests-design.md"
---

# served-store-rules

## Decision
Reaching a served store is refused under three new rules of kb's own, which join the published names: `connection` (the connection cannot be read or names no address; the fault names the connection), `unreachable` (the server cannot be reached or stops answering; the fault names the address and the call comes back with its answer) and `served` (a change asked of a served store by a client that found it directly; the fault names the server's address); a change asked of a server by a client readied with a clock keeps kb's rule `clock`, and that client's reads are answered.
