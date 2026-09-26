"""The one reading of links: every link an artifact carries, wherever it sits, read through its type's composition,
and whether a link points at an artifact. The checks, removal, reads and walks all read links here."""
from typing import NamedTuple

from kb.composition import composition


class Link(NamedTuple):
    """One link an artifact carries: the field that holds it, the place of that field in the artifact, the name it
    points at, and the field's `ref`, which says what it may land on."""
    field: str
    place: str
    target: str
    ref: dict


def references(schema: dict, corpus) -> dict[str, dict]:
    """Every field that links to other artifacts, from every schema in the composition, base first, with its `ref`."""
    return {
        name: field["ref"]
        for part in composition(schema, corpus)
        for name, field in part.get("properties", {}).items()
        if "ref" in field
    }


def carried(artifact: dict, schema: dict, corpus) -> list[Link]:
    """Every link an artifact carries, wherever it sits: in its own fields, and in the fields of each item of each of
    its collections, at every depth."""
    return _links_in(artifact, references(schema, corpus), schema.get("parts", {}), "", corpus)


def _links_in(node: dict, refs: dict[str, dict], parts: dict, at: str, corpus) -> list[Link]:
    """The links in one node, an artifact or an item, its place in the artifact before each of theirs."""
    found = []
    for field, ref in refs.items():
        value = node.get(field)
        if isinstance(value, list):
            found += [Link(field, f"{at}{field}/{index}", target, ref) for index, target in enumerate(value)]
        elif value is not None:
            found.append(Link(field, f"{at}{field}", value, ref))
    for collection, part in parts.items():
        items = node.get(collection)
        if not isinstance(items, list):
            continue
        item_schema = part.get("items", {})
        item_refs = references(item_schema, corpus)
        for index, item in enumerate(items):
            if isinstance(item, dict):
                found += _links_in(item, item_refs, item_schema.get("parts", {}), f"{at}{collection}/{index}/", corpus)
    return found


def points_at(target: str, artifact_id) -> bool:
    """Whether a link lands on the artifact or on a part inside it."""
    return target.partition("#")[0] == str(artifact_id)
