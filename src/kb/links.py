"""The one reading of links: every link an artifact carries, wherever it sits, read through its type's composition,
those links as the port takes them, and an artifact with each of its links rewritten. The checks, removal, reads,
walks and a set's keys all read links here."""
import copy
from typing import Callable, NamedTuple

from kb import composition, names, port, values
from kb.composition import declared


class Link(NamedTuple):
    """One link an artifact carries: the field that holds it, the place of that field in the artifact, the name it
    points at, the field's `ref`, which says what it may land on, and whether the field is one of the artifact's own,
    holding the link alone or in a list, rather than a field of one of its items."""
    field: str
    place: str
    target: str
    ref: dict
    own: bool


def references(schema: dict, corpus) -> dict[str, dict]:
    """Every field that links to other artifacts, from every schema in the composition, base first, with its `ref`."""
    return {name: field["ref"] for name, field in declared(schema, corpus)["properties"].items() if "ref" in field}


def carried(artifact: dict, schema: dict, corpus) -> list[Link]:
    """Every link an artifact carries, wherever it sits: in its own fields, and in the fields of each item of each of
    its collections, at every depth."""
    return inside(artifact, schema, corpus, artifact)


def handed(artifact_id: values.ArtifactId, artifact: dict, corpus) -> list[port.Link]:
    """Every link an artifact carries as the port takes it: the artifact and the part it lands on read apart, with
    the kinds its field allows, read through the artifact's type as the corpus holds it; none when the corpus holds
    no such type. Every artifact carries one implicit link, first, to the artifact of its type. A value that could name nothing, which a type changed after it was written can leave in a link
    field, is not handed."""
    typed = values.type_of(artifact_id.kind)
    implicit = port.Link("", "", typed, "", (values.TYPE_KIND.name,), implicit=True)
    if not corpus.holds(typed):
        return [implicit]
    schema = composition.kind_schema(artifact_id.kind, corpus)["schema"]
    found = [implicit]
    for link in carried(artifact, schema, corpus):
        if not isinstance(link.target, str):
            continue
        try:
            target = values.target(link.target)
        except values.Refused:
            continue
        found.append(port.Link(
            link.field, link.place, target.id, names.placed(target.place), tuple(link.ref["targets"]),
        ))
    return found


def inside(artifact: dict, schema: dict, corpus, node) -> list[Link]:
    """The links an artifact carries in one node of it, as `places.node` finds it, and in the items inside that node:
    all of them for the artifact itself, none for a field's value, which is not a node."""
    return [spot.link for spot in _spots(artifact, schema, corpus, node)]


def rewritten(artifact: dict, schema: dict, corpus, given: Callable[[Link], object]) -> dict:
    """A copy of an artifact with each link it carries, wherever it sits, holding what `given` gives for it."""
    copied = copy.deepcopy(artifact)
    for spot in _spots(copied, schema, corpus, copied):
        spot.holder[spot.key] = given(spot.link)
    return copied


class _Spot(NamedTuple):
    """Where one link sits: the mapping or list holding it, the key or index it is held at, and the link."""
    holder: dict | list
    key: str | int
    link: Link


def _spots(artifact: dict, schema: dict, corpus, node) -> list[_Spot]:
    return _links_in(artifact, references(schema, corpus), declared(schema, corpus)["parts"], "", corpus, node, False)


def _links_in(node: dict, refs: dict[str, dict], parts: dict, at: str, corpus, within, entered: bool) -> list[_Spot]:
    """The links in one node, an artifact or an item, and in the items inside it, its place in the artifact before each
    of theirs; a node's own fields are read only once within, or a node it sits inside, has been entered."""
    entered = entered or node is within
    found = _fields(node, refs, at) if entered else []
    for collection, part in parts.items():
        items = node.get(collection)
        if not isinstance(items, list):
            continue
        item_schema = part.get("items", {})
        item_refs = references(item_schema, corpus)
        for index, item in enumerate(items):
            if isinstance(item, dict):
                found += _links_in(
                    item, item_refs, declared(item_schema, corpus)["parts"], f"{at}{collection}/{index}/", corpus,
                    within, entered,
                )
    return found


def _fields(node: dict, refs: dict[str, dict], at: str) -> list[_Spot]:
    """The links in a node's own fields, each alone or in a list."""
    found = []
    for field, ref in refs.items():
        value = node.get(field)
        if isinstance(value, list):
            found += [
                _Spot(value, index, Link(field, f"{at}{field}/{index}", target, ref, not at))
                for index, target in enumerate(value)
            ]
        elif value is not None:
            found.append(_Spot(node, field, Link(field, f"{at}{field}", value, ref, not at)))
    return found
