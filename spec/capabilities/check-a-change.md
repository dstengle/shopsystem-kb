---
id: capability/check-a-change
title: Check a change
narrator: the client
rests_on: [decision/0006-validation-from-composed-schema, decision/every-fault-at-once, decision/a-refused-write-changes-nothing, decision/stale-is-safe, decision/0011-sections-carry-no-links, decision/storage-behind-a-port, decision/integrity-checked-both-ways, decision/write-lock-and-expected-revision, decision/faults-ordered-by-reading-order-then-rule-name]
formulated_as: features/check-a-change.feature
---

# Check a change

## Purpose

Every create, change and added item is checked against the current version of its type and the store as it stands before anything lands. That covers the fields and their shapes, the shape of every section, required sections in order, links that land, and links into what the change drops. A refusal gives every fault at once, in an order kb decides, and leaves the store as it was. An artifact behind its type is checked like any other. This capability is not the check of the whole store (check-the-store).

## Behaviour

- If an artifact is missing a section its type requires, the artifact is refused because the sections the type requires must all be present, in order.
- If an artifact points at something the store does not hold, the artifact is refused because a link must land on a node of a kind the type allows.
- If an artifact has several faults, it is refused with every one of them, each naming the artifact, the place in it and the rule broken, and the store is unchanged.
- If an artifact has faults found by different rules, such as a shape its type does not allow and a missing section, it is refused with all of them together, each naming the artifact, the place in it and the rule broken, and the store is unchanged.
- If an artifact is refused with several faults, they are given in the order its places stand in the artifact as it would read back, which is the order its type declares, a collection's items in their order, sections in their order and a section's inner sections after it, and faults at one place come in the alphabetical order of the names of the rules they break.
- If a section carries anything besides its title, its body and the sections inside it, the artifact is refused because a section holds exactly those, naming the extra entry.
- If a section carries a body and no title, the artifact is refused because a section carries both a title and a body, as anything else that does not fit its type is.
- If a section carries a title and no body, the artifact is refused because a section carries both a title and a body, as anything else that does not fit its type is.
- When a section's body is empty, the artifact is accepted and the section reads back with an empty body.
- While an artifact is behind its type, when the client changes it with content that fits the current version, it records the current version of its type and is no longer listed as behind it.
- If the client changes an artifact that is behind its type with content that does not fit the current version, the change is refused because the content does not fit the current version, like any change that does not fit; the artifact reads as before at the revision it held, and it is still listed as behind its type.
- If a change would leave an artifact missing a section its type requires, the change is refused because the sections the type requires must all be present, in order, and the artifact reads as before, at the revision it held.
- If an added item points at something the store does not hold, the item is refused because a link must land on a node of a kind the type allows, and the artifact holds the items it held before, at the revision it held.
- If an added item is missing something its own type requires, the item is refused because the content does not fit the type, and the artifact holds the items it held before, at the revision it held.
- Where a type requires sections, an artifact may carry further sections after the required ones, at any level.

## Implementation, may change

- A section is a `title`, a markdown `body` and an ordered list of child `sections`, and nothing else.
- kb's own structural rules (the section tree, items carrying an `id`, the identity keys) are JSON Schema fragments composed with the type's schema into one effective schema per artifact, checked by the standard validator in one pass. Code checks only what the schema language cannot express: a reference resolving to a node of a permitted type, required sections in their declared order, and id uniqueness in a collection.
- The write path: kb applies each operation to an in-memory draft and checks the draft's content against JSON Schema and kb's keywords, collecting every error and stopping if any; it then hands the set to the storage port in one call, `land(changes, entries, relinks, kinds)`, the signature riding in the entries. Each change carries the operation, the artifact's id, its whole content after the change (none for a removal), its links as kb derives them from the type (field, place in the artifact, target artifact and part, and the kinds the field allows, which are the field's targets as written), the parts it holds by place, the revision it was read at, and the revisions of the types it was read through. The journal entries ride with the set.
- A relink restates the links of an artifact the set leaves as it is, with the revisions of the types it was read through; the set names the kinds whose every artifact it restates.
- Inside one write transaction the adapter takes the write lock, compares each revision and refuses `conflict` on a mismatch, writes each change and then, inside the same savepoint, checks every link lands on an artifact or part of an allowed kind and refuses `linked` when anything outside the set links into an artifact or part the set removes, taking the set back on a refusal. It re-checks integrity inside the transaction, so a concurrent change cannot slip between the check and the write. The adapter keeps the link index, the search rows and the history as it writes.
- `conflict` and `linked` are the port's internal names and are never published. On `conflict`, kb re-drafts a change that carries no expected revision against the new state and lands it, so its client never sees it, and refuses one that carries an expected revision with rule `revision` (change-the-store); `linked` reaches the client as a fault with rule `on_delete`, naming each link.
- Every artifact carries one implicit link to its type artifact (`schema/<kind>`), so removing a type still in use is refused by the same rule; the adapter knows nothing of kinds.
- The port is a kb-internal Python interface, not published. Above it, unchanged: names, content checks, sections and items, signatures, faults, the contract. `store.py` keeps discovery and the marker; `port.py` holds the interface and `sqlite_store.py` the SQLite adapter; `journal.py` keeps entry naming and fingerprints but writes no files; the git code is gone.
- Faults are `{ artifact, place, rule, message }`; a fault for content that breaks a type's JSON Schema carries the keyword it breaks as its rule.
- Faults are put in kb's order before they are returned: places in the order the artifact reads back in (the order its type declares, which is the order the store writes it in), then rule names alphabetically; the order the library finds them in is not kept, and neither is the order the client wrote the artifact in.

## Not yet

- A second storage adapter. Promoted when a workload needs queries the port cannot answer within its bounds, such as transitive or pattern queries over transcripts and work state.
