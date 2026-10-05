---
id: capability/make-several-changes-in-one-go
title: Make several changes in one go
narrator: the client
rests_on: [decision/0004-journal-batch-and-snapshots, decision/0013-empty-set-refused, decision/0016-empty-set-fault, decision/a-refused-write-changes-nothing, decision/a-set-is-checked-whole-links-and-types, decision/a-set-lands-in-one-transaction, decision/write-lock-and-expected-revision, decision/busy-rule, decision/sets-one-kind-at-a-time, decision/references-inside-a-set, decision/expected-revision, decision/faults-ordered-by-reading-order-then-rule-name]
formulated_as: features/make-several-changes-in-one-go.feature
---

# Make several changes in one go

## Purpose

The client asks for an ordered set of changes of one kind (creates, replacements, additions or removals) as one act. The store names the set, and each change still reports its own result and leaves its own history entry. Each change acts on the store as the changes before it in the set left it. What a change points at, and the type it is checked against, are judged against the store as the whole set leaves it. New artifacts in one set point at each other by keys the client gives their creates. The set lands whole or not at all. This capability is not the individual changes themselves (change-the-store).

## Behaviour

- A set holds changes of one kind only, creates, replacements, additions of items or removals, so a client that needs a create and a replacement makes two calls.
- When the client asks for several changes in one go, saying which role and why, it is given one name for the set, which it never asked for, and each change's own result, and the store's history shows the set as one change.
- When the client reads the history under the name it was given for a set, it finds exactly that set's changes.
- If a change in a set does not fit its type, the set is refused because a change in it does not fit its type, the store holds none of its changes, and every fault in the set comes back, not only the first.
- If a change in a set is refused with several faults, that change's faults are given in the order its places stand in its artifact as it would read back, which is the order its type declares, a collection's items in their order, sections in their order and a section's inner sections after it, and faults at one place come in the alphabetical order of the names of the rules they break.
- If several changes in a set are refused, their faults are given in the order of the set.
- If a set is stopped for any reason (a change names an artifact the store holds nothing under, or removes an artifact something still points at), the set is refused naming that reason, the store holds none of its changes, and the history holds no entry for any of them.
- If a set holds no changes at all, it is refused because a set must hold at least one change, the store holds no artifact it did not hold before, and the history holds no entry for it.
- When a set changes one artifact twice, the history holds an entry for each change with the revision it left, and the artifact's revision goes up by two.
- If a set holds no changes, the client is given no name for the set and no results.
- If a set holding no changes also lacks a role or a message, only the faults of the role and the message come back.
- When a create in a set points at what another create in it makes, earlier or later, its links are checked against the store as the whole set leaves it; each change still acts on the store as the changes before it in the set left it.
- When the client creates several artifacts in one go, giving a create a key of its own choosing, a link anywhere in the set that refers to that key points at the artifact that create makes, and holds the name the store gave that artifact.
- When two new artifacts in one set point at each other, each by the key the other's create carries, the set lands.
- When the client creates several artifacts in one go, each create's result gives the name it was given, in the order of the set.
- If a link in a set refers to a key no create in the set carries, the set is refused because the link lands on nothing, naming the key, and the store holds none of its changes.
- If two creates in one set carry the same key, the set is refused because a key names one create in the set, naming the key, and the store holds none of its changes.
- If a link in a set refers to a key together with a place inside the artifact that create makes, the set is refused because the link lands on nothing, naming the reference, and the store holds none of its changes.
- If a replacement, an addition or a removal in a set says the revision the client read its artifact at, and the artifact stands at another revision when the set lands, the set is refused because the artifact moved since it was read, naming the revision it stands at, and nothing of the set is written.
- When a set changes one artifact twice and the second change says the revision the client read the artifact at, that revision is compared with the one the change before it in the set left.
- If a set waits longer than the store waits while another change is being written, the set is refused because the store was busy with another change, nothing is written, and the same set may be asked for again.

## Implementation, may change

- `Apply` and its four operation messages are gone. `BatchCreate`, `BatchReplace`, `BatchAdd` and `BatchRemove` each take an ordered list of one kind of change and one `Signature`, each with a request and a response message of its own, and return the set's name, minted by kb, and each change's own result in the order of the set; the set lands in one database transaction.
- A create in `BatchCreate` may carry a key, unique in the set. A link written as `@` followed by a key names the artifact that create makes; kb puts the name it mints in its place before anything is checked. A reference names a whole artifact, never a part.
- A key no create carries, a key carried twice and a key with a place are faults with rule `ref`.
- A replacement, an addition or a removal in a set may carry an expected revision; a mismatch is the fault with rule `revision` (change-the-store).
- The set's name is carried by every entry the set writes.
- An empty set is the fault with rule `operations`, no artifact and no place.
- A set refused as busy is the fault with rule `busy` (change-the-store).

## Not yet

- None.
