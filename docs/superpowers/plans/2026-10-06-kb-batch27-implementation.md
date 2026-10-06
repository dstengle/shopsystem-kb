# kb batch 27 Implementation Plan: serving, where(), the served double, and four publications (kb 0.6.0)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Each task is one slice, implemented under shopsystem-bdd:bdd-red-green. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** the operator's `kb serve` hosts a store over gRPC and a client reaches it through the connection its search finds (128), the server owning the store while it runs (129), taking changes one at a time (130), every way of not reaching it a named fault (131), with its own clock (132); a published double serves a store inside a client's tests (133); the client can ask where its store is (134); find-the-store's late-formulated lines are bound (135); what starting a store publishes is pinned (136); prose kb cannot write back names its place (137). Shipped as kb 0.6.0, contract v1 unchanged in what it already holds.

**Architecture:** the servicer stays the one adapter; nothing in the domain changes for serving. A new module hosts it under `grpc.server` for a root and an address, holding while it runs an OS lock on a file of the store's own inside `kb/` that says the address. Discovery (store.py) learns the connection file beside the marker and the "served" lock. The client chooses its transport on each call from what discovery found: the servicer in process, or a gRPC stub over a channel to the connection's address, through a new transport module that turns every gRPC failure into the rpc's own refusal. A published `kb.testing` module runs the same server in the test's process. `where()` is the client's discovery returned as a value.

**Tech Stack:** Python 3.11, grpcio 1.84 (`grpc.server`, `grpc.insecure_channel`, the generated `kb_pb2_grpc.KbStub`/`add_KbServicer_to_server`), `fcntl.flock`, pytest-bdd 8.1, pytest-xdist.

**Spec:** `spec/capabilities/reach-a-served-store.md`, `serve-a-store-for-tests.md`, `operate-a-store.md`, `find-the-store.md`, `start-a-store.md`, `hand-over-content.md`; `spec/index.md`; `spec/decisions.md` decision/serving-built, decision/served-store-marked-by-a-lock, decision/served-store-rules, decision/a-server-stamps-with-its-own-clock, decision/where-is-the-clients-search, decision/init-carries-a-piece-of-work, decision/type-of-types-id-published, decision/not-canonical-names-its-place, decision/served-double-is-kb-serve, decision/published-contract-v1-in-0-6-0, decision/unreachable-is-between-calls; note `docs/superpowers/specs/2026-10-06-kb-shop-knowledge-requests-design.md`. Slices: `docs/superpowers/plans/2026-09-24-kb-slices.md`, slices 128 to 137.

## Global Constraints

- One task per slice, in slice order. The plan holds no code: the implementer writes steps and code under bdd-red-green, after the red run.
- The controller dispatches each task by its `Review:` and `Model:` lines: `Review: per-task` and `Model: opus` for a task touching concurrency, the published contract, data integrity or moving stored data (128, 129, 130, 131, 133, 134); `Review: batch-end` and `Model: sonnet` for the rest (132, 135, 136, 137). A batch-end task gets no task review; the batch's branch review covers it.
- CLAUDE.md holds: no module under `src/kb/` over 250 lines, `servicer.py` under 150 (126 today); a change that would cross a limit splits first, inside the task. `values.py` is at 241 and must not grow: nothing in this batch puts a conversion there (a listen address and a connection are read in the modules that own them, below). `canonical.py` is at 220: slice 137 splits it first if it would cross 250. A new module gets its row in CLAUDE.md's module map in the same task. (CLAUDE.md has `fault_order.py` twice; the first task that edits the map removes the duplicate.)
- Rule 1: the server, the network transport and the double catch no broad exception except where the rule already allows (the servicer's one boundary). A gRPC failure is caught as `grpc.RpcError` alone, in the transport, and becomes the rpc's refusal; that is a conversion of a transport outcome, not a broad catch.
- Rule 2: a connection's `address` and the operator's `--listen` are read once, where they are owned, into a value; nothing passes the raw string further.
- Every test reaches only stores and servers inside its own temporary directory, on ports the system picks (`:0`) or that the test itself bound; no test calls an address it did not start (spec Testing). Servers a test starts are stopped when it ends, passed or failed.
- Verification in every task: `.venv/bin/python -m pytest -q -m slice-N` during red-green; `make test` once before the slice's last commit.
- Baseline at d79fa9e: `make test` gives **560 passed, 22 failed**: 21 batch-27 scenarios in bound modules (find-the-store 10 in `tests/test_read_an_artifact.py`, operate-a-store 2 in `tests/test_look_after_a_store.py` (3 collected), start-a-store 2, hand-over-content 1 in `tests/test_create_an_artifact.py`), `tests/test_every_scenario_is_bound.py` (reach-a-served-store and serve-a-store-for-tests have no test module), and `tests/test_the_published_contract.py::test_the_rule_names_kb_gives_are_exactly_the_spec_lists` (`connection`, `unreachable`, `served` are in spec/index.md, not in `rules.ALL`).

### Binding values, verbatim from the spec

- New published rules (spec/index.md, decision/served-store-rules): `connection`, `unreachable`, `served`; `clock` is kept for a change asked of a server by a client readied with a clock.
- The connection (reach-a-served-store, Implementation): "The connection is `kb/server.yaml`, written by whoever arranges the callers and read as YAML 1.2, the way kb reads content. It holds one entry, `address`, the server's `host:port` as a caller can reach it."
- The lock (decision/served-store-marked-by-a-lock): "While it serves, the server holds a lock of the operating system on a file of the store's own inside `kb/` that says the address it serves at ... the lock goes when the server's process does."
- The commands (operate-a-store, Implementation): "`kb serve <root> --listen <host:port>` ... hosts the store at `<root>/kb/` with `grpc.server`, the same servicer an in-process client reaches, and stamps each change with the server's own clock, the machine's."
- The double (serve-a-store-for-tests, Implementation): "`kb.testing.served(store_root, connection_dir, *, clock=None)` is a published context manager. It serves the store at `store_root` on `127.0.0.1` at a free port, in the test's own process, writes `kb/server.yaml` under `connection_dir` naming that address, and yields the address; on exit it stops the server and removes the connection. With no clock, the server stamps with the machine's."
- `where()` (find-the-store, Implementation): "It returns a value holding `root` (the directory the search stopped at), `address` (empty unless a connection was found) and `faults`; `root` and `faults` are never both filled."
- `NotCanonical.path` (hand-over-content, Implementation): "the place the refusal names, written as the names and list positions from the top of the content joined by `/` (`sections/0/body`), and empty when the refusal names no place."

## Decisions this plan takes (the Behaviour leaves them open)

1. **Which calls a served store refuses directly**: every rpc that writes, the eight changes and `Snapshot` (it lands a history entry; keep-the-history counts it among the changes a clock stamps). Every read is answered. The operator's commands run directly against a served store (validate, export, import) are not decided by any line: they behave as today (backlog line). Rests on "If a client that finds a served store directly asks for a change, the change is refused because the store is served".
2. **Where the served refusal is made**: in the servicer's boundary, for the writing rpcs, when the servicer was not made by the server itself. A servicer the server hosts is told it serves; every other servicer (the in-process client's) asks discovery whether the store is served before the domain call, and refuses with `served`, naming the address the lock file says, writing nothing. Rests on rule 1 (one wrapper) and decision/served-store-marked-by-a-lock.
3. **The lock**: `fcntl.flock` on a file inside `<root>/kb/` (its name is the store's own; e.g. `served.yaml`), exclusive and non-blocking, taken by the server before it starts answering and held for its life; the file's content is canonical YAML naming the address. A direct client tells it is served by failing to take a shared non-blocking lock on that file; a file present but unlocked means not served (a stopped or killed server leaves the file, never the lock). A file that is absent means not served. flock conflicts between open file descriptions in one process too, which slice 133's double relies on. Rests on decision/served-store-marked-by-a-lock.
4. **A second server on a served store**: refused before it listens, because the lock cannot be taken; `kb serve` exits 2 naming the address the store is served at, rule `served`. Rests on "owns the store it serves" (decision/0020). It is pinned by a test, not a scenario (Review Focus 3).
5. **`kb serve` without `--listen`**: the command prints to stderr that no address is assumed and exits 2, nothing served. It is a command-line refusal, carrying no fault rule (no rule is listed for it). Rests on "If the operator runs kb serve without an address, it is refused because no address is assumed."
6. **`kb serve` on a root holding no store**, or an earlier or later kb's, or one whose database cannot be read: refused as every command is, by the fault discovery or opening gives, exit 2, before it listens. The root is given outright (store.given), never searched upward. No line names this; it follows the operator's other commands (Review Focus 2).
7. **`kb serve`'s lifecycle**: binds, takes the lock, prints one line to stdout naming the address it serves at (the port the system gave when `:0` was asked), then serves until SIGINT or SIGTERM, stopping with no grace for calls in flight beyond grpc's `stop(grace)` of a few seconds, releasing the lock, exiting 0. The printed line lets tests ask for `:0` and learn the port; its wording is not published.
8. **The server's concurrency**: `grpc.server` with a thread pool; reads run concurrently; changes are taken one at a time by a lock the server holds around the writing rpcs, in the order they arrive at it, so "each change is checked against the store as every earlier change left it" holds by construction as well as by SQLite's write lock. Rests on decision/0020's "takes changes one at a time" and reach-a-served-store's ordering line.
9. **The network transport** is a new module: given the address a connection names, it makes an insecure channel and a `KbStub`, calls the rpc with the same request, and returns its response; any `grpc.RpcError` becomes the rpc's own response holding one refusal, rule `unreachable`, message naming the address. A channel is made per call (discovery runs per call; a channel cache keyed by address is allowed if the per-call cost shows in the suite, never across a changed connection). No call waits for a server to become ready (`wait_for_ready` off), so a closed port fails at once. A deadline is not set (no line bounds a slow server; Review Focus 4).
10. **Reading the connection**: `kb/server.yaml` read as canonical YAML 1.2 (canonical.load); it must be a mapping whose `address` is non-empty text of the form `host:port` with a port that is a number. Anything else (bytes that are not text, not canonical, not a mapping, no `address`, empty, no port, unreadable file) is one fault, rule `connection`, naming the connection file's path. Owned by store.py (what marks a store, and now what marks a connection), which hands the transport a value, never the raw string (rule 2).
11. **Discovery** finds a knowledge base where `kb/store.yaml` or `kb/server.yaml` is a file, upward or by `KB_ROOT` or from the root the client was given, exactly as it finds a store today; both in one directory is one fault, rule `store`, naming that directory. `KB_ROOT` naming a directory holding only a connection reaches that server. What it returns says which was found. The operator's export, import check and import, which find a store, refuse a connection with rule `store` ("these commands run where the store is, not through a server") since they are not rpcs (no line; Review Focus 5). `kb validate` is an rpc (`Check`) and goes through the server.
12. **The clock refusal**: a client readied with a clock that finds a connection refuses each writing rpc (decision 1's set) itself, without calling the server, rule `clock`, message saying the clock belongs to a client that reaches its store in process. Its reads are called on the server. Rests on reach-a-served-store's two clock lines.
13. **The server's clock**: the servicer the server hosts is made with the server's clock: none (the machine's) under `kb serve`, the given one under `kb.testing.served`. Rests on decision/a-server-stamps-with-its-own-clock.
14. **`where()`** is a method of the client `connect` gives, runs the same discovery a call would, opens nothing and calls nothing, and returns a published value `kb.client.Where` with `root` (text, the directory the search stopped at, as discovery holds it), `address` (text, empty unless a connection was found) and `faults` (a list of contract Faults). A connection that cannot be read gives the `connection` fault and no root, as a call would. Rests on decision/where-is-the-clients-search.
15. **The double**: `kb/testing.py`, published, a context manager. It refuses (raising `ValueError` naming why) a `store_root` that holds no started store and a `connection_dir` that would hold both a store and a connection, before serving (no line asks for a refusal; failing loudly in a test is the least surprise, and it never writes). It makes `connection_dir/kb/` if missing, writes `server.yaml` canonically, and on exit, however the block ended, stops the server, releases the lock and removes `server.yaml`, and `kb/` too if it made it and it is empty. It yields the address as text `127.0.0.1:<port>`.
16. **Prose's place**: the place of prose kb cannot write back is the place of the `body` (or other prose value) as the content names it: names and list positions from the top, joined by `/`, e.g. `sections/0/body`, `options/1/body`. `kb.content.dumps` raises `NotCanonical` with that `path`; the store's refusal of a change carries it as the fault's `place`, the message unchanged. Rests on decision/not-canonical-names-its-place.

## Questions for the spec

None open. A server stopping partway through a call (a change landed while its client is told it was refused) is decided by no line (decision/unreachable-is-between-calls); it goes to the backlog at batch end, not into a task.

## Review Focus

1. **A killed server leaves the store writable, and a live one never does.** `kill -9` of `kb serve`, then a direct `Replace`, lands; while it runs, every writing rpc (all eight changes and `Snapshot`) from a direct client is refused with `served` and nothing written. Owner: Task 2. Test intent: one test table over the writing rpcs against a live server's store (the boundary table pattern of `tests/test_the_boundary.py`), each refused with `served` and the store's history unchanged; reads in the same table answered.
2. **`kb serve` on what is not a store.** A root holding no store, an earlier kb's store, a later kb's, a damaged database: exit 2 with the fault discovery or opening gives, nothing listening, no lock file made. Owner: Task 1. Test intent: `kb serve` in process on each, exit 2 and the rule (`store`, `unreadable`), and the address not answering.
3. **Two servers, one store.** A second `kb serve` on a served store exits 2 with `served`, naming the first's address; the first keeps answering. Owner: Task 2. Test intent: start one server, run a second on the same root, assert both.
4. **A connection naming something that is not a kb server, or a port that accepts and never answers.** A port where nothing listens is `unreachable` at once; a plain TCP listener that accepts and says nothing must not hang the suite. Owner: Task 4. Test intent: a test binding a raw socket that accepts and never writes, a connection naming it, a read refused with `unreachable` within a few seconds (if grpc waits forever on such a peer, the transport sets a connect timeout on the channel, not a call deadline, and the plan's decision 9 is amended in the log).
5. **The operator's file commands and a connection.** `kb export`, `kb import --check`, `kb import` where the search finds a connection: refused with `store`, nothing written (decision 11). Owner: Task 1. Test intent: each command in process in a directory holding only a connection, exit 2 with rule `store`.

---

### Task 1: Slice 128 — a store served and reached through its connection

Review: per-task
Model: opus

- [ ] **Scenarios** (`@slice-128`, 5 scenarios, 7 collected once bound): operate-a-store / The operator serves a store at the address they give (2 examples); operate-a-store / Serving a store without giving an address is refused; reach-a-served-store / A client that reaches a served store makes the same calls and is given the same answers as a client that reaches the store in process; reach-a-served-store / The store never writes the connection to a server; find-the-store / The search stops at a directory holding a store, or at one holding the connection to a server (2 examples).

- [ ] **Why each is red today** (run `.venv/bin/python -m pytest -q -m slice-128`: 5 collected, 5 failed, `StepDefinitionNotFoundError`; reach-a-served-store is bound by no module, so its two are not collected). There is no `serve` subcommand (`cli.main`'s parser has init, validate, export, import), no module hosts `KbServicer` under `grpc.server` (servicer.py's docstring says "grpc.server can host it later"), `store.locate`/`store.given`/`store.find_above` look only for `kb/store.yaml`, and `InProcessClient._servicer` only ever makes an in-process servicer.

- [ ] **Where the change lands.** A new module for the server (decisions 3, 7, 8, 13): hosts the servicer for a root and a listen address, binds, takes the lock (the lock itself is slice 129's; here the server only needs to bind, serve and stop), serves, stops. `cli.py` gains `serve <root> --listen <host:port>` (decisions 5, 6, 7), one call into that module. store.py learns the connection (decisions 10, 11): discovery returns which of a store or a connection it found, and reads a connection into a value. A new transport module (decision 9) calls a found connection's address through `KbStub`. client.py chooses per call (rename `InProcessClient` if its name now misleads; it is not published, `connect` is). New rules and their faults wait for slices 129 and 131; a connection that cannot be read may raise here, since no scenario of this slice reads one. CLAUDE.md rows for both new modules, and for store.py's and client.py's widened ownership; servicer.py's docstring loses "later".

- [ ] **Steps to reuse.** `the client is working in a folder deep inside the directory the store sits in` and `the client reads the decision` (tests/test_read_an_artifact.py); the Background's store builders in tests/calls.py (`start_a_store`, `define`, `create`, `DECISION_TYPE`); `held.in_process` to run `kb serve`'s argument handling for the no-address refusal. A real served store for the scenarios: a test helper that starts `kb serve` as a subprocess (the installed `.venv/bin/kb`, or `sys.executable` with the cli module) on `127.0.0.1:0`, reads the printed address, writes the connection where the scenario says, and kills the server at teardown (fixture finaliser, so a failed test stops it too). Bind reach-a-served-store.feature in a new `tests/test_reach_a_served_store.py` (scenarios of later slices fail there until their slice; that is expected).

- [ ] **Decisions applied.** 5, 6, 7, 9, 10 (reading only a well-formed connection), 11, 13. The "every interface" example: listen on `0.0.0.0:<port>` and reach it through `127.0.0.2:<port>`; the "one interface" example listens on `127.0.0.1` and is reached there (on Linux every `127.x` is loopback, and only an all-interfaces listener answers `127.0.0.2`). "The same answers": compare the served `Read` response with an in-process `Read` of the same store, field for field (the messages are equal). "Never writes the connection": after a change through the server, the store's root holds no `kb/server.yaml` and the connection file's bytes are unchanged.

- [ ] **Verify.** `.venv/bin/python -m pytest --collect-only -q -m slice-128` → 7 tests; `-m slice-128` all pass; Review Focus 2 and 5 tests pass; `make test` before the last commit: `test_every_scenario_is_bound` passes once the module exists.

- [ ] **Checkpoint.** Log in the slices plan: `Slice 128 green: <suite line>`; note the per-call channel cost if the suite's time grew noticeably.

### Task 2: Slice 129 — a served store refuses changes asked of it directly

Review: per-task
Model: opus

- [ ] **Scenarios** (`@slice-129`, 3 scenarios, 4 collected): reach-a-served-store / A client that finds a served store directly can read it; ... / A change asked by a client that finds a served store directly is refused, naming the server's address; ... / After the server that served a store has stopped, however it stopped, a change from a client that finds the store directly is not refused as served (2 examples: stopped by the operator, killed without warning).

- [ ] **Why each is red today.** After Task 1 nothing marks a store as served: a direct client's `Replace` lands while the server runs. The read and the after-stop scenarios fail only on missing steps until then; the after-stop ones guard against the lock being stale.

- [ ] **Where the change lands.** The server takes the lock before it listens and holds it for life (decision 3); store.py answers whether a store is served and at what address (what marks a store); the servicer's boundary, for the writing rpcs, refuses with `served` when its servicer is not the server's (decisions 1, 2). rules.py gains `served`; refusals.py makes its fault from the address (plain values). The second-server refusal (decision 4).

- [ ] **Steps to reuse.** Task 1's served-store helper; `the client is working in the directory the store sits in` (new in reach-a-served-store; write it once); `the client replaces the decision, saying which role and why` if a step of that wording exists in tests/test_change_an_artifact.py, else write it in the new module; killing without warning is `SIGKILL` to the subprocess; stopping by the operator is `SIGTERM` (or `SIGINT`) and waiting for exit.

- [ ] **Decisions applied.** 1, 2, 3, 4.

- [ ] **Verify.** `--collect-only -q -m slice-129` → 4; `-m slice-129` passes; Review Focus 1 and 3 tests pass; `make test`.

- [ ] **Checkpoint.** `Slice 129 green: <suite line>`.

### Task 3: Slice 130 — a served store takes changes one at a time

Review: per-task
Model: opus

- [ ] **Scenarios** (`@slice-130`, 1): reach-a-served-store / Each change a served store takes is checked against the store as every earlier change left it, in the order the changes arrive.

- [ ] **Why it is red today.** Missing steps; with Task 1's server the removal arriving after the creation would already be refused by the store's link check. The slice's work is to make arrival order the order changes are checked in, under the server's thread pool (decision 8), and to pin it: the step holds the creation inside the server (a seam the test controls in the server module, or a slow clock given to the double's server, not a sleep) while the removal arrives, so the removal is checked after the creation lands.

- [ ] **Where the change lands.** The server module's lock around the writing rpcs (decision 8). No domain change.

- [ ] **Steps to reuse.** `a store also holds a tag nothing points at` / creating a decision that points at a tag: tests/test_remove_an_artifact.py and tests/test_many_writers_at_once.py hold the nearest wordings and the two-writers pattern; `something still points at it` refusal step from remove-an-artifact.

- [ ] **Decisions applied.** 8.

- [ ] **Verify.** `-m slice-130` → 1 collected, passes, and passes 20 times in a row (`--count` is not installed; loop the command) with no flake; `make test`.

- [ ] **Checkpoint.** `Slice 130 green: <suite line>, 20 runs clean`.

### Task 4: Slice 131 — a connection that leads nowhere is a fault

Review: per-task
Model: opus

- [ ] **Scenarios** (`@slice-131`, 3 scenarios, 5 collected): reach-a-served-store / A connection to a server that cannot be read or names no address is refused, naming the connection (2); ... / A server the connection names that cannot be reached is refused, naming the address (2: never there; answered a read and has stopped); find-the-store / A call where the directory the search stops at holds both a store and the connection to a server is refused.

- [ ] **Why each is red today.** After Task 1 a connection that cannot be read raises out of the client (or is not read at all), a closed port raises `grpc.RpcError` to the caller, and a directory holding both is found as whichever discovery checks first.

- [ ] **Where the change lands.** rules.py gains `connection` and `unreachable`; refusals.py their faults (connection path, address); store.py's reading of the connection refuses with `connection` (decision 10) and discovery refuses both with `store` (decision 11); the transport turns `grpc.RpcError` into the rpc's refusal with `unreachable` (decision 9). The published-contract rule-name check goes green here.

- [ ] **Steps to reuse.** Task 1's helper (start, read, kill); for "never there", a port the test binds and closes; "the read is rejected ..., naming that directory" against existing find-the-store refusal steps in tests/test_read_an_artifact.py.

- [ ] **Decisions applied.** 9, 10, 11.

- [ ] **Verify.** `-m slice-131` → 5 collected, pass; `tests/test_the_published_contract.py` passes; Review Focus 4 test passes; `make test`.

- [ ] **Checkpoint.** `Slice 131 green: <suite line>`.

### Task 5: Slice 132 — a server stamps with its own clock

Review: batch-end
Model: sonnet

- [ ] **Scenarios** (`@slice-132`, 3): reach-a-served-store / A change made through a server the operator runs with kb serve is stamped with the moment the machine's clock gives; ... / A change asked of a server by a client readied with a clock is refused; ... / A client readied with a clock that finds a server has its reads answered.

- [ ] **Why each is red today.** After Task 1 a client readied with a clock that finds a connection calls the server, which stamps with the machine's clock: the change lands rather than being refused. The machine's-clock and reads scenarios fail on missing steps.

- [ ] **Where the change lands.** The client's per-call choice (decision 12): with a clock and a connection, the writing rpcs are refused with `clock` there, without a call; refusals.py's fault. The machine's-clock scenario asserts the entry's moment lies between a reading of the machine's clock taken before the call and one after.

- [ ] **Steps to reuse.** `the client was readied with a clock that reads 2026-09-23 at 14:30` and `every entry that change left in the journal says it happened at ...` (tests/test_read_the_journal.py, tests/calls.py `moment`).

- [ ] **Decisions applied.** 1 (the writing set), 12, 13.

- [ ] **Verify.** `-m slice-132` → 3, pass; `make test`.

- [ ] **Checkpoint.** `Slice 132 green: <suite line>`.

### Task 6: Slice 133 — a served-store double for clients' tests

Review: per-task
Model: opus

- [ ] **Scenarios** (`@slice-133`, 3 scenarios, 4 collected): serve-a-store-for-tests / The client serves a started store for its tests, naming another directory to hold the connection; ... / The client's tests are done with a store they served, however they ended (2: passed; broken off with an error); ... / The client serves a store for its tests with a clock.

- [ ] **Why each is red today.** No `kb.testing` module; serve-a-store-for-tests.feature is bound by no test module.

- [ ] **Where the change lands.** A new published module `kb/testing.py` (decision 15) over the server module of Task 1, run in a thread of the test's own process on `127.0.0.1:0`, with the clock (decision 13), holding the lock (decision 3). The server module exposes what the double needs (start for a root, an address and a clock; the bound address; stop) without duplicating `kb serve`'s path. A new `tests/test_serve_a_store_for_tests.py`. README: the published surface of 0.6.0's double and a three-line pytest fixture over it (decision/served-double-is-kb-serve).

- [ ] **Steps to reuse.** `a store the client started, holding a decision`; `with a clock that reads 2026-09-23 at 14:30`; `every entry that change left in the journal says it happened at ...` (keep-the-history steps); Task 1's reads through a connection. "Broken off with an error": the step runs the context manager around a block that raises, catches it in the step, then asserts. "No longer answers": a read through the yielded address is refused with `unreachable`.

- [ ] **Decisions applied.** 3, 13, 15.

- [ ] **Verify.** `-m slice-133` → 4, pass; `make test` under `-n auto` (several doubles at once on system-picked ports); `python -c "import kb.testing"` from a fresh venv install of the built wheel is not required here (release step).

- [ ] **Checkpoint.** `Slice 133 green: <suite line>`.

### Task 7: Slice 134 — the client asks where its store is

Review: per-task
Model: opus

- [ ] **Scenarios** (`@slice-134`, 5 scenarios, 8 collected): find-the-store / The client asks where its store is while the search stops at a directory holding a store; ... at a store this kb cannot read (2); ... at a directory holding the connection to a server; ... while the search a call would make finds nothing (3); ... while the directory the search stops at holds both a store and the connection to a server.

- [ ] **Why each is red today.** The client has no `where()`; the steps are missing.

- [ ] **Where the change lands.** client.py (decision 14): `where()` and the `Where` value, over store.py's discovery, with no new discovery logic. Published: README's contract section names `where()` and `Where`.

- [ ] **Steps to reuse.** Every Given of find-the-store's existing refusals in tests/test_read_an_artifact.py (`the client is working outside any store and nothing names one`, `... with KB_ROOT naming a directory that holds no store`, `the client is working in a directory that has since been removed, and nothing names a store`); answer-a-damaged-file's damage helpers in tests/held.py (`damage_the_database`, `made_by_a_later_kb`); Task 4's "holds both" Given. "The server is not called": the connection names a port nothing listens on, and `where()` still answers with it and no fault.

- [ ] **Decisions applied.** 11, 14.

- [ ] **Verify.** `-m slice-134` → 8, pass; `make test`.

- [ ] **Checkpoint.** `Slice 134 green: <suite line>`.

### Task 8: Slice 135 — find-the-store lines formulated late

Review: batch-end
Model: sonnet

- [ ] **Scenarios** (`@slice-135`, 3): find-the-store / The client's working directory has moved into a different store; ... / The client was readied with a root; ... / The client was readied with a root while KB_ROOT names a different store.

- [ ] **Why each is red today.** Steps missing for all three; and the root line's behaviour is missing: probed at d79fa9e, `connect("deep/er")` inside a store started at `.` answers `List` with the refusal "the root given holds no store: deep/er", because client.py's `_found` calls `store.given(root)`, which looks only in the root itself. The line says the store is looked for from that root the way it is looked for from the working directory: upward, finding a store or a connection, with KB_ROOT not consulted. The moved-directory scenario should pass on steps alone (discovery runs per call).

- [ ] **Where the change lands.** store.py: discovery from a given root searching upward as from the working directory (the same search, a different start), with KB_ROOT not consulted; client.py's `_found` calls it. `store.given` stays for the operator's `kb serve <root>` (decision 6), which names the root outright.

- [ ] **Steps to reuse.** `the client is working in a folder deep inside the directory the store sits in`; `the client reads the decision`; `the client is working inside a store, with KB_ROOT naming a different store` (its second-store builder).

- [ ] **Decisions applied.** None beyond the lines.

- [ ] **Verify.** `-m slice-135` → 3, pass; `make test`.

- [ ] **Checkpoint.** `Slice 135 green: <suite line>`, saying whether the root search changed.

### Task 9: Slice 136 — what starting a store publishes

Review: batch-end
Model: sonnet

- [ ] **Scenarios** (`@slice-136`, 2): start-a-store / Starting a store naming a piece of work is recorded under that piece of work; ... / Listing the kind of types in a store holding nothing but the type that describes types.

- [ ] **Why each is red today.** Steps missing only: probed at d79fa9e, `kb.init(".", "dev", execution="run-7")` gives a first entry with role `dev` and execution `run-7`, and `List(kind="schema")` answers `Listed` whose `ids` is `["schema/schema"]`. No production change is expected; if one is, hand back.

- [ ] **Where the change lands.** tests/test_start_a_store.py steps; README's contract line for `kb.init` already shows `execution`; add that `schema/schema` is the published id of the type of types.

- [ ] **Steps to reuse.** `an empty directory`, `the client starts a store there, saying which role it is` (start-a-store steps); `calls.listing`, `calls.journal`.

- [ ] **Verify.** `-m slice-136` → 2, pass; `make test`.

- [ ] **Checkpoint.** `Slice 136 green: <suite line>`.

### Task 10: Slice 137 — prose kb cannot write back names its place

Review: batch-end
Model: sonnet

- [ ] **Scenarios** (`@slice-137`, 1): hand-over-content / Prose the store could not write back in its one form is refused.

- [ ] **Why it is red today.** The changed Then has no step; and the behaviour is missing: canonical.py's prose representer raises `NotCanonical` with no path (it does not know where the prose stands), and drafting.py's `_serialised` makes `refusals.unwritable(artifact, str(fault))` with no place.

- [ ] **Where the change lands.** canonical.py's dump knows the place of each prose value it writes and raises with `path` (decision 16); split canonical.py first if it would cross 250 (the dump into a module of its own, CLAUDE.md row, rule 5 still one checker); refusals.unwritable takes the place; drafting passes `fault.path`. Also pin, in a unit test of `kb.content`'s public functions, `dumps` raising with `path` `sections/0/body` (request 7 of shop-knowledge) and an item's `options/1/body`.

- [ ] **Steps to reuse.** hand-over-content's existing Given and When in tests/test_create_an_artifact.py; the place assertion against the refusal's fault `place`.

- [ ] **Decisions applied.** 16.

- [ ] **Verify.** `-m slice-137` → 1, pass; `make test`.

- [ ] **Checkpoint.** `Slice 137 green: <suite line>`.

---

## After the batch

The controller runs the batch's branch review (shopsystem-bdd:bdd-branch-reviewer), the fix wave, `make bench` (bounds held), archives the batch, bumps the version to 0.6.0, updates README's contract section (serving, `where()`, `kb.testing.served`, the three rules, `NotCanonical.path`, `schema/schema`, `execution`), tags `v0.6.0`, and pushes only when the person asks.
