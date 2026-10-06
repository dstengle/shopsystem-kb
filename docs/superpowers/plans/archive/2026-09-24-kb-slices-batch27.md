# kb slices, batch 27 (slices 128 to 137, 128.1, 133.1): serving, where(), the served double, four publications (kb 0.6.0)

Archived from `docs/superpowers/plans/2026-09-24-kb-slices.md` on 2026-10-06. Implementation plan: `docs/superpowers/plans/2026-10-06-kb-batch27-implementation.md`.

## Slice 128: a store served and reached through its connection
- Kind: capability
- Scenarios: operate-a-store / The operator serves a store at the address they give; operate-a-store / Serving a store without giving an address is refused; reach-a-served-store / A client that reaches a served store makes the same calls and is given the same answers as a client that reaches the store in process; reach-a-served-store / The store never writes the connection to a server; find-the-store / The search stops at a directory holding a store, or at one holding the connection to a server
- Observable: the operator runs kb serve on a store, and a client working where a connection names that server reads through it what an in-process client reads.
- Unknown: whether the one servicer, hosted by a gRPC server, answers a client that chooses the network on each call from the connection its search finds, with nothing else between.
- Needs: a test module binding reach-a-served-store.feature (the every-scenario-is-bound check); a real `kb serve` started in the test's temporary directory on a port of its own (spec Testing); CLAUDE.md module-map rows for any new module.
- Status: green

## Slice 128.1: kb serve serves only where it is asked
- Kind: capability
- Scenarios: operate-a-store / Serving a store at an address it cannot be served at is refused
- Observable: an operator who gives kb serve an address with no port, a port past 65535, or one another server holds, is told so with the address, and nothing is served anywhere.
- Unknown: none
- Needs: none
- Status: green


## Slice 129: a served store refuses changes asked of it directly
- Kind: capability
- Scenarios: reach-a-served-store / A client that finds a served store directly can read it; reach-a-served-store / A change asked by a client that finds a served store directly is refused, naming the server's address; reach-a-served-store / After the server that served a store has stopped, however it stopped, a change from a client that finds the store directly is not refused as served
- Observable: while kb serve runs, a client inside the store reads it but is told a change must go through the server at its address; once the server is gone, even killed, changes land again.
- Unknown: whether a lock of the operating system the server holds is seen by a client in another process and goes with the server's process however it ends, leaving nothing stale.
- Needs: rule `served` added to the published rule names.
- Status: green

## Slice 130: a served store takes changes one at a time
- Kind: capability
- Scenarios: reach-a-served-store / Each change a served store takes is checked against the store as every earlier change left it, in the order the changes arrive
- Observable: two clients sharing a store through a server cannot together leave a link pointing at nothing.
- Unknown: whether the server's concurrent handling of calls keeps each change checked against the state every earlier change left, the order they arrive in deciding which is refused.
- Needs: none
- Status: green

## Slice 131: a connection that leads nowhere is a fault
- Kind: capability
- Scenarios: reach-a-served-store / A connection to a server that cannot be read or names no address is refused, naming the connection; reach-a-served-store / A server the connection names that cannot be reached is refused, naming the address; find-the-store / A call where the directory the search stops at holds both a store and the connection to a server is refused
- Observable: a client whose connection is unreadable, empty, or names a server that is gone is given a named fault promptly, never an exception or a hang.
- Unknown: whether a failed or broken gRPC call can always be turned into a refusal the client is given, within a bounded wait, for every rpc.
- Needs: rules `connection` and `unreachable` added to the published rule names; the published-contract check that kb's rule names are exactly the spec's goes green here, with 129's `served`.
- Status: green

## Slice 132: a server stamps with its own clock
- Kind: capability
- Scenarios: reach-a-served-store / A change made through a server the operator runs with kb serve is stamped with the moment the machine's clock gives; reach-a-served-store / A change asked of a server by a client readied with a clock is refused; reach-a-served-store / A client readied with a clock that finds a server has its reads answered
- Observable: a client that brought its own clock reads through a server but is refused a change, and changes made through kb serve carry the machine's moment.
- Unknown: none
- Needs: none
- Status: green

## Slice 133: a served-store double for clients' tests
- Kind: capability
- Scenarios: serve-a-store-for-tests / every scenario (3)
- Observable: a client's test serves a store it started on a free local port, reaches it through a connection in another directory, pins the moments of its changes, and is left with no server and no connection when it ends, whether it passed or raised.
- Unknown: whether the server kb serve runs can run inside the test's own process, on a port the system picks, with a clock given to it, and still mark the store as served.
- Needs: a test module binding serve-a-store-for-tests.feature; the README's three-line pytest fixture over the double.
- Status: green

## Slice 133.1: the double never overwrites a connection
- Kind: capability
- Scenarios: serve-a-store-for-tests / Serving a store for tests where the directory named already holds a connection is refused
- Observable: a client test that points the double at a directory already holding a connection is refused, and that connection is left as it was.
- Unknown: none
- Needs: none
- Status: green

## Slice 134: the client asks where its store is
- Kind: capability
- Scenarios: find-the-store / The client asks where its store is while the search stops at a directory holding a store; ... while the search stops at a store this kb cannot read; ... while the search stops at a directory holding the connection to a server; ... while the search a call would make finds nothing; ... while the directory the search stops at holds both a store and the connection to a server
- Observable: a client learns the directory, and the server's address, that its calls would reach, or why none would, without making a call.
- Unknown: none
- Needs: none
- Status: green

## Slice 135: find-the-store lines formulated late
- Kind: capability
- Scenarios: find-the-store / The client's working directory has moved into a different store; find-the-store / The client was readied with a root; find-the-store / The client was readied with a root while KB_ROOT names a different store
- Observable: the search is redone on every call, and a root the client was readied with stands in for where it works and overrides KB_ROOT.
- Unknown: none
- Needs: none
- Status: green

## Slice 136: what starting a store publishes
- Kind: capability
- Scenarios: start-a-store / Starting a store naming a piece of work is recorded under that piece of work; start-a-store / Listing the kind of types in a store holding nothing but the type that describes types
- Observable: a store's first entry names the piece of work that started it, and a new store lists `schema/schema` as its one type.
- Unknown: none
- Needs: none
- Status: green

## Slice 137: prose kb cannot write back names its place
- Kind: capability
- Scenarios: hand-over-content / Prose the store could not write back in its one form is refused
- Observable: a client handing over prose with a line ending in a space is told where that prose stands, and `kb.content.dumps` names the same place.
- Unknown: none
- Needs: none
- Status: green

## Log
- 2026-10-06 Suite: 560 passed, 22 failed (6c7abda: the scenarios formulated for batch 27, and the published-contract rule-name check, all red; reach-a-served-store and serve-a-store-for-tests not yet bound to a test module).
- 2026-10-06 Batch 27 cut: slices 128 to 137 from shop-knowledge's requests of 2026-10-06; ordered by unknown (serving, the served lock, one change at a time, wire refusals), then the slices with none. Reading B of a server dying partway through a call (a change landed while its client is told otherwise) is decided by no line (decision/unreachable-is-between-calls).
- 2026-10-06 slice 128 green. Someone can now: run `kb serve <root> --listen <host:port>` on a store and reach it from a client working where `kb/server.yaml` names that address, given what an in-process client is given. Slice 128 green: 575 passed, 29 failed (the 17 not-yet-built batch-27 scenarios and checks of the baseline, and the 12 reach-a-served-store scenarios of slices 129-132, now bound in tests/test_reach_a_served_store.py); the suite's time did not grow (12.6 s against 13.0 s), so a channel per call stays.
- 2026-10-06 slice 129 green. Someone can now: run `kb serve` on a store and know no client inside that store changes it meanwhile (every rpc that writes, and `Snapshot`, refused with `served` naming the server's address, nothing written; reads answered), and that once the server stops, even killed with SIGKILL, changes land again; a second `kb serve` on a served store is refused with `served`, the first serving on. Slice 129 green: 597 passed, 24 failed (the 24 not-yet-built batch-27 scenarios and checks; 17 new tests in tests/test_a_served_store_takes_changes_only_through_its_server.py pin the writing and reading rpcs, the killed server and the second server).
- 2026-10-06 slice 130 green. Someone can now: share a store among clients through one server and know it takes their changes one at a time, in the order they arrive, each checked against the store as every earlier change left it, so a removal arriving while a creation linking to it is being taken is refused (`on_delete`) and never leaves a link pointing at nothing. Slice 130 green: 598 passed, 23 failed (the 23 not-yet-built batch-27 scenarios and checks), 20 runs clean.
- 2026-10-06 Amendment to the batch-27 plan's decision 9: the channel sets a connect timeout, `grpc.min_reconnect_backoff_ms` of 5 s (`network.CONNECTING`); a call still sets no deadline. Without it a plain TCP listener that accepts and never answers held a read for 20 s (grpc's own minimum connect timeout) before `UNAVAILABLE`; with it the read is refused `unreachable` in 5 s (Review Focus 4, pinned by tests/test_reach_a_served_store.py::test_a_connection_naming_a_listener_that_accepts_and_never_answers_is_refused_as_unreachable_soon). A closed port is refused at once either way.
- 2026-10-06 slice 131 green. Someone can now: be told, as a fault and never an exception or a hang, that the connection a client found cannot be read or names no address (`connection`, naming the file), that the server it names cannot be reached, never there or stopped since it answered (`unreachable`, naming the address), or that the directory the search stopped at holds both a store and a connection (`store`, naming the directory). Slice 131 green: 606 passed, 17 failed (the 17 not-yet-built batch-27 scenarios); the published-contract rule-name check is green.
- 2026-10-06 slice 133 green. Someone can now: serve a store their tests started with `kb.testing.served(store_root, connection_dir, *, clock=None)`, kb's own server in the test's own process on 127.0.0.1 at a port the system picks, reach it through the connection the double writes under another directory, pin the moments of the changes made through it with a clock, and be left with no server, no lock on the store and no connection when the block ends, passed or raised. Slice 133 green: 617 passed, 14 failed (the 14 not-yet-built batch-27 scenarios of slices 134 to 137); every scenario is bound.
- 2026-10-06 slice 134 green. Someone can now: ask the client `kb.client.connect` gives `where()` and be given a `kb.client.Where` holding the directory its calls would reach, the server's `host:port` when that directory holds the connection to one, or the faults a call would be refused with for finding nothing, from the search a call would make, opening nothing and calling nothing. Slice 134 green: 625 passed, 6 failed (the 6 not-yet-built batch-27 scenarios of slices 135 to 137); every scenario is bound.
- 2026-10-06 slice 135 green. Someone can now: ready a client with a root inside a store (or inside a directory holding the connection to a server) and have its calls find that store or server by the search a working directory gets, upward from the root, KB_ROOT never consulted; and move the working directory into another store and be answered from it. Slice 135 green: 628 passed, 3 failed (the 3 not-yet-built scenarios of slices 136 and 137); every scenario is bound. The root search changed: `store.locate_from(root)` searches upward from the root through `_found_at`, which client `_found` now calls; `store.given` stays for `kb serve <root>`.
- 2026-10-06 slice 136 green. Someone can now: start a store with `kb.init(root, role, execution=...)` and find the first history entry under that piece of work beside the role, and list the kind `schema` in a fresh store to be given `schema/schema` and nothing else. Slice 136 green: 630 passed, 1 failed (the not-yet-built scenario of slice 137); every scenario is bound. No production code: steps only (`calls.starting` takes `execution`); README states `schema/schema` and the first entry's execution.
- 2026-10-06 slice 137 green. Someone can now: hand over prose with a line ending in a space and be told where it stands in the fault's `place` (`sections/1/body`), and catch `kb.content.NotCanonical` from `kb.content.dumps` with `path` naming the same place. Slice 137 green: 634 passed, 0 failed; every scenario is bound. `canonical.dump` now makes prose of every `body` string by its place before dumping (`_prosed`), so the Prose representer no longer checks; `refusals.unwritable` takes the place and drafting passes `fault.path`; canonical.py is 235 lines, no split needed. A unit test pins `dumps` raising with `sections/0/body` and `options/1/body`.
- 2026-10-06 Slices 128 to 137 green (Suite: 634 passed, aa28534). Batch 27 branch review: with fixes (I1 message size, I2 clocked read unexercised, I3 kb serve address, I4 double overwrites a connection, I5 README/version; M-a to M-e). Slices 128.1 and 133.1 cut for I3 and I4 from lines approved under the person's delegation (7dee014).
- 2026-10-06 slice 128.1 green. Someone can now: give kb serve an address with no port, a port past 65535, or one another server holds, and be refused naming it, exit 2, nothing served and the store's lock let go. `addresses.address` refuses an empty host and a port that is not a number from 0 to 65535 (ValueError), which a connection's `address` now meets as rule `connection`; server.py turns gRPC's failed bind into the same ValueError, and `kb serve` prints `the store cannot be served at '<address>': <why>`.
- 2026-10-06 slice 133.1 green. Someone can now: point `kb.testing.served` at a directory that already holds `kb/server.yaml` and be refused with a `ValueError` naming the directory, before anything is served or the store's lock taken, the connection left byte for byte as it was.
- 2026-10-06 Batch 27 fix wave done (Suite: 646 passed; make bench: every bound held). I1 messages of any size both ways (a 5 MB Read and History through the double); I2 the clocked read made with the clock; M-a a connection's address read strictly (rule `connection`); M-b the import check passes over `served.yaml`; M-c `kb.client.Where` pinned; M-e two vacuous Thens pinned; the connect timeout kept on `grpc.min_reconnect_backoff_ms`, its comment saying grpc core reads it as the minimum connect timeout (`channel_ready_future` waited out its 5 s at a closed port, the serving tests 15 s to 38 s); I5 kb 0.6.0 and its README.
