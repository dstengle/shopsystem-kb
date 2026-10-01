---
id: capability/reach-a-served-store
title: Reach a served store
narrator: the client
rests_on: [decision/0020-a-server-found-where-the-store-is, decision/0018-the-published-contract, decision/runtime-shape, decision/write-lock-on-one-machine]
formulated_as: features/reach-a-served-store.feature
---

# Reach a served store

## Purpose

Several clients share one store through a server that hosts the same contract over the network. A client reaches it through a connection that sits where the store would be found. While a store is served, the server owns it: it takes changes one at a time and stamps them with its own clock. This capability is not starting the server (operate-a-store) or the search that finds the connection (find-the-store).

## Behaviour

- While a server serves a store, a client that reaches it makes the same calls and is given the same answers as a client that reaches the store in process.
- If the connection to a server cannot be read or names no address, the call is refused, naming the connection.
- If the server a connection names cannot be reached, or stops answering, the call is refused with a fault naming the address, never breaking off.
- While a server serves a store, each change is checked against the store as every earlier change left it, in the order the changes arrive.
- While a server serves a store, a client that finds that store directly can read it.
- If a client that finds a served store directly asks for a change, the change is refused because the store is served, naming the server's address.
- If the client starts a store through a server, starting is refused because a server serves the store it was started over.
- While a client reaches a server, each change it makes is stamped in the history with the server's clock.
- If a client readied with a clock finds a server and asks for a change, the change is refused because the clock belongs to a client that reaches its store in process.
- The store never writes the connection to a server.
- While a client readied with a clock finds a server, its reads are answered.

## Implementation, may change

- The connection is `kb/server.yaml`, written by whoever arranges the callers and read as YAML 1.2, the way kb reads content. It holds one entry, `address`, the server's `host:port` as a caller can reach it (in a set of containers, the server's name on their shared network). The file's form is part of the published contract.
- The network transport is `grpc.server` hosting the same servicer, called over a gRPC channel with the same method names, requests and responses; `connect` chooses the transport on each call.
- Reads run alongside a change being written.
- Across containers a server is the only way to share a store, since SQLite over a network filesystem is not safe.

## Not yet

- Authentication and encryption. Promoted when a caller outside the operator's own network needs to reach a server.
