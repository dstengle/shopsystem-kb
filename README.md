# kb

A schema-typed, graph-oriented artifact store. Typed documents with
addressable parts, schemas stored as artifacts, a git repository as the
canonical serialization, and one versioned API contract that an in-process
client uses today and a server can host later.

kb ships no domain schemas and no renderers. A client such as
[shopsystem-knowledge](https://github.com/dstengle/shopsystem-knowledge)
supplies the types, seed content, and presentation.

Design: `docs/superpowers/specs/2026-09-23-kb-design.md`.
