---
id: capability/name-artifacts-and-items
title: Name artifacts and items
narrator: the client
rests_on: [decision/0022-ids-are-chosen-by-the-client-in-a-namespace, decision/0023-an-artifacts-iri-sits-under-its-types, decision/0031-a-create-may-name-its-parts, decision/iri-grammar, decision/removed-iris-may-be-reused, decision/rules-for-iri-refusals]
formulated_as: features/name-artifacts-and-items.feature
---

# Name artifacts and items

## Purpose

The client names every artifact it creates with an IRI: its type's IRI, a `/`, and a path of segments it chooses. The store checks that the IRI is well formed, that it sits under its type's IRI and that no other artifact holds it, and never makes one up. An artifact keeps its IRI for life; once it is removed, its IRI may be taken by a new artifact. The store names every item of a collection from its title, or from its position when its kind has no title, once, a clash settled with a number, unless the create that carries it gives it a name of its own. A part is named by its artifact's IRI and its place in it as a fragment. This capability does not rename anything, and it is not the grammar of an IRI asked for (name-what-is-asked-for).

## Behaviour

- When the client creates an artifact, giving it an IRI made of its type's IRI, a `/` and a path of its own choosing, the artifact is held at that IRI, and the store never makes one up for it.
- If the client creates an artifact with an IRI that does not sit under the IRI of its type, the artifact is refused because an artifact's IRI sits under its type's IRI, naming the IRI, and nothing is written.
- If the client creates an artifact at an IRI the store already holds an artifact at, the artifact is refused because an IRI names one artifact, naming the IRI, and the artifact already there is unchanged.
- An artifact keeps the IRI it was created with for life.
- When an artifact has been removed, the client may create a new artifact at its IRI, at its first revision.
- A part is named by its artifact's IRI, `#` and the part's place in it, such as `#steps/draft`.
- When the client creates an artifact giving one of its parts a name of its own choosing, the part holds that name.
- When the client creates an artifact giving a part no name, the part is named by the store from its title or its place, as an added item is.
- If the client creates an artifact giving two parts of one collection the same name, the artifact is refused because a part's name is unique in its collection, naming the name, and nothing is written.
- If the client creates an artifact giving a part a name that is not a plain name, the artifact is refused because a part's name is a plain name, naming the place, and nothing is written.
- When the client creates an artifact carrying two items with the same title in one collection, neither given a name, each item is given a name of its own, the second the name of the first with a number added.
- When a title has capitals and punctuation, the name is the title in lower case, each run of anything that is not a letter or a digit turned into a single hyphen, and no hyphen at either end.
- When an artifact's title reads as a date, the title reads back as the text written.
- When an artifact's title reads as yes, the title reads back as the text written.
- When an artifact's title is given as the yes-or-no true, the title reads back as the text "true".
- When an artifact's title is given as the number 12, the title reads back as the text "12".
- When the client adds an item with a title, the name it is given for the item is made from that title, and the client never says what it should be.
- When the client adds an item to a collection whose items carry no title, the name it is given is made from the item's place in the collection.
- If an added item's title gives a name already used in its collection, the new item is given that name with a number added, and the item already there keeps its name.
- When an item is taken out of a collection, every item left keeps the name it was given, and none is named again from where it now sits.
- When the items of a collection are put in a different order, every item keeps its name, and anything pointing at one of them still lands on it.
- When the client adds an item, its title becomes its name: read as text whatever it looks like, and refused if it leaves nothing to make a name from.
- When the client rewrites a collection, an item sent back with its name is that same item, keeping its name, and an item sent without one is new and is given a name of its own.
- If a rewritten collection holds an item whose name no item of that collection has, two items with the same name, or a name that is not a plain name, the change is refused naming which, and the artifact reads as before, at the revision it held.

## Implementation, may change

- An artifact's id is an IRI, `<type IRI>/<segment>/.../<segment>`, each segment of kb's grammar (name-what-is-asked-for); the client gives it on `Create` and each create of `BatchCreate`. kb mints no artifact id. The store keeps no files; the place an artifact takes in an export follows its IRI's path.
- An IRI not under its type's IRI, and an IRI already held, carry rule `identity`.
- An item's `id` is unique within its collection and first in its key order. A create may carry it for any part; otherwise kb mints it from the item's `title` when the item schema has one, else from its position, with the suffix `-2`, `-3` and so on on collision. A part's IRI is `<artifact IRI>#<place>`, the place written as today (`steps/draft`). `Add`'s and `Create`'s results, and each create's result in `BatchCreate`, return what was minted.
- Titles are coerced to text after YAML 1.2 parsing. Only `Create` carries a title.

## Not yet

- Changing an artifact's title. Promoted when a client needs to retitle an artifact.
