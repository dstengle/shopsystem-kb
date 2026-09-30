---
id: capability/check-the-store
title: Check the store
narrator: the client
rests_on: [decision/0006-validation-from-composed-schema, decision/stale-is-safe]
formulated_as: features/check-the-store.feature
---

# Check the store

## Purpose

The client checks every artifact the store holds against the current version of its type. It is told every violation, each placed, and every artifact behind its type, listed apart from the violations. A damaged file or an artifact of a kind with no type is reported and the rest is still checked. The check never fails and never writes.

## Behaviour

- When the client checks a store where everything fits its type, it is told of no violation.
- When the client checks the store, every violation is reported, each naming the artifact, the place in it and the rule broken.
- When the client checks a store holding an artifact last checked against an older version of its type, that artifact is listed as behind its type and is not reported as a violation.
- When the client checks a store holding an artifact behind its type that no longer fits the current version, it is listed as behind its type and also reported as a violation naming the artifact, the place and the rule broken, and the check itself does not fail.
- When the client checks a store where a stored file cannot be read, that file is reported as a violation naming the file, everything else is checked and reported alongside it, and the check comes back with its answer rather than breaking off.
- When the client checks a store holding an artifact of a kind the store holds no type for, that artifact is reported as a violation naming the artifact and the kind it claims, everything else is checked and reported alongside it, and the check comes back with its answer.
- When the client checks a store where a stored file was left unreadable, empty, holding a list, holding a second document, telling a reader how to build a value, pointing back at a value written elsewhere, or naming the same entry twice, that file is reported as the one violation naming the file, everything else is checked alongside it, and the check comes back with its answer.

## Implementation, may change

- `Validate` takes nothing and returns every violation as artifact, path and message, with stale artifacts listed.
- An artifact is stale when its `schema_version` is behind its type's `version`.

## Not yet

- None.
