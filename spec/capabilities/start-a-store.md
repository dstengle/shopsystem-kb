---
id: capability/start-a-store
title: Start a store
narrator: the client
rests_on: [decision/sqlite-canonical, decision/kb-runs-no-git, decision/init-refuses-inside-or-above, decision/types-are-data]
formulated_as: features/start-a-store.feature
---

# Start a store

## Purpose

The client starts a store in a directory it names. The store takes a place of its own inside that directory, holds only the type that describes types, and its history begins with that write. Starting a store is the one call that does not look for a store first. This capability is not the operator's `kb init` (operate-a-store), and it never teaches the store any domain.

## Behaviour

- When the client starts a store in a directory, saying which role it is, the store holds the one type that describes what a type is, no other type and no content, and the client can define its own types in it straight away.
- When the client starts a store, the store's history holds one entry, under the client's role, with the message "initialise store", which is the writing of the type that describes types at its first revision, with a fingerprint of what was written.
- Where the client was readied with a clock, when it starts a store, the store's one history entry says it happened at the moment the clock gives.
- If the client starts a store without saying which role it is, starting is refused because a store can only be started under a role, and the directory holds no store.
- When the client starts a store in a directory holding other files, the store is made inside that directory in a place of its own, and the files already there are left as they were.
- If the directory named already has a store inside it, starting is refused because that directory already has a store inside it, and that store holds what it held before.
- If the directory named sits inside a store, starting is refused because that directory is inside a store, and that store holds what it held before.
- While the client is working inside a store, when it starts a store in a directory elsewhere that sits inside no store, the store is made in the directory named and the store it was working in is left as it was.
- If the client names no directory, starting is refused because a store is started in a directory that was named and that exists, and no store is made anywhere.
- If the directory named does not exist, starting is refused because a store is started in a directory that exists, and nothing is made at that place.
- If what is named is a file rather than a directory, starting is refused because a store is started in a directory and what was named is not one, and the file is left as it was.
- If the place a store goes inside the named directory already holds an empty folder or a file, starting is refused because that directory already holds the place a store goes, and what was there is left as it was.
- While the client was readied where no store could be found and nothing named one, when it starts a store in a directory it names, the store is made there and the client can read and write in it straight away.

## Implementation, may change

- The store is `<root>/kb/`, marked by `<root>/kb/store.yaml`, which records the contract version; its data lives in `<root>/kb/store.sqlite3`, in WAL mode. Nothing else in `<root>` is the store's concern.
- Starting a store makes the directory, the marker and the database, and writes the type that describes types and the first history entry. No git repository is made.
- `Init` takes the root path and the actor, and returns nothing. The root is an absolute or relative path.
- The type that describes types (the metaschema) is shipped in kb's code and written as artifact `schema/schema`; its entry is the write of `schema/schema` at revision 1 with its digest.

## Not yet

- None.
