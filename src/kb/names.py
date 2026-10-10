"""Names: kb's IRI grammar, how an IRI is split into its host and segments and a type version's IRI read, the place an
export gives an artifact and the IRI a file's place gives, how a link names a place inside an artifact and a type
version is referred to, the name an item's title gives, and the numbering that keeps an item's name free. Nothing
here reads or writes; whether a name is taken is asked of the caller."""
import re
from typing import Callable, NamedTuple

PLAIN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_DOTTED = r"[a-z0-9]+(?:-[a-z0-9]+)*(?:\.[a-z0-9]+(?:-[a-z0-9]+)*)*"
IRI = re.compile(rf"https://(?P<host>{_DOTTED})(?P<path>(?:/{_DOTTED})+)")
VERSION = re.compile(r"(?P<iri>[^@]+)@(?P<number>[1-9][0-9]*)")
LONGEST = 512
SCHEME = "https://"
FILE = ".yaml"

KEYED = "@"
VERSIONED = "@"

TYPES = "https://missingmass.io/kb/type"
TYPE_URI = "kb:"


def iri(text: str) -> bool:
    """Whether text is an IRI of kb's grammar: `https://`, a host of plain names joined by single dots, and one or
    more segments, each plain names joined by single dots; at most LONGEST characters; no `@` and no `#`."""
    return len(text) <= LONGEST and IRI.fullmatch(text) is not None


def split(iri_text: str) -> tuple[str, tuple[str, ...]]:
    """An IRI of kb's grammar read as its host and its segments."""
    host, *segments = iri_text.removeprefix(SCHEME).split("/")
    return host, tuple(segments)


def version(text: str) -> tuple[str, int] | None:
    """A type version's IRI read as the type's IRI and the version's number; None for text that is not one."""
    found = VERSION.fullmatch(text)
    if found is None or not iri(found["iri"]) or len(text) > LONGEST:
        return None
    return found["iri"], int(found["number"])


def versioned(type_iri: str, number: int) -> str:
    """A type version's IRI: the type's IRI, `@` and the version's number."""
    return f"{type_iri}{VERSIONED}{number}"


def order(artifact_id) -> tuple[str, ...]:
    """The one order artifacts' IRIs are given in: as the places the export layout gives them compare, step by
    step."""
    return place(artifact_id)


def place(artifact_id, number: int | None = None) -> tuple[str, ...]:
    """The place the export layout gives an artifact, as steps below the directory: the host and the segments of its
    IRI, the last written `<segment>.yaml`, or, for a type's version, `<segment>@<n>.yaml`; the inverse of
    `filed`."""
    host, segments = split(str(artifact_id))
    last = segments[-1] if number is None else versioned(segments[-1], number)
    return (host, *segments[:-1], f"{last}{FILE}")


def filed(steps: tuple[str, ...]) -> tuple[str, int | None] | None:
    """The IRI of the artifact the export layout puts at a file's place, given the place's steps below the directory,
    and the version's number when the place is a type version's, None when it is not; None for a place where the
    layout puts no artifact."""
    if len(steps) < 2 or not steps[-1].endswith(FILE):
        return None
    written = SCHEME + "/".join((*steps[:-1], steps[-1].removesuffix(FILE)))
    found = version(written)
    if found is not None:
        return found
    return (written, None) if iri(written) else None


def linked(text: str) -> tuple[str, str]:
    """A link as a field holds it read as the name it points at and, after `#`, the place inside that artifact."""
    name, _, place = text.partition("#")
    return name, place


def keyed(text) -> str | None:
    """The key a link written as `@` and a key refers to; None for a link written any other way."""
    return text.removeprefix(KEYED) if isinstance(text, str) and text.startswith(KEYED) else None


def placed(steps) -> str:
    """A place inside an artifact as it is written: its steps, each a collection, an item's or a section's name, or a
    field, joined by slashes."""
    return "/".join(steps)


def steps(text: str) -> tuple[str, ...]:
    """A written place read back as its steps, none for no place, none of them yet checked."""
    return tuple(text.split("/")) if text else ()


def referred(ref: str) -> tuple[str, str] | None:
    """What a `kb:` reference names: the IRI of a type's version, and what follows it from `#` on, empty when the
    reference is to the whole type. None for a reference that is not kb's."""
    if not ref.startswith(TYPE_URI):
        return None
    name, mark, fragment = ref.removeprefix(TYPE_URI).partition("#")
    return name, mark + fragment


def plain(text: str) -> bool:
    """Whether text is a plain name: lower-case letters and digits in runs joined by single hyphens."""
    return PLAIN.fullmatch(text) is not None


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
            if not isinstance(name, str) or not plain(name):
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
