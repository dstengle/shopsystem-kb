---
id: capability/define-a-type
title: Define a type
narrator: the client
rests_on: [decision/types-are-data, decision/0006-validation-from-composed-schema, decision/composition-covers-common-fields, decision/validation-engine, decision/stale-is-safe]
formulated_as: features/define-a-type.feature
---

# Define a type

## Purpose

The client decides what its artifacts are made of by defining types, which are ordinary artifacts. It writes them through the same calls as everything else and they are checked against the one type the store ships. A type can refer to a shape another type defines, or be built on a base whose declarations it carries in full. A type's version is what tells an artifact it has fallen behind. This capability does not migrate artifacts between versions.

## Behaviour

- When the client defines a type whose artifacts carry fields, a link to another artifact of the same type, required sections in order and a collection of parts, the type is an artifact the client can read back like any other, and artifacts of that type can be created.
- Where a type refers to a shape another type defines, artifacts of the referring type are checked against that shape.
- Where a type is built on a base, its artifacts are checked against the base's fields as well as its own, and the base's required sections come before the type's own.
- If the client defines a type that does not match the type that describes types, the type is refused because it does not match the type that describes types.
- If the client defines a type that refers to a shape from a type the store does not hold, names itself as the type it is built on, or declares a link field without saying which kinds it may point at, the type is refused because it could never check an artifact, naming which of these it is, and nothing is written anywhere in the store.
- Where a type is built on a base, it carries everything the base declares: the base's collections, whose items the store names, the fields it shows at a glance, and its link fields with the kinds they allow.
- If the client changes a type without moving its version on, the change is refused because a type's version goes up whenever the type changes, and the type reads back as it was.
- When a type is changed so that artifacts the store holds no longer fit it, the change is accepted, and checking the store reports those artifacts.

## Implementation, may change

- A type is an artifact of type `schema` whose body is a JSON Schema (Draft 2020-12) document in YAML, validated by python-jsonschema, plus kb keywords the library ignores and kb enforces: `ref` on a string or array field (`{ targets: [type...], cardinality: one|many, parts: bool, on_delete: refuse }`), `parts` at artifact or part level (`{ <collection>: { items: <schema> } }`, items get an `id`), `sections` at artifact level (an ordered tree of required section titles), `summary` at artifact level (fields shown in a stub besides `id`, `type`, `title`), `title` at artifact level (the type's human name).
- A reference is a field value: a string `decision/adr-0007` or, into a part, `process/x#steps/draft`. The type declares its target types, cardinality, whether part paths are allowed, and the delete rule.
- Cross-type `$ref` resolves through the `referencing` library against a registry of every `schema/*` artifact, with URIs `kb:schema/<type>#/...`.
- A type built on a base is written `allOf: [{ $ref: kb:schema/<base> }, { ...its own fields }]`. Reference fields are collected from every composed schema; the required section tree is the base's followed by the type's; `parts` and `summary` merge base first.
- Every type carries an integer `version`. The type that describes types is shipped in kb's code and written to `schema/schema.yaml` when a store is started.
- The identity key `type` is the id of the type artifact without the `schema/` prefix.

## Not yet

- Migrating artifacts between type versions. Promoted when a stale artifact causes wrong behaviour (decision/stale-is-safe).
- A type hierarchy and listing by a base type. Promoted when a client asks to list by a base type.
