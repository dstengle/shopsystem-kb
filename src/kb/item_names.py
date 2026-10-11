"""Item names: the name a title gives, the numbering that keeps an item's name free, the names the items of an
artifact's collections are given, those they carry kept, the names a create gives its items that an item may not
carry, and the names a revision hands back that the store could not have given, each in every collection at every
depth. Nothing here reads or writes; whether a name is taken is asked of the caller. The grammar of a plain name is
`names.py`'s."""
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


def items(parts: dict, node: dict, inner: Callable[[dict], dict]) -> None:
    """Every item of every collection the node holds given its name, and the items of the collections inside each
    item in turn, at every depth. parts is the collections the node's type declares, and inner gives those an item's
    type declares from the collection's declaration. An item already carrying a name, one its create gave it or one
    the store gave it before, keeps it: a name is given once and never worked out again. The names carried are taken
    first, wherever their items stand, so no name made here is one of them. Any other item is named from its title
    when the title is text, a number, true or false, as an artifact's is, otherwise from its place in the collection,
    counted from 1, with a number added when an item beside it already has that name. An item that is not a set of
    named entries carries no name, and is passed over, as is a collection that is not a list."""
    for collection, part in parts.items():
        found = _listed(node, collection)
        taken = {item["id"] for item in found if isinstance(item, dict) and "id" in item}
        for place, item in enumerate(found, start=1):
            if not isinstance(item, dict):
                continue
            if "id" not in item:
                text = title(item.get("title"))
                item["id"] = numbered(slug(text) if text is not None else str(place), taken.__contains__)
                taken.add(item["id"])
            items(inner(part), item, inner)


class Misnamed(NamedTuple):
    """A name on an item that it may not carry: the place of its collection and where in it the item stands, the
    name, and why not: "not-plain", "repeated", or, handed back on a change, "unknown" when no item of that
    collection had it."""
    collection: str
    index: int
    name: object
    why: str


def handed_back(
    parts: dict, node: dict, before: dict, inner: Callable[[dict], dict], under: tuple = (),
) -> list[Misnamed]:
    """Every name a revision's items carry that the store could not have given, in every collection at every depth,
    as `items` walks them: one that is not a plain name, one an item before it in its collection carries, and one no
    item of that collection had. before is the node as it was held, an item of it the item that had its name, and
    nothing for an item that had none. Each collection is said by its place, as `given` says it."""
    found = []
    for collection, part in parts.items():
        here, seen = names.placed((*under, collection)), set()
        had = {item["id"]: item for item in _listed(before, collection) if _named(item)}
        for index, item in enumerate(_listed(node, collection)):
            if not isinstance(item, dict):
                continue
            if "id" in item:
                found += _unfit(here, index, item["id"], seen) or _unknown(here, index, item, had)
            was = had.get(item["id"], {}) if _named(item) else {}
            found += handed_back(inner(part), item, was, inner, (here, str(index)))
    return found


def _named(item) -> bool:
    """Whether an item carries a name that is text, the only kind the store gives."""
    return isinstance(item, dict) and isinstance(item.get("id"), str)


def _unknown(collection: str, index: int, item: dict, had: dict) -> list[Misnamed]:
    return [] if item["id"] in had else [Misnamed(collection, index, item["id"], "unknown")]


def given(parts: dict, node: dict, inner: Callable[[dict], dict], under: tuple = ()) -> list[Misnamed]:
    """Every name a new artifact's items carry that an item may not be given, in every collection at every depth, as
    `items` walks them: one that is not a plain name, and one an item before it in its collection carries. Each
    collection is said by its place, an item on the way to it by where it stands."""
    found = []
    for collection, part in parts.items():
        here, seen = (*under, collection), set()
        for index, item in enumerate(_listed(node, collection)):
            if not isinstance(item, dict):
                continue
            if "id" in item:
                found += _unfit(names.placed(here), index, item["id"], seen)
            found += given(inner(part), item, inner, (*here, str(index)))
    return found


def _unfit(collection: str, index: int, name, seen: set) -> list[Misnamed]:
    """Why a name given to an item cannot be its name, if it cannot: it is not text, or not a plain name, or an
    item seen before it carries it; a plain name is seen from here on."""
    if not isinstance(name, str) or not names.plain(name):
        return [Misnamed(collection, index, name, "not-plain")]
    if name in seen:
        return [Misnamed(collection, index, name, "repeated")]
    seen.add(name)
    return []


def _listed(node: dict, collection: str) -> list:
    """The items of a collection a node holds; none when it holds none, or a value that is not a list."""
    found = node.get(collection, [])
    return found if isinstance(found, list) else []
