---
id: design-decision/missingmass.io/shopsystem/kb/v1-store-cannot-be-moved
summary: "A store made by a kb before contract `kb.v2`, a store of contract `kb.v1` or an earlier one, is refused as an earlier kb's store that this kb cannot read or move, its refusal saying so rather than advising an import of its files, which carry no IRIs; an earlier kb's store is no longer an import's source."
date: 2026-10-10
status: accepted
by: "the person's delegation of 2026-10-10; supersedes design-decision/missingmass.io/shopsystem/kb/earlier-store-told-apart (its advice to start a new store and import the old one's files, and its clause that an earlier kb's store is only ever an import's source)"
supersedes: design-decision/missingmass.io/shopsystem/kb/earlier-store-told-apart
---

# v1-store-cannot-be-moved

## Decision
A store made by a kb before contract `kb.v2`, a store of contract `kb.v1` or an earlier one, is refused as an earlier kb's store that this kb cannot read or move, its refusal saying so rather than advising an import of its files, which carry no IRIs; an earlier kb's store is no longer an import's source.
