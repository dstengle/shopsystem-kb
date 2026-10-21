---
id: design-decision/missingmass.io/shopsystem/kb/operator-directory-refused-by-shape
summary: "Export aimed at a file, and a check for import or an import aimed at something that is not a directory, are refused with rule `root`, because export writes into a directory and files for import are read from one; the export leaves the file as it was and the check and import write nothing."
date: 2026-10-01
status: accepted
by: ".shop/records/archive/design-notes/2026-10-01-kb-eleventh-review-answers.md"
source: decision-argument/missingmass.io/shopsystem/kb/2026-10-01-kb-eleventh-review-answers
---

# operator-directory-refused-by-shape

## Decision
Export aimed at a file, and a check for import or an import aimed at something that is not a directory, are refused with rule `root`, because export writes into a directory and files for import are read from one; the export leaves the file as it was and the check and import write nothing.
