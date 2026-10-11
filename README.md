# kb

A schema-typed, graph-oriented artifact store. Typed documents with
addressable parts, schemas stored as artifacts, one SQLite database as the
canonical store (written out as canonical YAML files on the operator's
`kb export`, and read back by `kb import`), and one versioned API contract,
hosted both by an in-process client and by a server (`kb serve`).

## The contract: kb.v2

The contract is `kb.v2` (`kb.contract.kb_pb2`, generated from `src/kb/contract/kb.proto`). It is published, with
everything else a client may depend on (spec/index.md), under kb's release tag, which a client pins: `v<version>`,
where `<version>` is the `version` in `pyproject.toml`. `kb.v2` replaces `kb.v1` in one breaking release; a store
made under `kb.v1` is never read, written or migrated.

- Names: every artifact, part and type is named by an https IRI of kb's grammar, `https://<host>/<segment>/...` in
  lower case, at most 512 characters. A type is defined at any IRI its client chooses, such as
  `https://shop.example/kb/process`. An artifact's IRI is chosen by its client under its type's,
  `https://shop.example/kb/process/restock`, and kept for life; kb never makes one up, and one that does not sit
  under its type's IRI, or is already held, is refused with rule `identity`. A part is named by its artifact's IRI,
  `#` and its place, `https://shop.example/kb/process/restock#steps/draft`; a version of a type by the type's IRI,
  `@` and its number, `https://shop.example/kb/process@1`. A kind is named by its type's IRI.
- Types: a type is an artifact of the type that describes types, which is held at `https://missingmass.io/kb/type`
  (its first version `https://missingmass.io/kb/type@1`), the one type a fresh store lists. A `Replace` of a type
  makes its next version, numbered by kb; every version is kept as it was made and reads back at its own IRI. An
  artifact conforms to the version it names until a replace names another (`ReplaceRequest.type`), and `Check`
  lists those behind their type as stale, never as violations.
- Changes: `Create`, `Replace`, `Add` and `Remove`, each taking one `Signature { role, execution, message }` and
  answering its result or a `Refusal`; the same four as sets, `BatchCreate`, `BatchReplace`, `BatchAdd` and
  `BatchRemove`. A `CreateRequest`, and each `CreateItem` of a set, carries `id`, the artifact's IRI, and `type`, the
  IRI of the type version it conforms to, beside its `title` and `content`. A create may name a part by giving the
  item an `id`; a part given none is named by kb. A link in a set names what another create of the set makes by the
  IRI that create carries, earlier in the set or later. `BatchCreate` and `BatchReplace` take `check_only`: the set
  is answered as it would land, or refused with every fault it would be refused with, and nothing is written. An
  artifact, or a place inside it, is named by a `Locator { id, place }`. A replace, add or remove may say the
  `revision` it read, and is refused with rule `revision` if the artifact moved since.
- Links and placeholders: a link is the IRI of an artifact, or of a part. A link to an IRI the store does not hold,
  under a type it holds that the link field allows, lands on a placeholder, which is never stored and never a fault.
  `Placeholders` lists every one with the links into it, `Check` lists them apart from the violations, and a read
  marks the stub of such a link `not_held` and gives it among the read's `placeholders`.
- Reads: `Read` (one level: `summary`, `whole` with a depth, or `section`) of an artifact by its IRI, of a part by
  `<IRI>#<place>` or by the locator's `place` (both together are refused), and of a version of a type by
  `<type IRI>@<n>`; `List`, by a kind, by a path below the type (`2026` selects `<type IRI>/2026/...`, whole
  segments only, whatever the type) or both, refused with neither; `Follow`, narrowed by a field, a kind or a path;
  `Search`, `History`, the signed `Snapshot`, and `Check`.
- `Export` gives the store as its canonical files, streamed: one message for each file, its `place` in the export
  layout (below) and its `text`, then one carrying the end, with the `position` in the history the files reflect.
  A kind, a path below the type, or both narrow it to the artifacts they select. Only a stream whose last message
  carries the end is the whole export; a caller that will not read to the end closes the stream.
- No rpc starts a store: `kb.init(root, role, *, execution="", clock=None)` does, in your own process, and raises
  `kb.NotStarted` carrying the faults when it refuses. The first history entry names the `execution` when one is
  given. `kb.client.connect(root, *, clock=None)` gives the client.
  The client's `where()` asks where its store is without making a call: it runs the search a call would make,
  opening nothing and calling nothing, and returns a `kb.client.Where` holding `root` (the directory the search
  stopped at), `address` (the server's `host:port`, empty unless the connection to a server was found) and `faults`
  (why a call would be refused for finding nothing); `root` and `faults` are never both filled.
- `kb.content` publishes `loads`, `dumps`, `text` and `NotCanonical`. `NotCanonical.path` names where the text
  kb cannot keep stands: names and list positions from the top of the content joined by `/`, such as
  `sections/0/body`, empty when the refusal names no place.
- A fault's `rule` is one of kb's own rule names, or, for content that breaks its type's JSON Schema, the JSON
  Schema keyword it breaks. kb's own: `not-found`, `kind`, `locator`, `collection`, `identity`, `on_delete`,
  `unreadable`, `item-name`, `shape`, `built-on`, `targets`, `version`, `content`, `sections`, `ref`, `actor`,
  `message`, `operations`, `since`, `title`, `root`, `store`, `clock`, `busy`, `revision`, `placement`,
  `connection`, `unreachable`, `served`, `differs`.

### Serving a store

`kb serve <root> --listen <host:port>` serves the store at `<root>` at exactly that address (port 0 asks the system
for one, and the line it prints says which) until it is signalled to stop; an address it cannot serve at is refused
and nothing is served. A client reaches it through the connection to the server: `kb/server.yaml` holding one entry,
`address: host:port`, written by whoever arranges the callers, never by kb. A client that finds the connection where
it finds a store makes every call over the network, with the same requests and answers; one it cannot reach is
refused with `unreachable`, a connection it cannot read with `connection`, and a client readied with a clock has its
changes refused with `clock` (the server stamps them with its own). While a store is served, a change asked of it
directly is refused with `served`, naming the server's address.

### Serving a store for tests

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

### The operator's commands

`kb` is the operator's command line. `kb validate`, `kb export`, `kb import` and `kb backup` find the store upward
from the working directory, or the one `KB_ROOT` names; `kb init`, `kb import` and a store `kb serve --start` starts
take the operator's role from `KB_ACTOR`. A refusal is one line for each fault on stderr and exit 2.

- `kb init <root>` starts an empty store inside an existing directory `<root>`, as `<root>/kb/`.
  `kb init <root> --seed <dir>` starts one holding the files in `<dir>`, as `kb import` lands them; a seed that
  does not check clean is refused with the check's report, and no store is left.
- `kb validate` checks the whole store: what does not fit its type (exit 1), what is behind its type, and every
  placeholder, each listed apart.
- `kb export <dir>` writes the store at one moment as canonical YAML into a directory that is empty or does not
  exist, never over anything. The layout follows each artifact's IRI, its host and its path:
  `<dir>/<host>/<path>.yaml`, so `https://shop.example/kb/process/restock` is at
  `<dir>/shop.example/kb/process/restock.yaml`; each version a type is held at has a file of its own at the type's
  place, `@` and its number, `<dir>/shop.example/kb/process@1.yaml`, and the type that describes types is at
  `<dir>/missingmass.io/kb/type@1.yaml`. Each file gives the artifact's `id`, `type`, `revision` and `title`, then
  its content. It is the layout the contract's `Export` names its files by.
- `kb import <dir> --check` reads every file of a directory laid out that way and reports each error, naming the
  file and the rule, and each file that would be skipped because it leads to a file with one, writing nothing; exit 1
  when it finds an error.
- `kb import <dir>` checks first, then lands everything as one signed set, into a store that is fresh or already
  holds artifacts. An artifact the store already holds at the same IRI with the same content and type version is
  passed over; one it holds with other content or another type version refuses the whole import with rule
  `differs`, naming the IRI: an import replaces nothing the store holds. Any other error refuses it with the check's
  report, unless `kb import <dir> --skip-errors` is asked, which lands all but the broken files and the files
  leading to them and says what it skipped. An import carries no history across.
- `kb backup <file>` copies the store whole into one file, its history included, as it stood at one moment, while
  clients go on writing and while a server serves it; it never overwrites. `kb restore <file> <root>` makes the
  store a backup holds inside a directory that holds none, its history ending where the backup's did; it needs no
  role, and refuses a file that is not a backup this kb made. A backup is the whole store for this kb; the
  readable, portable copy is the export.
- `kb serve <root> --listen <host:port> [--start]` serves a store, above.

There is no upgrade path from a store an earlier contract made: this kb refuses to open one, and an import reads
only the export layout above.

kb ships no domain schemas and no renderers. A client such as
[shopsystem-knowledge](https://github.com/dstengle/shopsystem-knowledge)
supplies the types, seed content, and presentation.

Spec: `spec/index.md`. Storage design: `docs/superpowers/specs/2026-10-01-kb-storage-sqlite-design.md`.
`make bench` checks the performance bounds at 30,000 artifacts.

## Running kb in Docker

kb's image serves a store as a service beside its callers, which reach it by its service name, `kb:50051`, never by a
port published to the host; the network it listens on is its boundary (no authentication, no encryption). Published:
the store directory `/data` (the store lives at `/data/kb/`), the port 50051, the entry point `kb` and the default
command `serve /data --listen 0.0.0.0:50051 --start`. The compose example, `docker/compose.example.yaml`, needs Docker
Compose 2.23.1 or later, for its `configs:` entry given by `content:`:

```yaml
services:
  kb:
    build: https://github.com/dstengle/shopsystem-kb.git#v${KB_VERSION:?set KB_VERSION to the release of kb to build}
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
- The `build:` URL's `#v${KB_VERSION}` names the tag of the release of kb to build: set `KB_VERSION` to that
  release's version (the `version` in its `pyproject.toml`) in the environment `docker compose` runs in, as in
  `KB_VERSION=<version> docker compose up`; with none set, compose refuses, saying so. Every `docker compose`
  command shown here reads the file and so needs it: export `KB_VERSION`, or put `KB_VERSION=<version>` in a `.env`
  file beside the compose file, once. The tag exists once that
  release is tagged and the repository is reachable from where you build. Until then, build from a checkout: `build: <path to the checkout>`, or `make image`
  in the checkout and `image: shopsystem-kb:dev` in place of `build:`.
- The example sets no `restart:` policy on purpose: a refusal (no `KB_ACTOR` on an empty volume, a store it cannot
  open) would restart the container in a loop. Once the store is set up and served, add `restart: unless-stopped` if
  you want it.
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
  container exits 2 with one line, kb's `root` fault naming `/data`, and nothing is made in it. Over a store already there, the
  refusal is kb's `unreadable` fault naming the database. Own the directory by uid 1000, or, for a bind mount whose
  files are already owned by another uid, run the service as that owner with `--user` (`user:` in compose, as in
  `docker compose run --rm --user "$(id -u):$(id -g)" kb ...`). Do not use `--user` on a named volume: its store is
  the user `kb`'s, and a command run as another uid is refused with `unreadable`, `validate` and `export` included.
- Getting the store's files out works whatever your uid: export inside the container and stream the files out as a
  tar, `docker compose run --rm -T --entrypoint sh kb -c 'kb export /tmp/x && tar -C /tmp/x -c .' > kb-export.tar`.
  It works with the server up, too; `tar -xf kb-export.tar -C <dir>` gives the files, laid out as `kb export` lays
  them out, ready to seed another store.
- Getting the store out whole, its history included, is a backup made inside the container and streamed out,
  `docker compose run --rm -T --entrypoint sh kb -c 'kb backup /tmp/store.backup && cat /tmp/store.backup' > store.backup`,
  which `kb restore store.backup <root>` makes a store of again. It works with the server up, too.
- The image is built from the repository at a release tag; `make image` builds one from a checkout, and
  `make image-check` checks one serves a store beside its callers.

## Developing

Python 3.11. `make dev` installs kb editable with its test and build tools.
`make contract` regenerates `src/kb/contract/kb_pb2*.py` from `kb.proto`;
the generated files are committed. `make test` runs the feature suite in the
checkout's virtualenv, in parallel; `.venv/bin/python -m pytest -q -m slice-133`
runs one slice's scenarios.
