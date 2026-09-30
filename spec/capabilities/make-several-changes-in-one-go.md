---
id: capability/make-several-changes-in-one-go
title: Make several changes in one go
narrator: the client
rests_on: [decision/0004-journal-batch-and-snapshots, decision/0013-empty-set-refused, decision/0016-empty-set-fault, decision/a-refused-write-changes-nothing, decision/scale]
formulated_as: features/make-several-changes-in-one-go.feature
---

# Make several changes in one go

## Purpose

The client asks for an ordered set of creates, replacements, additions and removals as one act. The store names the set, and each change still reports its own result and leaves its own history entry. The set lands whole or not at all. This capability is not the individual changes themselves (change-the-store).

## Behaviour

- When the client asks for several changes in one go, saying which role and why, it is given one name for the set, which it never asked for, and each change's own result, and the store's history shows the set as one change.
- When the client reads the history under the name it was given for a set, it finds exactly that set's changes.
- If a change in a set does not fit its type, the set is refused because a change in it does not fit its type, the store holds none of its changes, and every fault in the set comes back, not only the first.
- If a set is stopped for any reason (a change names an artifact the store holds nothing under, removes an artifact something still points at, or touches an artifact whose stored file cannot be read), the set is refused naming that reason, the store holds none of its changes, and the history holds no entry for any of them.
- If a set holds no changes at all, it is refused because a set must hold at least one change, the store holds no artifact it did not hold before, and the history holds no entry for it.
- When a set changes one artifact twice, the history holds an entry for each change with the revision it left, and the artifact's revision goes up by two.

## Implementation, may change

- `Apply` takes an ordered list of Create/Write/Append/Delete, actor and message, and returns the batch id minted by kb, per-operation results, and one commit.
- The batch id is carried by every entry the set writes.
- An empty set is the fault with rule `operations`.

## Not yet

- None.
