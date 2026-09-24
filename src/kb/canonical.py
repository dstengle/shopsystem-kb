"""Canonical YAML: the one serialization kb writes. kb is the only writer, so loading needs no round-trip preservation."""
import yaml

IDENTITY = ("id", "type", "schema_version", "revision", "title")


class Prose(str):
    """A prose body. Written as a literal block, however short."""


class _Dumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        """Sequences sit indented under their key, never flush with it."""
        return super().increase_indent(flow, False)


def _represent_mapping(dumper, mapping):
    """Every value under a `body` key is prose."""
    items = [
        (key, Prose(value) if key == "body" and isinstance(value, str) else value)
        for key, value in mapping.items()
    ]
    return dumper.represent_mapping("tag:yaml.org,2002:map", items)


def _represent_prose(dumper, value):
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(value), style="|")


def _represent_str(dumper, value):
    style = "|" if "\n" in value else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


_Dumper.add_representer(dict, _represent_mapping)
_Dumper.add_representer(Prose, _represent_prose)
_Dumper.add_representer(str, _represent_str)


def dump(artifact: dict) -> str:
    """Block style, keys in the order given, prose as literal blocks, no line folded at any width."""
    return yaml.dump(
        artifact, Dumper=_Dumper, sort_keys=False, default_flow_style=False,
        allow_unicode=True, width=float("inf"),
    )


def load(text: str) -> dict:
    return yaml.safe_load(text)


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
