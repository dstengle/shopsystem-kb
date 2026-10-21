---
id: design-decision/missingmass.io/shopsystem/kb/an-import-never-skips-a-difference
summary: "A file that differs from what the store holds at its IRI is not a broken file: with errors skipped the import is still refused naming each such IRI, and nothing lands, since skipping it would hide that the directory and the store disagree."
date: 2026-10-11
status: accepted
by: "slicing question (K3, slice 182: a differing file under `--skip-errors`), answered under the person's delegation of 2026-10-10"
---

# an-import-never-skips-a-difference

## Decision
A file that differs from what the store holds at its IRI is not a broken file: with errors skipped the import is still refused naming each such IRI, and nothing lands, since skipping it would hide that the directory and the store disagree.
