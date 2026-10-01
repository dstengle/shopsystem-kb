# kb storage behind a port, SQLite first

Date: 2026-10-01
Status: approved in brainstorming (2026-09-30 to 2026-10-01); note 1 of 3.

The three notes, built in order: (1) this one, storage behind a port with SQLite as its first adapter, behind
today's contract; (2) the public contract's v1 (starting a store off the wire, one method per action with its own
request and response, batches per kind with references inside a set, an expected revision on changes, one
signature message, a versioned package, result or refusal); (3) the type language, if still wanted.

## Why

The 2026-09-30 diagnosis found three holes in how kb holds its graph, each confirmed by a probe against the
in-process client:

- Integrity is checked one way. A change is checked for the links it carries, never for the links into what it
  changes, except when a whole artifact is removed. A `Write` that drops an item something links into is accepted
  and leaves a dangling link; removing a type while documents of its kind exist is accepted.
- Nothing controls concurrent writers. Two in-process writers race: a removal and a new link to the removed
  artifact both land; two writes to one artifact both return revision 2 and the first is lost. The lock in the
  design note was never built.
- There is no link index. Every inbound question parses the whole store: a summary read takes 0.8 s at 250
  artifacts, 3.2 s at 1,000 and 9.5 s at 3,000.

The store being files in a git repository is the root of all three: kb built a document model on files and never
the database underneath. Agent transcripts and work-state tracking will turn a corpus of hundreds of documents into
thousands of linked items quickly.

A spike (branch `spike/storage-2026-09-30`) put one port in front of two adapters, SQLite and TerminusDB 12.0.7,
both passing the same 28 conformance tests. SQLite met every criterion fixed beforehand: at 30,000 documents reads
and three-step traversals answer in about 0.02 ms, search in 4 ms, and its write lock plus a revision
compare-and-set closed every race. TerminusDB met two outright and the rest only with adapter code working around
it (its version check is skipped on transaction retry; its removal cascades into inbound links; no text index).

## Decisions

- The store is one SQLite database. Git is no longer kb's store, and kb runs no git at all.
- Reviewable files are an operator's output: `kb export` writes canonical YAML on demand; committing it to git is
  the operator's choice.
- Files on disk enter only through import, and the operator validates them first.
- kb's own rules stay above a port; an adapter keeps the graph below it. SQLite is the first adapter; the port
  exists so another can follow, gated by the same conformance tests.
- Performance is bounded, checked by a benchmark kept in the repository, not by scenarios.
- The public contract does not change in this note.

## The port

A kb-internal Python interface, not published.

**Writing: one call, `land(changes, signature)`.** Each change carries the operation, the artifact's id, its whole
content after the change (none for a removal), its links as kb derives them from the type (field, place in the
artifact, target artifact and part, and the kinds the field allows, already expanded to derived kinds), the parts it
holds by place, and the revision it was read at. The journal entries ride with the set, named by `journal.py` and
fingerprinted from the canonical text.

Inside one write transaction the adapter takes the write lock, compares each revision and refuses `conflict` on a
mismatch, checks every link lands on an artifact or part of an allowed kind, refuses `linked` when anything outside
the set links into an artifact or part the set removes, and only then writes the artifacts, the link index, the
search rows and the history. kb's draft still runs first and checks content against JSON Schema; the adapter
re-checks integrity inside the transaction, so a concurrent change cannot slip between the check and the write.

Every artifact carries one implicit link to its type artifact (`schema/<kind>`), so removing a type still in use is
refused `linked` by the same rule; the adapter knows nothing of kinds.

**Reading:** an artifact (now, or as of a set); whether a name is held; names by kind with field equality filters;
links out of an artifact or one place in it; links in, narrowed by field and source kind; inbound counts;
traversal; search, indexed per section and per field so results keep the section title and snippet; history with
today's filters.

**Above the port, unchanged:** names, content checks, sections and items, signatures, faults, the contract.

**Modules:** `store.py` keeps discovery and the marker; a new `port.py` holds the interface and a new
`sqlite_store.py` the adapter; `journal.py` keeps entry naming and fingerprints but writes no files; the git code
goes.

## The store on disk, concurrent callers, history

`<root>/kb/` and its marker `kb/store.yaml` stay, so discovery, `KB_ROOT`, stores never nesting, `kb/server.yaml`
and every find-the-store behaviour stay. The data lives in `kb/store.sqlite3`, in WAL mode. Starting a store makes
the directory, the marker and the database, writes the type of types and the first history entry; every refusal of
starting a store keeps its meaning. No git repository is made.

On one machine, SQLite's write lock serialises writers across threads and processes and readers never wait: two
`shop-knol` processes, or an agent and a person, are safe. Across containers the server (decision 0020) remains,
since SQLite over a network filesystem is not safe; a client that finds a served store directly still may read it
but not change it.

History entries keep their shape (id, moment, actor, operation, artifact, place, revision, type version,
fingerprint, message, set), and snapshots theirs; rows replace the journal files. The adapter also keeps each
artifact's content at every revision: today's contract does not read it, note 2's past-state reads will.

A database that cannot be opened or read refuses every call with one named fault (rule `unreadable`, naming the
database), never breaking off.

## Export, the import check, import

The operator narrates all three.

- `kb export <dir>` writes the store at one moment as canonical YAML, `<dir>/<kind>/<slug>.yaml` per artifact,
  types under `schema/`: identity first (id, type, type version, revision, title), then content, in the canonical
  form (prose as blocks, the same content as the same bytes). The directory must be empty or absent; export never
  overwrites.
- `kb import <dir> --check` reads every file and names each error with its file and reason: not readable as YAML
  1.2 or not canonical, a kind neither the import nor the store holds, content that does not fit its type, a link
  landing nowhere in the import or the store. Then it shows the impact: every file that would be skipped because it
  links, directly or through others, to a broken file, with the chain. Exit 0 when clean, 1 with errors.
- `kb import <dir>` always runs the check first. Clean: everything lands as one signed set under `KB_ACTOR`, its
  message naming the directory, names, titles and revisions kept, types before their artifacts, the new history
  beginning with one import entry per artifact. With errors: refused, report shown, nothing written. With
  `--skip-errors`: everything but the broken files and the files depending on them lands, and what was skipped is
  reported with why.
- Import goes only into a freshly started store. Merging into a store that holds artifacts is not yet.
- Today's `<root>/kb/` already has the export layout, so `kb import <old-root>/kb` migrates an existing store, its
  `journal/` and `store.yaml` ignored. Its old history stays in its own git repository.

## What clients observe

1. A `Write` that drops an item something links into is refused `linked`, naming each link.
2. Removing a type while artifacts of its kind exist is refused `linked`, naming them.
3. Each change is checked against the state the one before it left: a removal and a new link to it never both land;
   two changes to one artifact get distinct revisions, both in the history. Without an expected revision on the
   request the later replacement's content still wins; refusing a caller whose artifact moved since it read is
   note 2.
4. A set is checked once as a whole, against the state it leaves: two new artifacts in one set may point at each
   other, and a change may rely on any other in the set.

## Bounds

At 30,000 artifacts: a summary read and a three-step traversal under 100 ms each; a single change under 50 ms; a set
of 100 changes under 1 s. Checked by a benchmark in the repository; a release that misses one does not ship. They
are provisional until the scale targets are set.

## What retires or changes meaning

- The four scenarios about a caller's environment naming a git repository (starting a store, finding the store,
  the history, the operator's init): retired.
- Reviewing the files on disk (2): re-narrated as export.
- A damaged artifact, type or history file (4), and the damaged-file findings of checking the store (2): replaced by
  the import check and the one fault of a damaged database.
- The "stored file cannot be read" reason for a stopped set: retired.

Superseded: decision 0001 (git and YAML files canonical) by SQLite canonical with YAML as the export and wire form;
0019 (kb's git) retired; restore-on-commit-failure by database transactions; scale-without-a-lock by the write lock
on one machine and a server across containers; "incremental load is measured, not specified" by the bounds.

## Not yet

- Merging an import into a store that holds artifacts. Promoted when someone needs to combine stores.
- Carrying history across an export. Promoted when a second adapter needs a store moved with its history.
- A second adapter. Promoted when a workload needs queries the port cannot answer within its bounds, such as
  transitive or pattern queries over transcripts and work state.
