---
id: capability/hand-over-content
title: Hand over content
narrator: the client
rests_on: [decision/0005-content-as-canonical-text, decision/0007-input-safety-at-the-boundary, decision/sqlite-canonical, decision/yaml-is-export-and-wire, decision/one-method-per-action, decision/paired-escapes-are-one-character, decision/not-canonical-names-its-place]
formulated_as: features/hand-over-content.feature
---

# Hand over content

## Purpose

When the client creates, changes or adds, it hands the store content as text. The store reads that text one plain way and refuses anything it cannot take, naming the place. Content holds only what the type declares; what only the store settles (name, kind, revisions, title) travels beside it. This capability covers reading the text. Whether the content fits its type is check-a-change.

## Behaviour

- If content given to a create carries what only the store settles, such as a name or a revision for the artifact itself, the artifact is refused because content holds only what the type declares, naming each such entry.
- If content given to a create carries a title of its own as well as the title given alongside it, the artifact is refused because a title is given alongside the content, never inside it, naming the title the content carried.
- If content given to a change carries a revision of its own, the change is refused because content holds only what the type declares, naming that entry, and the artifact reads as before, at the revision it held.
- If an added item's content carries a name of its own, the item is refused because content holds only what the type declares, naming that entry, and the artifact holds the items it held before, at the revision it held.
- If content carries a tag on one of its values, it is refused because content is read plainly as written and carries no tags.
- If content holds more than one document, it is refused because content holds exactly one document.
- When content carries one field written "on" and another written "1:20", both read back as the text written, not as a yes or a no and not as a number.
- If content writes a value once and points back at it from another place, it is refused because nothing in content stands in for a value written somewhere else.
- If content opens by declaring the format it is written in, it is refused because content opens with no declaration of its format, naming the place the declaration stands.
- If content names the same entry twice in one place, it is refused because an entry is named once and only once, naming the place the second one stands.
- When content carries a field written "true", one left as nothing and one written "12.5", they read back as a yes-or-no, as nothing and as a number, and none as text.
- If content cannot be read as written, is not a set of named entries (a list, a single bare value, or nothing at all), or holds sections or collections of a shape the type does not declare, it is refused naming the reason and the place it went wrong, the call comes back with its answer rather than breaking off, and nothing is written.
- When content writes a character beyond the first 65,536 as two escapes, one for each half, as JSON does, the two halves read together as that one character, and the content reads back holding it.
- If content holds half of a character alone, with no other half beside it, it is refused because the content cannot be read as written.
- When content carries a field written as a bare date, it reads back as the text written, not as a date.
- If a line of prose ends in a space, so the store could not write it back as a block, the content is refused because every piece of prose is written as a block, naming the place, and nothing is written.

## Implementation, may change

- `content` is canonical YAML 1.2 text holding only fields, sections and parts; the identity keys (the id, the kind, `schema_version`, `revision` and `title`) are typed fields of the messages that carry an artifact, the kind's field named `kind`, never `type`. Clients parse content with any YAML parser.
- Content is parsed with a safe YAML 1.2 loader using the core schema: only `true`, `false`, `null`, integers and floats are typed. Tags, anchors, aliases, `%YAML` and `%TAG` directives, documents beyond the first, and duplicate keys are each a fault naming the place.
- One canonical checker runs on content after parsing and on the canonical text about to be stored or exported.
- `kb.content` publishes `loads`, `dumps`, `text` and `NotCanonical`, the refusal of text kb cannot keep.
- `NotCanonical` carries `path`: the place the refusal names, written as the names and list positions from the top of the content joined by `/` (`sections/0/body`), and empty when the refusal names no place. When `kb.content.dumps` refuses prose because a line of it ends in a space, its `NotCanonical` carries the place of that prose in `path`, as every other refusal with a place does.

## Not yet

- None.
