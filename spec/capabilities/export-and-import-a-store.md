---
id: capability/export-and-import-a-store
title: Export and import a store
narrator: the operator
rests_on: [decision/files-are-an-export, decision/sqlite-canonical, decision/yaml-is-export-and-wire, decision/kb-runs-no-git, decision/busy-rule, decision/earlier-store-told-apart, decision/operator-directory-refused-by-shape, decision/0026-import-passes-over-identical-refuses-differing, decision/0024-a-link-may-land-on-a-placeholder, decision/0023-an-artifacts-iri-sits-under-its-types, decision/each-type-version-a-file, decision/import-skips-only-by-type, decision/import-check-reports-differing, decision/rules-for-iri-refusals, decision/an-artifact-is-read-through-its-version]
formulated_as: features/export-and-import-a-store.feature
---

# Export and import a store

## Purpose

The operator takes a store out as files people can read and review, checks a directory of such files, and brings them into a store, fresh or already holding artifacts. Export writes the store at one moment as canonical YAML, each file at a place that follows its artifact's IRI, the same content always as the same bytes, and never overwrites. Export is a read, and is never refused because another change is being written. The check names every error, file by file, and writes nothing. Import always checks first and lands what it takes as one signed set: an artifact the store already holds identically is passed over, one that differs refuses the whole import, and a link to an IRI neither the directory nor the store holds lands on a placeholder. Files on disk enter a store this way, or whole as a store through the operator's restore of a backup (operate-a-store). This capability is not committing exported files anywhere (the operator's choice), replacing content the store holds, which is a change through the contract, the client's export through the contract (export-through-the-contract), or carrying history across.

## Behaviour

- When the operator exports the store to a directory that is empty or does not exist, the directory holds one file for each artifact, at a place that follows the path of its IRI, and for a type one file for each version the store holds and no other, at the type's place, `@` and the version's number, a version's file giving that version's own revision and title, each giving the artifact's identity first (its IRI, the IRI of the version of its type it conforms to, its revision and its title) and then its content, as the store stood at one moment.
- When the operator exports a store holding an artifact that conforms to an earlier version of its type, that artifact's file gives its content in the order the version it conforms to declares.
- When the operator opens an exported artifact's file, every piece of prose stands as a block of its own however short, each list is written beneath the name it belongs to, indented under it, no line of prose is broken to fit a width, and nothing in the file tells a reader how to build a value.
- When two stores given the same content by the same client are exported, their files for it are the same, byte for byte.
- If the directory named for an export holds anything, the export is refused because export never overwrites, and what the directory holds is left as it was.
- If the operator exports to something that is a file, not a directory, the export is refused because export writes into a directory, and the file is left as it was.
- If the operator checks for import something that is not a directory, the check is refused because files for import are read from a directory, and nothing is written.
- If the operator imports from something that is not a directory, the import is refused because files for import are read from a directory, and nothing is written.
- When the operator checks a directory for import, every file is read and each error is reported, naming the file and the reason: it cannot be read as YAML 1.2 or is not in canonical form, it claims a type neither the directory nor the store holds, it conforms to a version of its type neither the directory nor the store holds, its content does not fit its type, or it carries a link to an IRI under a type neither the directory nor the store holds.
- When the operator checks a directory for import holding an artifact the store holds at the same IRI with other content or another type version, the check reports it as an error, naming the IRI.
- When the operator checks a directory for import that holds a type version's file with an error, every file of a type version referring to it by a `kb:` reference, directly or through other type versions, of an artifact conforming to that version or to any of those, and of an artifact carrying a link to an IRI under a type no version of which would land, is reported as one that would be skipped, with the chain that leads to the broken file.
- When the operator checks a directory for import that holds no error, the check reports success.
- If a directory checked for import holds an error, the check reports failure.
- When the operator imports a directory that checks clean into a store, saying which role they are, everything in it lands as one set signed by that role, with a message naming the directory, each artifact keeping its IRI, title, revision and type version.
- When the operator imports a directory that checks clean, each type lands before the artifacts of its kind, and the store's history gains one import entry for each file that lands, each version of a type counted.
- When the operator imports the export of a store that held an artifact conforming to an earlier version of its type, every version of that type lands as its file gives it, the artifact is checked against the version it conforms to, and afterwards it is read, listed, checked and replaced as it was in the store exported.
- When the operator imports a directory holding an artifact the store already holds at the same IRI, with the same content and the same type version, that artifact is passed over and the rest lands.
- If the operator imports a directory holding an artifact the store already holds at the same IRI with other content or another type version, with errors skipped or not, the import is refused naming each such IRI, and nothing lands.
- When the operator imports a directory holding a link to an IRI neither the directory nor the store holds, under a type one of them holds that the link field allows, the import lands and the link lands on a placeholder at that IRI.
- When the operator imports a directory holding a link into a part that the artifact at its IRI, held by the directory or the store, lacks, the import lands and the link waits on a placeholder for that part.
- When the operator imports a file holding an item that carries no name, the item lands named as a write names it, and an item that carries a name keeps it.
- If a directory imported holds an error, the import is refused because the check found errors, the check's report is shown, and nothing is written.
- Where the operator imports with errors skipped, everything lands except the broken files, the files of type versions referring to a broken type version by a `kb:` reference, directly or through other type versions, of artifacts conforming to the broken version or to any of those, and of artifacts carrying a link to an IRI under a type no version of which lands, a link to a file that does not land landing on a placeholder under a type that does, and the operator is told what was skipped and why.
- When the operator imports the kb directory of an existing store, it is imported as an export is, its history and its store marker passed over.
- If nothing names the operator's role, the import is refused because the role must be named through `KB_ACTOR`, and nothing is written.
- When the operator checks a directory for import, the store holds what it held before.
- kb export and kb import find the store as kb validate does, with the same refusals.
- If, with errors skipped, nothing would land, the import is refused because nothing would land, and nothing is written.
- When the operator imports a directory whose type that describes types matches the store's, the directory's copy is passed over and the store's is kept.
- When the operator checks a directory for import whose type that describes types differs from the store's, that file is reported as an error, naming the file.
- If the import waits longer than the store waits while another change is being written, the import is refused because the store was busy with another change, nothing is written, and the same import may be run again.
- While another change is being written to the store, when the operator exports the store, the export is written and is not refused because the store was busy with another change.

## Implementation, may change

- The commands are `kb export <dir>`, `kb import <dir> --check`, `kb import <dir>` and `kb import <dir> --skip-errors`. `kb import` always runs the check first; the role it signs under comes from `KB_ACTOR`. Both commands find the store upward from the working directory or from `KB_ROOT` (find-the-store).
- A directory refused by its shape, for export, check or import, is the fault with rule `root`.
- Layout of an export: `<dir>/<host>/<segment>/.../<segment>.yaml`, one file per artifact, its place the host and path of its IRI; each held version of a type at the place of the type's IRI followed by `@<n>`, so the type that describes types is at `<dir>/missingmass.io/kb/type@1.yaml`. The layout is the one the client's export through the contract names its files by.
- Canonical form: identity keys first, in the order `id` (the IRI), the type version's IRI, `revision`, `title`, then fields in schema order, then `sections`, then part collections in schema order. Every prose body is a literal block scalar. Two-space indent, sequences indented under their key, no line folding at any width, no flow style, no comments, no anchors, no tags.
- Loading uses a standard YAML 1.2 parser; no YAML 1.1 loader or emitter appears anywhere in kb.
- `kb import <dir> --check` exits 0 when clean and 1 with errors.
- The check's skip analysis follows each artifact's implicit link to its type version's file and each type's `kb:` references, so artifacts of a type whose file is broken are skipped with the chain artifact → type file. A link to an artifact's file is not followed: a file that does not land leaves its IRI a placeholder.
- An artifact the store holds is compared with its file by its content and its type version; its revision is not compared. An identical one is passed over and has no import entry; a differing one is a check error with rule `differs`, a published rule name, and is never one of the errors skipped. The type that describes types is compared and passed over the same way.
- A file conforming to a version of its type neither the directory nor the store holds is a check error with rule `version`.
- An import passes over a store's history, its marker, `.git/`, `journal/`, and the database with its side files.
- An import refused as busy is the fault with rule `busy` (change-the-store). Reads never wait for the write lock, so an export never meets it.

## Not yet

- Carrying history across an export. Promoted when a second adapter needs a store moved with its history.
