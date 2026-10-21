---
id: design-decision/missingmass.io/shopsystem/kb/iri-grammar
summary: "An IRI kb accepts has scheme `https` only; a lowercase host of plain names joined by single dots; path segments each a plain name or plain names joined by single dots (a plain name being lowercase letters and digits in hyphen-separated runs); no query, no trailing slash, no percent-encoding and no empty segment; at most 512 characters. A part is the artifact's IRI, `#` and the part's place in it as places are written today (a collection and a name, such as `#steps/draft`), a part's name being unique in its collection; a type version is the type's IRI, `@` and the version number, and `@` appears nowhere else. kb's IRI grammar is published."
date: 2026-10-10
status: accepted
by: "the person's delegation of 2026-10-10"
---

# iri-grammar

## Decision
An IRI kb accepts has scheme `https` only; a lowercase host of plain names joined by single dots; path segments each a plain name or plain names joined by single dots (a plain name being lowercase letters and digits in hyphen-separated runs); no query, no trailing slash, no percent-encoding and no empty segment; at most 512 characters. A part is the artifact's IRI, `#` and the part's place in it as places are written today (a collection and a name, such as `#steps/draft`), a part's name being unique in its collection; a type version is the type's IRI, `@` and the version number, and `@` appears nowhere else. kb's IRI grammar is published.
