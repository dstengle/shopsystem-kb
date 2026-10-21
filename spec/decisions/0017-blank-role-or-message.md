---
id: design-decision/missingmass.io/shopsystem/kb/blank-role-or-message
summary: "A role or message that is nothing once `str.isspace` blank space is stripped from either end counts as none and is refused as a missing one; one with anything else in it is kept exactly as given, its blank space included."
date: 2026-09-27
status: accepted
by: ".shop/records/decision-arguments/0017-blank-role-or-message.md"
source: decision-argument/missingmass.io/shopsystem/kb/0017-blank-role-or-message
---

# blank-role-or-message

## Decision
A role or message that is nothing once `str.isspace` blank space is stripped from either end counts as none and is refused as a missing one; one with anything else in it is kept exactly as given, its blank space included.
