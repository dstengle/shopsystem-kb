---
id: capability/export-and-import-a-store
title: Export and import a store
narrator: the operator
rests_on: [decision/files-are-an-export, decision/sqlite-canonical, decision/yaml-is-export-and-wire, decision/kb-runs-no-git, decision/busy-rule, decision/earlier-store-told-apart]
formulated_as: features/export-and-import-a-store.feature
---

# Export and import a store

## Purpose

The operator takes a store out as files people can read and review, checks a directory of such files, and brings them into a freshly started store. Export writes the store at one moment as canonical YAML, the same content always as the same bytes, and never overwrites. Export is a read, and is never refused because another change is being written. The check names every error, file by file, and every file that would be skipped because it links to a broken one, and writes nothing. Import always checks first and lands what it takes as one signed set. Files on disk enter a store only this way, and it is how a store made by an earlier kb is moved, its files the import's source. This capability is not committing exported files anywhere (the operator's choice), merging into a store that already holds artifacts, or carrying history across.

## Behaviour

- When the operator exports the store to a directory that is empty or does not exist, the directory holds one file for each artifact, under a folder named for its kind, types under the folder for types, each giving the artifact's identity first (its name, kind, type version, revision and title) and then its content, as the store stood at one moment.
- When the operator opens an exported artifact's file, every piece of prose stands as a block of its own however short, each list is written beneath the name it belongs to, indented under it, no line of prose is broken to fit a width, and nothing in the file tells a reader how to build a value.
- When two stores given the same content by the same client are exported, their files for it are the same, byte for byte.
- If the directory named for an export holds anything, the export is refused because export never overwrites, and what the directory holds is left as it was.
- When the operator checks a directory for import, every file is read and each error is reported, naming the file and the reason: it cannot be read as YAML 1.2 or is not in canonical form, it claims a kind neither the directory nor the store holds a type for, its content does not fit its type, or it carries a link that lands on nothing in the directory or the store.
- When the operator checks a directory for import that holds a file with an error, every file linking to it, directly or through other files, an artifact's link to its own type included, is reported as one that would be skipped, with the chain of links that leads to the broken file.
- When the operator checks a directory for import that holds no error, the check reports success.
- If a directory checked for import holds an error, the check reports failure.
- When the operator imports a directory that checks clean into a freshly started store, saying which role they are, everything in it lands as one set signed by that role, with a message naming the directory, each artifact keeping its name, title, revision and type version.
- When the operator imports a directory that checks clean, each type lands before the artifacts of its kind, and the store's history holds its starting entry followed by one import entry for each artifact that lands.
- If a directory imported holds an error, the import is refused because the check found errors, the check's report is shown, and nothing is written.
- Where the operator imports with errors skipped, everything lands except the broken files and the files linking to them, directly or through other files, an artifact's link to its own type included, and the operator is told what was skipped and why.
- If the store imported into holds any artifact besides the type that describes types, the import is refused because import goes only into a freshly started store.
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
- Layout of an export: `<dir>/<kind>/<slug>.yaml`, one file per artifact; types at `<dir>/schema/<kind>.yaml`, the type that describes types at `<dir>/schema/schema.yaml`.
- Canonical form: identity keys first, in the order `id`, `type`, `schema_version`, `revision`, `title`, then fields in schema order, then `sections`, then part collections in schema order. Every prose body is a literal block scalar. Two-space indent, sequences indented under their key, no line folding at any width, no flow style, no comments, no anchors, no tags.
- Loading uses a standard YAML 1.2 parser; no YAML 1.1 loader or emitter appears anywhere in kb.
- `kb import <dir> --check` exits 0 when clean and 1 with errors.
- The check's skip analysis follows every link a file carries, plus each artifact's implicit link to its type file (`schema/<kind>.yaml`), so artifacts of a kind whose type file is broken are skipped with the chain artifact → type file.
- A freshly started store holds no artifact besides `schema/schema`. An imported `schema/schema.yaml` is compared with the store's and passed over when it matches; it is not one of the artifacts that land and has no import entry.
- A store laid out before the database (`<root>/kb/`) already has the export layout; its `journal/` and `store.yaml` are ignored on import.
- An import refused as busy is the fault with rule `busy` (change-the-store). Reads never wait for the write lock, so an export never meets it.

## Not yet

- Merging an import into a store that holds artifacts. Promoted when someone needs to combine stores.
- Carrying history across an export. Promoted when a second adapter needs a store moved with its history.
