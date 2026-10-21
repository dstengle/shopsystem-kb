---
id: design-decision/missingmass.io/shopsystem/kb/init-refuses-inside-or-above
summary: "Starting a store is refused only where a store sits directly inside the named directory or above it; a store deeper below the named directory does not refuse it. This supersedes 0003's "above or below" only; 0003's discovery rule stands."
date: 2026-09-30
status: accepted
by: "the migration gate"
supersedes: design-decision/missingmass.io/shopsystem/kb/init-refuses-inside-a-store
---

# init-refuses-inside-or-above

## Decision
Starting a store is refused only where a store sits directly inside the named directory or above it; a store deeper below the named directory does not refuse it. This supersedes 0003's "above or below" only; 0003's discovery rule stands.
