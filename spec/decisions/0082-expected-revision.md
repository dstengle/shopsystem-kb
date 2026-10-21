---
id: design-decision/missingmass.io/shopsystem/kb/expected-revision
summary: "`Replace`, `Add` and `Remove`, alone or in a set, may say the revision the client read the artifact at, and are then refused, with nothing of the set written, when the artifact stands at another revision as the change lands, a later change in a set to an artifact an earlier one changed being compared with the revision that earlier one left; the refusal names the revision it stands at and carries a rule of its own, `revision`, which joins kb's published rule names; a change that says none acts on the artifact as it stands."
date: 2026-10-01
status: accepted
by: ".shop/records/archive/design-notes/2026-10-01-kb-contract-v1-design.md; the controller's answers to the integration's questions 3 and 4, under the person's delegation of 2026-10-01"
---

# expected-revision

## Decision
`Replace`, `Add` and `Remove`, alone or in a set, may say the revision the client read the artifact at, and are then refused, with nothing of the set written, when the artifact stands at another revision as the change lands, a later change in a set to an artifact an earlier one changed being compared with the revision that earlier one left; the refusal names the revision it stands at and carries a rule of its own, `revision`, which joins kb's published rule names; a change that says none acts on the artifact as it stands.
