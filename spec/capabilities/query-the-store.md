---
id: capability/query-the-store
title: Query the store
narrator: the client
rests_on: [decision/typed-refs-cover-the-questions, decision/search-ranking, decision/0011-sections-carry-no-links, decision/storage-behind-a-port, decision/one-method-per-action]
formulated_as: features/query-the-store.feature
---

# Query the store

## Purpose

The client finds artifacts without knowing their names. It can list a kind, optionally narrowed by a field. It can follow links out of or into an artifact, or out of one place inside it, narrowed by link and kind and taken several steps. It can search prose and fields, ranked. Answers come back as stubs or names. This capability is not reading one artifact (read-an-artifact).

## Behaviour

- When the client lists a kind, it is given a stub of each artifact of that kind.
- When the client lists a kind narrowed by a field, it is given only the artifacts that match.
- When the client lists a kind asking for names only, it is given the names and nothing else.
- When the client follows the links out of an artifact, it is given a stub of each thing the artifact points at.
- When the client follows the links into an artifact, it is given a stub of each thing that points at it.
- When the client follows the links into an artifact only through one link and only from one kind, it is given only what points at it through that link from that kind.
- When the client follows the links out of an artifact two steps, it is given what is found at each step, each with the route taken to it.
- When the client follows the links out of one place inside an artifact, it is given a stub of what that place points at and nothing else the artifact points at.
- A link into a part of an artifact counts as a link into that artifact: following the links into the artifact finds what points at the part, reading the artifact at a glance counts it, and removing the artifact is refused while it points there.
- When the client searches the prose, each result comes with the title of the section it matched and a snippet of it, and the one whose section mentions the words most often comes first.
- When the client searches within one kind, it is given only artifacts of that kind.
- When the client searches the fields as well as the prose, it is also given artifacts whose fields, such as a title, match.
- If the client follows links out of a section, it is given nothing.

## Implementation, may change

- `List` takes a kind, field filters and an output form (`stubs` or `ids`), and returns matches.
- `Follow` (until v1 `Refs`) takes a locator, a direction, an optional via-field, an optional kind and a depth, and returns stubs with the route taken.
- `Search` takes text, an optional kind and a scope (`sections`, `fields`, `all`), and returns stubs with the matching section title and snippet, ranked by term frequency in the section.
- Each has a request and a response message of its own; a request or response names a kind as a kind, never a type, and a place inside an artifact as a place, never a path.
- The storage port answers reads: whether a name is held; an artifact now; names by kind with field filters; links in, narrowed by field and source kind; inbound counts; search, indexed per section and per field so results keep the section title and snippet; and the history. It has no traversal, no links-out read and no read of a past state; the queries above it do those. The adapter keeps the link index and the search rows as it writes. A section carries no links.

## Not yet

- None.
