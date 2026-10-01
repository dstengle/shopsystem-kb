---
id: capability/check-the-store
title: Check the store
narrator: the client
rests_on: [decision/0006-validation-from-composed-schema, decision/stale-is-safe, decision/result-or-refusal, decision/faults-ordered-by-place-then-rule]
formulated_as: features/check-the-store.feature
---

# Check the store

## Purpose

The client checks every artifact the store holds against the current version of its type. It is told every violation, each placed, in an order kb decides, and every artifact behind its type, listed apart from the violations. The check never fails and never writes.

## Behaviour

- When the client checks a store where everything fits its type, it is told of no violation.
- When the client checks the store, every violation is reported, each naming the artifact, the place in it and the rule broken.
- When the client checks the store, each artifact's violations are given in the order of their places in it, then of the rules they break.
- When the client checks a store holding an artifact last checked against an older version of its type, that artifact is listed as behind its type and is not reported as a violation.
- When the client checks a store holding an artifact behind its type that no longer fits the current version, it is listed as behind its type and also reported as a violation naming the artifact, the place and the rule broken, and the check itself does not fail.

## Implementation, may change

- `Check` (until v1 `Validate`) takes nothing. Its result is every violation as artifact, place, rule and message, and the stale artifacts listed apart; the violations are what the store holds, not a refusal.
- An artifact is stale when its `schema_version` is behind its type's `version`.

## Not yet

- None.
