# Answers to the PR #1 review's questions

Date: 2026-10-01. Answers to four questions for the spec raised while reviewing the batch 23 storage change
(kb's store in SQLite behind a port), decided by the person on 2026-10-01: Q12 as they ruled it, Q9, Q3 and Q13 as
recommended.

## A store on a read-only filesystem is not supported (Q12)

What a read-only store would mean is not defined: whether it may be read while nothing may change it, what its
history says, how a served store relates to it. Until it is defined, kb does not read one. A store whose database
cannot be opened for writing, because the directory, the file or the mount it is on is read-only, is a database
that cannot be read: every call and every operator command that needs the store is refused because the database
cannot be read, naming it, and nothing is written, as for a damaged or missing database. Starting a store in a
read-only directory stays refused as it is today.

## A change that waits too long for the write lock is refused as busy (Q9)

On one machine the database's write lock serialises writers. A change that waits for the lock longer than the store
waits (30 seconds today) is refused because the store was busy with another change; nothing is written, and the
same change may be made again. This is not the fault of a database that cannot be read, whose advice (the store is
damaged or missing) is wrong for it. The refusal carries a rule of its own, `busy`, which joins kb's published rule
names. It applies to every call that changes the store and to the operator's import. Reads never wait for the lock,
so no read is refused as busy.

## A store made by an earlier kb is told apart, and told how to move (Q3)

The store's marker says which form of store it marks. Stores started from this change on carry a new marker value;
a store made by kb 0.3.0 carries the old one, with no database beside it. When the store found is one an earlier kb
made, in a form this kb cannot read, every call and every operator command that needs the store other than the
import is refused because the store was made by an earlier version of kb, saying how to move it: start a new store
and import the old one's files. The rule is `unreadable`, since what the client can do about it is the same (the
store cannot be read by this kb); only the reason differs. Nothing is written.

## Moments order each artifact's history, not the whole store's (Q13)

The history gives one artifact's entries in the order its changes landed. Across artifacts, entries are given in
the order of their moments, and two changes to different artifacts made at about the same time can be stamped in
the opposite order to the one they landed in. A read of the history since a moment gives the entries stamped from
that moment on, as the store holds them when it is read; an entry stamped before a moment that lands after a read
since that moment is not given by a later read since the same moment either. A client following the history reads
since a moment a little before the last one it saw and drops the entries it already has.
