---
id: capability/keep-the-history
title: Keep the history
narrator: the client
rests_on: [decision/0004-journal-batch-and-snapshots, decision/kb-runs-no-git, decision/every-change-is-attributable, decision/past-states-kept-not-yet-read]
formulated_as: features/keep-the-history.feature
---

# Keep the history

## Purpose

Every change leaves an entry in the store's own history. The entry says when, by which role, for which piece of work, what was done and where, the revision left, a fingerprint, the message, and the set it landed with. The client reads the history, filtered by artifact, role, piece of work, set or moment. Moments are kept in UTC, and a client may give its own clock. This capability does not read past states of content.

## Behaviour

- When the client reads the history of an artifact, there is one entry for each change, and each says when it happened, which role made it, for which piece of work, what it did, to which artifact and place in it, the revision it left, a fingerprint of what was written, the message given, and which set of changes it landed with.
- When the client reads the history, the entries of changes made in one go name the same set, and a change made on its own names itself as its own set.
- When the client reads the history for one role, it is given only that role's entries.
- When the client reads the history for one piece of work, it is given only the entries made for it.
- When the client reads the history since a moment, it is given only the entries made from that moment on, and none made before it.
- Where the client was readied with a clock, when it makes any change, every entry the change left says it happened at the moment the clock gives.
- Where the client's clock stands still, when it makes several changes one after another, each leaves an entry of its own at that moment, each names itself as its own set, and no two name the same set.
- Where several sets land at the same moment, each set's name finds exactly its own changes, and a change made on its own between them names itself as its own set.
- Where the client's clock gives a moment in another zone, the entry records the same moment and gives it in UTC.
- Where the client's clock gives a moment with no zone, the entry records that moment as UTC.
- When the client reads the history since a moment, entries are chosen by the moment itself, whatever zone the clock or the moment asked for was given in, and when none follows it the client is given no entries and no fault.
- When the client reads the history for a set or a role it holds nothing under, it is given no entries and no fault; if the moment it reads since cannot be read as a moment, the read is refused because since names a moment in time.
- When a change was aimed at one place inside an artifact, its history entry names that place.
- Where the client's clock stands still, when it starts a store and then makes a change, the history holds two entries at that moment, each naming itself as its own set.
- Where the client was given no clock, each entry says it happened at the moment the machine's clock gives.
- An entry made at exactly the moment asked for is included.

## Implementation, may change

- A journal entry is `id`, `at`, `actor: { role, execution }`, `op`, `artifact`, `path`, `revision`, `schema_version`, `digest` (sha256 of the canonical bytes after the write), `message` and `batch`: the id of the `Apply` that wrote it, or the entry's own id for a single operation. Snapshot entries keep their shape.
- History entries are rows in the store's database, replacing the journal files. They ride with the set handed to the storage port, named by `journal.py` and fingerprinted from the canonical text.
- The adapter keeps each artifact's content at every revision; today's contract does not read it.
- `Journal` takes filters: artifact, actor, execution, batch, since.
- A clock returns a `datetime`, read as UTC when it has no zone; the journal holds every moment in UTC. The clock is the in-process client's (`connect`) and is part of the published contract.
- An unreadable `since` is the fault with rule `since`.

## Not yet

- Reading a past state through the contract. Promoted when a client needs a past state through the contract (decision/past-states-kept-not-yet-read).
