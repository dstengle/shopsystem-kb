---
id: design-decision/missingmass.io/shopsystem/kb/unreachable-is-between-calls
summary: "A server that "stops answering" is one that answered earlier calls and has since stopped, refused with rule `unreachable` as a server never there is; a server that stops partway through a call, which could leave a change landed while its client is told otherwise, is not decided by any line yet."
date: 2026-10-06
status: accepted
by: "the formulation of reach-a-served-store's question, answered by the controller's recommendation under the person's delegation of 2026-10-06"
---

# unreachable-is-between-calls

## Decision
A server that "stops answering" is one that answered earlier calls and has since stopped, refused with rule `unreachable` as a server never there is; a server that stops partway through a call, which could leave a change landed while its client is told otherwise, is not decided by any line yet.
