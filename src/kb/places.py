"""Places inside an artifact: pairs of a collection and the name of an item in it, a section named by its title's name
and a part by its id, which may end in a field. A place is resolved here, once, to where its node stands, or refused
saying why nothing stands there."""
from typing import NamedTuple

from kb import names, refusals, settled
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
    if locator.place[0] in settled.IDENTITY:
        raise Refused([refusals.settled_place(locator)])
    spot = _walk(content, locator.place)
    if spot is None:
        raise Refused([refusals.nothing_at(locator)])
    return spot


def node(content: dict, locator: Locator):
    """What stands at the locator's place in an artifact's content: the content itself for no place, otherwise the
    item, the section or the field's value there, None for a field the node there does not hold. Raises Refused as
    resolve does."""
    if not locator.place:
        return content
    spot = resolve(content, locator)
    return spot.holder[spot.key] if spot.collection else spot.holder.get(spot.key)


def holds_part(content: dict, place: tuple) -> bool:
    """Whether a place names a part the content holds: an item of a collection, named by its id, at any depth; never
    a section, and never a field of an item. What a link inside an artifact may land on."""
    return not len(place) % 2 and "sections" not in place[::2] and _walk(content, place) is not None


def parts(content: dict) -> list[str]:
    """The place of every part the content holds, at every depth, written as a link names it: each a place
    `holds_part` says names a part."""
    found = []
    for collection, items in content.items():
        if collection == "sections" or not isinstance(collection, str) or not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                place = names.placed((collection, item["id"]))
                found += [place, *(names.placed((place, inner)) for inner in parts(item))]
    return found


def _walk(content: dict, place: tuple) -> Spot | None:
    """Where a place stands in the content, step by step, or None when a step names nothing there."""
    steps = list(place)
    holder = content
    while len(steps) > 1:
        collection, name = steps.pop(0), steps.pop(0)
        items = holder.get(collection)
        index = _index(collection, items, name)
        if index is None:
            return None
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
