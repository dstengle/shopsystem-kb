---
id: capability/check-a-change
title: Check a change
narrator: the client
rests_on: [decision/0006-validation-from-composed-schema, decision/every-fault-at-once, decision/a-refused-write-changes-nothing, decision/stale-is-safe, decision/0011-sections-carry-no-links, decision/storage-behind-a-port, decision/integrity-checked-both-ways, decision/write-lock-and-expected-revision, decision/faults-ordered-by-reading-order-then-rule-name, decision/0024-a-link-may-land-on-a-placeholder, decision/0027-each-type-version-is-its-own-iri, decision/an-artifact-keeps-its-version, decision/links-into-parts-of-placeholders, decision/a-link-that-waits-keeps-waiting]
formulated_as: features/check-a-change.feature
---

# Check a change

## Purpose

Every create, change and added item is checked against a version of its type and the store as it stands before anything lands: a create, or a replacement naming a later version, against the version it names, and any other change against the version its artifact conforms to. That covers the fields and their shapes, the shape of every section, required sections in order, links that land, and links into what the change drops. A link to an IRI the store does not hold, or into a part of one, under a type it holds, lands on a placeholder, which an artifact created at that IRI later fills. A refusal gives every fault at once, in an order kb decides, and leaves the store as it was. An artifact behind its type is checked like any other. This capability is not the check of the whole store (check-the-store).

## Behaviour

- When the client creates an artifact naming a version of its type, the artifact is checked against that version.
- If an artifact is missing a section its type requires, the artifact is refused because the sections the type requires must all be present, in order.
- If an artifact points at an IRI under a type the store does not hold, the artifact is refused because a link must land on a node of a kind the type allows.
- When an artifact points at an IRI the store does not hold, under a type the store holds that the link field allows, the artifact is accepted and the link lands on a placeholder at that IRI.
- When an artifact points into a part of an IRI the store does not hold, under a type the store holds that the link field allows, the artifact is accepted and the link lands on a placeholder.
- If an artifact points into a part an artifact the store holds does not have, the artifact is refused because a link must land on a node of a kind the type allows.
- If an artifact points at an IRI the store does not hold, under a type the store holds that the link field does not allow, the artifact is refused because a link must land on a node of a kind the type allows.
- When the client creates an artifact at an IRI that links already point at, those links land on the new artifact, and the IRI is no longer a placeholder.
- When the client creates an artifact at an IRI a link points into a part of, and the new artifact has no such part, that link stays on a placeholder and is listed as any placeholder is.
- When the client changes an artifact that holds a link waiting on a part its target does not have, and the change leaves that link as it is, the change is accepted and the link still waits; a link the change adds or alters is checked as any new link is.
- If an artifact has several faults, it is refused with every one of them, each naming the artifact, the place in it and the rule broken, and the store is unchanged.
- If an artifact has faults found by different rules, such as a shape its type does not allow and a missing section, it is refused with all of them together, each naming the artifact, the place in it and the rule broken, and the store is unchanged.
- If an artifact is refused with several faults, they are given in the order its places stand in the artifact as it would read back, which is the order its type declares, a collection's items in their order, sections in their order and a section's inner sections after it, and faults at one place come in the alphabetical order of the names of the rules they break.
- If a section carries anything besides its title, its body and the sections inside it, the artifact is refused because a section holds exactly those, naming the extra entry.
- If a section carries a body and no title, the artifact is refused because a section carries both a title and a body, as anything else that does not fit its type is.
- If a section carries a title and no body, the artifact is refused because a section carries both a title and a body, as anything else that does not fit its type is.
- When a section's body is empty, the artifact is accepted and the section reads back with an empty body.
- While an artifact is behind its type, when the client changes it naming no version, it is checked against the version it conforms to and is still listed as behind its type.
- While an artifact is behind its type, when the client changes it naming the latest version of its type with content that fits that version, it records that version and is no longer listed as behind it.
- If the client changes an artifact that is behind its type naming a later version with content that does not fit that version, the change is refused because the content does not fit the version it names, like any change that does not fit; the artifact reads as before at the revision it held, and it is still listed as behind its type.
- If a change would leave an artifact missing a section its type requires, the change is refused because the sections the type requires must all be present, in order, and the artifact reads as before, at the revision it held.
- If an added item points at an IRI under a type the store does not hold, the item is refused because a link must land on a node of a kind the type allows, and the artifact holds the items it held before, at the revision it held.
- If an added item is missing something its own type requires, the item is refused because the content does not fit the type, and the artifact holds the items it held before, at the revision it held.
- Where a type requires sections, an artifact may carry further sections after the required ones, at any level.

## Implementation, may change

- A section is a `title`, a markdown `body` and an ordered list of child `sections`, and nothing else.
- kb's own structural rules (the section tree, items carrying an `id`, the identity keys) are JSON Schema fragments composed with the type version's schema into one effective schema per artifact, checked by the standard validator in one pass. Code checks only what the schema language cannot express: a reference resolving to a node of a permitted type, or to an IRI not held under a permitted type, required sections in their declared order, and id uniqueness in a collection.
- A placeholder is not stored: it is an IRI linked to and not held. A link's target is kept as the IRI it names, whether or not anything is held there, and an artifact created at that IRI is what the link lands on from then.
- The write path: kb applies each operation to an in-memory draft and checks the draft's content against JSON Schema and kb's keywords, collecting every error and stopping if any; it then hands the set to the storage port in one call, `land(changes, entries)`, the signature riding in the entries. Each change carries the operation, the artifact's IRI, its whole content after the change (none for a removal), its links as kb derives them from the type (field, place in the artifact, target IRI and part, and the types the field allows, which are the field's targets as written), the parts it holds by place, the revision it was read at, and the revisions of the types it was read through. The journal entries ride with the set.
- A set restates no links of an artifact it leaves as it is: an artifact's links change only when a write changes that artifact, and a change to a type makes a version with it, which rides on that change (decision/an-artifact-is-read-through-its-version).
- Inside one write transaction the adapter takes the write lock, compares each revision and refuses `conflict` on a mismatch, writes each change and then, inside the same savepoint, checks every link lands on an artifact or part of an allowed type, or on an IRI not held under an allowed type, and refuses `linked` when anything outside the set links into an artifact or part the set removes, taking the set back on a refusal. It re-checks integrity inside the transaction, so a concurrent change cannot slip between the check and the write. The adapter keeps the link index, the search rows and the history as it writes.
- `conflict` and `linked` are the port's internal names and are never published. On `conflict`, kb re-drafts a change that carries no expected revision against the new state and lands it, so its client never sees it, and refuses one that carries an expected revision with rule `revision` (change-the-store); `linked` reaches the client as a fault with rule `on_delete`, naming each link.
- Every artifact carries one implicit link to the type version it conforms to, so removing a type still in use is refused by the same rule; the adapter knows nothing of types.
- The port is a kb-internal Python interface, not published. Above it, unchanged: names, content checks, sections and items, signatures, faults, the contract. `store.py` keeps discovery and the marker; `port.py` holds the interface and `sqlite_store.py` the SQLite adapter; `journal.py` keeps entry naming and fingerprints but writes no files; the git code is gone.
- Faults are `{ artifact, place, rule, message }`; a fault for content that breaks a type's JSON Schema carries the keyword it breaks as its rule.
- Faults are put in kb's order before they are returned: places in the order the artifact reads back in (the order its type declares, which is the order the store writes it in), then rule names alphabetically; the order the library finds them in is not kept, and neither is the order the client wrote the artifact in.

## Not yet

- A second storage adapter. Promoted when a workload needs queries the port cannot answer within its bounds, such as transitive or pattern queries over transcripts and work state.
