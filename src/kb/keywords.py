"""Where kb reads its own keywords in a type, and every place one of them stands. kb reads `ref` only on a field
directly under `properties` of the top of a type's schema or of the top of a collection's `items`; `parts` and
`summary` only at either top; `sections` only at the top of a type's schema. The top of a schema is the schema and
each of its `allOf` members, as `composition.composition` reads them. Only places where JSON Schema 2020-12 puts a
schema are walked, so a field named like a keyword, or a value keyword holding one, is never a keyword of kb's; a
whole `$ref` is not followed, since the type it names is checked when it is written."""
from typing import Iterator, NamedTuple

OWN = ("ref", "parts", "sections", "summary")

_TOP, _ITEMS, _FIELD, _ELSEWHERE = "top", "items", "field", "elsewhere"
_READ = {_TOP: {"parts", "summary", "sections"}, _ITEMS: {"parts", "summary"}, _FIELD: {"ref"}, _ELSEWHERE: set()}

_ONE = ("items", "additionalProperties", "contains", "not", "if", "then", "else", "propertyNames",
        "unevaluatedItems", "unevaluatedProperties", "contentSchema")
_EACH = ("prefixItems", "anyOf", "oneOf")
_NAMED = ("$defs", "definitions", "patternProperties", "dependentSchemas")


class Standing(NamedTuple):
    """One of kb's keywords where it stands in a type: the keyword, its place (`schema/...`), the place of the schema
    holding it, whether kb reads it there, and its value."""
    keyword: str
    place: str
    holder: str
    read: bool
    value: object


def standing(schema, place: str = "schema") -> Iterator[Standing]:
    """Every one of kb's keywords in a type's schema, in the order it is written, with whether kb reads it there."""
    yield from _walk(schema, place, _TOP)


def _walk(node, place: str, where: str) -> Iterator[Standing]:
    if not isinstance(node, dict):
        return
    for key, value in node.items():
        if key in OWN:
            read = key in _READ[where]
            yield Standing(key, f"{place}/{key}", place, read, value)
            if key == "parts" and read:
                yield from _collections(value, f"{place}/{key}")
        else:
            yield from _inside(key, value, f"{place}/{key}", where)


def _inside(key: str, value, place: str, where: str) -> Iterator[Standing]:
    """The keywords inside one JSON Schema keyword's value, where it holds schemas."""
    top = where if where in (_TOP, _ITEMS) else _ELSEWHERE
    if key == "allOf" and isinstance(value, list):
        for index, member in enumerate(value):
            yield from _walk(member, f"{place}/{index}", top)
    elif key == "properties" and isinstance(value, dict):
        for name, field in value.items():
            yield from _walk(field, f"{place}/{name}", _FIELD if top != _ELSEWHERE else _ELSEWHERE)
    elif key in _ONE:
        yield from _walk(value, place, _ELSEWHERE)
    elif key in _EACH and isinstance(value, list):
        for index, member in enumerate(value):
            yield from _walk(member, f"{place}/{index}", _ELSEWHERE)
    elif key in _NAMED and isinstance(value, dict):
        for name, member in value.items():
            yield from _walk(member, f"{place}/{name}", _ELSEWHERE)


def _collections(parts, place: str) -> Iterator[Standing]:
    """The keywords at the top of each collection's items, and inside them."""
    if not isinstance(parts, dict):
        return
    for name, collection in parts.items():
        if isinstance(collection, dict):
            yield from _walk(collection.get("items"), f"{place}/{name}/items", _ITEMS)
