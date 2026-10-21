---
id: capability/missingmass.io/shopsystem/kb/export-through-the-contract
title: Export through the contract
narrator: the client
rests_on: [design-decision/missingmass.io/shopsystem/kb/export-over-the-contract, design-decision/missingmass.io/shopsystem/kb/export-streams-and-carries-its-position, design-decision/missingmass.io/shopsystem/kb/an-artifacts-iri-sits-under-its-types, design-decision/missingmass.io/shopsystem/kb/yaml-is-export-and-wire, design-decision/missingmass.io/shopsystem/kb/busy-rule, design-decision/missingmass.io/shopsystem/kb/contract-v2, design-decision/missingmass.io/shopsystem/kb/path-selection-is-a-segment-prefix, design-decision/missingmass.io/shopsystem/kb/export-selections-combine, design-decision/missingmass.io/shopsystem/kb/journal-position-is-an-entry, design-decision/missingmass.io/shopsystem/kb/each-type-version-a-file]
retired: []
---

# Export through the contract

## Purpose

The client takes the store out through the contract as its canonical files, the store at one moment, whole or selected by the path below each type, by type, or by both, one file at a time, and is told the position in the history the files reflect, the position of the last entry landed at that moment. Each file's place follows its artifact's IRI, and each held version of a type is a file of its own. It is the same call against a store in process or a server, and a read, never refused because another change is being written. This capability is not the operator's export and import (export-and-import-a-store), importing anything, or exporting only what changed since a position.

## Behaviour

- [r1] When the client exports the store, it is given the store's canonical files one at a time, each with the place that follows its artifact's IRI, as the store stood at one moment, and is told the position in the history those files reflect.
- [r2] When the client exports the store, the position it is told is the position of the last history entry landed when the store stood at that moment.
- [r3] When the client exports a store holding several versions of a type, it is given one file for each version, at the type's place, `@` and the version's number.
- [r4] When the client exports selecting a path below the type, it is given only the files of the artifacts whose IRI's path below its type's IRI begins with the segments given, whole segments only, whatever their type.
- [r5] When the client exports selecting a type, it is given only the files of that type's artifacts.
- [r6] When the client exports selecting a path below the type and a type together, it is given only the files of that type's artifacts whose IRI's path below the type begins with the segments given.
- [r7] While a server serves the store, when the client exports through it, it is given the same files and the same position as a client that reaches the store in process.
- [r8] While another change is being written to the store, when the client exports it, the export is given and is not refused because the store was busy with another change.

## Implementation, may change

- `Export` is an rpc of `kb.v2` with a request and a server-streamed response of its own: the request carries an optional path below the type and an optional kind, either or both; each message of the stream carries one file, its place and its canonical text; the stream's answer carries the journal position the export reflects, the `id` of the last history entry landed at its moment.
- A kind the store holds no type for is refused as `List` refuses it (name-what-is-asked-for).
- The files are read in one read transaction, so they are the store at one moment; reads never wait for the write lock.
- A file's place is given by `names.py` alone, from the artifact's IRI, by the layout export-and-import-a-store describes, a type version's at `<type place>@<n>.yaml`.
- An export of what changed since a position is to be added as an optional field of the same request, so adding it does not break the contract.

## Not yet

- Exporting only what changed since a position, as an optional field of the same call. Promoted when a store needs an export of only what changed since a position (decision/0030-export-streams-and-carries-its-position).
