---
id: design-decision/missingmass.io/shopsystem/kb/batch-rpcs-prefixed
summary: "The four set rpcs are named with the prefix `Batch`, not the suffix `Many`: `BatchCreate`, `BatchReplace`, `BatchAdd` and `BatchRemove`, with their messages `Batch<Change>Request`, `Batch<Change>Response` and the result `Batch<Changed>` (`BatchCreated`, `BatchReplaced`, `BatchAdded`, `BatchRemoved`); what a set does is unchanged. Contract v1 was not yet tagged and no client pinned it, so the rename lands inside v1."
date: 2026-10-05
status: accepted
by: "the person's request of 2026-10-05; lines approved under the person's delegation; supersedes design-decision/missingmass.io/shopsystem/kb/sets-one-kind-at-a-time (its rpc names); supersedes design-decision/missingmass.io/shopsystem/kb/references-inside-a-set (its rpc name)"
supersedes: [design-decision/missingmass.io/shopsystem/kb/sets-one-kind-at-a-time, design-decision/missingmass.io/shopsystem/kb/references-inside-a-set]
---

# batch-rpcs-prefixed

## Decision
The four set rpcs are named with the prefix `Batch`, not the suffix `Many`: `BatchCreate`, `BatchReplace`, `BatchAdd` and `BatchRemove`, with their messages `Batch<Change>Request`, `Batch<Change>Response` and the result `Batch<Changed>` (`BatchCreated`, `BatchReplaced`, `BatchAdded`, `BatchRemoved`); what a set does is unchanged. Contract v1 was not yet tagged and no client pinned it, so the rename lands inside v1.
