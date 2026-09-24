"""Canonical YAML: the one serialization kb writes, and the one reading of YAML kb does. YAML 1.2 throughout.

kb is the only writer, so loading needs no round-trip preservation.
"""
import io

from ruamel.yaml import YAML
from ruamel.yaml.representer import SafeRepresenter

IDENTITY = ("id", "type", "schema_version", "revision", "title")


class Prose(str):
    """A prose body. Written as a literal block, however short."""


class _Representer(SafeRepresenter):
    def ignore_aliases(self, data):
        """A value used twice is written out twice, never as an anchor and an alias."""
        return True


def _represent_mapping(representer, mapping):
    """Every value under a `body` key is prose."""
    items = [
        (key, Prose(value) if key == "body" and isinstance(value, str) else value)
        for key, value in mapping.items()
    ]
    return representer.represent_mapping("tag:yaml.org,2002:map", items)


def _represent_prose(representer, value):
    return representer.represent_scalar("tag:yaml.org,2002:str", str(value), style="|")


def _represent_str(representer, value):
    style = "|" if "\n" in value else None
    return representer.represent_scalar("tag:yaml.org,2002:str", value, style=style)


_Representer.add_representer(dict, _represent_mapping)
_Representer.add_representer(Prose, _represent_prose)
_Representer.add_representer(str, _represent_str)


def _yaml() -> YAML:
    """The pure-Python safe loader and emitter, YAML 1.2. Never the C one, which is YAML 1.1."""
    yaml = YAML(typ="safe", pure=True)
    yaml.Representer = _Representer
    yaml.default_flow_style = False
    yaml.allow_unicode = True
    yaml.width = float("inf")
    yaml.indent(mapping=2, sequence=4, offset=2)
    return yaml


def dump(artifact: dict) -> str:
    """Block style, keys in the order given, prose as literal blocks, sequences indented under their key, no line folded."""
    stream = io.StringIO()
    _yaml().dump(artifact, stream)
    return stream.getvalue()


def load(text: str):
    return _yaml().load(text)


def events(text: str):
    """The YAML 1.2 parse of `text`, as events, for checks that look at how a value is written."""
    return _yaml().parse(text)


def order(artifact: dict, schema: dict) -> dict:
    """Identity keys first, then fields in schema order, then sections, then part collections in schema order."""
    parts = schema.get("parts", {})
    ordered = {key: artifact[key] for key in IDENTITY}
    for name in schema.get("properties", {}):
        if name in artifact and name not in ordered:
            ordered[name] = artifact[name]
    for name, value in artifact.items():
        if name not in ordered and name != "sections" and name not in parts:
            ordered[name] = value
    if "sections" in artifact:
        ordered["sections"] = [_section(section) for section in artifact["sections"]]
    for name in parts:
        if name in artifact:
            ordered[name] = [_item(item, parts[name]["items"]) for item in artifact[name]]
    return ordered


def _section(section: dict) -> dict:
    ordered = {"title": section["title"], "body": section["body"]}
    if "sections" in section:
        ordered["sections"] = [_section(child) for child in section["sections"]]
    return ordered


def _item(item: dict, item_schema: dict) -> dict:
    """An item's id first, then its fields in the item schema's order."""
    ordered = {"id": item["id"]}
    for name in item_schema.get("properties", {}):
        if name in item and name not in ordered:
            ordered[name] = item[name]
    for name, value in item.items():
        if name not in ordered:
            ordered[name] = value
    return ordered
