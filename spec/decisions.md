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

## decision/a-set-is-checked-whole-links-and-types
A set's links and types are checked once against the state the whole set leaves, so its changes may point at each other, earlier or later, while each change acts on the store as the changes before it in the set left it; each separate change is checked against the state the one before it left.
date: 2026-10-01
supersedes: decision/a-set-is-checked-whole
source: docs/superpowers/specs/2026-10-01-kb-storage-sqlite-design.md; the formulation question on make-several-changes-in-one-go #9, answered 2026-10-01

## decision/clock-failure-rule
A clock that fails during a change gives the client a fault with rule `clock`, no artifact and no path, and `clock` joins kb's published rule names, since no existing name fits and the list is closed.
date: 2026-10-01
source: docs/superpowers/specs/2026-10-01-kb-storage-sqlite-design.md; the controller's answer of 2026-10-01

## decision/read-only-store-unreadable
A store whose database cannot be opened for writing, because the directory, the file or the mount it is on is read-only, is a database that cannot be read, refused with rule `unreadable` and nothing written, as a damaged or missing one is; kb does not read a read-only store until what one means is defined (whether it may be read while nothing may change it, what its history says, how a served store relates to it).
date: 2026-10-01
source: docs/superpowers/specs/2026-10-01-kb-pr1-review-answers.md

## decision/busy-rule
A change, a set or the operator's import that waits for the write lock longer than the store waits is refused with a rule of its own, `busy`, which joins kb's published rule names, nothing written and the same change free to be made again; not `unreadable`, whose advice (the store is damaged or missing) is wrong for it; reads never wait for the lock, so none is refused as busy.
date: 2026-10-01
source: docs/superpowers/specs/2026-10-01-kb-pr1-review-answers.md

## decision/earlier-store-told-apart
The store's marker says which form of store it marks, so a store made by an earlier kb in a form this kb cannot read is told apart: it counts as a store when one is started and when it is found, and every call and command that needs it, the import included, is refused, saying to start a new store and import the old one's files, an earlier kb's store being only ever an import's source; its rule is `unreadable`, since what the client can do about it is the same (this kb cannot read the store), and only the reason differs.
date: 2026-10-01
source: docs/superpowers/specs/2026-10-01-kb-pr1-review-answers.md; the person's answers of 2026-10-01 to the integration's questions 3 and 9

## decision/history-ordered-per-artifact
Moments order each artifact's history, not the whole store's: one artifact's entries come in the order its changes landed, entries across artifacts in the order of their moments, and a read since a moment gives what is stamped from that moment on as the store holds it when read, so a client following the history reads since a moment a little before the last one it saw and drops the entries it already has.
date: 2026-10-01
source: docs/superpowers/specs/2026-10-01-kb-pr1-review-answers.md

## decision/snapshot-and-reads-under-busy
A snapshot writes to the store, so it is a call that changes the store and is refused as `busy` like a change; kb export and kb validate are reads and are never refused as busy; where entries for different artifacts carry the same moment they are given in the order they landed, and a read of one artifact's history keeps landing order even where its moments run the other way.
date: 2026-10-01
source: docs/superpowers/specs/2026-10-01-kb-pr1-review-answers.md; the person's answers of 2026-10-01 to the integration's questions 5 to 8

## decision/contract-v1
kb's contract is published again as one breaking release in which every rpc is renamed or reshaped, what a call does unchanged except where note 2 changes it, and its package is `kb.v1`, so a client of one version calling a server of another is refused by the transport rather than answered wrongly.
date: 2026-10-01
source: docs/superpowers/specs/2026-10-01-kb-contract-v1-design.md

## decision/starting-leaves-the-wire
A store is started by the operator's `kb init` or by a client in its own process calling `kb.init(root, role)`, which takes the same optional clock `connect` takes and raises `kb.NotStarted` carrying the faults when it refuses; there is no `Init` rpc, a served store cannot be started through its server, and starting keeps every behaviour it had, only the way it is asked for changing.
date: 2026-10-01
source: docs/superpowers/specs/2026-10-01-kb-contract-v1-design.md; the controller's answer to the integration's question 5, under the person's delegation of 2026-10-01

## decision/one-method-per-action
Every rpc is one action named in the spec's words (`Create`, `Replace`, `Add`, `Remove`, `Read`, `List`, `Follow`, `Search`, `History`, `Snapshot`, `Check`) with a request and a response message of its own, no message shared between two requests except the small values every call names things with (a locator, a signature, a fault, a stub); a kind is called a kind and a place a place, never a type or a path, wherever a request or a response names one.
date: 2026-10-01
source: docs/superpowers/specs/2026-10-01-kb-contract-v1-design.md

## decision/sets-one-kind-at-a-time
`Apply` and its four operation messages go; a set is one kind of change at a time, `CreateMany`, `ReplaceMany`, `AddMany` or `RemoveMany`, and never mixes kinds, so a create and a replacement are two calls; a set still lands whole or not at all, is checked against the state the whole set leaves, names itself and gives each change's own result.
date: 2026-10-01
source: docs/superpowers/specs/2026-10-01-kb-contract-v1-design.md

## decision/references-inside-a-set
A create in `CreateMany` may carry a key of the client's choosing, unique in the set, and a link written `@<key>` anywhere in the set names the artifact that create makes, kb putting the minted name in its place before anything is checked; a reference names a whole artifact, never a part; a key no create carries, a key two creates carry, and a key with a place are refused with rule `ref`.
date: 2026-10-01
source: docs/superpowers/specs/2026-10-01-kb-contract-v1-design.md; the controller's answers to the integration's questions 1, 2 and 8, under the person's delegation of 2026-10-01

## decision/expected-revision
`Replace`, `Add` and `Remove`, alone or in a set, may say the revision the client read the artifact at, and are then refused, with nothing of the set written, when the artifact stands at another revision as the change lands, a later change in a set to an artifact an earlier one changed being compared with the revision that earlier one left; the refusal names the revision it stands at and carries a rule of its own, `revision`, which joins kb's published rule names; a change that says none acts on the artifact as it stands.
date: 2026-10-01
source: docs/superpowers/specs/2026-10-01-kb-contract-v1-design.md; the controller's answers to the integration's questions 3 and 4, under the person's delegation of 2026-10-01

## decision/write-lock-and-expected-revision
On one machine the database's write lock serialises writers across threads and processes, each change's revision compared inside the transaction; on a mismatch a change that says no expected revision is re-drafted against the new state and landed, so its client sees no conflict, and one that says an expected revision is refused with rule `revision`; readers never wait; across containers callers share a store through a server (0020), because SQLite over a network filesystem is not safe; there is no daemon.
date: 2026-10-01
supersedes: decision/write-lock-on-one-machine
source: docs/superpowers/specs/2026-10-01-kb-contract-v1-design.md

## decision/one-signature
Every request that changes the store, and `Snapshot`, carries one `Signature` holding the role, the piece of work and the message, a snapshot's piece of work being its signature's; the rules of signing do not change, only the shape they arrive in.
date: 2026-10-01
source: docs/superpowers/specs/2026-10-01-kb-contract-v1-design.md

## decision/result-or-refusal
Every response is either the call's result or a refusal holding every fault, never both: a refusal carries no half-filled result and a result carries no faults; `Check`'s result is the violations and the stale, the violations being what the store holds, not a refusal.
date: 2026-10-01
source: docs/superpowers/specs/2026-10-01-kb-contract-v1-design.md

## decision/read-asks-for-one-level
A `Read` asks for one level, a summary, the whole artifact with its links followed to a depth, or one section by its title, and its request carries only what that level takes.
date: 2026-10-01
source: docs/superpowers/specs/2026-10-01-kb-contract-v1-design.md

## decision/published-contract-v1
What a client may depend on is still versioned together by the release tag: `kb.proto` in package `kb.v1`, `kb.init` and `kb.NotStarted`, `kb.client.connect` with its clock, `kb.content`, the connection file's form, and every fault's `rule` name; everything else may change without notice.
date: 2026-10-01
supersedes: decision/0018-the-published-contract
source: docs/superpowers/specs/2026-10-01-kb-contract-v1-design.md

## decision/operator-directory-refused-by-shape
Export aimed at a file, and a check for import or an import aimed at something that is not a directory, are refused with rule `root`, because export writes into a directory and files for import are read from one; the export leaves the file as it was and the check and import write nothing.
date: 2026-10-01
source: docs/superpowers/specs/2026-10-01-kb-eleventh-review-answers.md

## decision/later-store-told-apart
A store whose marker names a form of store this kb does not know, one a later kb made, and a store whose marker cannot be read at all, whatever its bytes, are told apart from a damaged database: every call and command that needs the store, the import included, is refused because the store was made by a later version of kb, which is needed to read it, nothing is written, and the store is not opened; starting a store over one is refused as over any store. The rule is `unreadable`, as for an earlier kb's store, since what the client can do is the same (this kb cannot read the store).
date: 2026-10-01
source: docs/superpowers/specs/2026-10-01-kb-batch24-review-answers.md; the controller's answer to the integration's question 1, under the person's delegation

## decision/paired-escapes-are-one-character
Content may write a character beyond the first 65,536 as two escapes, one for each half, as JSON does, and reads back holding that one character; half of a character alone, in either order, is still refused because the content cannot be read as written.
date: 2026-10-01
source: docs/superpowers/specs/2026-10-01-kb-batch24-review-answers.md

## decision/type-language-stays-json-schema
kb keeps JSON Schema 2020-12, with its own keywords, as the language types are written in, not a smaller structural model of kb's own: the one client's eight types use about ten JSON Schema keywords and fit inside it; a replacement would break contract v1 (a fault's rule is the JSON Schema keyword it breaks) and every type a store holds, with no migration to carry them; and kb would rebuild the validator, its errors and the type of types that the library gives it today.
date: 2026-10-01
revisit_when: a client needs a type JSON Schema cannot state, or types must migrate between versions
source: docs/superpowers/specs/2026-10-01-kb-type-language-design.md; the controller's recommendation under the person's delegation of 2026-10-01

## decision/kb-keywords-read-where-written
A type carrying one of kb's keywords where kb does not read it is refused, naming the place, with nothing written, because until now a `ref` nested in an object or a `oneOf` branch was accepted and never read as a link (not checked to land, not counted, not holding up a removal): `ref` is read only on a field directly under `properties` of the type, of a base it is built on, of the items of any of its collections at any depth, or of a named shape another field uses; `parts` and `summary` only at the top of a type's schema or of a collection's items; `sections` only at the top of a type's schema; the `parts` inside a `ref` is the ref's own. A `ref` must state `targets`, `cardinality` (one or many), `parts` and `on_delete` (refuse, the one rule kb knows), or the type is refused, naming the place, with nothing written. A misplaced or incomplete `ref`, or one with a `cardinality` or `on_delete` kb does not know, carries rule `ref`, a missing `targets` keeps `targets`, and a misplaced `parts`, `sections` or `summary` carries `placement`, which joins kb's published rule names. Where kb reads its keywords and the shape of a `ref` are published as the rule a client defines types by. A type the store already holds stays as it is until it is next changed, when the change is refused if the type as changed still carries one. Every other JSON Schema keyword stays open to types.
date: 2026-10-01
source: docs/superpowers/specs/2026-10-01-kb-type-language-design.md; the controller's answers to the integration's questions, under the person's delegation of 2026-10-01

## decision/metaschema-from-a-registry-of-kbs-own
The type of types resolves the 2020-12 metaschema through a registry kb builds itself from the library's published specifications, declared as kb's dependency, not through what the validator happens to add.
date: 2026-10-01
source: docs/superpowers/specs/2026-10-01-kb-type-language-design.md

## decision/faults-ordered-by-place-then-rule
Faults come in an order kb decides, not the order the library finds them in: by place, places in the order they stand in the artifact, then by rule; across the changes of a set, in the order of the set. This holds for a refused artifact, a type refused as it is written, each change of a set, and each artifact's violations in a check.
date: 2026-10-01
source: docs/superpowers/specs/2026-10-01-kb-type-language-design.md; the controller's answers to the integration's questions, under the person's delegation of 2026-10-01

## decision/faults-ordered-by-reading-order-then-rule-name
Faults at different places come in the order the artifact reads back in, which is its type's declared order and the order the store writes it in (a collection's items in their order, sections in their order, a section's inner sections after it), not the order the client wrote it in; faults at one place come by rule name, alphabetically; a type refused as it is written has the places of the type as it reads back; across the changes of a set, the order of the set. This holds for a refused artifact, a type refused as it is written, each change of a set, and each artifact's violations in a check.
date: 2026-10-01
supersedes: decision/faults-ordered-by-place-then-rule
source: the person's answers under their delegation of 2026-10-01, to the questions on the fault-order lines of check-a-change, check-the-store, make-several-changes-in-one-go and define-a-type

## decision/no-held-types-before-the-placement-rule
A type the store held before kb read its keywords only where it reads them is not provided for: there are no stores or clients to carry, as everything is new code, so a type is checked against the placement rule whenever it is written and the lines about held types are removed.
date: 2026-10-01
supersedes: decision/kb-keywords-read-where-written (its clause on a type the store already holds)
source: the person, 2026-10-01: "Don't worry about migration. This is all new code so migration is not needed at this point"

## decision/links-read-only-where-kb-reads-them-today
A link field is read only directly among the fields of a type, of a base it is built on, or of the items of any of its collections at any depth; one in a named shape another field uses is refused like any other misplaced link field, because kb has never read links there and reading them would be new behaviour the type-language note does not ask for.
date: 2026-10-01
supersedes: decision/kb-keywords-read-where-written (its clause on a named shape another field uses)
source: the batch 26 planning question, decided by the controller under the person's delegation of 2026-10-01

## decision/a-types-faults-in-the-order-it-was-written
A type reads back exactly as it was written, so a type refused with several faults has them in the order its places stand as it was written, then by rule name; there is no declared order for a type's own entries.
date: 2026-10-01
supersedes: decision/faults-ordered-by-reading-order-then-rule-name (its clause on a type's places)
source: the batch 26 planning question, decided by the controller under the person's delegation of 2026-10-01

## decision/summary-read-only-at-the-top
The fields shown at a glance (`summary`) are read only at the top of a type's schema; one at the top of a collection's items is refused like any misplaced keyword, rule `placement`, because a part's stub carries only its collection, name and title and kb reads `summary` nowhere else; showing item fields in part stubs would change the published contract and no client asks for it.
date: 2026-10-01
supersedes: decision/kb-keywords-read-where-written (its clause on `summary` at the top of a collection's items)
source: the batch 26 review's question, decided by the controller under the person's delegation of 2026-10-01
