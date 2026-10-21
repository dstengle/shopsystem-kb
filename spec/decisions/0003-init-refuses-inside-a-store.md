---
id: design-decision/missingmass.io/shopsystem/kb/init-refuses-inside-a-store
summary: "Starting a store where one already exists, above or below, is refused; discovery follows git's search, `kb/store.yaml` upward from the working directory or `KB_ROOT`, and when the two disagree the call is refused rather than going somewhere unexpected."
date: 2026-09-23
status: superseded
by: ".shop/records/decision-arguments/0003-init-refuses-inside-a-store.md"
---

# init-refuses-inside-a-store

## Decision
Starting a store where one already exists, above or below, is refused; discovery follows git's search, `kb/store.yaml` upward from the working directory or `KB_ROOT`, and when the two disagree the call is refused rather than going somewhere unexpected.
