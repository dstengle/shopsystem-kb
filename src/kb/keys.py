"""A set's keys: each key a create in the set carries, standing for the name that create was given, and every link
written `@` and a key in what the set's creates made holding that name in its place, put in the draft once every
create in the set has acted and before anything the set leaves is checked. A link written `@` and anything no create
carries as its key is left as it is written, and lands on nothing."""
from kb import changes, composition, links, names
from kb.draft import Draft
from kb.edits import Change


def resolved(draft: Draft, operations: list, outcomes: list) -> list:
    """What each operation of a set did, every link to a key in what its creates made holding the name that key
    stands for, in the draft too."""
    minted = {
        operation.key: outcome.artifact_id for operation, outcome in zip(operations, outcomes, strict=True)
        if isinstance(operation, changes.Create) and operation.key and isinstance(outcome, Change)
    }
    if not minted:
        return outcomes
    return [_named(draft, outcome, minted) if _created(outcome) else outcome for outcome in outcomes]


def _created(outcome) -> bool:
    return isinstance(outcome, Change) and outcome.op == "create"


def _named(draft: Draft, change: Change, minted: dict) -> Change:
    """A create's artifact with each link to a key holding the name that key stands for."""
    schema = composition.kind_schema(change.artifact_id.kind, draft)["schema"]
    left = links.rewritten(change.left, schema, draft, lambda link: _target(link.target, minted))
    draft.put(change.artifact_id, left)
    return change._replace(left=left)


def _target(target, minted: dict):
    key = names.keyed(target)
    return str(minted[key]) if key in minted else target
