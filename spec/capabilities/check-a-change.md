---
id: capability/check-a-change
title: Check a change
narrator: the client
rests_on: [decision/0006-validation-from-composed-schema, decision/every-fault-at-once, decision/a-refused-write-changes-nothing, decision/stale-is-safe, decision/0011-sections-carry-no-links]
formulated_as: features/check-a-change.feature
---

# Check a change

## Purpose

Every create, change and added item is checked against the current version of its type and the store as it stands before anything lands. That covers the fields and their shapes, the shape of every section, required sections in order, and links that land. A refusal gives every fault at once and leaves the store as it was. An artifact behind its type is checked like any other. This capability is not the check of the whole store (check-the-store).

## Behaviour

- If an artifact is missing a section its type requires, the artifact is refused because the sections the type requires must all be present, in order.
- If an artifact points at something the store does not hold, the artifact is refused because a link must land on a node of a kind the type allows.
- If an artifact has several faults, it is refused with every one of them, each naming the artifact, the place in it and the rule broken, and the store is unchanged.
- If an artifact has faults found by different rules, such as a shape its type does not allow and a missing section, it is refused with all of them together, each naming the artifact, the place in it and the rule broken, and the store is unchanged.
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
- The write path: load, parsing files whose hash differs from the cache and rebuilding the reference index (both directions) and the search index; apply each operation to a copy of the touched artifact; validate each touched artifact (JSON Schema, then kb keywords with the graph in hand), collecting every error and stopping if any; bump `revision`, set `schema_version` to current, serialize canonically to a temp file and rename it into place; write one journal file per operation; `git add` every written file by name and make one commit; update the cache. There is no lock; several callers share a store through a server, which takes changes one at a time. The incremental cache lives beside the store, outside the repository, and is never committed.
- Faults are `{ artifact, path, rule, message }`; a fault for content that breaks a type's JSON Schema carries the keyword it breaks as its rule.

## Not yet

- None.
