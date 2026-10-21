---
id: design-decision/missingmass.io/shopsystem/kb/where-is-the-clients-search
summary: "The client publishes `where()`, which searches as a call would and answers either where the search stopped (and, for a connection, the server's address) or the faults that say why nothing was found, never both; a store this kb cannot read is still where the search stopped, and a directory holding both a store and a connection is the search's fault; it is the client's own search, so no rpc says where a store is and no server is called, and how a client tells its user where that is (`KB_ROOT`'s value, a named directory, an address) is the client's, since it knows its own environment."
date: 2026-10-06
status: accepted
by: ".shop/records/archive/design-notes/2026-10-06-kb-shop-knowledge-requests-design.md; the integration's questions 5-7 answered under the person's delegation"
---

# where-is-the-clients-search

## Decision
The client publishes `where()`, which searches as a call would and answers either where the search stopped (and, for a connection, the server's address) or the faults that say why nothing was found, never both; a store this kb cannot read is still where the search stopped, and a directory holding both a store and a connection is the search's fault; it is the client's own search, so no rpc says where a store is and no server is called, and how a client tells its user where that is (`KB_ROOT`'s value, a named directory, an address) is the client's, since it knows its own environment.
