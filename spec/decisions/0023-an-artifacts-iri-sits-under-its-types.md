---
id: design-decision/missingmass.io/shopsystem/kb/an-artifacts-iri-sits-under-its-types
summary: "An artifact's id is an https IRI made of its type's IRI, a `/`, and a path of plain names the client chooses; a part is the artifact's IRI and a fragment; a type's own IRI is any https IRI its client chooses, and the type that describes types has one under a domain kb owns; kb checks the grammar, the place under the type and uniqueness, selects artifacts by the path below their type, and holds no prefixes, a shortened form being a client's; RDF's naming taken and none of its model."
date: 2026-10-09
status: accepted
by: ".shop/records/decision-arguments/0023-an-artifacts-iri-sits-under-its-types.md"
source: decision-argument/missingmass.io/shopsystem/kb/0023-an-artifacts-iri-sits-under-its-types
---

# an-artifacts-iri-sits-under-its-types

## Decision
An artifact's id is an https IRI made of its type's IRI, a `/`, and a path of plain names the client chooses; a part is the artifact's IRI and a fragment; a type's own IRI is any https IRI its client chooses, and the type that describes types has one under a domain kb owns; kb checks the grammar, the place under the type and uniqueness, selects artifacts by the path below their type, and holds no prefixes, a shortened form being a client's; RDF's naming taken and none of its model.
