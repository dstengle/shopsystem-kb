---
id: design-decision/missingmass.io/shopsystem/kb/unwritable-root-refused
summary: "A root kb cannot write is refused before anything is made, by kb init (with a seed directory or without), kb serve --start and `kb.init` alike, with rule `root`, naming the root, rather than as a store that could not answer naming a place kb would have made; nothing is served and nothing is made in it. The rule is kb's existing one for where a store may be started; no rule name is added."
date: 2026-10-08
status: accepted
by: "the batch 28 review (B1), lines approved by the controller under the person's delegation of 2026-10-08"
---

# unwritable-root-refused

## Decision
A root kb cannot write is refused before anything is made, by kb init (with a seed directory or without), kb serve --start and `kb.init` alike, with rule `root`, naming the root, rather than as a store that could not answer naming a place kb would have made; nothing is served and nothing is made in it. The rule is kb's existing one for where a store may be started; no rule name is added.
