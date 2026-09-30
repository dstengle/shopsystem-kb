---
id: capability/name-what-is-asked-for
title: Name what is asked for
narrator: the client
rests_on: [decision/0007-input-safety-at-the-boundary]
formulated_as: features/name-what-is-asked-for.feature
---

# Name what is asked for

## Purpose

Every call names what it means: a kind, an artifact's name, a place inside an artifact. Each is checked for shape before anything is looked up or any file is found from it, and then checked against what the store holds. A name that is badly shaped, or names nothing, is an ordinary refusal that gives back what was asked for. This capability is not about finding the store (find-the-store) or what names look like when minted (name-artifacts-and-items).

## Behaviour

- If the client reads an artifact by a name that is not a kind and a plain name, such as "decision/../elsewhere", the read is refused because a name is a kind and a plain name of lower-case letters, digits and single hyphens, and no content comes back from inside the store or outside it.
- If the client reads an artifact by a name that begins at the root of the disk, the read is refused because a name is a kind and a plain name, never a path, and no content comes back from inside the store or outside it.
- If the client reads a place inside an artifact that is not a plain place, such as "sections/../..", the read is refused because a place inside an artifact is named by parts of the same plain alphabet, or a collection and an item in it, and no content comes back from inside the store or outside it.
- If the client changes an artifact by a name that is not a plain name, the change is refused because a name is a kind and a plain name of lower-case letters, digits and single hyphens, and nothing is written, inside the store or outside it.
- If the client creates an artifact of a kind that is not a plain name, such as "../schema/decision", the artifact is refused because a kind is a plain name of lower-case letters, digits and single hyphens, never a path, and nothing is looked up or written, inside the store or outside it.
- If the client reads an artifact by a name the store holds nothing under, the read is refused because the store holds nothing by that name, and the name asked for is given back.
- If the client changes an artifact by a name the store holds nothing under, the change is refused because the store holds nothing by that name, the name asked for is given back, and nothing is written.
- If the client adds an item to an artifact by a name the store holds nothing under, the item is refused because the store holds nothing by that name, the name asked for is given back, and nothing is written.
- If the client removes an artifact by a name the store holds nothing under, the removal is refused because the store holds nothing by that name, the name asked for is given back, and the store holds what it held before.
- If a read names a place the artifact does not hold (a section title it holds no section under, a place that is not there, or a place that runs on past a piece of prose), the read is refused because the artifact holds nothing at that place, what was asked for is given back, and no content comes back.
- If a change is aimed at a place the artifact holds nothing under, a place that runs on past a piece of prose, a place beginning at what only the store settles, or adds an item at a place that is not a collection, the change is refused naming which, and the artifact reads as before, at the revision it held.
- If the client creates an artifact of a kind the store holds no type for, the artifact is refused because a kind must name a type the store holds, the kind asked for is given back, that fault stands on its own apart from anything wrong with the content, and nothing is written.
- If the client lists, searches or follows links restricted to a kind the store holds no type for, the call is refused because a kind must name a type the store holds, and the kind asked for is given back.
- If the client reads an artifact by a name whose kind the store holds no type for, the read is refused because the store holds nothing by that name, and the name asked for is given back.

## Implementation, may change

- A locator is `{ id, path }`, with `path` empty for the artifact root. Every node is addressable by a path from the root, such as `steps/draft/branches/0` or `sections/purpose/sections/rationale`.
- An id matches `<type>/<slug>`, where `type` is a type the store holds and `slug` is `[a-z0-9]+(-[a-z0-9]+)*`. A part path is a sequence of node names of the same alphabet, or a collection name followed by an item id. `.`, `..`, `/` in a segment and absolute paths are faults; no file is resolved from them.
- Every request is converted at the boundary into validated values (an id, a locator, a content tree) by one function per kind of value. Storage accepts only those values, one function derives a file path from a validated id, and a file is written only at that path, inside `<root>/kb/`.

## Not yet

- None.
