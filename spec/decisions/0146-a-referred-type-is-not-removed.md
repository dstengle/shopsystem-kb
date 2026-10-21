---
id: design-decision/missingmass.io/shopsystem/kb/a-referred-type-is-not-removed
summary: "A type is not removed while a held version of another type reads one of its versions, by a `kb:` reference to a shape or by being built on it: the removal is refused as one is while artifacts of its kind exist, naming each referring type, since every version of a type is kept as made and would otherwise read through a version no longer held. A removed type's own versions go with it."
date: 2026-10-10
status: accepted
by: "review question (slice 165: a removal left `kb:<T>@1` dangling, and writes through it and the store's check refused as the store's own fault), answered under the person's delegation of 2026-10-10"
---

# a-referred-type-is-not-removed

## Decision
A type is not removed while a held version of another type reads one of its versions, by a `kb:` reference to a shape or by being built on it: the removal is refused as one is while artifacts of its kind exist, naming each referring type, since every version of a type is kept as made and would otherwise read through a version no longer held. A removed type's own versions go with it.
