---
id: design-decision/missingmass.io/shopsystem/kb/yaml-1-2-git-canonical
summary: "Every artifact is one YAML 1.2 file under `<root>/kb/`, itself the git repository, marked by `kb/store.yaml`; kb writes one canonical form (literal blocks, indented sequences, no folding, deterministic bytes), is the only writer, and reads and writes all YAML as 1.2 through a pure-Python loader."
date: 2026-09-23
status: superseded
by: ".shop/records/decision-arguments/0001-yaml-1-2-git-canonical.md"
---

# yaml-1-2-git-canonical

## Decision
Every artifact is one YAML 1.2 file under `<root>/kb/`, itself the git repository, marked by `kb/store.yaml`; kb writes one canonical form (literal blocks, indented sequences, no folding, deterministic bytes), is the only writer, and reads and writes all YAML as 1.2 through a pure-Python loader.
