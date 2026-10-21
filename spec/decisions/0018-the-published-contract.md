---
id: design-decision/missingmass.io/shopsystem/kb/the-published-contract
summary: "A client depends on kb only through `kb.proto` and `kb.contract.kb_pb2`, `kb.client.connect` with its clock, `kb.content` (`loads`, `dumps`, `text`, `NotCanonical`), the connection file's form, and every fault's `rule` name, versioned together by the release tag; everything else may change without notice (refines 0008)."
date: 2026-09-27
status: superseded
by: ".shop/records/decision-arguments/0018-the-published-contract.md"
source: decision-argument/missingmass.io/shopsystem/kb/0018-the-published-contract
---

# the-published-contract

## Decision
A client depends on kb only through `kb.proto` and `kb.contract.kb_pb2`, `kb.client.connect` with its clock, `kb.content` (`loads`, `dumps`, `text`, `NotCanonical`), the connection file's form, and every fault's `rule` name, versioned together by the release tag; everything else may change without notice (refines 0008).
