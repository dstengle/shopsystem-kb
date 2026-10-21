---
id: design-decision/missingmass.io/shopsystem/kb/serving-built
summary: "`kb serve` and the reaching of a served store are built, so serving leaves operate-a-store's Not yet: `kb serve <root> --listen <host:port>` hosts the store at `<root>/kb/` with `grpc.server` and the same servicer an in-process client reaches, and when the search stops at `kb/server.yaml`, `connect` calls the address it names over a gRPC channel with the same method names, requests and responses."
date: 2026-10-06
status: accepted
by: ".shop/records/archive/design-notes/2026-10-06-kb-shop-knowledge-requests-design.md"
---

# serving-built

## Decision
`kb serve` and the reaching of a served store are built, so serving leaves operate-a-store's Not yet: `kb serve <root> --listen <host:port>` hosts the store at `<root>/kb/` with `grpc.server` and the same servicer an in-process client reaches, and when the search stops at `kb/server.yaml`, `connect` calls the address it names over a gRPC channel with the same method names, requests and responses.
