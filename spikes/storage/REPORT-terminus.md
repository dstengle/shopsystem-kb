# TerminusDB adapter: report (THROWAWAY spike)

Written by the controller from the adapter agent's final message (the agent could not write files outside its
module). Server `terminusdb/terminusdb-server:v12.0.7`, client `terminusdb` 12.0.5. Verified by the controller:
`28 passed` on 2 further runs (22 to 24 s).

## Result
`28 passed, 1 warning in 21.82s`; green 5 more runs in a row. No test failed or was worked around.
`terminus_adapter.py`: 912 lines (755 non-blank, non-comment).

## Mapping
| port | TerminusDB |
|---|---|
| kind | a class, `@inherits` its base (or abstract `KbDoc`), `@key: Lexical [kb_slug]`; the neutral kind dict kept whole in `@metadata.kb` |
| id `kind/slug` | the Lexical key yields `kind/slug` exactly; `-2`, `-3` minted by the adapter; `DocumentIdAlreadyExists` used to re-mint under a race |
| title, revision | `kb_title`, `kb_revision` on `KbDoc` (TerminusDB versions branches, not documents) |
| field | `Optional` or `Array` of an xsd type or class; never mandatory natively (see below) |
| link | class-typed reference (range = target class, or `KbDoc` for several targets) |
| link into parts | `KbPartLink {to: <document ref>, part: "coll/item/..."}` subdocument |
| collection | `Set` of an `@subdocument` class keyed Lexical on the item id; order kept in `kb_pos` (a `List` embeds position in subdocument ids) |
| sections | `Array` of recursive `KbSection` subdocuments |
| a set of changes | one WOQL query of guards plus Insert/Update/DeleteDocument: one commit, all or nothing |
| signature | commit `author` = role; commit `message` = JSON {execution, message, changes} |
| `at` | time travel: reads against `.../local/commit/<id>` |

## Diagnosis holes
| hole | closed by | evidence |
|---|---|---|
| h1 removing a linked part | adapter | native refusal exists only for native references to subdocuments, which lock the referring document (below); with `KbPartLink` the adapter diffs dropped parts and guards in-query |
| h2 removing a kind in use | TerminusDB | deleting a class with instances (`invalid_predicate`) or subclasses refused natively; stricter than the port |
| h5 removal vs new link | adapter, riding native retry | link after removal: refused natively; removal after link: WOQL `DeleteDocument` silently deletes inbound references (and corrupts Arrays), so the adapter guards in-query; 50 races, never both landed |
| h5b lost update | adapter, riding native retry | `TerminusDB-Data-Version` is not re-checked on transaction retry: racing writers with the same version both landed 10/10. An in-query revision guard, re-evaluated on retry: 50/50 races one landed, one 'conflict' |
| h8 mutual new documents | TerminusDB | both inserts in one WOQL query, references checked at commit |

## Capability table
| port capability | status |
|---|---|
| fresh store per name | native |
| define: classes, bases, metadata | partly native (version rule, well-formedness, retaining old properties: adapter) |
| define accepting a kind that leaves documents unfit | adapter (TerminusDB checks every instance on schema change, so native schema stays loose) |
| remove_kind / in-use | native |
| id minting | partly native |
| one commit per set | native (WOQL; the document API cannot hold a set) |
| `{"ref": key}` in a set | adapter (`@capture` silently ignored in WOQL) |
| expect / conflict | adapter on native retry |
| shape | partly native (unknown field, wrong xsd type native; required, sections, unique item ids: adapter) |
| ref: dangling | native |
| ref: wrong kind | adapter (TerminusDB accepts a reference to a document of the wrong class) |
| ref / linked for parts | adapter |
| linked: removing a linked document | adapter (WOQL DeleteDocument cascades) |
| read, read(at=), list, list(at=), where, derived kinds | native |
| links_out | adapter |
| links_in, inbound_counts | partly native (one object-index WOQL query; adapter reads sources for place and field) |
| traverse | adapter BFS, one round trip per node (WOQL `path` not tried) |
| search | adapter scan (no text index found in TerminusDB 12) |
| history | partly native (commit log; execution and changes in the adapter's JSON message) |
| check | adapter |
| export / import | adapter over native reads and writes |

## Native defects reproduced against v12.0.7
1. WOQL `DeleteDocument` removes inbound references instead of refusing (Optional/Set: silent unlink; Array: cells
   corrupted, referring document then answers HTTP 500); the document API's DELETE refuses correctly.
2. Class-typed references are not checked for class.
3. `TerminusDB-Data-Version` is not re-checked on a transaction retry.
4. WOQL `@capture`/`@ref` is silently a no-op.
5. A reference to another document's subdocument locks the referring document against update and delete.
6. GET of a deleted id via the document API returns HTTP 200 with a 404 body; the Python client fails decoding it.
7. List subdocument ids embed the list position.
8. Inserting the same new document twice in one WOQL query succeeds; document-API DELETE of a missing id returns OK.
9. Document-API responses stall about 40 ms on kept-alive connections (consistent with Nagle vs delayed ACK);
   the adapter reads through WOQL and closes connections (suite 39 s to 22 s).

## Measurements (agent's; the controller re-measures with bench.py)
| measure | value |
|---|---|
| server start-up | 1.28 to 1.32 s |
| fresh store (database + base schema), median of 20 | 0.074 to 0.086 s |
| fresh store with the suite's 8 kinds | 0.51 s |
| memory idle / after suite / 30k docs | 43 MiB / 113 to 117 MiB / 106 to 145 MiB |
| at 30k: glance (read + inbound counts) | 51.6 ms |
| at 30k: traverse out 3 | 58.8 ms |
| at 30k: traverse in 3 | 202.9 ms (adapter BFS; batching levels would plausibly bring it under 100 ms, untried) |
| at 30k: list with where / without | 22.2 ms / 823 ms |
| at 30k: search (scan) | 441 ms |
| one-document commit | 56.7 ms |

## Client library (`terminusdb` 12.0.5)
Reports `__version__` 11.1.0; WOQL document writes need an undocumented `Doc(...)` wrapper; `Doc` types every string
as `xsd:string` (refused inside Arrays of references, so the adapter has its own encoder); `Client.query()` discards
bindings, counts, retry count and data version; no per-call commit author; `log()` returns naive local datetimes;
honours `HTTP(S)_PROXY`. The adapter uses the client only to connect and manage databases; everything else is plain
HTTP.

## Unfinished
A field's type changed across kind versions while documents hold the old type; faster inward traversal; the native
per-document history endpoint; float round-trip (stored as `xsd:decimal`).
