"""Canonical YAML: the one serialization kb writes. kb is the only writer, so loading needs no round-trip preservation."""
import yaml

IDENTITY = ("id", "type", "schema_version", "revision", "title")


class _Dumper(yaml.SafeDumper):
    pass


def _represent_str(dumper, value):
    style = "|" if "\n" in value else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


_Dumper.add_representer(str, _represent_str)


def dump(artifact: dict) -> str:
    return yaml.dump(artifact, Dumper=_Dumper, sort_keys=False, default_flow_style=False, allow_unicode=True)


def load(text: str) -> dict:
    return yaml.safe_load(text)


def order(artifact: dict, schema: dict) -> dict:
    """Identity keys first, then fields in schema order, then anything else as given."""
    ordered = {key: artifact[key] for key in IDENTITY}
    for name in schema.get("properties", {}):
        if name in artifact and name not in ordered:
            ordered[name] = artifact[name]
    for name, value in artifact.items():
        if name not in ordered:
            ordered[name] = value
    return ordered
