---
id: capability/operate-a-store
title: Operate a store
narrator: the operator
rests_on: [decision/init-refuses-inside-or-above, decision/0003-init-refuses-inside-a-store, decision/0008-contract-is-the-stable-boundary, decision/0020-a-server-found-where-the-store-is, decision/0019-kb-git-owns-its-store]
formulated_as: features/operate-a-store.feature
---

# Operate a store

## Purpose

From a shell, without any client, the operator sets a store up, checks the whole store, and serves a store to several callers. The command line never changes content; every change to content goes through a client.

## Behaviour

- When the operator runs kb init against a directory with no store inside it, saying which role they are, there is a store inside that directory in a place of its own, and a client can define its own types in it straight away.
- While the operator's environment names that directory's git repository to work in, when they run kb init against it, there is a store inside it, the store's history holds one entry under that role with the message "initialise store", and that repository gains nothing in its history and nothing made ready for its next commit.
- If nothing names the operator's role, kb init is refused because the role must be named through `KB_ACTOR`, and the directory still has no store inside it.
- If the directory already has a store inside it, kb init is refused because that directory already has a store inside it, and that store holds what it held before.
- If the directory sits inside a store, kb init is refused because that directory is inside a store, and that store holds what it held before.
- When the operator runs kb validate, they are told of everything in the store that does not fit its type, and where, and of everything behind the type it was last checked against.
- The command line offers setting a store up and checking one, and nothing that changes what the store holds.
- While the operator works in a folder deep inside the directory a store sits in, when they run kb validate, the store found above where they are working is the one checked.
- While the operator works outside any store with `KB_ROOT` naming one, when they run kb validate, the store `KB_ROOT` names is the one checked.
- If the operator works outside any store and nothing names one, kb validate is refused because no store was found, neither above where they are working nor named outright.
- If `KB_ROOT` names a directory that holds no store, kb validate is refused because `KB_ROOT` names a directory that holds no store.
- If the operator works inside one store while `KB_ROOT` names a different store, kb validate is refused because `KB_ROOT` names a store other than the one they are standing in, and neither is guessed at.
- When the operator runs kb serve on a directory holding a store, giving an address, the store is served at that address, on whatever interface it names, all of them included.
- If the operator runs kb serve without an address, it is refused because no address is assumed.

## Implementation, may change

- The commands are `kb init <root>`, `kb validate` and `kb serve <root> --listen <host:port>`; the role for `kb init` comes from `KB_ACTOR`. `kb serve` hosts the store at `<root>/kb/` with `grpc.server`.

## Not yet

- None.
