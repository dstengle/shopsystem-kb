---
id: capability/answer-a-damaged-file
title: Answer a damaged file
narrator: the client
rests_on: [decision/damaged-database-one-fault, decision/read-only-store-unreadable, decision/earlier-store-told-apart, decision/0007-input-safety-at-the-boundary]
formulated_as: features/answer-a-damaged-file.feature
---

# Answer a damaged file

## Purpose

A store this kb cannot read never reaches a client or the operator as a crash. That covers four cases: its one file, the database, is damaged behind the store's back, is missing beside its marker, or cannot be opened for writing because it sits on a read-only filesystem; or the store was made by an earlier kb in a form this kb cannot read. Every call that needs a store, and the operator's commands that read or write one, answer with a named fault and write nothing anywhere. For a store made by an earlier kb, the fault says how to move it: its files are imported into a new store. Starting a store is not one of these: it never opens a database, and a directory whose store is damaged already has a store inside it (start-a-store). Damaged files on disk are found by the import check (export-and-import-a-store), not here. Reading a store on a read-only filesystem is not supported.

## Behaviour

- If the store's database cannot be read, because it is damaged or missing beside its marker, then every call other than starting a store, and the operator's kb validate, kb export and kb import, is refused because the database cannot be read, naming the database; the refusal is given as any other fault, never breaking off, and nothing is written, in the store or in a directory an export was aimed at, which stays as it was.
- If the store's database cannot be opened for writing, because the directory, the file or the mount it is on is read-only, then every call other than starting a store, and the operator's kb validate, kb export and kb import, is refused because the database cannot be read, naming the database; the refusal is given as any other fault, never breaking off, and nothing is written, in the store or in a directory an export was aimed at, which stays as it was.
- If the store found was made by an earlier kb, in a form this kb cannot read, then every call other than starting a store, and the operator's kb validate, kb export and kb import, is refused because the store was made by an earlier version of kb, saying how to move it: start a new store and import the old one's files; nothing is written.

## Implementation, may change

- Each of these faults carries rule `unreadable`. Every rpc runs inside one fail-closed wrapper that turns any escaping exception into a fault with nothing written; the command line reports the same fault.
- A database cannot be read when `kb/store.sqlite3` cannot be opened or read, or is absent beside a marker this kb wrote. Both cases are the same fault.
- Stores started by this kb carry a new marker value. A store made by kb 0.3.0 carries the old one (`contract: "0.1"`) with no database beside it, and is answered as an earlier kb's store, not as a missing database.
- A store is found the same way whether it is an earlier kb's or not, upward from the working directory or where `KB_ROOT` names it (find-the-store); the refusal follows the finding.

## Not yet

- kb serve refusing to serve a store whose database cannot be read, nothing served. Promoted when the served-store lines (reach-a-served-store, operate-a-store's kb serve lines) are formulated and built.
- Reading a store on a read-only filesystem. Promoted when what a read-only store means is defined: whether it may be read while nothing may change it, what its history says, how a served store relates to it.
