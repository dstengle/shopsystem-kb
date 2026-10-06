# shop-knowledge's requests of 2026-10-06: serving, where a store is, and what is relied on unpublished

Date: 2026-10-06. shop-knowledge pins kb 0.5.0 (contract v1) and asked for seven things. Three block its
scenarios (serving, where a found knowledge base is, a served-store double); four cover what it already relies on
without kb publishing it. The person approved the controller's recommendations on 2026-10-06. Everything here adds
to contract v1, nothing in it changes; the package stays `kb.v1` and the release is kb 0.6.0.

## 1. Serving is built

The served-store lines already in the spec (reach-a-served-store, and operate-a-store's `kb serve` lines) are
formulated and built; serving leaves operate-a-store's Not yet.

- `kb serve <root> --listen <host:port>` hosts the store at `<root>/kb/` with `grpc.server`, the same servicer an
  in-process client reaches, and stamps each change with the server's own clock (the machine's).
- While it serves, the server holds a lock of the operating system on a file of the store's own, inside `kb/`,
  which says the address it serves at. A client that finds the store directly reads while it is served, and a change
  it asks for is refused because the store is served, naming that address. The lock goes when the server's process
  does, so a server that stopped, however it stopped, leaves no store marked as served.
- When the search stops at `kb/server.yaml`, `connect` calls the address it names over a gRPC channel with the same
  method names, requests and responses.
- Four refusals, three under new rules of kb's own, which join the published list:
  - `connection`: the connection cannot be read, or names no address; the fault names the connection.
  - `unreachable`: the server the connection names cannot be reached, or stops answering; the fault names the
    address, and the call comes back with its answer rather than breaking off.
  - `served`: a change asked of a served store by a client that found it directly; the fault names the server's
    address.
  - `clock` (already kb's): a change asked of a server by a client readied with a clock, since that clock belongs
    to a client that reaches its store in process. Its reads are answered.

## 2. Where a found knowledge base is

The client publishes `where()`. It searches as a call would and answers either where the search stopped (the root,
the directory holding `kb/store.yaml` or `kb/server.yaml`) and, when it found a connection, the server's address;
or the faults that say why nothing was found; never both. It is the client's own search, so no rpc is added and a
server is not called. How a client tells its user where that is (`KB_ROOT`'s value, a named directory, an address)
is the client's: it knows its own environment.

## 3. `kb.init`'s piece of work is published

`kb.init(root, role, *, execution="", clock=None)`: the piece of work, when named, is carried by the store's first
history entry beside the role.

## 4. The id of the type that describes types is published

The type that describes types is `schema/schema`, and that id is published. A client can tell a store that holds
nothing but kb's own type by listing the kind `schema` and finding that id alone. No new call.

## 5. `NotCanonical.path` is published

`kb.content.NotCanonical` carries `path`: the place the refusal names, written as the names and list positions from
the top of the content, joined by `/` (`sections/0/body`), and empty when the refusal names no place.

## 6. A served-store double for clients' tests

`kb.testing.served(store_root, connection_dir, *, clock=None)` is a published context manager. Given the root of a
started store and a directory to hold the connection (a different one, since a directory never holds both), it
serves the store on `127.0.0.1` at a free port, in the test's own process, writes `kb/server.yaml` under
`connection_dir` naming that address, and yields the address. On exit it stops the server and removes the
connection. With a clock, the server stamps changes with it, so a client's tests can pin moments. It is the server
`kb serve` runs, not an imitation. A pytest fixture over it is the client's (three lines; the README shows one).

## 7. `dumps` names the place when it refuses prose

When `kb.content.dumps` refuses prose because a line before its last ends in a space, the `NotCanonical` it raises
carries the place of that prose in `path`, as every other refusal with a place does. The hand-over-content line on
such prose gains "naming the place".

## Not done

- No pytest plugin loaded on install: a fixture is the client's three lines over the context manager.
- No rpc saying where a store is: the answer is the client's search, not the server's.
- Authentication and encryption stay Not yet.
