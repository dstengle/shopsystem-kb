"""Places inside an artifact: pairs of a collection and the name of an item in it, a section named by its title's name
and a part by its id, which may end in a field. A place is resolved here, once, to where its node stands, or refused
saying why nothing stands there."""
from typing import NamedTuple

from kb import canonical, names, refusals
from kb.values import Locator, Refused


class Spot(NamedTuple):
    """Where a place's node stands: what holds it, the key or index it stands under there, and, when it is an item,
    the collection it is an item of."""
    holder: dict | list
    key: str | int
    collection: str = ""


def resolve(content: dict, locator: Locator) -> Spot:
    """Where the locator's place, which is not empty, stands in an artifact's content. Raises Refused for a place that
    begins at what only the store settles, or that names nothing the content holds."""
    steps = list(locator.place)
    if steps[0] in canonical.IDENTITY:
        raise Refused([refusals.settled_place(locator)])
    holder = content
    while len(steps) > 1:
        collection, name = steps.pop(0), steps.pop(0)
        items = holder.get(collection)
        index = _index(collection, items, name)
        if index is None:
            raise Refused([refusals.nothing_at(locator)])
        if not steps:
            return Spot(items, index, collection)
        holder = items[index]
    return Spot(holder, steps[0])


def _index(collection: str, items, name: str) -> int | None:
    """Where in a collection the item of that name stands, or None when the collection is not one or lacks it."""
    if not isinstance(items, list):
        return None
    for index, item in enumerate(items):
        if isinstance(item, dict) and _name(collection, item) == name:
            return index
    return None


def _name(collection: str, item: dict) -> str | None:
    """How a place names an item: a section by its title's name, a part by its id."""
    if collection == "sections":
        return names.slug(item["title"]) if isinstance(item.get("title"), str) else None
    return item.get("id")
