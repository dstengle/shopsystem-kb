---
id: capability/review-the-files-on-disk
title: Review the files on disk
narrator: the operator
rests_on: [decision/0001-yaml-1-2-git-canonical, decision/serialization-yaml]
formulated_as: features/review-the-files-on-disk.feature
---

# Review the files on disk

## Purpose

The store's files are meant to be read and reviewed by people. Prose sits in blocks, lists sit under their names, nothing is rewrapped, and nothing instructs a reader how to build a value. The same content always lands as the same bytes, so a difference between two versions is a real change. The files are never edited by hand as a way of changing the store.

## Behaviour

- When the operator opens an artifact's file, every piece of prose stands as a block of its own however short, each list is written beneath the name it belongs to, indented under it, no line of prose is broken to fit a width, and nothing in the file tells a reader how to build a value.
- When two stores are given the same content by the same client, their files for it are the same, byte for byte.

## Implementation, may change

- Layout inside the store: `<type>/<slug>.yaml`, one file per artifact; types at `schema/<type>.yaml`; the journal under `journal/`.
- Canonical form: identity keys first, in the order `id`, `type`, `schema_version`, `revision`, `title`, then fields in schema order, then `sections`, then part collections in schema order. Every prose body is a literal block scalar. Two-space indent, sequences indented under their key, no line folding at any width, no flow style, no comments, no anchors, no tags.
- Loading uses a standard YAML 1.2 parser; no YAML 1.1 loader or emitter appears anywhere in kb.

## Not yet

- None.
