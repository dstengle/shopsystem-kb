---
id: capability/missingmass.io/shopsystem/kb/query-the-store
title: Query the store
narrator: the client
rests_on: [design-decision/missingmass.io/shopsystem/kb/typed-refs-cover-the-questions, design-decision/missingmass.io/shopsystem/kb/search-ranking, design-decision/missingmass.io/shopsystem/kb/sections-carry-no-links, design-decision/missingmass.io/shopsystem/kb/storage-behind-a-port, design-decision/missingmass.io/shopsystem/kb/one-method-per-action, design-decision/missingmass.io/shopsystem/kb/an-artifacts-iri-sits-under-its-types, design-decision/missingmass.io/shopsystem/kb/a-link-may-land-on-a-placeholder, design-decision/missingmass.io/shopsystem/kb/path-selection-is-a-segment-prefix]
retired: []
---

# Query the store

## Purpose

The client finds artifacts without knowing their names. It can list a kind, optionally narrowed by a field, or list by the path below the type across types. It can follow links out of or into an artifact, or out of one place inside it, narrowed by link, by kind or by the path below the type, and taken several steps. It can list every placeholder with what links to it. It can search prose and fields, ranked. Answers come back as stubs or names. This capability is not reading one artifact (read-an-artifact).

## Behaviour

- [r1] When the client lists a kind, it is given a stub of each artifact of that kind.
- [r2] When the client lists a kind narrowed by a field, it is given only the artifacts that match.
- [r3] When the client lists a kind asking for names only, it is given the names and nothing else.
- [r4] When the client lists by a path below the type, it is given a stub of each artifact whose IRI's path below its type's IRI begins with the segments given, whole segments only, whatever its type.
- [r5] When the client follows links narrowed to a path below the type, it is given only what is found whose IRI's path below its type's IRI begins with the segments given, whole segments only, whatever its type.
- [r6] When the client asks for the placeholders, it is given every IRI a link points at that the store does not hold, each with what links to it.
- [r7] When the client follows the links out of an artifact, it is given a stub of each thing the artifact points at.
- [r8] When the client follows the links into an artifact, it is given a stub of each thing that points at it.
- [r9] When the client follows the links into an artifact only through one link and only from one kind, it is given only what points at it through that link from that kind.
- [r10] When the client follows the links out of an artifact two steps, it is given what is found at each step, each with the route taken to it.
- [r11] When the client follows the links out of one place inside an artifact, it is given a stub of what that place points at and nothing else the artifact points at.
- [r12] A link into a part of an artifact counts as a link into that artifact: following the links into the artifact finds what points at the part, reading the artifact at a glance counts it, and removing the artifact is refused while it points there.
- [r13] When the client searches the prose, each result comes with the title of the section it matched and a snippet of it, and the one whose section mentions the words most often comes first.
- [r14] When the client searches within one kind, it is given only artifacts of that kind.
- [r15] When the client searches the fields as well as the prose, it is also given artifacts whose fields, such as a title, match.
- [r16] If the client follows links out of a section, it is given nothing.

## Implementation, may change

- `List` takes a kind (a type's IRI) or a path below the type, field filters and an output form (`stubs` or `ids`), and returns matches.
- `Follow` (until v1 `Refs`) takes a locator, a direction, an optional via-field, an optional kind, an optional path below the type and a depth, and returns stubs with the route taken.
- A query of its own answers the placeholders: each IRI linked to and not held, with the links into it.
- `Search` takes text, an optional kind and a scope (`sections`, `fields`, `all`), and returns stubs with the matching section title and snippet, ranked by term frequency in the section.
- Each has a request and a response message of its own; a request or response names a kind as a kind, never a type, and a place inside an artifact as a place, never a path.
- The storage port answers reads: whether a name is held; an artifact now; names by kind or by path below the type, with field filters; links in, narrowed by field and source kind; the IRIs linked to and not held; inbound counts; search, indexed per section and per field so results keep the section title and snippet; and the history. It has no traversal, no links-out read and no read of a past state; the queries above it do those. The adapter keeps the link index and the search rows as it writes. A section carries no links.

## Not yet

- None.
