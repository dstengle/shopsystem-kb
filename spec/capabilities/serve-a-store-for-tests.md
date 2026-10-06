---
id: capability/serve-a-store-for-tests
title: Serve a store for tests
narrator: the client
rests_on: [decision/served-double-is-kb-serve, decision/a-server-stamps-with-its-own-clock, decision/published-contract-v1-in-0-6-0, decision/runtime-shape]
formulated_as: features/serve-a-store-for-tests.feature
---

# Serve a store for tests

## Purpose

The client's own tests serve a store they started with kb's own server, so the client can test how it reaches a served store without running `kb serve`. This capability is not what a client sees once it reaches a server (reach-a-served-store) or the operator's `kb serve` (operate-a-store).

## Behaviour

- When the client serves a started store for its tests, naming another directory to hold the connection, it is given the address the store is served at, and a client working in that directory reaches the store through a server at that address.
- When the client's tests are done with a store they served, however they ended, the server is stopped and the directory named for the connection no longer holds it.
- If the client serves a store for its tests naming a directory that already holds the connection to a server, serving is refused because that directory already holds a connection, and that connection is left as it was.
- Where the client serves a store for its tests with a clock, each change made through that server is stamped in the history with the moment the clock gives.

## Implementation, may change

- `kb.testing.served(store_root, connection_dir, *, clock=None)` is a published context manager. It serves the store at `store_root` on `127.0.0.1` at a free port, in the test's own process, writes `kb/server.yaml` under `connection_dir` naming that address, and yields the address; on exit it stops the server and removes the connection. With no clock, the server stamps with the machine's.
- It is the server `kb serve` runs, not an imitation.
- kb publishes no pytest fixture or plugin. A fixture over the context manager is the client's (three lines), and the README shows one.

## Not yet

- None.
