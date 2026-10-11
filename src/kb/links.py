"""The one reading of links: every link an artifact carries, wherever it sits, read through its type's composition,
and those links as the port takes them, each saying the held type its target sits under, what holds it, by name,
and whether it is one the store already held waiting, and what tells each from every other (`port.told`). The checks,
removal, reads and walks all read links here."""
import dataclasses
from typing import NamedTuple

from kb import composition, names, port, values
from kb.composition import declared


class Link(NamedTuple):
    """One link an artifact carries: the field that holds it, the place of that field in the artifact, the name it
    points at, the field's `ref`, which says what it may land on, whether the field is one of the artifact's own,
    holding the link alone or in a list, rather than a field of one of its items, and what holds the field, by name
    (`port.Link.holder`): nothing for the artifact, the place of the item by its name, None for one with no name."""
    field: str
    place: str
    target: str
    ref: dict
    own: bool
    holder: str | None = ""


def references(schema: dict, corpus) -> dict[str, dict]:
    """Every field that links to other artifacts, from every schema in the composition, base first, with its `ref`."""
    return {name: field["ref"] for name, field in declared(schema, corpus)["properties"].items() if "ref" in field}


def carried(artifact: dict, schema: dict, corpus) -> list[Link]:
    """Every link an artifact carries, wherever it sits: in its own fields, and in the fields of each item of each of
    its collections, at every depth."""
    return inside(artifact, schema, corpus, artifact)


def handed(artifact_id: values.ArtifactId, artifact: dict, corpus, typed: dict, waited=frozenset()) -> list[port.Link]:
    """Every link an artifact carries as the port takes it: the artifact and the part it lands on read apart, with
    the kinds its field allows, read through the type given, the version of its type the artifact conforms to,
    whatever its type stands at, and the held type its target's IRI sits under (`port.Link.under`), held or not,
    since a held target may be removed before the link lands and the link then waits on its IRI. Every artifact
    carries one implicit link, first, to the artifact of its type, which says nothing of what that sits under. Each
    but that one says it waits (`port.Link.waits`) when it is among `waited`, the links the store held for the
    artifact that landed on nothing held, each as `port.told` gives it. A value that could name nothing, which a
    type changed after it was written can leave in a link field, is not handed."""
    kind = composition.artifact_kind(artifact)
    own = [each for each in map(_read, carried(artifact, typed["schema"], corpus)) if each is not None]
    return [
        port.Link("", "", values.type_of(kind), "", (values.TYPE_KIND.name,), implicit=True),
        *(dataclasses.replace(link, under=_under(link.target, corpus), waits=as_told in waited)
          for link, as_told in zip(own, port.told(own))),
    ]


def told(carried: list[Link]) -> list[tuple | None]:
    """What tells each link an artifact carries from every other it holds, as `port.told` gives it for the link
    handed: None for a value that could name nothing, which is not handed."""
    read = [_read(link) for link in carried]
    found = iter(port.told([each for each in read if each is not None]))
    return [None if each is None else next(found) for each in read]


def _read(link: Link) -> port.Link | None:
    """A link an artifact carries with the artifact and the part it names read apart; None for a value that could
    name nothing."""
    if not isinstance(link.target, str):
        return None
    try:
        target = values.target(link.target)
    except values.Refused:
        return None
    return port.Link(
        link.field, link.place, target.id, names.placed(target.place), tuple(link.ref["targets"]), holder=link.holder,
    )


def _under(target: values.ArtifactId, corpus) -> values.ArtifactId | None:
    """The held type a target's IRI sits under, whether or not the corpus holds the target, which may be removed
    before the link lands; None for one under no held type."""
    return composition.nearest_type(target, corpus)


def inside(artifact: dict, schema: dict, corpus, node) -> list[Link]:
    """The links an artifact carries in one node of it, as `places.node` finds it, and in the items inside that node:
    all of them for the artifact itself, none for a field's value, which is not a node."""
    parts = declared(schema, corpus)["parts"]
    return _links_in(artifact, references(schema, corpus), parts, "", corpus, node, False, "")


def _links_in(node: dict, refs: dict[str, dict], parts: dict, at: str, corpus, within, entered: bool,
              holder: str | None) -> list[Link]:
    """The links in one node, an artifact or an item, and in the items inside it, its place in the artifact before each
    of theirs; a node's own fields are read only once within, or a node it sits inside, has been entered. `holder`
    is the node by name."""
    entered = entered or node is within
    found = _fields(node, refs, at, holder) if entered else []
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
                    within, entered, _named(holder, collection, item),
                )
    return found


def _named(holder: str | None, collection: str, item: dict) -> str | None:
    """An item by name: its collection and its name after what holds it; None for an item with no name, or in one."""
    name = item.get("id")
    if holder is None or not isinstance(name, str):
        return None
    return names.placed((holder, collection, name) if holder else (collection, name))


def _fields(node: dict, refs: dict[str, dict], at: str, holder: str | None) -> list[Link]:
    """The links in a node's own fields, each alone or in a list."""
    found = []
    for field, ref in refs.items():
        value = node.get(field)
        if isinstance(value, list):
            found += [
                Link(field, f"{at}{field}/{index}", target, ref, not at, holder) for index, target in enumerate(value)
            ]
        elif value is not None:
            found.append(Link(field, f"{at}{field}", value, ref, not at, holder))
    return found
