---
id: design-decision/missingmass.io/shopsystem/kb/an-import-counts-files
summary: "An import's history gains one entry for each file that lands, each version of a type counted; a file conforming to a version of its type that neither the directory nor the store holds is an error of the check."
date: 2026-10-11
status: accepted
by: "slicing questions (K3, slices 165.6 and 181: version files in the history's count; a version nobody holds), answered under the person's delegation of 2026-10-10"
---

# an-import-counts-files

## Decision
An import's history gains one entry for each file that lands, each version of a type counted; a file conforming to a version of its type that neither the directory nor the store holds is an error of the check.
