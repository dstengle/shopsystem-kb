---
id: capability/change-the-store
title: Change the store
narrator: the client
rests_on: [decision/graph-as-records, decision/shared-parts-are-artifacts, decision/refuse-is-enough-for-deletes, decision/integrity-checked-both-ways, decision/a-refused-write-changes-nothing, decision/a-set-lands-in-one-transaction, decision/write-lock-and-expected-revision, decision/busy-rule, decision/clock-failure-rule, decision/0007-input-safety-at-the-boundary, decision/expected-revision, decision/one-method-per-action, decision/result-or-refusal]
formulated_as: features/change-the-store.feature
---

# Change the store

## Purpose

The client creates an artifact, replaces an artifact or one node inside it, adds an item to a collection, or removes an artifact. Each change comes back with what it produced: the name the store gave and the new revision. Only a whole artifact is removed. A removal, or a replacement that drops an item, is refused while anything points at what would go, the refusal handing back every link in the way. A replacement, an addition or a removal may say the revision the client read the artifact at, and is then refused if the artifact has moved since. Without one, it acts on the artifact as it stands. Clients on one machine changing one store at the same time, in one program or in several, each have their change checked against the store as the one before left it. A change that waits too long for another to finish is refused as busy and may be made again; a read is never refused as busy. A change that fails partway leaves the store as it was. This capability does not cover checking (check-a-change), naming (name-artifacts-and-items) or sets of changes (make-several-changes-in-one-go).

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
- If the clock fails during a change, the client is given a fault and the store holds what it held before.
- If the client removes a place inside an artifact, the removal is refused because only a whole artifact is removed.
- If the client replaces an artifact, or a node in it, so that an item something links into is no longer there, the change is refused because something still points at that item, and the client is given each such link.
- When the client replaces an artifact, adds an item to it or removes it, saying the revision it read the artifact at, and the artifact still stands at that revision, the change lands.
- If the client replaces an artifact, adds an item to it or removes it, saying the revision it read the artifact at, and the artifact stands at another revision when the change lands, the change is refused because the artifact moved since it was read, naming the revision it stands at, and nothing is written.
- When the client replaces an artifact, adds an item to it or removes it without saying the revision it read the artifact at, the change acts on the artifact as it stands.
- While several clients on one machine, in one program or in several, change one store at the same time, none saying the revision it read the artifact at, each change is checked against the store as every earlier change left it, so two items added to one collection at once are both kept.
- When one client removes an artifact while another adds a link to it, the removal and the new link never both land: whichever lands second is refused, the removal because something still points at it, or the link because a link must land on a node of a kind the type allows.
- When two clients replace one artifact at the same time, neither saying the revision it read the artifact at, each replacement leaves a revision of its own, both are in the history, and the artifact holds the content of the later one.
- If a change waits longer than the store waits while another change is being written, the change is refused because the store was busy with another change, nothing is written, and the same change may be made again.
- No read is refused because the store was busy with another change.

## Implementation, may change

- The changes are `Create`, `Replace`, `Add` and `Remove` (until v1 `Create`, `Write`, `Append`, `Delete`), each with a request and a response message of its own, named after it, and each carrying one `Signature`. `Create` takes a kind, a title and content, and returns the name and revision. `Replace` takes a locator and content, and returns the revision. `Add` takes the locator of a collection and the item's content, and returns the item's name and the revision. `Remove` takes a locator naming a whole artifact, and returns the revision; a removal blocked by links is a refusal whose faults name them.
- `Replace`, `Add` and `Remove` may carry an expected revision, the revision the client read the artifact at. A change that carries one, whose artifact stands at another revision when it lands, is the fault with rule `revision`, naming the revision the artifact stands at; `revision` is a published rule name.
- Every response is the call's result or a refusal holding every fault, never both.
- `revision` is an integer kb increments on every write; `schema_version` is set to the type's current version on every write.
- A delete is refused while there are inbound references to the artifact or anything beneath it; the only delete rule is `on_delete: refuse`. A part is taken out by rewriting its collection. Every refusal because something still points at what would go (a whole artifact, a dropped item, a type in use) carries the rule `on_delete` and names each link; the port's own name for it, `linked`, is not published.
- Every change, single or in a set, lands in one database transaction. SQLite's write lock serialises writers across threads and processes on one machine, and readers never wait. When the adapter finds a change's revision moved since kb read it (`conflict`, internal to the port), kb re-drafts a change that carries no expected revision against the new state and lands it, so its client never sees that fault; a change that carries one is refused with rule `revision`. Every rpc runs inside one fail-closed wrapper, so an exception a clock or the database raises becomes a fault.
- A clock that fails during a change gives a fault with rule `clock`, no artifact and no place.
- The store waits for the write lock for 30 seconds today. A change that waits longer is refused with rule `busy`, a published rule name.

## Not yet

- Delete rules other than refuse (cascade, detach). Promoted when operators need cascade or detach (decision/refuse-is-enough-for-deletes).
- A daemon. Promoted when changes wait at the server in growing numbers (decision/write-lock-and-expected-revision).
