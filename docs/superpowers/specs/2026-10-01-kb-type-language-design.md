# kb's type language: kept, and narrowed to what kb reads

Date: 2026-10-01. Note 3 of three (storage, the contract, the type language), "if still wanted". The person
delegated the decision to the controller's recommendation on 2026-10-01.

## The decision

kb keeps JSON Schema 2020-12, with its own keywords, as the language types are written in. A smaller structural
model of kb's own is not wanted now: the one client's eight types use about ten JSON Schema keywords and fit inside
it, a replacement would break contract v1 (a fault's rule is the JSON Schema keyword it breaks) and every type a
store holds, with no migration to carry them, and kb would rebuild the validator, its errors and the type of types
that the library gives it today. The decision is revisited when a client needs a type JSON Schema cannot state, or
when types must migrate between versions.

## What changes: kb's keywords are read where they are written, or refused

Today a type can carry kb's keywords where kb never reads them, and nothing says so. A `ref` inside a nested
object, or inside one branch of a `oneOf`, is accepted when the type is defined, but is never read as a link: it
is not checked to land, not counted, and does not hold up a removal.

From this change, a type is refused when it carries one of kb's keywords where kb does not read it, naming the
place, and nothing is written:

- `ref` is read only on a field directly under the `properties` of the type itself, of a type it is built on, of
  the items of one of its collections, or of a named shape another field uses; anywhere else it is refused.
- `parts`, `sections` and `summary` are read only at the top of a type's schema, and `summary` also at the top of
  a collection's items; anywhere else they are refused.

A `ref` is refused unless it says which kinds it may point at (`targets`, a list of kinds), whether it points at one
artifact or several (`cardinality`, one or many), whether it may point into a part (`parts`, yes or no), and what a
removal does (`on_delete`, which is `refuse`, the one rule kb knows).

The rest of JSON Schema stays open to types (`enum`, `pattern`, `format` and the rest), since checking a field's
shape is the library's work and costs kb nothing.

## Published

Where kb reads its keywords, and the shape of a `ref`, are written into the spec as the rule a client defines types
by. A type refused for either carries a rule of kb's own, as other refusals of a type as it is written do.

## Riding along

- The type of types resolves the 2020-12 metaschema through a registry kb builds itself, from the library's
  published specifications, which kb declares as a dependency, not through what the validator happens to add.
- The faults of a refused artifact come in an order kb decides (by place, then rule), not the order the library
  finds them in.
