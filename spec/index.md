# kb

## Purpose

kb is a schema-typed, graph-oriented artifact store. It holds typed documents whose parts are addressable nodes, checks every change against types that are themselves stored artifacts, keeps its graph in one SQLite database behind an internal port, writes reviewable canonical YAML files on the operator's demand, and exposes one versioned contract that an in-process client and a network server both host.

kb knows nothing about any domain. It ships no type beyond the one that describes types, and no renderers. A client such as shop-knowledge supplies the types, the seed content and every presentation of the data. Renderers of any kind (a markdown projection included), domain types and seed content, and MCP or any other presentation of the contract are not kb's.

## Constraints carried

- The database is canonical; canonical YAML is its export and wire form. The contract is the only access path for clients; files on disk enter a store only through the operator's import, checked first, into a freshly started store. kb runs no git.
- Every change goes through the contract or the operator's import: drafted, checked, then landed with its history in one transaction. Nothing else edits the store.
- Artifacts are typed, ordered documents. Domain parts are typed nodes with names, never text quoted inside a code fence. Inline formatting is never modelled; a prose body is one markdown string.
- Renderings are outputs written elsewhere, never stored in their source, and never in the store's tree.
- Every artifact carries the version of the type it was last checked against. Migration is not built; versioning is.
- The boundary is enforced mechanically: a corpus-only role gets the client and no shell; a shell-bearing role runs where the store is not.
- All YAML kb reads or writes is YAML 1.2: content over the contract, types, exported and imported files, and the type that describes types.
- What a client may depend on is published and versioned together by kb's release tag, which clients pin: `kb.proto` and its messages, the in-process client's `connect` with its clock, `kb.content` (content as canonical text, and `NotCanonical`), the connection file's form (`kb/server.yaml` and its `address`), and each fault's `rule` name. A fault's message wording, the store's files and layout, the storage port and every other module may change behind the contract.
- A fault's `rule` is one of kb's own rule names, or, for content that breaks a type's JSON Schema, the JSON Schema keyword it breaks. kb's own rule names: `not-found`, `kind`, `locator`, `collection`, `identity`, `on_delete`, `unreadable`, `item-name`, `shape`, `built-on`, `targets`, `version`, `content`, `sections`, `ref`, `actor`, `message`, `operations`, `since`, `title`, `root`, `store`, `clock`.
- Errors are a typed list of `{ artifact, path, rule, message }`.
- Bounds: one database per store; at most one store above any directory (stores never nest); one delete rule, refuse; a server's network is its only boundary (no authentication or encryption); on one machine several callers share a store directly, the database's write lock serialising their changes, and across containers only through a server, which takes changes one at a time.
- Performance bounds, at 30,000 artifacts: a summary read and a three-step traversal under 100 ms each; a single change under 50 ms; a set of 100 changes under 1 s. Provisional until the scale targets are set.

## Composition

Reading order:

1. `capabilities/start-a-store.md`: the client brings a store into being.
2. `capabilities/find-the-store.md`: every other call finds its store from where the client works or `KB_ROOT`.
3. `capabilities/reach-a-served-store.md`: a store served to several callers over the network.
4. `capabilities/define-a-type.md`: types as data, composition, versions.
5. `capabilities/hand-over-content.md`: how content handed to the store is read.
6. `capabilities/name-artifacts-and-items.md`: names minted from titles and positions.
7. `capabilities/name-what-is-asked-for.md`: names, kinds and places checked and resolved.
8. `capabilities/sign-a-change.md`: every change carries a role and a reason.
9. `capabilities/check-a-change.md`: every change checked against its type and the links into it before it lands.
10. `capabilities/change-the-store.md`: create, replace, add, remove, alone or alongside other writers.
11. `capabilities/make-several-changes-in-one-go.md`: a set of changes, checked whole, all or nothing.
12. `capabilities/read-an-artifact.md`: reads at every level, links followed to a depth.
13. `capabilities/query-the-store.md`: list, follow links, search.
14. `capabilities/keep-the-history.md`: the history, its sets and its moments.
15. `capabilities/snapshot-what-work-read.md`: a piece of work records what it read.
16. `capabilities/check-the-store.md`: the whole store against its types.
17. `capabilities/answer-a-damaged-file.md`: a database the store cannot read is a named fault.
18. `capabilities/operate-a-store.md`: the operator's `kb init`, `kb validate`, `kb serve`.
19. `capabilities/export-and-import-a-store.md`: the operator's `kb export` and `kb import`, the files as people read them.

## Order of building

kb and shop-knowledge were one effort until the walking skeleton was green, then two. Feature files for both were formulated in one session from both specs and committed to the repo whose behaviour they describe; every kb scenario cites the shop-knowledge scenario that needs it, and a kb scenario nothing upstream needs is a question for the spec, not a feature. One living plan, kept in shop-knowledge, covered both repos until slice 1 was green: create a decision and read it back through `shop-knol`, which needed `Init`, `Create` and summary `Read` here; the repos were checked out side by side and shop-knowledge installed kb as an editable path dependency; slices in that phase could touch both repos and said which repo each scenario runs in. When slice 1 was green, the messages it needed became the contract's first version: kb was tagged 0.1, shop-knowledge pins it, and from then each repo has its own plan. shop-knowledge's scenarios remain the demand signal for kb, arriving as a request to bump the contract version.

Three changes follow, built in order: (1) storage behind a port with SQLite as its first adapter, behind today's contract; (2) the public contract's v1 (starting a store off the wire, one method per action with its own request and response, batches per kind with references inside a set, an expected revision on changes, one signature message, a versioned package, result or refusal); (3) the type language, if still wanted.

## Testing

kb is built with the shopsystem-bdd workflow. Feature files are formulated from this spec, from the perspective of a client of the contract and, for the admin CLI, export and import, of the operator. They are implemented red-green against the in-process transport, and, for the server, against a real `kb serve` started in the test's own temporary directory on a port of its own; no test calls an address it did not start. No test reaches a store outside its own temporary directory. A set of changes is a scenario. Every storage adapter passes the same conformance tests of the port. The performance bounds are checked by a benchmark kept in the repository, not by scenarios; a release that misses one does not ship.
