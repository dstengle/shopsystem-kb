---
id: design-decision/missingmass.io/shopsystem/kb/resolve-depth-defaults-to-zero
summary: "A read takes a resolve depth whose default is 0, so links come back as names unless following is asked for; a cycle still ends at a name."
date: 2026-09-30
status: accepted
by: "this migration's gate (the approved scenario read-an-artifact / "Without being asked to follow them, links come back as names")"
supersedes: design-decision/missingmass.io/shopsystem/kb/resolve-depth-and-cycles
---

# resolve-depth-defaults-to-zero

## Decision
A read takes a resolve depth whose default is 0, so links come back as names unless following is asked for; a cycle still ends at a name.
