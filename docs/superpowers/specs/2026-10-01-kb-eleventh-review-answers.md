# Answers to the eleventh architecture review

Date: 2026-10-01. The review is kept at /home/vscode/kb-reviews/eleventh-review.md. The person delegated every question
to the controller's recommendations on 2026-10-01; these are those recommendations.

## The operator's directory refused by its shape

An export aimed at something that is a file, not a directory, is refused because export writes into a directory,
and the file is left as it was. A check for import, or an import, aimed at something that is not a directory is
refused because files for import are read from a directory, and nothing is written. Both refusals keep the rule
`root`, the rule a directory named by its shape already carries.

## Implementation lines brought up to date

The review found Implementation lines that no longer say what the code does. They change as follows, and no
Behaviour line changes with them.

- check-a-change: the port's call is `land(changes, entries, relinks, kinds)`, the signature riding in the entries;
  the adapter writes each change and then checks links and integrity inside the same savepoint, taking the set back
  on a refusal; the kinds a link may land on are the field's targets as written; a relink restates the links of an
  artifact the set leaves as it is, with the revisions of the types it was read through, and the set names the
  kinds whose every artifact it restates; the adapter keeps search rows as it writes.
- query-the-store: the port answers whether a name is held, an artifact now, names by kind with field filters,
  links in narrowed by field and source kind, inbound counts, search and the history; it has no traversal, no
  links-out read and no read of a past state, which the queries do above it.
- name-what-is-asked-for: an id's grammar is checked when a request is converted, and whether the store holds a
  type for its kind when it is looked up; one function in `names.py` gives the place a name takes in an export.
- name-artifacts-and-items: the store keeps no files; the place an artifact takes in an export derives from its
  name.
- keep-the-history: the digest is of the canonical text, encoded as UTF-8.
- export-and-import-a-store: an import passes over a store's history, its marker, `.git/`, `journal/`, and the
  database with its side files.
