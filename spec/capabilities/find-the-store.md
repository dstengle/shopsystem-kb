---
id: capability/find-the-store
title: Find the store
narrator: the client
rests_on: [decision/0003-init-refuses-inside-a-store, decision/0020-a-server-found-where-the-store-is, decision/0007-input-safety-at-the-boundary, decision/where-is-the-clients-search]
formulated_as: features/find-the-store.feature
---

# Find the store

## Purpose

Every call except starting a store finds its store on each call, the way git finds a repository: upward from where the client works, or where `KB_ROOT` names. What it finds also decides whether the store is reached in process or through a server. The client can also ask where the search stops without making a call. Nothing is guessed: two answers, or none, are refusals the client is given as faults. This capability is not what a server does once it is reached (reach-a-served-store).

## Behaviour

- While the client works in a folder deep inside the directory a store sits in, when it calls, the call is answered from the store found above where it is working.
- While the client works outside any store and `KB_ROOT` names a store, when it calls, the call is answered from the store `KB_ROOT` names.
- If the client works outside any store and nothing names one, the call is refused because no store was found, neither above where it is working nor named outright.
- If `KB_ROOT` names a directory that holds no store, the call is refused because `KB_ROOT` names a directory that holds no store, and no content comes back.
- If the client works inside one store while `KB_ROOT` names a different store, the call is refused because `KB_ROOT` names a store other than the one it is working in, neither is guessed at, and no content comes back from either.
- While the client's working directory has been removed and `KB_ROOT` names a store, when it calls, the call is answered from the store `KB_ROOT` names, whether the removed directory was outside any store or inside a different one.
- If the client's working directory has been removed and nothing names a store, the call is refused because the directory it is working in is gone, whether or not a store once sat above it, and no content comes back.
- If the client's working directory has gone and nothing names a store, the client is given that refusal as it is given any other fault, the call never breaking off.
- When a client readied where there was no store calls after a store has been started where it is working, the call is answered from that store without the client being readied again.
- If `KB_ROOT` is set to nothing, names a directory that does not exist, or names a file, the call is refused because `KB_ROOT` names no store, naming `KB_ROOT`, where the client is working is not fallen back on, and no content comes back.
- When the search stops at a directory holding a store, the call is answered by that store in process; when it stops at a directory holding the connection to a server, the call is answered by that server over the network.
- If the directory the search stops at holds both a store and the connection to a server, the call is refused, naming that directory.
- When the client's working directory has moved into a different store, its next call is answered from the store it now sits in.
- Where the client was readied with a root, the store is looked for from that root the way it is looked for from the working directory.
- Where the client was readied with a root, `KB_ROOT` is not consulted.
- While the search a call would make stops at a directory holding a store, when the client asks where its store is, it is given that directory and no fault.
- While the search a call would make stops at a store this kb cannot read, when the client asks where its store is, it is given that directory and no fault.
- While the search a call would make stops at a directory holding the connection to a server, when the client asks where its store is, it is given that directory and the address the connection names, and the server is not called.
- If the search a call would make finds nothing when the client asks where its store is, the client is given the faults that say why nothing was found, and no directory.
- If the directory the search stops at holds both a store and the connection to a server, when the client asks where its store is, it is given a fault naming that directory, and no directory.

## Implementation, may change

- A directory holds a knowledge base when it holds `kb/store.yaml` (the store) or `kb/server.yaml` (the connection to a server); the search looks for both in the same place.
- The client is `kb.client.connect`; it is constructed without finding a store, and discovery runs on each call.
- The client publishes `where()`, the client's own search: no rpc is added for it and it calls no server. It returns a value holding `root` (the directory the search stopped at), `address` (empty unless a connection was found) and `faults`; `root` and `faults` are never both filled.
- The operator's commands find the store the same way (operate-a-store, export-and-import-a-store).

## Not yet

- A `KB_SERVER` variable naming a server for callers; the connection stays `kb/server.yaml`. Promoted when a caller cannot mount `kb/server.yaml` where its `KB_ROOT` names.
