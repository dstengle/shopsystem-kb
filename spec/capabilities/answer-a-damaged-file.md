---
id: capability/answer-a-damaged-file
title: Answer a damaged file
narrator: the client
rests_on: [decision/damaged-database-one-fault, decision/0007-input-safety-at-the-boundary]
formulated_as: features/answer-a-damaged-file.feature
---

# Answer a damaged file

## Purpose

The store's one file, its database, damaged behind the store's back, never reaches a client or the operator as a crash. Every call and every command of the command line that meets a database it cannot open or read answers with the same named fault, naming the database, and writes nothing. Damaged files on disk are found by the import check (export-and-import-a-store), not here.

## Behaviour

- If the store's database cannot be opened or read, every call and every command of the command line is refused because the database cannot be read, naming the database, the refusal is given as any other fault, never breaking off, and nothing is written.

## Implementation, may change

- The fault's rule is `unreadable`. Every rpc runs inside one fail-closed wrapper that turns any escaping exception into a fault with nothing written; the command line reports the same fault.

## Not yet

- None.
