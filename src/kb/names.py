"""Names: the grammar of an artifact's and an item's name, the name a title gives, and the numbering that keeps a name
free. Nothing here reads or writes; whether a name is taken is asked of the caller."""
import re
from typing import NamedTuple

PLAIN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def plain(text: str) -> bool:
    """Whether text is a plain name: lower-case letters and digits in runs joined by single hyphens."""
    return PLAIN.fullmatch(text) is not None


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


def items(schema: dict, content: dict, keep_named: bool) -> None:
    """Every item of every part collection given its name: from its title when it carries one, otherwise from its
    place in the collection, counted from 1, with a number added as an artifact's name has when an item beside it
    already has that name. On a write an item already carrying a name is the item of that name, moved or changed
    where it stands, and keeps it; a name is minted once and never worked out again."""
    for collection in schema.get("parts", {}):
        found = content.get(collection, [])
        taken = {item["id"] for item in found if keep_named and "id" in item}
        for place, item in enumerate(found, start=1):
            if keep_named and "id" in item:
                continue
            item["id"] = numbered(slug(item["title"]) if "title" in item else str(place), taken.__contains__)
            taken.add(item["id"])


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
        for index, item in enumerate(content.get(collection, [])):
            if not isinstance(item, dict) or "id" not in item:
                continue
            name = item["id"]
            if not isinstance(name, str) or not plain(name):
                found.append(Misnamed(collection, index, name, "not-plain"))
            elif name in seen:
                found.append(Misnamed(collection, index, name, "repeated"))
            elif name not in held.get(collection, set()):
                found.append(Misnamed(collection, index, name, "unknown"))
            seen.add(name)
    return found
