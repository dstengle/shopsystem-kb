---
id: design-decision/missingmass.io/shopsystem/kb/a-link-that-waits-keeps-waiting
summary: "A link that already waits on a part its held target lacks does not stand in the way of later changes to the artifact that holds it: a change that leaves the link as it is lands and the link still waits, since another client's create is what made it wait and the store's check already lists it as a placeholder, not a violation. A link a change adds or alters into a part a held artifact lacks is still refused. An import lets such a link wait as the exporting store held it."
date: 2026-10-11
status: accepted
by: "review question (batch 35: an artifact holding a link into a part its filled target lacks could not be changed at all, and its store's export could not be imported), answered under the person's delegation of 2026-10-10"
---

# a-link-that-waits-keeps-waiting

## Decision
A link that already waits on a part its held target lacks does not stand in the way of later changes to the artifact that holds it: a change that leaves the link as it is lands and the link still waits, since another client's create is what made it wait and the store's check already lists it as a placeholder, not a violation. A link a change adds or alters into a part a held artifact lacks is still refused. An import lets such a link wait as the exporting store held it.
