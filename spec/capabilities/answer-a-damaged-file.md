---
id: capability/answer-a-damaged-file
title: Answer a damaged file
narrator: the client
rests_on: [decision/0007-input-safety-at-the-boundary]
formulated_as: features/answer-a-damaged-file.feature
---

# Answer a damaged file

## Purpose

A file damaged behind the store's back never reaches a client as a crash. Every call that meets it answers with the same named fault, naming the file, and writes nothing. That holds for an artifact, a type or a history entry. Reporting damage across the whole store is check-the-store.

## Behaviour

- If the client reads an artifact whose stored file cannot be read, the read is refused because that file cannot be read, naming the file, and the client is given that fault as any other, the call never breaking off.
- If the client replaces, adds an item to, removes, lists, searches, or follows the links into or out of an artifact whose stored file cannot be read, the call is refused because that file cannot be read, naming the file, the client is given that fault as any other, and nothing is written.
- If the client creates an artifact of a kind whose type's stored file cannot be read, the create is refused because that file cannot be read, naming the file, and nothing is written.
- If an entry of the store's history cannot be read, reading the history is refused because that file cannot be read, naming the file, and the client is given that fault as any other, the call never breaking off.

## Implementation, may change

- Loading returns either the artifact or a fault naming the file, and never raises. Every rpc runs inside one fail-closed wrapper that turns any escaping exception into a fault with nothing written.
- The fault's rule is `unreadable`.

## Not yet

- None.
