---
id: design-decision/missingmass.io/shopsystem/kb/check-only-sets
summary: "`BatchCreate` and `BatchReplace` may be asked to check only, in the same release as `kb.v2`: the answer is each change's result or the faults as the set would land, with no name for the set, since none lands; it is a read, never refused as busy; an expected revision in it is compared with the revision the artifact stands at."
date: 2026-10-10
status: accepted
by: "the person's delegation of 2026-10-10"
---

# check-only-sets

## Decision
`BatchCreate` and `BatchReplace` may be asked to check only, in the same release as `kb.v2`: the answer is each change's result or the faults as the set would land, with no name for the set, since none lands; it is a read, never refused as busy; an expected revision in it is compared with the revision the artifact stands at.
