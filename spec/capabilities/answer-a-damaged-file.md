---
id: capability/answer-a-damaged-file
title: Answer a damaged file
narrator: the client
rests_on: [decision/damaged-database-one-fault, decision/0007-input-safety-at-the-boundary]
formulated_as: features/answer-a-damaged-file.feature
---

# Answer a damaged file

## Purpose

The store's one file, its database, never reaches a client or the operator as a crash when it is damaged behind the store's back or missing beside its marker. Every call that needs a store, and every command the operator runs against one, answers with the same named fault, naming the database, and writes nothing anywhere. Starting a store is not one of these: it never opens a database, and a directory whose store is damaged already has a store inside it (start-a-store). Damaged files on disk are found by the import check (export-and-import-a-store), not here.

## Behaviour

- If the store's database cannot be read, because it is damaged or missing beside its marker, then every call other than starting a store, and the operator's kb validate, kb serve, kb export and kb import, is refused because the database cannot be read, naming the database; the refusal is given as any other fault, never breaking off, nothing is served, and nothing is written, in the store or in a directory an export was aimed at, which stays as it was.

## Implementation, may change

- The fault's rule is `unreadable`. Every rpc runs inside one fail-closed wrapper that turns any escaping exception into a fault with nothing written; the command line reports the same fault.
- A database cannot be read when `kb/store.sqlite3` cannot be opened or read, or is absent while `kb/store.yaml` is present. Both cases are the same fault.
- `kb serve` opens the database when it is run and stops with the fault before it listens.

## Not yet

- None.
