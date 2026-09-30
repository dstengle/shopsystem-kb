---
id: capability/change-the-store
title: Change the store
narrator: the client
rests_on: [decision/graph-as-documents, decision/shared-parts-are-artifacts, decision/refuse-is-enough-for-deletes, decision/a-refused-write-changes-nothing, decision/restore-on-commit-failure]
formulated_as: features/change-the-store.feature
---

# Change the store

## Purpose

The client creates an artifact, replaces an artifact or one node inside it, adds an item to a collection, or removes an artifact. Each change comes back with what it produced: the name the store gave and the new revision. A removal is refused while anything points at the artifact, and the refusal hands back every link in the way. This capability does not cover checking (check-a-change), naming (name-artifacts-and-items) or sets of changes (make-several-changes-in-one-go).

## Behaviour

- When the client creates an artifact with a title and content, saying which role and why, it is given the name the artifact keeps for life and its first revision; the artifact records the version of its type it was checked against, and reads back as written, in the order the type declares.
- If the client creates an artifact without a title, the artifact is refused because an artifact cannot be created without a title.
- When the client replaces an artifact, saying which role and why, its revision goes up by one and it records the current version of its type.
- When the client replaces one node inside an artifact, only that node changes and the rest of the artifact reads as before.
- When the client replaces one item of a collection, only that item changes, it keeps the name it was given when it was created, and anything pointing at it still lands on it.
- When the client adds an item to a collection, it is given the new item's name and the artifact's new revision, and the new item comes after the items already there.
- When the client adds an item that points at a shared artifact together with its settings, the settings are held by the new item and the shared artifact is unchanged.
- When the client adds an item to a collection inside an item, it is given the new item's name and the artifact's new revision, and the rest of the artifact is unchanged.
- When the client removes an artifact nothing points at, the store no longer holds it and the removal is recorded in the history like any other change.
- If something points at the artifact being removed, the removal is refused because something still points at it, and the client is given every link that blocks it.
- If an item inside another artifact points at the artifact being removed, the removal is refused because something still points at it, and that link is among the links given.
- If recording a change in the store's history fails, the client is given a fault and the store holds what it held before.

## Implementation, may change

- `Create` takes type, title, content, actor and message, and returns id and revision. `Write` takes a locator, content, actor and message, and returns revision. `Append` takes the locator of a collection, item content, actor and message, and returns item id and revision. `Delete` takes a locator, actor and message, and returns revision, or the list of inbound references that block it.
- `revision` is an integer kb increments on every write; `schema_version` is set to the type's current version on every write.
- A delete is refused while there are inbound references to the node or anything beneath it; the only delete rule is `on_delete: refuse`.
- On a git failure, kb restores the written files from HEAD and reports the failure. Per-file writes are atomic through rename.

## Not yet

- Delete rules other than refuse (cascade, detach). Promoted when operators need cascade or detach (decision/refuse-is-enough-for-deletes).
- A daemon. Promoted when the lock queue grows (decision/scale).
