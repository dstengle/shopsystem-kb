---
id: capability/make-several-changes-in-one-go
title: Make several changes in one go
narrator: the client
rests_on: [decision/0004-journal-batch-and-snapshots, decision/0013-empty-set-refused, decision/0016-empty-set-fault, decision/a-refused-write-changes-nothing, decision/a-set-is-checked-whole-links-and-types, decision/a-set-lands-in-one-transaction, decision/write-lock-on-one-machine]
formulated_as: features/make-several-changes-in-one-go.feature
---

# Make several changes in one go

## Purpose

The client asks for an ordered set of creates, replacements, additions and removals as one act. The store names the set, and each change still reports its own result and leaves its own history entry. Each change acts on the store as the changes before it in the set left it. What a change points at, and the type it is checked against, are judged against the store as the whole set leaves it, so changes in one set may point at each other. The set lands whole or not at all. This capability is not the individual changes themselves (change-the-store).

## Behaviour

- When the client asks for several changes in one go, saying which role and why, it is given one name for the set, which it never asked for, and each change's own result, and the store's history shows the set as one change.
- When the client reads the history under the name it was given for a set, it finds exactly that set's changes.
- If a change in a set does not fit its type, the set is refused because a change in it does not fit its type, the store holds none of its changes, and every fault in the set comes back, not only the first.
- If a set is stopped for any reason (a change names an artifact the store holds nothing under, or removes an artifact something still points at), the set is refused naming that reason, the store holds none of its changes, and the history holds no entry for any of them.
- If a set holds no changes at all, it is refused because a set must hold at least one change, the store holds no artifact it did not hold before, and the history holds no entry for it.
- When a set changes one artifact twice, the history holds an entry for each change with the revision it left, and the artifact's revision goes up by two.
- If a set holds no changes, the client is given no name for the set and no results.
- If a set holding no changes also lacks a role or a message, only the faults of the role and the message come back.
- When a change in a set points at what another change in it makes, earlier or later, its links are checked against the store as the whole set leaves it; each change still acts on the store as the changes before it in the set left it.
- When two new artifacts in one set point at each other, the set lands.

## Implementation, may change

- `Apply` takes an ordered list of Create/Write/Append/Delete, actor and message, and returns the batch id minted by kb and per-operation results; the set lands in one database transaction.
- The batch id is carried by every entry the set writes.
- An empty set is the fault with rule `operations`, no artifact and no path.

## Not yet

- None.
