---
id: capability/operate-a-store
title: Operate a store
narrator: the operator
rests_on: [decision/init-refuses-inside-or-above, decision/0003-init-refuses-inside-a-store, decision/0008-contract-is-the-stable-boundary, decision/0020-a-server-found-where-the-store-is, decision/files-are-an-export, decision/busy-rule, decision/serving-built, decision/a-server-stamps-with-its-own-clock, decision/0021-kb-served-from-a-container, decision/published-contract-v2, decision/seed-may-be-the-root, decision/unwritable-root-refused, decision/0028-backup-and-restore-beside-export, decision/0025-placeholders-are-reported-never-a-fault, decision/0026-import-passes-over-identical-refuses-differing]
formulated_as: features/operate-a-store.feature
---

# Operate a store

## Purpose

From a shell, without any client, the operator sets a store up, empty or seeded from a directory of files, checks the whole store, backs a running store up whole, its history and journal included, restores a backup as a store in an empty place, and serves a store to several callers, starting it first when asked and none is there. The same commands run in kb's image, in a container beside the callers. The command line changes content only through import into a store (export-and-import-a-store), a seed included, and through restoring a backup; every other change to content goes through a client. Checking the store is a read, and is never refused because another change is being written; it lists placeholders and never fails on one. This capability is not publishing the image, or the readable, portable copy of a store, which is export (export-and-import-a-store).

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
- When the operator runs kb validate, they are told of everything in the store that does not fit its type, and where, of everything behind the type it conforms to, and of every placeholder with what links to it, each listed apart.
- When the operator runs kb validate on a store whose only findings are placeholders, the store checks clean.
- The command line offers setting a store up, checking and exporting one, backing one up, restoring a backup, and importing into a store, and nothing else that changes what the store holds.
- When the operator backs up a store, the backup holds the store whole, its history and its journal included.
- When the operator backs up a store, the backup holds the store as it stood at one moment, each set landing meanwhile either in it whole or not at all.
- While clients are writing to the store, when the operator backs it up, the backup is made and the clients go on writing, none of their changes refused because of the backup.
- While another change is being written to the store, when the operator backs it up, the backup is made and is not refused because the store was busy with another change.
- While a server serves the store, when the operator backs it up, the backup is made and the server goes on serving.
- If anything is already at the place a backup would be written, even an empty file or directory, the backup is refused because a backup never overwrites, and what is there is left as it was.
- kb backup finds the store as kb validate does, and is refused as kb validate is: when no store is found, when `KB_ROOT` names none or another, when the store was made by an earlier or a later kb, and when its database cannot be read.
- Where a connection to a server is found and no store, kb backup is refused because a backup is made where the store's files are, not through a server.
- When the operator restores a backup in a directory with no store inside it, there is a store inside that directory holding everything the store backed up held, its history and its journal included, and no role is needed.
- When the operator restores a backup, the restored store's history ends with the last entry the store held when backed up.
- If the directory already has a store inside it, the restore is refused because that directory already has a store inside it, and that store holds what it held before.
- If the directory sits inside a store, the restore is refused because that directory is inside a store, and that store holds what it held before.
- If the directory a backup would be restored in cannot be written, the restore is refused because a store can only be restored in a directory kb can write, naming the directory, and nothing is made in it.
- If what the operator restores is not a backup kb made, the restore is refused because it is not a backup, and nothing is made.
- If the backup was made by an earlier kb, the restore is refused because this kb cannot read a store an earlier kb made, and nothing is made.
- If the backup was made by a later kb, the restore is refused because a later version of kb is needed to read it, and nothing is made.
- If a restore is stopped before it finishes, however it was stopped, the directory has no store inside it, and the same restore run again restores the backup.
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

- The commands are `kb init <root> [--seed <dir>]`, `kb validate`, `kb serve <root> --listen <host:port> [--start]`, `kb backup <file>` and `kb restore <file> <root>`; the role for `kb init` and for a store `kb serve --start` starts comes from `KB_ACTOR`. `kb serve` hosts the store at `<root>/kb/` with `grpc.server`, the same servicer an in-process client reaches, and stamps each change with the server's own clock, the machine's. `kb export` and `kb import` are export-and-import-a-store.
- `kb backup <file>` writes the backup as one file.
- Backing up and restoring are the operator's commands only, not rpcs: the contract does not change for them.
- Reads never wait for the write lock (change-the-store).
- A module of its own, `staging.py`, owns a store started, and seeded, out of sight, then put in place whole: `kb init --seed` starts the store (`kb.init`) and imports the seed (the operator's import) under `<root>/.kb-starting/`, then moves `.kb-starting/kb` to `<root>/kb` with one `os.rename`, atomic because both lie on one filesystem. Whatever an earlier stopped run left in `.kb-starting/` is removed first. The staging directory is part of the store's files and layout, which may change, and is not published.
- `kb serve --start` with no store is `kb.init` and then serving, as `kb serve` serves today.
- A seed directory that is the root itself, or holds it, is read with kb's staging place passed over wherever the root lies inside it, as an import passes over a store's own files. A root kb cannot write is refused with rule `root`, naming the root, before anything is made, the way `kb.init` refuses a root it cannot start a store in.
- Getting a store out of a container whole is `kb backup` run inside it, its file carried out; `kb export` gives the readable copy. A store's files are never read through a bind mount owned by another user.
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
- An example compose file ships as `docker/compose.example.yaml` and is shown in the README: a `kb` service built from `https://github.com/dstengle/shopsystem-kb.git#v${KB_VERSION}`, the tag of the release of kb to build, which compose refuses to go without, with `KB_ACTOR` and a named volume `kb-store` at `/data`, and a caller with `KB_ROOT: /kb-connection`, the config `kb-connection` (`address: kb:50051`) mounted at `/kb-connection/kb/server.yaml`, depending on `kb` being healthy.
- The README gains "Running kb in Docker": the compose example, the seed step, the operator's commands, the empty-store trap (`up` before seeding starts an empty store, over which `kb init --seed` is refused; nothing is lost in an empty store, so `docker compose down -v` and seed again), and the bind mount's ownership.

## Not yet

- Publishing the image to GHCR from a release tag, and the repository's first CI workflow. Promoted when a caller needs kb's image without building it from the repository.
- Images for more than one architecture. Promoted when someone needs to run the image on a machine whose architecture it was not built for.
