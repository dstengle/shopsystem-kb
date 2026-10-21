---
id: capability/missingmass.io/shopsystem/kb/name-what-is-asked-for
title: Name what is asked for
narrator: the client
rests_on: [design-decision/missingmass.io/shopsystem/kb/input-safety-at-the-boundary, design-decision/missingmass.io/shopsystem/kb/one-method-per-action, design-decision/missingmass.io/shopsystem/kb/an-artifacts-iri-sits-under-its-types, design-decision/missingmass.io/shopsystem/kb/iri-grammar, design-decision/missingmass.io/shopsystem/kb/contract-style-in-behaviour, design-decision/missingmass.io/shopsystem/kb/placeholders-seen-in-stubs-not-read, design-decision/missingmass.io/shopsystem/kb/export-selections-combine, design-decision/missingmass.io/shopsystem/kb/rules-for-iri-refusals]
retired: []
---

# Name what is asked for

## Purpose

Every call names what it means: a kind, an artifact, a version of a type, a place inside an artifact. Every name of an artifact, a part or a type a call carries or answers is an IRI. Each is checked for shape before anything is looked up or any file is found from it, and then checked against what the store holds. A name that is badly shaped, or names nothing, is an ordinary refusal that gives back what was asked for. kb holds no prefixes: a shortened form of an IRI is a client's. This capability is not about finding the store (find-the-store) or how an artifact is given its IRI (name-artifacts-and-items).

## Behaviour

- [r1] Every name of an artifact, a part or a version of a type that a call carries or answers is an IRI of kb's grammar, which holds only an IRI:
  - whose scheme is `https`;
  - whose host is in lower case, plain names joined by single dots;
  - each segment of whose path is a plain name, lower-case letters and digits in runs joined by single hyphens, or plain names joined by single dots, and none empty;
  - with no query, no trailing slash and no percent-encoding;
  - of at most 512 characters;
  - holding `@` only to name a version of a type, after the type's IRI and before the version's number;
  - holding `#` only to name a part, after the artifact's IRI and before the part's place in it.
- [r2] If the client reads an artifact by a name that is not an IRI of kb's grammar, such as one whose path holds "..", the read is refused because a name is an IRI of kb's grammar, naming the name, and no content comes back from inside the store or outside it.
- [r3] If the client reads an artifact by a name that is a path on the disk rather than an IRI, the read is refused because a name is an IRI, never a path, and no content comes back from inside the store or outside it.
- [r4] If the client reads a place inside an artifact that is not a plain place, such as "sections/../..", the read is refused because a place inside an artifact is named by parts of the same plain alphabet, or a collection and an item in it, and no content comes back from inside the store or outside it.
- [r5] If the client changes an artifact by a name that is not an IRI of kb's grammar, the change is refused because a name is an IRI of kb's grammar, naming the name, and nothing is written, inside the store or outside it.
- [r6] If the client creates an artifact naming a version of a type that is not a type's IRI, `@` and a version's number, the artifact is refused because a version of a type is named by the type's IRI, `@` and its number, and nothing is looked up or written, inside the store or outside it.
- [r7] If the client reads an artifact by a name the store holds nothing under, the read is refused because the store holds nothing by that name, and the name asked for is given back.
- [r8] If the client reads an artifact by an IRI that links point at and the store does not hold, the read is refused because the store holds nothing by that name, and the name asked for is given back.
- [r9] If the client changes an artifact by a name the store holds nothing under, the change is refused because the store holds nothing by that name, the name asked for is given back, and nothing is written.
- [r10] If the client adds an item to an artifact by a name the store holds nothing under, the item is refused because the store holds nothing by that name, the name asked for is given back, and nothing is written.
- [r11] If the client removes an artifact by a name the store holds nothing under, the removal is refused because the store holds nothing by that name, the name asked for is given back, and the store holds what it held before.
- [r12] If a read names a place the artifact does not hold (a section title it holds no section under, a place that is not there, or a place that runs on past a piece of prose), the read is refused because the artifact holds nothing at that place, what was asked for is given back, and no content comes back.
- [r13] If a change is aimed at a place the artifact holds nothing under, a place that runs on past a piece of prose, a place beginning at what only the store settles, or adds an item at a place that is not a collection, the change is refused naming which, and the artifact reads as before, at the revision it held.
- [r14] If the client creates an artifact naming a type version the store does not hold, whether or not it holds that type, the artifact is refused because a create names a version of a type the store holds, the version asked for is given back, that fault stands on its own apart from anything wrong with the content, and nothing is written.
- [r15] If the client lists, searches, follows links or exports restricted to a kind the store holds no type for, the call is refused because a kind must name a type the store holds, and the kind asked for is given back.
- [r16] If the client reads an artifact by an IRI under no type the store holds, the read is refused because the store holds nothing by that name, and the name asked for is given back.

## Implementation, may change

- A locator is `{ id, place }`, with `id` an artifact's IRI and `place` empty for the artifact root; a request or response names a place inside an artifact as a place, never a path, and a kind as a kind, never a type, a kind being named by its type's IRI. Every node is addressable by a place from the root, such as `steps/draft/branches/0` or `sections/purpose/sections/rationale`.
- An IRI matches `https://<host>/<segment>(/<segment>)*`, the host `<name>(.<name>)*` in lower case and each segment `<name>(.<name>)*`, where `<name>` is `[a-z0-9]+(-[a-z0-9]+)*`, at most 512 characters; a type version's IRI is a type's IRI followed by `@<n>`; a part's is an artifact's IRI followed by `#<place>`. An IRI's grammar is checked when a request is converted; whether the store holds its type is checked when it is looked up. A place is a sequence of node names of the same alphabet, or a collection name followed by an item id. `.`, `..`, `/` in a segment and absolute paths are faults; no file is resolved from them.
- An IRI not of kb's grammar carries rule `locator`; a version the store does not hold carries rule `version`.
- Every request is converted at the boundary into validated values (an IRI, a locator, a content tree) by one function per kind of value. Storage accepts only those values; one function in `names.py` gives the place a name takes in an export, following the IRI's path, and export writes a file only at that place, inside the directory it was given.

## Not yet

- None.
