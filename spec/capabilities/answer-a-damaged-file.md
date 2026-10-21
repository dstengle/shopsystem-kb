---
id: capability/missingmass.io/shopsystem/kb/answer-a-damaged-file
title: Answer a damaged file
narrator: the client
rests_on: [design-decision/missingmass.io/shopsystem/kb/damaged-database-one-fault, design-decision/missingmass.io/shopsystem/kb/read-only-store-unreadable, design-decision/missingmass.io/shopsystem/kb/earlier-store-told-apart, design-decision/missingmass.io/shopsystem/kb/later-store-told-apart, design-decision/missingmass.io/shopsystem/kb/input-safety-at-the-boundary, design-decision/missingmass.io/shopsystem/kb/pre-v2-stores-not-migrated, design-decision/missingmass.io/shopsystem/kb/v1-store-cannot-be-moved]
retired: []
---

# Answer a damaged file

## Purpose

A store this kb cannot read never reaches a client or the operator as a crash. That covers five cases: its one file, the database, is damaged behind the store's back, is missing beside its marker, or cannot be opened for writing because it sits on a read-only filesystem; the store was made by a kb before contract v2, in a form this kb cannot read; or the store was made by a later kb, in a form this kb does not know. Every call that needs a store, and the operator's commands that read or write one, answer with a named fault and write nothing anywhere. For a store made by a kb before contract v2, the fault says this kb can neither read nor move it. For a store made by a later kb, the fault says a later version of kb is needed to read it. Starting a store is not one of these: it never opens a database, and a directory whose store is damaged already has a store inside it (start-a-store). Damaged files on disk are found by the import check (export-and-import-a-store), not here. Reading a store on a read-only filesystem is not supported.

## Behaviour

- [r1] If the store's database cannot be read, because it is damaged or missing beside its marker, then every call other than starting a store, and the operator's kb validate, kb export and kb import, is refused because the database cannot be read, naming the database; the refusal is given as any other fault, never breaking off, and nothing is written, in the store or in a directory an export was aimed at, which stays as it was.
- [r2] If the store's database cannot be opened for writing, because the directory, the file or the mount it is on is read-only, then every call other than starting a store, and the operator's kb validate, kb export and kb import, is refused because the database cannot be read, naming the database; the refusal is given as any other fault, never breaking off, and nothing is written, in the store or in a directory an export was aimed at, which stays as it was.
- [r3] If the store found was made by a kb before contract v2, then every call other than starting a store, and the operator's kb validate, kb export and kb import, is refused because the store was made by an earlier version of kb, which this kb cannot read or move; nothing is written.
- [r4] If the store found has a marker naming a form of store this kb does not know, one a later kb made, then every call other than starting a store, and the operator's kb validate, kb export and kb import, is refused because the store was made by a later version of kb, which is needed to read it; the store is not opened and nothing is written.
- [r5] If the store found has a marker that cannot be read at all, whatever its bytes, then every call other than starting a store, and the operator's kb validate, kb export and kb import, is refused because the store was made by a later version of kb, which is needed to read it, as for a form this kb does not know; the refusal is given as any other fault, never breaking off, and nothing is written.
- [r6] If the operator runs kb serve on a store whose database cannot be read, it is refused because the database cannot be read, naming the database, and nothing is served.

## Implementation, may change

- Each of these faults carries rule `unreadable`, a later kb's store included, as for an earlier kb's. Every rpc runs inside one fail-closed wrapper that turns any escaping exception into a fault with nothing written; the command line reports the same fault.
- A database cannot be read when `kb/store.sqlite3` cannot be opened or read, or is absent beside a marker this kb wrote. Both cases are the same fault.
- Stores started by this kb carry a new marker value. A store made by kb 0.3.0 carries the old one (`contract: "0.1"`) with no database beside it, and is answered as an earlier kb's store, not as a missing database.
- A store made by a kb of contract `kb.v1` carries that kb's marker value and is answered as an earlier kb's store; no migration is built for it.
- The marker says which form of store it marks; a form this kb does not know, and a marker that cannot be read, are answered as a later kb's store.
- A store is found the same way whether it is an earlier kb's or not, upward from the working directory or where `KB_ROOT` names it (find-the-store); the refusal follows the finding.

## Not yet

- Reading a store on a read-only filesystem. Promoted when what a read-only store means is defined: whether it may be read while nothing may change it, what its history says, how a served store relates to it.
