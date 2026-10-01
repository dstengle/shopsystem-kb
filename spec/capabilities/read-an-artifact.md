---
id: capability/read-an-artifact
title: Read an artifact
narrator: the client
rests_on: [decision/resolve-depth-defaults-to-zero, decision/summary-is-enough-to-navigate, decision/section-reads-are-the-common-read]
formulated_as: features/read-an-artifact.feature
---

# Read an artifact

## Purpose

The client reads an artifact at a glance, one section by its title, or whole. It can have links filled in with their targets to the depth it asks for, and a loop in the links always ends. A read never changes the store. This capability is not finding what to read (query-the-store) or reading its history (keep-the-history).

## Behaviour

- When the client reads an artifact at a glance, it is given its name, its kind, its title and the fields its type shows at a glance, a stub of each thing it points at and of each of its parts, and how many things point at it, counted by their kind and by the link they use.
- When the client reads one section of an artifact by its title, it is given that section and nothing else.
- When the client reads a whole artifact, it is given every field, every section and every part, in the order the type declares.
- When the client reads a whole artifact without asking for its links to be followed, each link comes back as the name of what it points at, and nothing more.
- When the client reads a whole artifact following its links one step, each target is given in place of its link, as the store holds it now, and what the target points at is given as names.
- When the client reads a whole artifact following its links two steps, each target is given in place of its link, and the targets' own links are filled in too.
- When a read following links meets a target already filled in on the way, that target is given as a name rather than filled in again, so the read ends.
- When the client reads a whole process following its links, the branches between steps of that process are given as written, naming the steps, and are not followed.
- When a link is filled in, the target comes with its name, its kind, its title and its revision, ahead of its content.

## Implementation, may change

- `Read` takes a locator, a level (`summary`, `section` with a title, `whole`) and a resolve depth, and returns node content.
- A resolve depth of 0, the default, returns references as ids; depth 1 inlines each direct target; depth n follows references n hops. A target already inlined on the current resolution path is returned as a reference.
- Branches inside a process point at steps of the same process by id and are not references.

## Not yet

- Reading a past state through the contract. Promoted when a client needs a past state through the contract (decision/past-states-kept-not-yet-read).
