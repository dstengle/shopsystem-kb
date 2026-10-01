# Answers to the batch 24 review

Date: 2026-10-01. The review is at /home/vscode/kb-reviews/batch24-review.md. The person delegated every question to
the controller's recommendations on 2026-10-01.

## A store made by a later kb

The store's marker says which form of store it marks. A store whose marker names a form this kb does not know (one
a later kb made) is not opened: every call other than starting a store, and the operator's kb validate, kb export
and kb import, is refused because the store was made by a later version of kb, which is needed to read it, and
nothing is written. A marker that cannot be read at all, whatever its bytes, is no form this kb knows either, and is
refused the same way rather than breaking off. The rule is `unreadable`, as for an earlier kb's store.

## A character written as two escapes

Content may write a character beyond the first 65,536 as two escapes, one for each half, as JSON does. Read
together, the two halves are that one character, and the content reads back holding it. Half of a character alone,
with no other half beside it, is still refused because the content cannot be read as written.
