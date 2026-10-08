# kb

A schema-typed, graph-oriented artifact store. Typed documents with
addressable parts, schemas stored as artifacts, one SQLite database as the
canonical store (written out as canonical YAML files on the operator's
`kb export`, and read back by `kb import`), and one versioned API contract,
hosted both by an in-process client and by a server (`kb serve`).

## The contract: v1 (kb 0.7.0)

The contract is `kb.v1` (`kb.contract.kb_pb2`); 0.5.0 was the breaking release that removed every v0 rpc and request
(`Actor` stays only as the type of `Entry.actor`), and 0.6.0 adds serving a store over the network.
0.7.0 adds `kb init <root> --seed <dir>`, `kb serve <root> --listen <host:port> --start` and kb's image, which serves
a store from a Docker container (below).

- Changes: `Create`, `Replace`, `Add` and `Remove`, each taking one `Signature { role, execution, message }` and
  answering its result or a `Refusal`; the same four as sets, `BatchCreate`, `BatchReplace`, `BatchAdd` and
  `BatchRemove`. A `CreateItem` of a set carries a `key`, and links in that set written `@<key>` reach the artifact
  that create makes. An artifact, or a place inside it, is named by a `Locator { id, place }`. A replace, add or remove
  may say the `revision` it read, and is refused with rule `revision` if the artifact moved since.
- Reads: `Read` (one level: `summary`, `whole` with a depth, or `section`), `List`, `Follow`, `Search`, `History`,
  the signed `Snapshot`, and `Check`. They replace v0's `Refs`, `Journal` and `Validate`.
- No rpc starts a store: `kb.init(root, role, *, execution="", clock=None)` does, in your own process, and raises
  `kb.NotStarted` carrying the faults when it refuses. The first history entry names the `execution` when one is
  given, and a fresh store lists `schema/schema` as its one type, the published id of the type of types.
  `kb.client.connect(root, *, clock=None)` gives the client.
  The client's `where()` asks where its store is without making a call: it runs the search a call would make,
  opening nothing and calling nothing, and returns a `kb.client.Where` holding `root` (the directory the search
  stopped at), `address` (the server's `host:port`, empty unless the connection to a server was found) and `faults`
  (why a call would be refused for finding nothing); `root` and `faults` are never both filled.
- `kb.content` publishes `loads`, `dumps`, `text` and `NotCanonical`. `NotCanonical.path` names where the text
  kb cannot keep stands: names and list positions from the top of the content joined by `/`, such as
  `sections/0/body`, empty when the refusal names no place. The published rule names are listed in spec/index.md,
  with `busy` and `revision` among them, and, new in 0.6.0, `connection`, `unreachable` and `served`; a JSON Schema
  keyword passes through as the rule of a content fault.

### Serving a store (kb 0.6.0)

`kb serve <root> --listen <host:port>` serves the store at `<root>` at exactly that address (port 0 asks the system
for one, and the line it prints says which) until it is signalled to stop; an address it cannot serve at is refused
and nothing is served. A client reaches it through the connection to the server: `kb/server.yaml` holding one entry,
`address: host:port`, written by whoever arranges the callers, never by kb. A client that finds the connection where
it finds a store makes every call over the network, with the same requests and answers; one it cannot reach is
refused with `unreachable`, a connection it cannot read with `connection`, and a client readied with a clock has its
changes refused with `clock` (the server stamps them with its own). While a store is served, a change asked of it
directly is refused with `served`, naming the server's address.

### Serving a store for tests (kb 0.6.0)

`kb.testing.served(store_root, connection_dir, *, clock=None)` is a context manager that puts the store at
`store_root` behind kb's own server, the one `kb serve` runs, in your test's own process on `127.0.0.1` at a port
the system picks. It writes `kb/server.yaml` under `connection_dir` naming that address and yields the address as
`host:port`; a client working in `connection_dir` reaches the store through the server. A `connection_dir` that
already holds a connection is refused with a `ValueError`, before anything is served, the connection left as it was. Changes made through it are
stamped with the moment `clock` gives, or the machine's with none. When the block ends, passed or raised, the server
is stopped, the store let go, and the connection removed (with `kb/`, if the double made it and nothing else is in
it). While it serves, a change asked of the store directly is refused with `served`. A pytest fixture over it, with `import kb.testing`:

```python
@pytest.fixture
def served_store(store_root, tmp_path):
    with kb.testing.served(store_root, tmp_path) as address: yield address
```

Upgrading a store made by kb 0.3.0: start a new store and import the old
one's files: `kb init <new-root>`, then `kb import <old-root>/kb` run inside
the new store (or with `KB_ROOT=<new-root>`).

kb ships no domain schemas and no renderers. A client such as
[shopsystem-knowledge](https://github.com/dstengle/shopsystem-knowledge)
supplies the types, seed content, and presentation.

Spec: `spec/index.md`. Storage design: `docs/superpowers/specs/2026-10-01-kb-storage-sqlite-design.md`.
`make bench` checks the performance bounds at 30,000 artifacts.

## Running kb in Docker

kb's image serves a store as a service beside its callers, which reach it by its service name, `kb:50051`, never by a
port published to the host; the network it listens on is its boundary (no authentication, no encryption). Published:
the store directory `/data` (the store lives at `/data/kb/`), the port 50051, the entry point `kb` and the default
command `serve /data --listen 0.0.0.0:50051 --start`. The compose example, `docker/compose.example.yaml`:

```yaml
services:
  kb:
    build: https://github.com/dstengle/shopsystem-kb.git#v0.7.0
    environment:
      KB_ACTOR: operator            # needed only when the store is started
    volumes:
      - kb-store:/data              # the store lives at /data/kb/
  agent:
    image: my-shop-knol-role        # your caller's image
    environment:
      KB_ROOT: /kb-connection
    configs:
      - source: kb-connection
        target: /kb-connection/kb/server.yaml
    depends_on:
      kb: { condition: service_healthy }
configs:
  kb-connection:
    content: "address: kb:50051\n"
volumes:
  kb-store: {}
```

- `agent` stands for your caller: put your caller's image in place of `my-shop-knol-role`.
- Seeding, when wanted, is one step before the first `up`, from a directory of files laid out as `kb export` lays
  them out: `docker compose run --rm -v ./seed:/seed:ro kb init /data --seed /seed`. A seed that does not check clean
  is refused with the check's report, as `kb import` shows it, and the volume is left holding no store.
- `docker compose up` serves the store, and the log says `serving\t0.0.0.0:50051` once it does. On an empty volume
  with `KB_ACTOR` set, an empty store is started there and served; with no `KB_ACTOR`, the container exits 2 with
  `kb serve: refused: actor: a store can only be started under a role, named through KB_ACTOR`. Once the store
  exists, `up` serves it as it stands and no role is needed. `docker compose stop` stops the server, which lets the
  store go.
- A caller gets its connection from a compose `configs:` entry mounted as `kb/server.yaml` under the directory its
  `KB_ROOT` names; kb never writes the connection.
- The operator's commands run in the container, whose working directory is `/data`, so the store is found without
  `KB_ROOT`: `docker compose run --rm kb validate`, or `docker compose exec kb kb validate` against the running
  server (a read, which a served store answers).
- The service is healthy when its port accepts a connection; `kb serve` refuses a store it cannot open before it
  listens, so an open port means the store opened. The image's healthcheck connects to port 50051: a command that
  serves at another port needs its own healthcheck.
- The empty-store trap: `up` run before seeding starts an empty store, and `kb init --seed` is then refused because a
  store is already there. Nothing is lost in an empty store: run `docker compose down -v`, which removes the volume
  and the store in it, and seed again.
- The container runs as the user `kb` (uid and gid 1000), which owns `/data` in the image, so a named volume takes
  that ownership. A bind mount that user cannot write (a host directory Docker made as root, say) is refused: the
  container exits 2 with one line naming the cause, and nothing is made in it. Over a store already there, the
  refusal is kb's `unreadable` fault naming the database. Own the directory by uid 1000, or run the service as its
  owner with `--user` (`user:` in compose, as in `docker compose run --rm --user "$(id -u):$(id -g)" kb ...`).
- The image is built from the repository at a release tag; `make image` builds one from a checkout, and
  `make image-check` checks one serves a store beside its callers.

## Developing

Python 3.11. `make dev` installs kb editable with its test and build tools.
`make contract` regenerates `src/kb/contract/kb_pb2*.py` from `kb.proto`;
the generated files are committed. `python -m pytest -q` runs the feature
suite; `python -m pytest -q -m slice-1` runs one slice.
