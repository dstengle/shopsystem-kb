# kb

A schema-typed, graph-oriented artifact store. Typed documents with
addressable parts, schemas stored as artifacts, one SQLite database as the
canonical store (written out as canonical YAML files on the operator's
`kb export`, and read back by `kb import`), and one versioned API contract
that an in-process client uses today and a server can host later.

## The contract: v1 (kb 0.5.0)

The contract is `kb.v1` (`kb.contract.kb_pb2`), and 0.5.0 is a breaking release: no v0 rpc or request remains (`Actor` stays only as the type of `Entry.actor`).

- Changes: `Create`, `Replace`, `Add` and `Remove`, each taking one `Signature { role, execution, message }` and
  answering its result or a `Refusal`; the same four as sets, `BatchCreate`, `BatchReplace`, `BatchAdd` and
  `BatchRemove`. A `CreateItem` of a set carries a `key`, and links in that set written `@<key>` reach the artifact
  that create makes. An artifact, or a place inside it, is named by a `Locator { id, place }`. A replace, add or remove
  may say the `revision` it read, and is refused with rule `revision` if the artifact moved since.
- Reads: `Read` (one level: `summary`, `whole` with a depth, or `section`), `List`, `Follow`, `Search`, `History`,
  the signed `Snapshot`, and `Check`. They replace v0's `Refs`, `Journal` and `Validate`.
- No rpc starts a store: `kb.init(root, role, *, execution="", clock=None)` does, in your own process, and raises
  `kb.NotStarted` carrying the faults when it refuses. `kb.client.connect(root, *, clock=None)` gives the client.
- `kb.content` publishes `loads`, `dumps`, `text` and `NotCanonical`. The published rule names are listed in spec/index.md, with `busy`
  and `revision` among them; a JSON Schema keyword passes through as the rule of a content fault.

Upgrading a store made by kb 0.3.0: start a new store and import the old
one's files: `kb init <new-root>`, then `kb import <old-root>/kb` run inside
the new store (or with `KB_ROOT=<new-root>`).

kb ships no domain schemas and no renderers. A client such as
[shopsystem-knowledge](https://github.com/dstengle/shopsystem-knowledge)
supplies the types, seed content, and presentation.

Spec: `spec/index.md`. Storage design: `docs/superpowers/specs/2026-10-01-kb-storage-sqlite-design.md`.
`make bench` checks the performance bounds at 30,000 artifacts.

## Developing

Python 3.11. `make dev` installs kb editable with its test and build tools.
`make contract` regenerates `src/kb/contract/kb_pb2*.py` from `kb.proto`;
the generated files are committed. `python -m pytest -q` runs the feature
suite; `python -m pytest -q -m slice-1` runs one slice.
