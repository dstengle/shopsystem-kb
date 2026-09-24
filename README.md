# kb

A schema-typed, graph-oriented artifact store. Typed documents with
addressable parts, schemas stored as artifacts, a git repository as the
canonical serialization, and one versioned API contract that an in-process
client uses today and a server can host later.

kb ships no domain schemas and no renderers. A client such as
[shopsystem-knowledge](https://github.com/dstengle/shopsystem-knowledge)
supplies the types, seed content, and presentation.

Design: `docs/superpowers/specs/2026-09-23-kb-design.md`.

## Developing

Python 3.11. `make dev` installs kb editable with its test and build tools.
`make contract` regenerates `src/kb/contract/kb_pb2*.py` from `kb.proto`;
the generated files are committed. `python -m pytest -q` runs the feature
suite; `python -m pytest -q -m slice-1` runs one slice.
