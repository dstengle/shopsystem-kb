---
id: design-decision/missingmass.io/shopsystem/kb/paired-escapes-are-one-character
summary: "Content may write a character beyond the first 65,536 as two escapes, one for each half, as JSON does, and reads back holding that one character; half of a character alone, in either order, is still refused because the content cannot be read as written."
date: 2026-10-01
status: accepted
by: ".shop/records/archive/design-notes/2026-10-01-kb-batch24-review-answers.md"
---

# paired-escapes-are-one-character

## Decision
Content may write a character beyond the first 65,536 as two escapes, one for each half, as JSON does, and reads back holding that one character; half of a character alone, in either order, is still refused because the content cannot be read as written.
