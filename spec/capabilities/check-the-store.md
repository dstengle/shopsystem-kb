---
id: capability/missingmass.io/shopsystem/kb/check-the-store
title: Check the store
narrator: the client
rests_on: [design-decision/missingmass.io/shopsystem/kb/validation-from-composed-schema, design-decision/missingmass.io/shopsystem/kb/stale-is-safe, design-decision/missingmass.io/shopsystem/kb/result-or-refusal, design-decision/missingmass.io/shopsystem/kb/faults-ordered-by-reading-order-then-rule-name, design-decision/missingmass.io/shopsystem/kb/placeholders-are-reported-never-a-fault, design-decision/missingmass.io/shopsystem/kb/each-type-version-is-its-own-iri, design-decision/missingmass.io/shopsystem/kb/an-artifact-keeps-its-version]
retired: []
---

# Check the store

## Purpose

The client checks every artifact the store holds against the version of its type it conforms to. It is told every violation, each placed, in an order kb decides; every artifact behind its type, one that conforms to a version a later version has followed; and every placeholder with what links to it, each listed apart. Being behind its type is never a violation, and neither is a placeholder. The check never fails and never writes.

## Behaviour

- [r1] When the client checks a store where everything fits its type, it is told of no violation.
- [r2] When the client checks the store, every violation is reported, each naming the artifact, the place in it and the rule broken.
- [r3] When the client checks the store, each artifact's violations are given in the order its places stand in the artifact as it reads back, which is the order its type declares, a collection's items in their order, sections in their order and a section's inner sections after it, and violations at one place come in the alphabetical order of the names of the rules they break.
- [r4] When the client checks a store holding an artifact that conforms to a version of its type a later version has followed, that artifact is listed as behind its type and is not reported as a violation.
- [r5] When the client checks the store, each artifact is checked against the version of its type it conforms to, so an artifact behind its type is reported as a violation only if it does not fit that version.
- [r6] When the client checks a store holding links to IRIs it does not hold, each placeholder is listed with what links to it, apart from the violations and from the artifacts behind their type.
- [r7] When the client checks a store whose only findings are placeholders, it is told of no violation.

## Implementation, may change

- `Check` (until v1 `Validate`) takes nothing. Its result is every violation as artifact, place, rule and message, the stale artifacts listed apart, and the placeholders listed apart, each with the links into it; the violations are what the store holds, not a refusal, and a placeholder is never one.
- Each artifact is checked against the type version it conforms to. An artifact is stale when that version has a later version.

## Not yet

- None.
