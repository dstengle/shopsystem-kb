# SQLite adapter: report (THROWAWAY spike)

Written by the controller from the adapter agent's final message (the agent could not write files outside its
module). Verified by the controller: `28 passed` on 3 further runs.

## Result
`SPIKE_ADAPTERS=sqlite_adapter .venv/bin/python -m pytest spikes/storage -q`: 28 passed in 0.44s; green 5/5 runs,
both race tests included. No failing tests; no test found to contradict port.py.

## Shape
One WAL-mode file per store (`workdir/<name>.sqlite3`); one connection per handle (`check_same_thread=False`,
`isolation_level=None`, `timeout=30`) behind a lock; every change one `BEGIN IMMEDIATE` transaction, every read one
deferred transaction. Tables: `kinds` (JSON), `docs` (current content JSON + revision), `links` (source, source_kind,
field, place, target, target_doc, target_part, target_kind; indexes `(source, place)`, `(target_doc, source, place)`,
`(target_doc, target_part)`), `commits`, `revisions` (one row per document per change; NULL content = removal),
`kind_events`, FTS5 `search(id, kind, title, body)`.

Commit: check `expect`; mint ids (any id ever held, or minted earlier in the set, is taken); map keys to ids ('set' if
captured twice); apply changes in order to an in-memory draft resolving `{"ref": key}` ('set' if never captured);
validate the whole draft (kind, shape, every link landing against draft over store, 'linked' for links from outside
the set into removed documents or dropped parts); refuse with all faults; else write commit row, revision rows, and
for each touched document a compare-and-set delete on the revision read at start, then docs, links and FTS rows.

## Diagnosis holes
- h1: a replace diffs the document's parts before and after; any link from outside the set into a vanished part is
  refused 'linked'.
- h2: `remove_kind` refused 'in-use' while documents of it or of derived kinds exist (also while another kind is
  based on it or links to it, beyond the docstring).
- h5: `BEGIN IMMEDIATE` serialises writers before any read, so the second validates against the first's result
  ('linked' or 'ref'); `check()` stays empty.
- h5b: the same serialisation, plus revision compare-and-set and `expect` checked inside the transaction. Two
  replaces with no `expect` both land (revisions 2 and 3; later wins), as the port allows.
- h8: ids and keys are minted before validation and links are checked against the draft, so mutually-linked new
  documents land, even through a required link.

## Native vs built by hand
| concern | SQLite gave | adapter built |
|---|---|---|
| atomic set | transactions and rollback | the draft; collecting every fault |
| two writers | write lock, WAL snapshots, busy timeout | revision compare-and-set, `expect` |
| links index both ways | B-tree indexes, `GROUP BY` | extracting links and places from content, per kind |
| referential integrity | nothing usable (links in JSON, parts are paths) | landing checks, derived kinds, parts, 'linked' |
| shape | nothing | kind composition and the content checker |
| field filters | `json_extract` / `json_type` | derived-kind inclusion |
| search | FTS5, `bm25` with column weights, `snippet` | what text to index |
| history, past reads | tables and indexes | revision rows; latest revision at or before a commit |
| traversal | indexed lookups | breadth-first search in Python, one query per step |
| export / import | nothing | kinds ordered base first; id-keeping import through the same checks |

## Ambiguities met in port.py
- Whether a removed id stays taken (never reused here).
- Whether `kind=` on links and traversal includes derived kinds (included; `inbound_counts` groups by exact kind).
- Removing a kind that other kinds depend on (refused here); narrowing on `define` accepted though RULES mentions it.
- Kinds that link to each other cannot be defined one at a time; `import_` checks all kinds together.
- `define` and `remove_kind` recorded as commits, stretching `Entry.changes`.
- Malformed link strings refused 'ref', not 'shape'.
- `list(at=)` uses today's kinds.
- Item ids holding '/', '#' or whitespace refused 'shape'.
- Place ordering is string order (`tags/10` before `tags/2`).

## Not done
Scale not measured by the agent (the controller runs bench.py). Suspected costs: `check()` loads the corpus into
Python; a replace reads every inbound link to detect lost parts; traversal is one query per step. Signatures are
not validated.

## Size
749 lines (656 without blanks and comments).
