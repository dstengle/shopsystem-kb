"""Item names: the name a title gives, the numbering that keeps an item's name free, the names the items of an
artifact's collections are given and the names they held, and the names a revision hands back that the store could not
have given. Nothing here reads or writes; whether a name is taken is asked of the caller. The grammar of a plain name
is `names.py`'s."""
import re
from typing import Callable, NamedTuple

from kb import names


def title(value) -> str | None:
    """A title as the text a name is made from: text as it is, and a number, true or false as YAML 1.2 writes it.
    None for anything a title is never written as: nothing, a list or a mapping."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int, float)):
        return str(value)
    return None


def slug(title: str) -> str:
    """The name a title gives: lower-cased, every run of anything else a hyphen, none at either end."""
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def numbered(name: str, taken) -> str:
    """The name, or, when taken says it is taken, that name with -2, -3 and so on added: the first it does not."""
    candidate, number = name, 1
    while taken(candidate):
        number += 1
        candidate = f"{name}-{number}"
    return candidate


def items(parts: dict, node: dict, keep_named: bool, inner: Callable[[dict], dict]) -> None:
    """Every item of every collection the node holds given its name, and the items of the collections inside each
    item in turn, at every depth. parts is the collections the node's type declares, and inner gives those an item's
    type declares from the collection's declaration. An item is named from its title when the title is text, a
    number, true or false, as an artifact's is, otherwise from its place in the collection, counted from 1, with a
    number added when an item beside it already has that name. On a write an item already
    carrying a name is the item of that name, moved or changed where it stands, and keeps it; a name is minted once
    and never worked out again. An item that is not a set of named entries carries no name, and is passed over, as is
    a collection that is not a list."""
    for collection, part in parts.items():
        found = _listed(node, collection)
        taken = {item["id"] for item in found if isinstance(item, dict) and keep_named and "id" in item}
        for place, item in enumerate(found, start=1):
            if not isinstance(item, dict):
                continue
            if not (keep_named and "id" in item):
                text = title(item.get("title"))
                item["id"] = numbered(slug(text) if text is not None else str(place), taken.__contains__)
                taken.add(item["id"])
            items(inner(part), item, keep_named, inner)


def held(parts: dict, node: dict) -> dict[str, set]:
    """The names the items of each collection the node holds carry; an item that is not a set of named entries, or a
    collection that is not a list, carries none."""
    return {
        collection: {item.get("id") for item in _listed(node, collection) if isinstance(item, dict)}
        for collection in parts
    }


class Misnamed(NamedTuple):
    """A name handed back on an item that the store could not have given it: where it is, the name, and why not:
    "not-plain", "repeated", or "unknown" when no item of that collection had it."""
    collection: str
    index: int
    name: object
    why: str


def handed_back(schema: dict, content: dict, held: dict[str, set]) -> list[Misnamed]:
    """Every name on an item of a collection that is not the name of an item the collection held, given once. held
    is the names each collection held before the change."""
    found = []
    for collection in schema.get("parts", {}):
        seen = set()
        for index, item in enumerate(_listed(content, collection)):
            if not isinstance(item, dict) or "id" not in item:
                continue
            name = item["id"]
            if not isinstance(name, str) or not names.plain(name):
                found.append(Misnamed(collection, index, name, "not-plain"))
            elif name in seen:
                found.append(Misnamed(collection, index, name, "repeated"))
            elif name not in held.get(collection, set()):
                found.append(Misnamed(collection, index, name, "unknown"))
            seen.add(name)
    return found


def _listed(node: dict, collection: str) -> list:
    """The items of a collection a node holds; none when it holds none, or a value that is not a list."""
    found = node.get(collection, [])
    return found if isinstance(found, list) else []
