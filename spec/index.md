# kb

## Purpose

kb is a schema-typed, graph-oriented artifact store. It holds typed documents whose parts are addressable nodes, checks every change against types that are themselves stored artifacts, keeps a git repository as the canonical serialization, and exposes one versioned contract that an in-process client and a network server both host.

kb knows nothing about any domain. It ships no type beyond the one that describes types, and no renderers. A client such as shop-knowledge supplies the types, the seed content and every presentation of the data. Renderers of any kind (a markdown projection included), domain types and seed content, and MCP or any other presentation of the contract are not kb's.

## Constraints carried

- Git is canonical. The contract is the only access path. The store is derived.
- Every change goes through the contract: validate, write, journal, serialize, commit. Nothing else edits the serialized text.
- Artifacts are typed, ordered documents. Domain parts are typed nodes with names, never text quoted inside a code fence. Inline formatting is never modelled; a prose body is one markdown string.
- Renderings are outputs written elsewhere, never stored in their source, and never in the store's tree.
- Every artifact carries the version of the type it was last checked against. Migration is not built; versioning is.
- The boundary is enforced mechanically: a corpus-only role gets the client and no shell; a shell-bearing role runs where the repository is not.
- All YAML kb reads or writes is YAML 1.2: content over the contract, types, files on disk, the journal, and the type that describes types.
- What a client may depend on is published and versioned together by kb's release tag, which clients pin: `kb.proto` and its messages, the in-process client's `connect` with its clock, `kb.content` (content as canonical text, and `NotCanonical`), the connection file's form (`kb/server.yaml` and its `address`), and each fault's `rule` name. A fault's message wording, the store's files and layout, and every other module may change behind the contract.
- A fault's `rule` is one of kb's own rule names, or, for content that breaks a type's JSON Schema, the JSON Schema keyword it breaks. kb's own rule names: `not-found`, `kind`, `locator`, `collection`, `identity`, `on_delete`, `unreadable`, `item-name`, `shape`, `built-on`, `targets`, `version`, `content`, `sections`, `ref`, `actor`, `message`, `operations`, `since`, `title`, `root`, `store`.
- Errors are a typed list of `{ artifact, path, rule, message }`.
- Bounds: at most one repository root per store, promoted to more when one store's history outgrows one repository; at most one store above any directory (stores never nest); one delete rule, refuse; a server's network is its only boundary (no authentication or encryption); several callers share a store only through a server, which takes changes one at a time, and there is no lock.

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
9. `capabilities/check-a-change.md`: every change checked against its type before it lands.
10. `capabilities/change-the-store.md`: create, replace, add, remove.
11. `capabilities/make-several-changes-in-one-go.md`: a set of changes, all or nothing.
12. `capabilities/read-an-artifact.md`: reads at every level, links followed to a depth.
13. `capabilities/query-the-store.md`: list, follow links, search.
14. `capabilities/keep-the-history.md`: the journal, its sets and its moments.
15. `capabilities/snapshot-what-work-read.md`: a piece of work records what it read.
16. `capabilities/check-the-store.md`: the whole store against its types.
17. `capabilities/answer-a-damaged-file.md`: a file the store cannot read is a named fault.
18. `capabilities/operate-a-store.md`: the operator's `kb init`, `kb validate`, `kb serve`.
19. `capabilities/review-the-files-on-disk.md`: the files as people read them.

## Order of building

kb and shop-knowledge were one effort until the walking skeleton was green, then two. Feature files for both were formulated in one session from both specs and committed to the repo whose behaviour they describe; every kb scenario cites the shop-knowledge scenario that needs it, and a kb scenario nothing upstream needs is a question for the spec, not a feature. One living plan, kept in shop-knowledge, covered both repos until slice 1 was green: create a decision and read it back through `shop-knol`, which needed `Init`, `Create` and summary `Read` here; the repos were checked out side by side and shop-knowledge installed kb as an editable path dependency; slices in that phase could touch both repos and said which repo each scenario runs in. When slice 1 was green, the messages it needed became the contract's first version: kb was tagged 0.1, shop-knowledge pins it, and from then each repo has its own plan. shop-knowledge's scenarios remain the demand signal for kb, arriving as a request to bump the contract version.

## Testing

kb is built with the shopsystem-bdd workflow. Feature files are formulated from this spec, from the perspective of a client of the contract and, for the admin CLI and the files on disk, of the operator. They are implemented red-green against the in-process transport, and, for the server, against a real `kb serve` started in the test's own temporary directory on a port of its own; no test calls an address it did not start. No test reaches a store outside its own temporary directory. A set of changes is a scenario. Incremental load is not observable through the contract and is measured, not specified.
