---
id: decision-argument/missingmass.io/shopsystem/kb/0023-an-artifacts-iri-sits-under-its-types
kind: decision-argument
about: bounded-context/missingmass.io/shopsystem/kb
---
# 0023 An artifact's id is an IRI under its type's IRI

2026-10-09. An artifact's id is an https IRI made of its type's IRI, a `/`, and a path of plain names the client chooses; a part is the artifact's IRI and a fragment. A type's own IRI is any https IRI its client chooses, and the type that describes types has one under a domain kb owns. kb checks the grammar, the place under the type and uniqueness, selects artifacts by the path below their type, and holds no prefixes: a shortened form is a client's. Refines 0022. The user's decision, as a compromise that takes RDF's naming and none of its model.
