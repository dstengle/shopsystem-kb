---
id: capability/missingmass.io/shopsystem/kb/read-an-artifact
title: Read an artifact
narrator: the client
rests_on: [design-decision/missingmass.io/shopsystem/kb/resolve-depth-defaults-to-zero, design-decision/missingmass.io/shopsystem/kb/summary-is-enough-to-navigate, design-decision/missingmass.io/shopsystem/kb/section-reads-are-the-common-read, design-decision/missingmass.io/shopsystem/kb/read-asks-for-one-level, design-decision/missingmass.io/shopsystem/kb/a-link-may-land-on-a-placeholder, design-decision/missingmass.io/shopsystem/kb/each-type-version-is-its-own-iri, design-decision/missingmass.io/shopsystem/kb/placeholders-seen-in-stubs-not-read, design-decision/missingmass.io/shopsystem/kb/an-artifact-is-read-through-its-version]
retired: []
---

# Read an artifact

## Purpose

The client reads an artifact at a glance, one section by its title, or whole. It can have links filled in with their targets to the depth it asks for, and a loop in the links always ends. A link whose target the store does not hold is marked as such, apart from a link that lands. A read never changes the store. This capability is not finding what to read (query-the-store) or reading its history (keep-the-history).

## Behaviour

- [r1] When the client reads an artifact at a glance, it is given its name, its kind, its title and the fields its type shows at a glance, a stub of each thing it points at and of each of its parts, and how many things point at it, counted by their kind and by the link they use.
- [r2] When the client reads an artifact at a glance, the stub of a link to an IRI the store does not hold is marked as not held.
- [r3] When the client reads one section of an artifact by its title, it is given that section and nothing else.
- [r4] When the client reads a whole artifact, it is given every field, every section and every part, in the order the type declares.
- [r5] When the client reads a whole artifact, it is given beside its content its IRI, the IRI of the version of its type it conforms to, its revision and its title.
- [r6] When the client reads a whole artifact without asking for its links to be followed, each link comes back as the name of what it points at, and nothing more.
- [r7] When the client reads an artifact holding a link to an IRI the store does not hold, at any level and following links or not, that link comes back marked as landing on nothing held and is never filled in, while a link that lands carries no such mark.
- [r8] When the client reads a whole artifact following its links one step, each target is given in place of its link, as the store holds it now, and what the target points at is given as names.
- [r9] When the client reads a whole artifact following its links two steps, each target is given in place of its link, and the targets' own links are filled in too.
- [r10] When a read following links meets a target already filled in on the way, that target is given as a name rather than filled in again, so the read ends.
- [r11] When the client reads a whole process following its links, the branches between steps of that process are given as written, naming the steps, and are not followed.
- [r12] When a link is filled in, the target comes with its IRI, the IRI of the version of its type it conforms to, its title and its revision, ahead of its content.
- [r13] When the client reads an artifact that conforms to an earlier version of its type, at a glance or whole, and following links or not, it is read as that version declares: the fields shown at a glance and which of its fields are links are that version's, whatever a later version says.

## Implementation, may change

- `Read` takes a locator and asks for one level: a summary, the whole artifact with its links followed to a resolve depth, or one section by its title. The request carries only what that level takes, and the response returns node content.
- A resolve depth of 0, the default, returns references as IRIs; depth 1 inlines each direct target; depth n follows references n hops. A target already inlined on the current resolution path is returned as a reference. A reference to an IRI the store does not hold carries a mark saying so, at every depth, and is never inlined.
- Branches inside a process point at steps of the same process by id and are not references.

## Not yet

- Reading a past state through the contract. Promoted when a client needs a past state through the contract (decision/past-states-kept-not-yet-read).
