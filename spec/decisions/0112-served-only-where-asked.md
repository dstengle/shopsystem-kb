---
id: design-decision/missingmass.io/shopsystem/kb/served-only-where-asked
summary: "`kb serve` serves at exactly the address the operator gives or not at all: an address that is not a host and a port (a port from 0 to 65535, 0 asking the system for one), or one nothing can listen at, is refused naming it, with nothing served, never served at another port; and `kb.testing.served` refuses a directory for the connection that already holds one, leaving it as it was, rather than overwriting and then deleting a connection someone else wrote."
date: 2026-10-06
status: accepted
by: "the batch 27 branch review (I3, I4), lines approved by the controller under the person's delegation of 2026-10-06"
---

# served-only-where-asked

## Decision
`kb serve` serves at exactly the address the operator gives or not at all: an address that is not a host and a port (a port from 0 to 65535, 0 asking the system for one), or one nothing can listen at, is refused naming it, with nothing served, never served at another port; and `kb.testing.served` refuses a directory for the connection that already holds one, leaving it as it was, rather than overwriting and then deleting a connection someone else wrote.
