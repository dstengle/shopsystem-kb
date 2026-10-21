---
id: design-decision/missingmass.io/shopsystem/kb/each-type-version-is-its-own-iri
summary: "A type has a stable IRI, the root its artifacts' IRIs sit under, and each version an IRI of its own, the type's with `@` and the version; a version is fixed once made and a change to a type is a new version; several versions are held while artifacts conform to them; an artifact names the version it conforms to by its IRI, in place of `schema_version`, and moves to a later version by a write checked against it, keeping its own IRI; a link's targets name the type, any version; moving content between versions is not part of this."
date: 2026-10-10
status: accepted
by: ".shop/records/decision-arguments/0027-each-type-version-is-its-own-iri.md"
source: decision-argument/missingmass.io/shopsystem/kb/0027-each-type-version-is-its-own-iri
---

# each-type-version-is-its-own-iri

## Decision
A type has a stable IRI, the root its artifacts' IRIs sit under, and each version an IRI of its own, the type's with `@` and the version; a version is fixed once made and a change to a type is a new version; several versions are held while artifacts conform to them; an artifact names the version it conforms to by its IRI, in place of `schema_version`, and moves to a later version by a write checked against it, keeping its own IRI; a link's targets name the type, any version; moving content between versions is not part of this.
