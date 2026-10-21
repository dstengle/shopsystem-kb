---
id: design-decision/missingmass.io/shopsystem/kb/kb-served-from-a-container
summary: "The operator is an activity a developer takes on, not a person, and the development environment is containerized, so a laptop and a deployment have one shape: kb is a service beside its callers on a shared network, which callers reach by its service name (`kb:50051`), never by a port published to the host; a store is started on the first `up` when a role is named; seeding belongs to `kb init`, refused over a store that exists; the connection reaches callers through compose, with no change to kb's discovery; the image is built from the repository first and published later."
date: 2026-10-07
status: accepted
by: ".shop/records/decision-arguments/0021-kb-served-from-a-container.md"
---

# kb-served-from-a-container

## Decision
The operator is an activity a developer takes on, not a person, and the development environment is containerized, so a laptop and a deployment have one shape: kb is a service beside its callers on a shared network, which callers reach by its service name (`kb:50051`), never by a port published to the host; a store is started on the first `up` when a role is named; seeding belongs to `kb init`, refused over a store that exists; the connection reaches callers through compose, with no change to kb's discovery; the image is built from the repository first and published later.
