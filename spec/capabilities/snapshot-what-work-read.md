---
id: capability/missingmass.io/shopsystem/kb/snapshot-what-work-read
title: Snapshot what work read
narrator: the client
rests_on: [design-decision/missingmass.io/shopsystem/kb/journal-batch-and-snapshots, design-decision/missingmass.io/shopsystem/kb/one-current-corpus, design-decision/missingmass.io/shopsystem/kb/signature-refused-before-operations, design-decision/missingmass.io/shopsystem/kb/busy-rule, design-decision/missingmass.io/shopsystem/kb/one-signature, design-decision/missingmass.io/shopsystem/kb/ids-are-chosen-by-the-client-in-a-namespace]
retired: []
---

# Snapshot what work read

## Purpose

A named piece of work records which revisions of which artifacts it read, in one history entry, while the store keeps moving. It is how one floating store is reconciled with reproducible work. A snapshot changes no content, but it writes to the store, so it can be refused as busy like a change.

## Behaviour

- [r1] When the client snapshots artifacts for a piece of work, the history holds one entry listing each of them with the revision read and a fingerprint of it, and the client is given the name of that entry.
- [r2] If a snapshot names no piece of work, names an artifact the store holds nothing under, does not say which role it is or why, or gives either as blank space only, the snapshot is refused naming the reason, and the history holds no entry for it.
- [r3] If a snapshot waits longer than the store waits while another change is being written, the snapshot is refused because the store was busy with another change, the history holds no entry for it, and the same snapshot may be asked for again.

## Implementation, may change

- `Snapshot` takes a `Signature` and artifact IRIs, and returns the journal entry id; the snapshot's piece of work is its signature's. A snapshot entry carries `op: snapshot` and a list of `{ artifact, revision, digest }`, each `artifact` an IRI.
- A snapshot refused as busy is the fault with rule `busy` (change-the-store).

## Not yet

- None.
