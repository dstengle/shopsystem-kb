---
id: capability/define-a-type
title: Define a type
narrator: the client
rests_on: [decision/types-are-data, decision/0006-validation-from-composed-schema, decision/composition-covers-common-fields, decision/validation-engine, decision/stale-is-safe, decision/integrity-checked-both-ways, decision/type-language-stays-json-schema, decision/kb-keywords-read-where-written, decision/metaschema-from-a-registry-of-kbs-own, decision/faults-ordered-by-reading-order-then-rule-name, decision/0023-an-artifacts-iri-sits-under-its-types, decision/0027-each-type-version-is-its-own-iri, decision/type-of-types-iri, decision/unused-type-versions-kept, decision/kb-numbers-type-versions, decision/type-iris-are-free, decision/references-name-a-version, decision/an-artifact-keeps-its-version, decision/an-artifact-is-read-through-its-version]
formulated_as: features/define-a-type.feature
---

# Define a type

## Purpose

The client decides what its artifacts are made of by defining types, which are ordinary artifacts. It writes them through the same calls as everything else and they are checked against the one type the store ships. A type has a stable IRI its client chooses, which its artifacts' IRIs sit under, and each of its versions has an IRI of its own, numbered by the store and fixed once made; a change to a type is a new version, and the versions artifacts conform to are held beside each other. A type is written in JSON Schema 2020-12 with kb's own keywords, and kb's keywords are accepted only where kb reads them. A type can refer to the shape a version of another type defines, or be built on a base whose declarations it carries in full. A type cannot be removed while artifacts of its kind exist. This capability does not move artifacts between versions, removes no version, and offers no type language of kb's own.

## Behaviour

- When the client defines a type whose artifacts carry fields, a link to another artifact of the same type, required sections in order and a collection of parts, the type is an artifact the client can read back like any other, and artifacts of that type can be created.
- When the client defines a type, giving it any https IRI of kb's grammar, the type is held at that IRI, its version at that IRI, `@` and the version's number, and the IRIs of its artifacts sit under the type's IRI.
- A type's IRI need not sit under the IRI of the type that describes types.
- When the client changes a type, the change makes a new version at the type's IRI, `@` and the new version's number, and every version made before it reads back as it was made.
- When the client changes a type, the store gives the new version the next number.
- While any artifact conforms to a version of a type, the store holds that version.
- When no artifact conforms to a version of a type any longer, the store still holds that version.
- Where a link field names the kinds it may point at, it names each by its type's IRI, and an artifact conforming to any version of that type may be pointed at.
- The type that describes types is held at `https://missingmass.io/kb/type`, and its versions at that IRI, `@` and the version's number.
- Where a type refers to a shape another type defines, it names by its IRI the version of that type it reads, and artifacts of the referring type are checked against that version's shape.
- Where a type is built on a base, its artifacts are checked against the base's fields as well as its own, and the base's required sections come before the type's own.
- If the client defines a type that does not match the type that describes types, the type is refused because it does not match the type that describes types.
- If the client defines a type that refers to a shape from a type version the store does not hold, whether or not it holds that type, names itself as the type it is built on, or declares a link field without saying which kinds it may point at, the type is refused because it could never check an artifact, naming which of these it is, and nothing is written anywhere in the store.
- If the client defines a type that declares a link field anywhere but directly among the fields of the type itself, of a type it is built on, or of the items of any of its collections at any depth, the type is refused because kb does not read a link field there, naming the place, and nothing is written anywhere in the store.
- If the client defines a type that declares collections anywhere but at the top of its schema or at the top of a collection's items, the type is refused because kb does not read them there, naming the place, and nothing is written anywhere in the store.
- If the client defines a type that declares required sections anywhere but at the top of its schema, the type is refused because kb does not read them there, naming the place, and nothing is written anywhere in the store.
- If the client defines a type that declares the fields shown at a glance anywhere but at the top of its schema, the type is refused because kb does not read them there, naming the place, and nothing is written anywhere in the store.
- If the client defines a type with a link field that does not say whether it points at one artifact or several, whether it may point into a part, or what a removal does, the type is refused because a link field says which kinds it may point at, whether it points at one artifact or several, whether it may point into a part and what a removal does, naming the place, and nothing is written anywhere in the store.
- If the client defines a type with a link field whose removal rule is anything but refuse, the type is refused because refuse is the one removal rule kb knows, naming the place, and nothing is written anywhere in the store.
- If the client defines a type with a link field that says it points at anything but one artifact or several, the type is refused because a link field points at one artifact or several, naming the place, and nothing is written anywhere in the store.
- If a type the client defines is refused with several faults, they are given in the order its places stand in the type as it reads back, which is the order the client wrote it in, and faults at one place come in the alphabetical order of the names of the rules they break.
- A type may use any keyword of JSON Schema 2020-12 that is not one of kb's own, anywhere in its schema.
- Where a type is built on a base, it carries everything the base declares: the base's collections, whose items the store names, the fields it shows at a glance, and its link fields with the kinds they allow.
- When a type is changed so that artifacts the store holds would no longer fit it, the change is accepted as a new version, those artifacts still conform to the version they named, and checking the store lists them as behind their type, not as violations.
- When the client changes a type, the links of an artifact conforming to an earlier version stay as that version declares them: what such a link points at still cannot be removed, and a field only the new version makes a link is not a link for that artifact.
- If the client removes a type while the store holds artifacts of its kind, the removal is refused because something still points at it, naming each of those artifacts.

## Implementation, may change

- A type is an artifact of the type that describes types whose body is a JSON Schema (Draft 2020-12) document in YAML, validated by python-jsonschema, plus kb keywords the library ignores and kb enforces: `ref` on a string or array field (`{ targets: [type IRI...], cardinality: one|many, parts: bool, on_delete: refuse }`), `parts` at artifact or part level (`{ <collection>: { items: <schema> } }`, items get an `id`), `sections` at artifact level (an ordered tree of required section titles), `summary` at artifact level (fields shown in a stub besides `id`, `type`, `title`), `title` at artifact level (the type's human name).
- kb reads `ref` only on a field directly under `properties` of the type's own schema, of a base it is built on, or of the `items` of any of its collections at any depth; `parts` only at the top of a type's schema or at the top of a collection's `items`; `sections` and `summary` only at the top of a type's schema. Anywhere else each is refused, naming the place. The `parts` inside a `ref` is the ref's own and is never refused as a misplaced collection.
- A `ref` carries all four of `targets` (a list of type IRIs, no version), `cardinality` (`one` or `many`), `parts` (yes or no) and `on_delete` (`refuse`, the one rule kb knows), or the type is refused.
- Where kb reads its keywords, and the shape of a `ref`, are published: they are the rule a client defines types by.
- A type refused for one of these carries a rule of kb's own, as every other refusal of a type as it is written does, never a JSON Schema keyword: a misplaced `ref`, a `ref` missing part of its shape, and a `ref` whose `cardinality` or `on_delete` kb does not know carry `ref`; a `ref` without `targets` keeps `targets`; a misplaced `parts`, `sections` or `summary` carries `placement`.
- Every other JSON Schema 2020-12 keyword (`enum`, `pattern`, `format` and the rest) is left to the library, wherever it stands.
- A reference is a field value: an artifact's IRI, or, into a part, the artifact's IRI, `#` and the part's place (`…#steps/draft`). The type declares its target types, cardinality, whether parts may be pointed into, and the delete rule.
- A `kb:` reference, in a cross-type `$ref` or in `allOf` naming a base, names a type version by its IRI. It resolves through the `referencing` library against a registry of every type version the store holds, each by its IRI.
- The type that describes types is shipped in kb's code and written at `https://missingmass.io/kb/type`, its first version `https://missingmass.io/kb/type@1`, when a store is started; the IRI is published in place of `schema/schema`.
- kb numbers a type's versions: the first is 1, and each change to the type makes the next. A version's IRI is the type's IRI, `@` and that number. Every held version is kept as it was made. A type's IRI is exempt from the rule that an artifact's IRI sits under its type's.
- An artifact's identity names the IRI of the type version it conforms to, in place of `type` and `schema_version`.
- Every artifact carries one implicit link to the type version it conforms to; removing a type in use is refused with rule `on_delete`, naming each artifact of its kind.

## Not yet

- Migrating artifacts between type versions. Promoted when a stale artifact causes wrong behaviour (decision/stale-is-safe).
- Removing a version of a type no artifact conforms to. Promoted when a client asks to remove a version no artifact conforms to (decision/unused-type-versions-kept).
- A type hierarchy and listing by a base type. Promoted when a client asks to list by a base type.
- A smaller structural type model of kb's own in place of JSON Schema. Promoted when a client needs a type JSON Schema cannot state, or when types must migrate between versions (decision/type-language-stays-json-schema).
