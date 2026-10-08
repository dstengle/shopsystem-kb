# kb served from a Docker container

Date: 2026-10-07. The person asked for kb to be wrapped so its server runs easily from a Docker container, with the
experience of running it put first. The design below was approved section by section on 2026-10-07. It adds to the
contract and changes nothing in it; the package stays `kb.v1` and the release is kb 0.7.0.

## Who it is for

The operator, which names an activity rather than a person: a developer on a laptop is the operator whenever they set
a store up or serve one. The development environment is itself containerized, so the laptop and a deployment have one
shape: kb is a service beside its callers on a shared network, and callers reach it by its service name (`kb:50051`),
never by a port published to the host. The bounds stay as they are: no authentication or encryption, the network the
server listens on is its boundary.

## 1. What the operator does

A compose file, shipped as `docker/compose.example.yaml` and shown in the README:

```yaml
services:
  kb:
    build: https://github.com/dstengle/shopsystem-kb.git#v0.7.0
    environment:
      KB_ACTOR: operator            # needed only when the store is started
    volumes:
      - kb-store:/data              # the store lives at /data/kb/
  agent:
    image: my-shop-knol-role
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

- Seeding, when wanted, is one step before the first `up`:
  `docker compose run --rm -v ./seed:/seed:ro kb init /data --seed /seed`.
- `docker compose up` serves the store. On an empty volume with `KB_ACTOR` set, an empty store is started and then
  served; on an empty volume with no `KB_ACTOR`, the container exits 2 with one line saying the store can only be
  started under a role named through `KB_ACTOR`. Once the store exists, `up` just serves it.
- A caller gets its connection from a compose `configs:` entry mounted as `kb/server.yaml` under the directory its
  `KB_ROOT` names. kb's discovery, the connection's form and decision 0020 are unchanged; kb still never writes the
  connection.
- The operator's commands run in the container: `docker compose run --rm kb validate`, or
  `docker compose exec kb kb validate` against the running server (a read, which a served store answers). The working
  directory is `/data`, so the store is found without `KB_ROOT`.
- The log says `serving\t0.0.0.0:50051` once it serves, and any refusal. `docker compose stop` sends SIGTERM; the
  server stops and lets the store go.
- The service is healthy when its port accepts a connection. `kb serve` refuses a store it cannot open before it
  listens, so an open port means the store opened.
- The trap: running `up` before seeding starts an empty store, and `kb init --seed` is then refused because a store is
  already there. Nothing is lost in an empty store, so the README says to run `docker compose down -v` and seed again.

## 2. `kb init --seed` and `kb serve --start`

`kb init <root> [--seed <dir>]` and `kb serve <root> --listen <host:port> [--start]`. Without the new flags both
behave as today.

Behaviour lines for `capability/operate-a-store`:

- When the operator runs kb init with a seed directory on a directory with no store inside it, saying which role they
  are, there is a store inside that directory holding the files in the seed directory.
- If the seed directory's files do not check clean, kb init is refused with the check's report shown, and the
  directory still has no store inside it.
- If kb init with a seed directory is stopped before it finishes, the directory has no store inside it, and kb init
  run again starts one.
- If the directory already has a store inside it, kb init with a seed directory is refused because that directory
  already has a store inside it, and that store holds what it held before (today's refusal of kb init, which it
  shares).
- When the operator runs kb serve with `--start` on a directory holding no store, saying which role they are, a store
  is started there and then served at the address given.
- When the operator runs kb serve with `--start` on a directory already holding a store, that store is served as it
  stands, and no role is needed.
- If the operator runs kb serve with `--start` on a directory holding no store and nothing names their role, it is
  refused because a store can only be started under a role named through `KB_ACTOR`; nothing is served, and the
  directory still holds no store.
- kb serve's other refusals hold with `--start`: an address it cannot serve at, a store another server owns, a store
  made by an earlier or a later kb, a directory holding a connection.

Implementation, may change:

- A new module, `staging.py`, owns a store started, and seeded, out of sight, then put in place whole. `kb init
  --seed` starts the store (`kb.init`) and imports the seed (the operator's import) under `<root>/.kb-starting/`, then
  moves `.kb-starting/kb` to `<root>/kb` with one `os.rename`, atomic because both lie on one filesystem. Whatever an
  earlier stopped run left in `.kb-starting/` is removed first. The staging directory is part of the store's files
  and layout, which may change, and is not published.
- `kb serve --start` with no store is `kb.init` and then serving, as today.
- `cli.py` dispatches only. Exit codes stay: 2 for a refusal (a seed's report printed first, as `kb import` prints
  it), 0 after a clean stop.

## 3. The image

- One `Dockerfile` at the repository's root, so compose can build from the repository's URL at a tag without naming
  a file. A `.dockerignore` leaves out `.venv`, `.git`, `tests`, `features`, `bench` and `docs`.
- Two stages: the first builds kb's wheel; the second installs that wheel and its runtime dependencies alone into a
  virtualenv on `python:3.12-slim`, pinned to an exact tag. No test or build tools.
- It runs as a user `kb`, not root. `/data` is made and owned by that user in the image, so a named volume takes its
  ownership. A bind mount that user cannot write is kb's own `unreadable` fault naming the database; the README says
  so and how `--user` overrides it.
- `ENTRYPOINT ["kb"]`, `CMD ["serve", "/data", "--listen", "0.0.0.0:50051", "--start"]`, `WORKDIR /data`,
  `VOLUME /data`, `EXPOSE 50051`.
- `kb` is PID 1 in exec form and already stops on SIGTERM and SIGINT; no init process is added.
- `HEALTHCHECK` is a short Python connect to `127.0.0.1:50051`, every few seconds after a short start period. A
  command that serves at another port needs its own healthcheck; the README says so.
- `KB_ACTOR` has no default: whoever starts a store names the role.
- Published, and added to `spec/index.md`'s list of what a client may depend on: the image's store directory
  (`/data`), its port (50051), its entry point (`kb`) and its default command. The Dockerfile's insides are not.

## 4. Testing and release

- Each Behaviour line in section 2 is formulated as a scenario in `features/operate-a-store.feature` and built
  red-green in the suite: the operator's commands in process, `kb serve --start` as a real `kb serve` in the test's
  own temporary directory at port 0. No scenario touches Docker or `.kb-starting/`; a stopped or refused seed is seen
  from the operator's side, as no store in the directory and a later kb init that starts one.
- The image is checked outside `make test`, as the performance bounds are. `make image` builds it; `make image-check`
  runs a script against a throwaway compose project and checks that: `kb init --seed` lands a small seed, and a
  refused seed leaves the volume holding no store; `up` becomes healthy; a second container reaches `kb:50051`
  through a connection given by a compose config, reads and makes a change; `docker compose run --rm kb validate`
  answers; a stop and a start keep the store; an empty volume with no `KB_ACTOR` exits 2 with the role's line. The
  spec's Testing paragraph gains: the image is checked by that script, and a release that fails it does not ship.
- kb 0.7.0: `kb init --seed`, `kb serve --start`, the image's published surface. The README gains "Running kb in
  Docker": the compose example, the seed step, the operator's commands, the empty-store trap and `down -v`, and the
  bind mount's ownership.
- Decision 0021 records the person's decisions of 2026-10-07: the operator is an activity a developer takes on, and
  the development environment is containerized, so callers reach kb by service name; a store is started on first `up`
  when a role is named; seeding belongs to `kb init`, refused over a store that exists; the connection reaches callers
  through compose, with no change to kb's discovery; the image is built from the repository first, published later.

## Not done

- Publishing the image to GHCR from a release tag, and the repository's first CI workflow: a later change.
- Images for more than one architecture.
- Authentication and encryption: still Not yet.
- A `KB_SERVER` variable naming a server for callers: the connection stays `kb/server.yaml`.
- Backups and managing volumes beyond `kb export`.
- An image for a client or for shop-knol: shop-knowledge's.
