---
id: capability/name-artifacts-and-items
title: Name artifacts and items
narrator: the client
rests_on: [decision/0002-ids-minted-from-titles]
formulated_as: features/name-artifacts-and-items.feature
---

# Name artifacts and items

## Purpose

The store gives every artifact and every item of a collection its name. The name comes from the title, or from the item's position when its kind has no title. It is made once and kept for life, and a clash is settled with a number. The client never chooses a name; it only hands back names the store gave. This capability does not rename anything: an artifact's name is fixed until migration exists, and its title is fixed once it is created.

## Behaviour

- When the client creates an artifact, the name it is given is made from the title, and the client never says what the name should be.
- If an artifact's title gives a name another artifact of its kind already has, the new artifact is given that name with a number added, and the artifact already there keeps its name.
- When the client creates an artifact carrying two items with the same title in one collection, each item is given a name of its own, the second the name of the first with a number added.
- When a title has capitals and punctuation, the name is the title in lower case, each run of anything that is not a letter or a digit turned into a single hyphen, and no hyphen at either end.
- If an artifact's title leaves nothing to make a name from, the artifact is refused because a title must leave something to make a name from.
- When an artifact's title reads as a date, the title reads back as the text written and the name is made from that text.
- When an artifact's title reads as yes, the title reads back as the text written and the name is made from that text.
- When an artifact's title is given as the yes-or-no true, the title reads back as the text "true" and the name is made from that text.
- When an artifact's title is given as the number 12, the title reads back as the text "12" and the name is made from that text.
- When the client adds an item with a title, the name it is given for the item is made from that title, and the client never says what it should be.
- When the client adds an item to a collection whose items carry no title, the name it is given is made from the item's place in the collection.
- If an added item's title gives a name already used in its collection, the new item is given that name with a number added, and the item already there keeps its name.
- When an item is taken out of a collection, every item left keeps the name it was given, and none is named again from where it now sits.
- When the items of a collection are put in a different order, every item keeps its name, and anything pointing at one of them still lands on it.
- When the client adds an item, its title becomes its name by the same rules as an artifact's: read as text whatever it looks like, and refused if it leaves nothing to make a name from.
- When the client rewrites a collection, an item sent back with its name is that same item, keeping its name, and an item sent without one is new and is given a name of its own.
- If a rewritten collection holds an item whose name no item of that collection has, two items with the same name, or a name that is not a plain name, the change is refused naming which, and the artifact reads as before, at the revision it held.
- When an artifact has been removed, a new artifact whose title gives the removed one's name takes that name with no number added, at its first revision.

## Implementation, may change

- An artifact's id is `<type>/<slug>`. The slug is the title lowercased, runs of anything outside `[a-z0-9]` replaced by one hyphen, hyphens trimmed. On collision kb appends `-2`, `-3` and so on. The file path derives from the id.
- An item's `id` is unique within its collection and first in its key order; it is minted from the item's `title` when the item schema has one, otherwise from its position, with the same suffix. `Add`'s and `Create`'s results, and each create's result in `CreateMany`, return what was minted.
- Titles are coerced to text after YAML 1.2 parsing. Only `Create` carries a title.

## Not yet

- Changing an artifact's name. Promoted when migration between type versions exists.
- Changing an artifact's title. Promoted when a client needs to retitle an artifact.
