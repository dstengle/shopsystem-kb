---
id: capability/define-a-type
title: Define a type
narrator: the client
rests_on: [decision/types-are-data, decision/0006-validation-from-composed-schema, decision/composition-covers-common-fields, decision/validation-engine, decision/stale-is-safe, decision/integrity-checked-both-ways, decision/type-language-stays-json-schema, decision/kb-keywords-read-where-written, decision/metaschema-from-a-registry-of-kbs-own, decision/faults-ordered-by-place-then-rule]
formulated_as: features/define-a-type.feature
---

# Define a type

## Purpose

The client decides what its artifacts are made of by defining types, which are ordinary artifacts. It writes them through the same calls as everything else and they are checked against the one type the store ships. A type is written in JSON Schema 2020-12 with kb's own keywords, and kb's keywords are accepted only where kb reads them. A type can refer to a shape another type defines, or be built on a base whose declarations it carries in full. A type's version is what tells an artifact it has fallen behind. A type cannot be removed while artifacts of its kind exist. This capability does not migrate artifacts between versions and offers no type language of kb's own.

## Behaviour

- When the client defines a type whose artifacts carry fields, a link to another artifact of the same type, required sections in order and a collection of parts, the type is an artifact the client can read back like any other, and artifacts of that type can be created.
- Where a type refers to a shape another type defines, artifacts of the referring type are checked against that shape.
- Where a type is built on a base, its artifacts are checked against the base's fields as well as its own, and the base's required sections come before the type's own.
- If the client defines a type that does not match the type that describes types, the type is refused because it does not match the type that describes types.
- If the client defines a type that refers to a shape from a type the store does not hold, names itself as the type it is built on, or declares a link field without saying which kinds it may point at, the type is refused because it could never check an artifact, naming which of these it is, and nothing is written anywhere in the store.
- If the client defines a type that declares a link field anywhere but directly among the fields of the type itself, of a type it is built on, of the items of any of its collections at any depth, or of a named shape another field uses, the type is refused because kb does not read a link field there, naming the place, and nothing is written anywhere in the store.
- If the client defines a type that declares collections anywhere but at the top of its schema or at the top of a collection's items, the type is refused because kb does not read them there, naming the place, and nothing is written anywhere in the store.
- If the client defines a type that declares required sections anywhere but at the top of its schema, the type is refused because kb does not read them there, naming the place, and nothing is written anywhere in the store.
- If the client defines a type that declares the fields shown at a glance anywhere but at the top of its schema or at the top of a collection's items, the type is refused because kb does not read them there, naming the place, and nothing is written anywhere in the store.
- If the client defines a type with a link field that does not say whether it points at one artifact or several, whether it may point into a part, or what a removal does, the type is refused because a link field says which kinds it may point at, whether it points at one artifact or several, whether it may point into a part and what a removal does, naming the place, and nothing is written anywhere in the store.
- If the client defines a type with a link field whose removal rule is anything but refuse, the type is refused because refuse is the one removal rule kb knows, naming the place, and nothing is written anywhere in the store.
- If the client defines a type with a link field that says it points at anything but one artifact or several, the type is refused because a link field points at one artifact or several, naming the place, and nothing is written anywhere in the store.
- If a type the client defines is refused with several faults, they are given in the order of their places in it, then of the rules they break.
- A type may use any keyword of JSON Schema 2020-12 that is not one of kb's own, anywhere in its schema.
- While the store holds a type that carries one of kb's keywords where kb does not read it, the type stays in the store as it is.
- If the client changes a type the store holds and the type as changed still carries one of kb's keywords where kb does not read it, the change is refused because kb does not read it there, naming the place.
- Where a type is built on a base, it carries everything the base declares: the base's collections, whose items the store names, the fields it shows at a glance, and its link fields with the kinds they allow.
- If the client changes a type without moving its version on, the change is refused because a type's version goes up whenever the type changes, and the type reads back as it was.
- When a type is changed so that artifacts the store holds no longer fit it, the change is accepted, and checking the store reports those artifacts.
- If the client removes a type while the store holds artifacts of its kind, the removal is refused because something still points at it, naming each of those artifacts.

## Implementation, may change

- A type is an artifact of type `schema` whose body is a JSON Schema (Draft 2020-12) document in YAML, validated by python-jsonschema, plus kb keywords the library ignores and kb enforces: `ref` on a string or array field (`{ targets: [type...], cardinality: one|many, parts: bool, on_delete: refuse }`), `parts` at artifact or part level (`{ <collection>: { items: <schema> } }`, items get an `id`), `sections` at artifact level (an ordered tree of required section titles), `summary` at artifact level and at the top of a collection's items (fields shown in a stub besides `id`, `type`, `title`), `title` at artifact level (the type's human name).
- kb reads `ref` only on a field directly under `properties` of the type's own schema, of a base it is built on, of the `items` of any of its collections at any depth, or of a named shape another field uses; `parts` and `summary` only at the top of a type's schema or at the top of a collection's `items`; `sections` only at the top of a type's schema. Anywhere else each is refused, naming the place. The `parts` inside a `ref` is the ref's own and is never refused as a misplaced collection.
- A `ref` carries all four of `targets` (a list of kinds), `cardinality` (`one` or `many`), `parts` (yes or no) and `on_delete` (`refuse`, the one rule kb knows), or the type is refused.
- Where kb reads its keywords, and the shape of a `ref`, are published: they are the rule a client defines types by.
- A type refused for one of these carries a rule of kb's own, as every other refusal of a type as it is written does, never a JSON Schema keyword: a misplaced `ref`, a `ref` missing part of its shape, and a `ref` whose `cardinality` or `on_delete` kb does not know carry `ref`; a `ref` without `targets` keeps `targets`; a misplaced `parts`, `sections` or `summary` carries `placement`.
- A type the store held before this rule stays as it is; only a change to it is checked against the rule.
- Every other JSON Schema 2020-12 keyword (`enum`, `pattern`, `format` and the rest) is left to the library, wherever it stands.
- A reference is a field value: a string `decision/adr-0007` or, into a part, `process/x#steps/draft`. The type declares its target types, cardinality, whether part paths are allowed, and the delete rule.
- Cross-type `$ref` resolves through the `referencing` library against a registry of every `schema/*` artifact, with URIs `kb:schema/<type>#/...`.
- The type of types resolves the 2020-12 metaschema through a registry kb builds itself from the library's published specifications, which kb declares as a dependency, not through what the validator happens to add.
- A type built on a base is written `allOf: [{ $ref: kb:schema/<base> }, { ...its own fields }]`. Reference fields are collected from every composed schema; the required section tree is the base's followed by the type's; `parts` and `summary` merge base first.
- Every type carries an integer `version`. The type that describes types is shipped in kb's code and written as artifact `schema/schema` when a store is started.
- The identity key `type` is the id of the type artifact without the `schema/` prefix.
- Every artifact carries one implicit link to its type artifact (`schema/<kind>`); removing a type in use is refused with rule `on_delete`, naming each artifact of its kind.

## Not yet

- Migrating artifacts between type versions. Promoted when a stale artifact causes wrong behaviour (decision/stale-is-safe).
- A type hierarchy and listing by a base type. Promoted when a client asks to list by a base type.
- A smaller structural type model of kb's own in place of JSON Schema. Promoted when a client needs a type JSON Schema cannot state, or when types must migrate between versions (decision/type-language-stays-json-schema).
