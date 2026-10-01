---
id: capability/operate-a-store
title: Operate a store
narrator: the operator
rests_on: [decision/init-refuses-inside-or-above, decision/0003-init-refuses-inside-a-store, decision/0008-contract-is-the-stable-boundary, decision/0020-a-server-found-where-the-store-is, decision/files-are-an-export, decision/busy-rule]
formulated_as: features/operate-a-store.feature
---

# Operate a store

## Purpose

From a shell, without any client, the operator sets a store up, checks the whole store, and serves a store to several callers. The command line changes content only through import into a freshly started store (export-and-import-a-store); every other change to content goes through a client. Checking the store is a read, and is never refused because another change is being written.

## Behaviour

- When the operator runs kb init against a directory with no store inside it, saying which role they are, there is a store inside that directory in a place of its own, and a client can define its own types in it straight away.
- If nothing names the operator's role, kb init is refused because the role must be named through `KB_ACTOR`, and the directory still has no store inside it.
- If the directory already has a store inside it, kb init is refused because that directory already has a store inside it, and that store holds what it held before.
- If the directory sits inside a store, kb init is refused because that directory is inside a store, and that store holds what it held before.
- When the operator runs kb validate, they are told of everything in the store that does not fit its type, and where, and of everything behind the type it was last checked against.
- The command line offers setting a store up, checking and exporting one, and importing into a freshly started store, and nothing else that changes what the store holds.
- While the operator works in a folder deep inside the directory a store sits in, when they run kb validate, the store found above where they are working is the one checked.
- While the operator works outside any store with `KB_ROOT` naming one, when they run kb validate, the store `KB_ROOT` names is the one checked.
- If the operator works outside any store and nothing names one, kb validate is refused because no store was found, neither above where they are working nor named outright.
- If `KB_ROOT` names a directory that holds no store, kb validate is refused because `KB_ROOT` names a directory that holds no store.
- If the operator works inside one store while `KB_ROOT` names a different store, kb validate is refused because `KB_ROOT` names a store other than the one they are standing in, and neither is guessed at.
- When the operator runs kb serve on a directory holding a store, giving an address, the store is served at that address, on whatever interface it names, all of them included.
- If the operator runs kb serve without an address, it is refused because no address is assumed.
- While another change is being written to the store, when the operator runs kb validate, the store is checked and kb validate is not refused because the store was busy with another change.

## Implementation, may change

- The commands are `kb init <root>`, `kb validate` and `kb serve <root> --listen <host:port>`; the role for `kb init` comes from `KB_ACTOR`. `kb serve` hosts the store at `<root>/kb/` with `grpc.server`. `kb export` and `kb import` are export-and-import-a-store.
- Reads never wait for the write lock (change-the-store).

## Not yet

- Serving among what the command line offers. Promoted when the served-store lines (reach-a-served-store, this capability's kb serve lines) are formulated and built.
