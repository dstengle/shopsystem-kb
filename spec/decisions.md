# Decisions

## decision/0001-yaml-1-2-git-canonical
Every artifact is one YAML 1.2 file under `<root>/kb/`, itself the git repository, marked by `kb/store.yaml`; kb writes one canonical form (literal blocks, indented sequences, no folding, deterministic bytes), is the only writer, and reads and writes all YAML as 1.2 through a pure-Python loader.
date: 2026-09-23
source: adrs/0001-yaml-1-2-git-canonical.md

## decision/0002-ids-minted-from-titles
An artifact's id is `kind/name`, the name made from its title by kb's grammar with -2, -3 on collision; parts are named from their title or position, once; a client hands existing ids back on a write and never chooses one.
date: 2026-09-23
source: adrs/0002-ids-minted-from-titles.md

## decision/0003-init-refuses-inside-a-store
Starting a store where one already exists, above or below, is refused; discovery follows git's search, `kb/store.yaml` upward from the working directory or `KB_ROOT`, and when the two disagree the call is refused rather than going somewhere unexpected.
date: 2026-09-23
source: adrs/0003-init-refuses-inside-a-store.md

## decision/0004-journal-batch-and-snapshots
Every journal entry names the set (batch) it landed in and the journal filters by it; artifacts carry a revision, and a piece of work records what it read as a snapshot in the journal rather than pinning versions.
date: 2026-09-23
source: adrs/0004-journal-batch-and-snapshots.md

## decision/0005-content-as-canonical-text
Artifact content crosses the protobuf contract as canonical YAML text, not a Struct, so key order and integers survive; identity keys are typed fields.
date: 2026-09-24
source: adrs/0005-content-as-canonical-text.md

## decision/0006-validation-from-composed-schema
Required fields and structural rules are JSON Schema 2020-12 fragments composed into one effective schema per type with kb's keywords; hand-written checks cover only what JSON Schema cannot express; stale artifacts are checked against the current type and a failing write to one is refused.
date: 2026-09-24
source: adrs/0006-validation-from-composed-schema.md

## decision/0007-input-safety-at-the-boundary
Every request field becomes a validated value before the domain sees it; names follow a plain-name grammar with no `..` or absolute paths; the boundary fails closed, one wrapper turning refusals into faults with nothing written.
date: 2026-09-24
source: adrs/0007-input-safety-at-the-boundary.md

## decision/0008-contract-is-the-stable-boundary
`kb.proto` with the in-process transport first is the interface clients depend on and git-first storage may change behind it; types are data and special outputs are client code; no MCP hop; scenario status is a future ledger, not a work-item field.
date: 2026-09-23
source: adrs/0008-contract-is-the-stable-boundary.md

## decision/0009-resolve-depth-and-cycles
A read takes a depth (default 1) and a cycle terminates by returning the name rather than recursing.
date: 2026-09-23
source: adrs/0009-resolve-depth-and-cycles.md

## decision/0010-tags
kb is released by tag, the user's decision: v0.1.0 (2026-09-24), v0.2.0 (2026-09-26), v0.2.1 and v0.3.0 (2026-09-27).
date: 2026-09-24
source: adrs/0010-tags.md

## decision/0011-sections-carry-no-links
A section has exactly title, body and sections; a place a traversal starts at is a part or a field, never a section.
date: 2026-09-26
source: adrs/0011-sections-carry-no-links.md

## decision/0012-writes-need-role-and-message
Create, Write, Append, Delete, Apply and Snapshot under an actor with no role, or with no message, are refused with nothing on disk and nothing in the history.
date: 2026-09-26
source: adrs/0012-writes-need-role-and-message.md

## decision/0013-empty-set-refused
Apply with no operations is refused before anything is written, so kb never reaches git with nothing to commit.
date: 2026-09-27
source: adrs/0013-empty-set-refused.md

## decision/0014-signature-refused-before-operations
A change or snapshot with no role, no message or neither is refused with those faults alone, the role's first, then the message's, then (for a snapshot) the piece of work's; its operations or names are not checked.
date: 2026-09-27
source: adrs/0014-signature-refused-before-operations.md

## decision/0015-missing-message-rule
A missing message is refused with rule `message`, no artifact and no path; a missing role with rule `actor`, no artifact and no path.
date: 2026-09-27
source: adrs/0015-missing-message-rule.md

## decision/0016-empty-set-fault
An Apply with no operations is refused with one fault, rule `operations`, no artifact, no path, no set name and no results; an empty set with no role or message answers those faults alone.
date: 2026-09-27
source: adrs/0016-empty-set-fault.md

## decision/0017-blank-role-or-message
A role or message that is nothing once `str.isspace` blank space is stripped from either end counts as none and is refused as a missing one; one with anything else in it is kept exactly as given, its blank space included.
date: 2026-09-27
source: adrs/0017-blank-role-or-message.md

## decision/0018-the-published-contract
A client depends on kb only through `kb.proto` and `kb.contract.kb_pb2`, `kb.client.connect` with its clock, `kb.content` (`loads`, `dumps`, `text`, `NotCanonical`), the connection file's form, and every fault's `rule` name, versioned together by the release tag; everything else may change without notice (refines 0008).
date: 2026-09-27
source: adrs/0018-the-published-contract.md

## decision/0019-kb-git-owns-its-store
Every git call kb makes clears the variables git lists as locating a repository, and `GIT_CONFIG_PARAMETERS` and `GIT_CONFIG_COUNT`, so a caller's `GIT_DIR`, its kin and its `-c` settings never redirect or change the store's history; kb's own `-c` settings stay in force.
date: 2026-09-27
source: adrs/0019-kb-git-owns-its-store.md

## decision/0020-a-server-found-where-the-store-is
Several callers reach one store through `kb serve <root> --listen <host:port>`, which takes changes one at a time and owns the store it serves; a caller finds it where it would find the store, `kb/store.yaml` or `kb/server.yaml` and never both; it listens on any interface it is given, with no authentication, its network its boundary; the clock stays the in-process client's; chosen over locking the store for several in-process callers (extends 0008 and 0018).
date: 2026-09-28
source: adrs/0020-a-server-found-where-the-store-is.md

## decision/serialization-yaml
Serialization is YAML, read with a standard parser and emitted canonically by kb alone, which never needs round-trip preservation because it is the only writer.
date: 2026-09-23
source: docs/superpowers/specs/2026-09-23-kb-design.md

## decision/graph-as-documents
The primary model is a graph whose serialization is documents: one file per artifact, parts inline with ids, references a schema primitive.
date: 2026-09-23
source: docs/superpowers/specs/2026-09-23-kb-design.md

## decision/shared-parts-are-artifacts
A thing used from more than one artifact, or changing independently of its container, is its own artifact, referenced with bindings by each using artifact; state that belongs to a use lives on the artifact representing the use, never on the thing.
date: 2026-09-23
revisit_when: a use needs state the bindings cannot carry
source: docs/superpowers/specs/2026-09-23-kb-design.md

## decision/one-current-corpus
Versions float: there is one current corpus, and executions snapshot what they read through the journal.
date: 2026-09-23
revisit_when: an execution's behaviour cannot be explained from its snapshot
source: docs/superpowers/specs/2026-09-23-kb-design.md

## decision/types-are-data
Types are data; anything behavioural about a type is client code, and a client adds a type through the contract alone.
date: 2026-09-23
revisit_when: a new type needs a change to kb
source: docs/superpowers/specs/2026-09-23-kb-design.md

## decision/validation-engine
Validation uses python-jsonschema with the `referencing` library, extended with kb keywords, so the JSON Schema side is checked natively in one pass and code checks only what the schema language cannot express.
date: 2026-09-23
source: docs/superpowers/specs/2026-09-23-kb-design.md

## decision/runtime-shape
The core is a library behind a protobuf contract; the same servicer is reached in-process or through a gRPC server.
date: 2026-09-23
source: docs/superpowers/specs/2026-09-23-kb-design.md

## decision/scale
One repository, an incremental load cache, batch operations under one lock, and a server when callers are several; no daemon.
date: 2026-09-23
revisit_when: the lock queue grows
source: docs/superpowers/specs/2026-09-23-kb-design.md

## decision/contract-stability
The API is the stable boundary; storage, git-first included, may change behind it.
date: 2026-09-23
source: docs/superpowers/specs/2026-09-23-kb-design.md

## decision/summary-is-enough-to-navigate
A summary read carries stubs of what an artifact points at and counts of what points at it, enough to move through the graph without whole reads.
date: 2026-09-23
revisit_when: clients routinely follow a summary with a whole read of the same artifact
source: docs/superpowers/specs/2026-09-23-kb-design.md

## decision/section-reads-are-the-common-read
Reading one section by title is the read kb expects agents to make most.
date: 2026-09-23
revisit_when: section reads are rare and whole reads are the norm
source: docs/superpowers/specs/2026-09-23-kb-design.md

## decision/typed-refs-cover-the-questions
List, follow-links and search are the whole query surface.
date: 2026-09-23
revisit_when: a question needs a traversal the contract cannot express
source: docs/superpowers/specs/2026-09-23-kb-design.md

## decision/every-fault-at-once
A refused change returns every fault found, not the first.
date: 2026-09-23
revisit_when: callers fix one fault per attempt anyway
source: docs/superpowers/specs/2026-09-23-kb-design.md

## decision/a-refused-write-changes-nothing
A change, single or in a set, is applied to a copy, validated against the corpus, and swapped in only on success.
date: 2026-09-23
revisit_when: a rejected write is observable afterwards
source: docs/superpowers/specs/2026-09-23-kb-design.md

## decision/refuse-is-enough-for-deletes
The only delete rule is refuse, naming every reference that blocks it.
date: 2026-09-23
revisit_when: operators need cascade or detach
source: docs/superpowers/specs/2026-09-23-kb-design.md

## decision/stale-is-safe
An artifact behind its type's version is reported stale, never failed, and can be read and written until someone updates it.
date: 2026-09-23
revisit_when: a stale artifact causes wrong behaviour
source: docs/superpowers/specs/2026-09-23-kb-design.md

## decision/composition-covers-common-fields
Types share fields only by `allOf` with `$ref`, kb's keywords composing base first; no type hierarchy.
date: 2026-09-23
revisit_when: a type needs to override or mix in
source: docs/superpowers/specs/2026-09-23-kb-design.md

## decision/every-change-is-attributable
Each journal entry carries actor, execution, message and a fingerprint per operation.
date: 2026-09-23
revisit_when: a question about how the store got here cannot be answered from the journal
source: docs/superpowers/specs/2026-09-23-kb-design.md

## decision/git-serves-time-travel
The contract has no historical read; git serves past states.
date: 2026-09-23
revisit_when: a client needs a past state through the contract
source: docs/superpowers/specs/2026-09-23-kb-design.md

## decision/restore-on-commit-failure
On a git failure after files are written, kb restores the files from HEAD and reports the failure; no scenario pins it.
date: 2026-09-23
revisit_when: a failed commit ever leaves a stray file
source: docs/superpowers/specs/2026-09-23-kb-design.md

## decision/search-ranking
Search ranks matches by term frequency in the section; ranking beyond that is open.
date: 2026-09-23
source: docs/superpowers/specs/2026-09-23-kb-design.md

## decision/resolve-depth-defaults-to-zero
A read takes a resolve depth whose default is 0, so links come back as names unless following is asked for; a cycle still ends at a name.
date: 2026-09-30
supersedes: decision/0009-resolve-depth-and-cycles
source: this migration's gate (the approved scenario read-an-artifact / "Without being asked to follow them, links come back as names")

## decision/init-refuses-inside-or-above
Starting a store is refused only where a store sits directly inside the named directory or above it; a store deeper below the named directory does not refuse it. This supersedes 0003's "above or below" only; 0003's discovery rule stands.
date: 2026-09-30
supersedes: decision/0003-init-refuses-inside-a-store
source: the migration gate

## decision/scale-without-a-lock
One repository, an incremental load cache, batch operations, and, when callers are several, a server that takes changes one at a time; there is no lock and no daemon.
date: 2026-09-30
revisit_when: changes wait at the server in growing numbers
supersedes: decision/scale
source: the migration gate; adrs/0020-a-server-found-where-the-store-is.md

## decision/sqlite-canonical
The store is one SQLite database, `kb/store.sqlite3` in WAL mode beside its marker `kb/store.yaml`, and canonical YAML 1.2, read and written by kb alone, is its export and wire form rather than its storage; chosen after a spike in which SQLite met every criterion fixed beforehand at 30,000 documents (reads and three-step traversals in about 0.02 ms, search in 4 ms, every race closed by its write lock and a revision compare-and-set), while TerminusDB 12.0.7 met two outright and the rest only with adapter code working around it.
date: 2026-10-01
supersedes: decision/0001-yaml-1-2-git-canonical
source: docs/superpowers/specs/2026-10-01-kb-storage-sqlite-design.md

## decision/kb-runs-no-git
Git is no longer kb's store and kb runs no git at all: starting a store makes no repository, the history is rows in the store's database, and committing exported files to git is the operator's choice.
date: 2026-10-01
supersedes: decision/0019-kb-git-owns-its-store
source: docs/superpowers/specs/2026-10-01-kb-storage-sqlite-design.md

## decision/files-are-an-export
Reviewable files are the operator's output, written on demand by `kb export` as canonical YAML; files on disk enter a store only through `kb import`, which checks them first and lands only in a freshly started store, one holding no artifact besides the type that describes types.
date: 2026-10-01
revisit_when: someone needs to combine stores
source: docs/superpowers/specs/2026-10-01-kb-storage-sqlite-design.md

## decision/storage-behind-a-port
kb's own rules (names, content checks, sections and items, signatures, faults, the contract) stay above a kb-internal, unpublished port and an adapter keeps the graph below it; SQLite is the first adapter, any other is gated by the same conformance tests, and the public contract, its rule names included, does not change with it.
date: 2026-10-01
revisit_when: a workload needs queries the port cannot answer within its bounds, such as transitive or pattern queries over transcripts and work state
source: docs/superpowers/specs/2026-10-01-kb-storage-sqlite-design.md

## decision/integrity-checked-both-ways
A change is checked for the links into what it changes as well as the links it carries: dropping an item, or removing an artifact or a type, that anything outside the set links into is refused with the published rule `on_delete` (`linked` is only the port's internal name), every artifact carrying one implicit link to its type, and the adapter re-checks this inside its write transaction so a concurrent change cannot slip between the check and the write.
date: 2026-10-01
source: docs/superpowers/specs/2026-10-01-kb-storage-sqlite-design.md

## decision/write-lock-on-one-machine
On one machine the database's write lock serialises writers across threads and processes, each change's revision compared inside the transaction and, on a mismatch, the change re-drafted against the new state and landed, so no client sees a conflict; readers never wait; across containers callers share a store through a server (0020), because SQLite over a network filesystem is not safe; there is no daemon.
date: 2026-10-01
supersedes: decision/scale-without-a-lock
source: docs/superpowers/specs/2026-10-01-kb-storage-sqlite-design.md

## decision/a-set-lands-in-one-transaction
A set lands in one database transaction, so a failure part-way leaves nothing written and nothing to restore.
date: 2026-10-01
supersedes: decision/restore-on-commit-failure
source: docs/superpowers/specs/2026-10-01-kb-storage-sqlite-design.md

## decision/a-set-is-checked-whole
A set is checked once as a whole against the state it leaves, so its changes may point at each other and rely on any other in the set; each separate change is checked against the state the one before it left.
date: 2026-10-01
source: docs/superpowers/specs/2026-10-01-kb-storage-sqlite-design.md

## decision/performance-bounds
At 30,000 artifacts a summary read and a three-step traversal take under 100 ms each, a single change under 50 ms and a set of 100 changes under 1 s, checked by a benchmark kept in the repository rather than by scenarios; a release that misses one does not ship.
date: 2026-10-01
revisit_when: the scale targets are set
source: docs/superpowers/specs/2026-10-01-kb-storage-sqlite-design.md

## decision/damaged-database-one-fault
A database that cannot be opened or read refuses every call and every command with one fault, rule `unreadable`, naming the database, and writes nothing; damage to files is found by the import check, not by the store.
date: 2026-10-01
source: docs/superpowers/specs/2026-10-01-kb-storage-sqlite-design.md

## decision/past-states-kept-not-yet-read
The contract has no historical read; the store keeps each artifact's content at every revision, which the contract's next version will read.
date: 2026-10-01
revisit_when: a client needs a past state through the contract
supersedes: decision/git-serves-time-travel
source: docs/superpowers/specs/2026-10-01-kb-storage-sqlite-design.md

## decision/graph-as-records
The primary model is a graph held as one record per artifact, parts inline with ids, references a schema primitive.
date: 2026-10-01
supersedes: decision/graph-as-documents
source: docs/superpowers/specs/2026-10-01-kb-storage-sqlite-design.md

## decision/yaml-is-export-and-wire
Canonical YAML is the export and wire form, read with a standard parser and emitted canonically by kb alone.
date: 2026-10-01
supersedes: decision/serialization-yaml
source: docs/superpowers/specs/2026-10-01-kb-storage-sqlite-design.md

## decision/storage-may-change
The API is the stable boundary; storage may change behind it, and changed to SQLite in note 1.
date: 2026-10-01
supersedes: decision/contract-stability
source: docs/superpowers/specs/2026-10-01-kb-storage-sqlite-design.md
