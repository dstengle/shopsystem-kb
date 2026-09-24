"""Artifact content crossing the contract as canonical YAML text, read as YAML 1.2."""
import datetime

from kb import canonical


def dumps(value: dict) -> str:
    """Canonical text: block style, keys in the order given, prose as literal blocks."""
    return canonical.dump(value)


def loads(text: str) -> dict:
    """Read content plainly, by the same check every file kb writes passes. Raises canonical.NotCanonical."""
    return canonical.load(text) or {}


def text(value) -> str:
    """A value as the text YAML 1.2 writes it. A title is text whatever arrived: true is "true", 12 is "12"."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, datetime.date):
        return value.isoformat()
    return str(value)
