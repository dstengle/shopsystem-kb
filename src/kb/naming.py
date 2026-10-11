"""What names a create's artifact and the items in what an operation puts in the draft: the IRI a create gives, which
the type it names must be the nearest held one under and nothing may be held at, and a type's free of any other
type's place (kb.standing); and the items of a new or a revised artifact named, those a create names and those it
held kept (kb.item_names decides what a name looks like and whether it is free); and a type's content given the
number of its version."""
import copy

from kb import composition, item_names, refusals, settled, standing, values
from kb.draft import Draft


def identity(draft: Draft, creation, type_id: values.ArtifactId) -> list:
    """The faults of the IRI a create gives: an artifact's belongs to the type its create names, the nearest held
    type it sits under, while a type's is any IRI its client chooses under which nothing yet belongs to another type
    (kb.standing); and neither a create before it in its set carries it, said once and as the set's, nor does the
    draft hold anything at it."""
    name, faults, defines = creation.name, [], type_id == values.type_of(values.TYPE_KIND)
    if not defines and composition.nearest_type(name, draft) != type_id:
        faults.append(refusals.not_under(name, type_id))
    if creation.carried:
        faults += creation.carried
    elif draft.holds(name):
        faults.append(refusals.already_held(name))
    elif defines:
        other, sitting = standing.under(name, draft)
        faults += [refusals.belongs(name, each, other) for each in sitting]
    return faults


def items(draft: Draft, artifact_id: values.ArtifactId, declared: dict, content: dict) -> tuple:
    """The items of a new artifact's content named, each as its collection's item type declares, those its create
    names keeping the names it gives them. Returns the faults of the names it gives that an item may not carry, with
    any of which no item is named."""
    inner = _parts(draft)
    given = item_names.given(declared["parts"], content, inner)
    misnamed = [refusals.misnamed_part(artifact_id, found) for found in given]
    if not misnamed:
        item_names.items(declared["parts"], content, inner)
    return tuple(misnamed)


def revised(draft: Draft, artifact_id: values.ArtifactId, declared: dict, content: dict, current: dict) -> tuple:
    """The items of a revised artifact's content named, those it held kept. Returns the faults of the names its items
    hand back that the artifact did not hold, in a collection at any depth, with any of which no item is named."""
    inner = _parts(draft)
    handed_back = item_names.handed_back(declared["parts"], content, current, inner)
    misnamed = [refusals.misnamed(artifact_id, found) for found in handed_back]
    if not misnamed:
        item_names.items(declared["parts"], content, inner)
    return tuple(misnamed)


def imported(draft: Draft, artifact_id: values.ArtifactId, artifact: dict) -> tuple:
    """An artifact an import brings, as it would land: its items named as a create names them, those a file names
    keeping the names it gives them, and its entries in the order its type's version declares, so a name given here
    stands where kb writes names. Returns the artifact and the faults of the names its file gives that an item may
    not carry, with any of which no item is named. Raises Refused when the draft holds no such version of its type."""
    declared = composition.declared(composition.conformed(artifact, draft)["schema"], draft)
    named = copy.deepcopy(artifact)
    misnamed = items(draft, artifact_id, declared, named)
    return settled.order(named, declared), misnamed


def numbered(draft: Draft, type_id: values.ArtifactId, content: dict) -> None:
    """A type's content given, as its `version`, the number kb makes this version of it at, over any number its
    client sent or none; what a client sent there that is no number stays, for the type of types to refuse."""
    number, sent = draft.numbered(type_id), content.get("version", 0)
    if isinstance(sent, (int, float)) and not isinstance(sent, bool):
        content["version"] = number


def _parts(draft: Draft):
    """What gives the collections an item's type declares, read through its composition, from the declaration of the
    collection the item is in."""
    return lambda part: composition.declared(part.get("items", {}), draft)["parts"]
