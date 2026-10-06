---
id: capability/reach-a-served-store
title: Reach a served store
narrator: the client
rests_on: [decision/0020-a-server-found-where-the-store-is, decision/published-contract-v1-in-0-6-0, decision/runtime-shape, decision/write-lock-and-expected-revision, decision/contract-v1, decision/starting-leaves-the-wire, decision/serving-built, decision/served-store-marked-by-a-lock, decision/served-store-rules, decision/a-server-stamps-with-its-own-clock]
formulated_as: features/reach-a-served-store.feature
---

# Reach a served store

## Purpose

Several clients share one store through a server that hosts the same contract over the network. A client reaches it through a connection that sits where the store would be found. While a store is served, the server owns it: it takes changes one at a time and stamps them with its own clock. A served store is never started through its server. This capability is not starting the server (operate-a-store), serving a store for a client's own tests (serve-a-store-for-tests), or the search that finds the connection (find-the-store).

## Behaviour

- While a server serves a store, a client that reaches it makes the same calls and is given the same answers as a client that reaches the store in process.
- If the connection to a server cannot be read or names no address, the call is refused because the connection cannot be read or names no address, naming the connection.
- If the server a connection names cannot be reached, whether no server was ever there or one that answered earlier calls has since stopped, the call is refused because the server cannot be reached, naming the address, and the call comes back with its answer rather than breaking off.
- While a server serves a store, each change is checked against the store as every earlier change left it, in the order the changes arrive.
- While a server serves a store, a client that finds that store directly can read it.
- If a client that finds a served store directly asks for a change, the change is refused because the store is served, naming the server's address.
- When the server that served a store has stopped, however it stopped, a change asked by a client that finds the store directly is not refused because the store is served.
- While a client reaches a server the operator runs with kb serve, each change it makes is stamped in the history with the moment the machine's clock gives.
- If a client readied with a clock finds a server and asks for a change, the change is refused because the clock belongs to a client that reaches its store in process.
- The store never writes the connection to a server.
- While a client readied with a clock finds a server, its reads are answered.

## Implementation, may change

- The connection is `kb/server.yaml`, written by whoever arranges the callers and read as YAML 1.2, the way kb reads content. It holds one entry, `address`, the server's `host:port` as a caller can reach it (in a set of containers, the server's name on their shared network). The file's form is part of the published contract.
- The network transport is `grpc.server` hosting the same servicer an in-process client reaches, called over a gRPC channel with the same method names, requests and responses; when the search stops at `kb/server.yaml`, `connect` calls the address it names. `connect` chooses the transport on each call.
- While it serves, the server holds a lock of the operating system on a file of the store's own, inside `kb/`, which says the address it serves at. The lock goes when the server's process does.
- The refusals carry kb's own rules: a connection that cannot be read or names no address, `connection`; a server that cannot be reached or stops answering, `unreachable`; a change asked of a served store by a client that found it directly, `served`; a change asked of a server by a client readied with a clock, `clock`.
- The contract's package is `kb.v1`, so a client of one version calling a server of another is refused by the transport rather than answered wrongly.
- There is no `Init` rpc; a store is started by `kb init` or `kb.init` (start-a-store).
- Reads run alongside a change being written.
- Across containers a server is the only way to share a store, since SQLite over a network filesystem is not safe.

## Not yet

- Authentication and encryption. Promoted when a caller outside the operator's own network needs to reach a server.
