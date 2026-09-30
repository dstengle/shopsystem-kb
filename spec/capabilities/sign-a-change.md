---
id: capability/sign-a-change
title: Sign a change
narrator: the client
rests_on: [decision/0012-writes-need-role-and-message, decision/0014-signature-refused-before-operations, decision/0015-missing-message-rule, decision/0017-blank-role-or-message, decision/every-change-is-attributable]
formulated_as: features/sign-a-change.feature
---

# Sign a change

## Purpose

Every change says which role made it and why, so that every entry in the history answers for itself. A change that does not sign is refused before anything is written, whichever call makes it. This capability covers the signature only; what the history records is keep-the-history.

## Behaviour

- If the client creates, changes, adds an item, removes, or asks for several changes in one go without saying which role it is or without saying why, or gives either as blank space only, the change is refused because every entry in the history names the role that made it, or because every entry says why it was made; the artifact reads as before at the revision it held, the store holds no artifact it did not hold before, and the history holds no entry for it.

## Implementation, may change

- The actor is `{ role, execution }`; the message is the request's `message`. The commit's author is the actor and its message the request's.
- A missing role is the fault with rule `actor`, no artifact and no path; a missing message is rule `message`, no artifact and no path.

## Not yet

- None.
