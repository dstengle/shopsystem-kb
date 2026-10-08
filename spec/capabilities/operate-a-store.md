---
id: capability/operate-a-store
title: Operate a store
narrator: the operator
rests_on: [decision/init-refuses-inside-or-above, decision/0003-init-refuses-inside-a-store, decision/0008-contract-is-the-stable-boundary, decision/0020-a-server-found-where-the-store-is, decision/files-are-an-export, decision/busy-rule, decision/serving-built, decision/a-server-stamps-with-its-own-clock, decision/0021-kb-served-from-a-container, decision/published-contract-v1-in-0-7-0, decision/seed-may-be-the-root, decision/unwritable-root-refused]
formulated_as: features/operate-a-store.feature
---

# Operate a store

## Purpose

From a shell, without any client, the operator sets a store up, empty or seeded from a directory of files, checks the whole store, and serves a store to several callers, starting it first when asked and none is there. The same commands run in kb's image, in a container beside the callers. The command line changes content only through import into a freshly started store (export-and-import-a-store), a seed included; every other change to content goes through a client. Checking the store is a read, and is never refused because another change is being written. This capability is not publishing the image, or managing the volumes a store lives on beyond `kb export`.

## Behaviour

- When the operator runs kb init against a directory with no store inside it, saying which role they are, there is a store inside that directory in a place of its own, and a client can define its own types in it straight away.
- If nothing names the operator's role, kb init is refused because the role must be named through `KB_ACTOR`, and the directory still has no store inside it.
- If the directory already has a store inside it, kb init is refused because that directory already has a store inside it, and that store holds what it held before.
- If the directory sits inside a store, kb init is refused because that directory is inside a store, and that store holds what it held before.
- When the operator runs kb init with a seed directory on a directory with no store inside it, saying which role they are, there is a store inside that directory holding the files in the seed directory as kb import lands them into a freshly started store (export-and-import-a-store).
- If the operator runs kb init with a seed directory whose files do not check clean, kb init is refused because the seed directory's files do not check clean, the check's report is shown, and the directory still has no store inside it.
- If kb init with a seed directory is stopped before it finishes, however it was stopped, the directory has no store inside it, and the same kb init run again starts a store holding the files in the seed directory.
- If the directory already has a store inside it, kb init with a seed directory is refused because that directory already has a store inside it, and that store holds what it held before.
- If nothing names the operator's role, kb init with a seed directory is refused because the role must be named through `KB_ACTOR`, and the directory still has no store inside it.
- If the directory sits inside a store, kb init with a seed directory is refused because that directory is inside a store, and that store holds what it held before.
- If the seed directory named is not a directory, kb init is refused because files for import are read from a directory, and the directory still has no store inside it.
- When the operator runs kb init with a seed directory that is the directory the store is started in, or holds it, saying which role they are, there is a store inside that directory holding the files the seed directory held, as kb import lands them into a freshly started store, and nothing kb made while starting it is among them.
- If the directory a store would be started in cannot be written, kb init, with a seed directory or without, and kb serve with `--start` are refused because a store can only be started in a directory kb can write, naming the directory; nothing is served, and nothing is made in it.
- When the operator runs kb validate, they are told of everything in the store that does not fit its type, and where, and of everything behind the type it was last checked against.
- The command line offers setting a store up, checking and exporting one, and importing into a freshly started store, and nothing else that changes what the store holds.
- While the operator works in a folder deep inside the directory a store sits in, when they run kb validate, the store found above where they are working is the one checked.
- While the operator works outside any store with `KB_ROOT` naming one, when they run kb validate, the store `KB_ROOT` names is the one checked.
- If the operator works outside any store and nothing names one, kb validate is refused because no store was found, neither above where they are working nor named outright.
- If `KB_ROOT` names a directory that holds no store, kb validate is refused because `KB_ROOT` names a directory that holds no store.
- If the operator works inside one store while `KB_ROOT` names a different store, kb validate is refused because `KB_ROOT` names a store other than the one they are standing in, and neither is guessed at.
- When the operator runs kb serve on a directory holding a store, giving an address, the store is served at that address, on whatever interface it names, all of them included.
- If the operator runs kb serve without an address, it is refused because no address is assumed.
- If the operator runs kb serve giving an address it cannot serve at, because it is not a host and a port or nothing can listen there, it is refused because the store cannot be served at that address, naming the address, and nothing is served.
- When the operator runs kb serve with `--start` on a directory holding no store, saying which role they are, a store is started there and then served at the address given.
- When the operator runs kb serve with `--start` on a directory already holding a store, that store is served as it stands, and no role is needed.
- If the operator runs kb serve with `--start` on a directory holding no store and nothing names their role, it is refused because a store can only be started under a role named through `KB_ACTOR`; nothing is served, and the directory still holds no store.
- If the operator runs kb serve with `--start` on a directory holding no store, giving an address it cannot serve at, it is refused because the store cannot be served at that address, naming the address; nothing is served, and the directory still holds no store.
- If the operator runs kb serve with `--start` on a directory that sits inside a store, it is refused because that directory is inside a store; nothing is served, and that store holds what it held before.
- kb serve with `--start` is refused as kb serve without it is:
  - at an address it cannot serve at;
  - on a store another server owns;
  - on a store made by an earlier or a later kb;
  - on a directory holding a connection.
- While another change is being written to the store, when the operator runs kb validate, the store is checked and kb validate is not refused because the store was busy with another change.

## Implementation, may change

- The commands are `kb init <root> [--seed <dir>]`, `kb validate` and `kb serve <root> --listen <host:port> [--start]`; the role for `kb init` and for a store `kb serve --start` starts comes from `KB_ACTOR`. `kb serve` hosts the store at `<root>/kb/` with `grpc.server`, the same servicer an in-process client reaches, and stamps each change with the server's own clock, the machine's. `kb export` and `kb import` are export-and-import-a-store.
- Reads never wait for the write lock (change-the-store).
- A module of its own, `staging.py`, owns a store started, and seeded, out of sight, then put in place whole: `kb init --seed` starts the store (`kb.init`) and imports the seed (the operator's import) under `<root>/.kb-starting/`, then moves `.kb-starting/kb` to `<root>/kb` with one `os.rename`, atomic because both lie on one filesystem. Whatever an earlier stopped run left in `.kb-starting/` is removed first. The staging directory is part of the store's files and layout, which may change, and is not published.
- `kb serve --start` with no store is `kb.init` and then serving, as `kb serve` serves today.
- A seed directory that is the root itself, or holds it, is read with kb's staging place passed over wherever the root lies inside it, as an import passes over a store's own files. A root kb cannot write is refused with rule `root`, naming the root, before anything is made, the way `kb.init` refuses a root it cannot start a store in.
- Getting a store out of a container is `kb export` run inside it, its files carried out as a tar stream (the README's recipe); no command is added for it, and a store's files are never read through a bind mount owned by another user.
- `cli.py` dispatches only. Exit codes: 2 for a refusal (a seed's report printed first, as `kb import` prints it), 0 after a clean stop.
- The image: one `Dockerfile` at the repository's root, so compose can build from the repository's URL at a tag without naming a file; a `.dockerignore` leaves out `.venv`, `.git`, `tests`, `features`, `bench` and `docs`.
- Two stages: the first builds kb's wheel; the second installs that wheel and its runtime dependencies alone into a virtualenv on `python:3.12-slim`, pinned to an exact tag. No test or build tools.
- It runs as a user `kb`, not root. `/data` is made and owned by that user in the image, so a named volume takes its ownership. A bind mount that user cannot write is refused, exit 2, with one line naming the cause and nothing made in it; over a store already there, that line is kb's own `unreadable` fault naming the database. The README says so, and how `--user` overrides it.
- `ENTRYPOINT ["kb"]`, `CMD ["serve", "/data", "--listen", "0.0.0.0:50051", "--start"]`, `WORKDIR /data`, `VOLUME /data`, `EXPOSE 50051`. The store lives at `/data/kb/`; with the working directory `/data`, the operator's commands find it without `KB_ROOT`.
- `kb` is PID 1 in exec form and stops on SIGTERM and SIGINT; no init process is added. `docker compose stop` sends SIGTERM; the server stops and lets the store go.
- `HEALTHCHECK` is a short Python connect to `127.0.0.1:50051`, every few seconds after a short start period: the service is healthy when its port accepts a connection. A command that serves at another port needs its own healthcheck; the README says so.
- `KB_ACTOR` has no default in the image: whoever starts a store names the role.
- `docker compose up` runs the default command: on an empty volume with `KB_ACTOR` set, an empty store is started and then served; on an empty volume with no `KB_ACTOR`, the container exits 2 with one line saying the store can only be started under a role named through `KB_ACTOR`; once the store exists, `up` serves it.
- Seeding, when wanted, is one step before the first `up`: `docker compose run --rm -v ./seed:/seed:ro kb init /data --seed /seed`.
- The operator's commands run in the container: `docker compose run --rm kb validate`, or `docker compose exec kb kb validate` against the running server (a read, which a served store answers).
- The log says `serving\t0.0.0.0:50051` once the store is served, and any refusal.
- A caller gets its connection from a compose `configs:` entry mounted as `kb/server.yaml` under the directory its `KB_ROOT` names, and reaches kb by its service name (`kb:50051`).
- An example compose file ships as `docker/compose.example.yaml` and is shown in the README: a `kb` service built from `https://github.com/dstengle/shopsystem-kb.git#v0.7.0` with `KB_ACTOR` and a named volume `kb-store` at `/data`, and a caller with `KB_ROOT: /kb-connection`, the config `kb-connection` (`address: kb:50051`) mounted at `/kb-connection/kb/server.yaml`, depending on `kb` being healthy.
- The README gains "Running kb in Docker": the compose example, the seed step, the operator's commands, the empty-store trap (`up` before seeding starts an empty store, over which `kb init --seed` is refused; nothing is lost in an empty store, so `docker compose down -v` and seed again), and the bind mount's ownership.

## Not yet

- Publishing the image to GHCR from a release tag, and the repository's first CI workflow. Promoted when a caller needs kb's image without building it from the repository.
- Images for more than one architecture. Promoted when someone needs to run the image on a machine whose architecture it was not built for.
- Backups and managing volumes beyond `kb export`. Promoted when an operator needs to restore a store that `kb export` and import cannot bring back.
