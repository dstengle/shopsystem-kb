"""Artifact content crossing the contract as canonical YAML text, read as YAML 1.2."""
import datetime

from kb import canonical
from kb.canonical import NotCanonical

__all__ = ["dumps", "loads", "entries", "text", "NotCanonical"]


def dumps(value: dict) -> str:
    """Canonical text: block style, keys in the order given, prose as literal blocks. Raises NotCanonical for
    content kb cannot keep, such as prose with a line ending in a space before its last."""
    return canonical.dump(value)


def loads(text: str) -> dict:
    """Read content plainly, by the same check every file kb writes passes. Raises NotCanonical."""
    return canonical.load(text) or {}


def entries(text: str) -> dict:
    """A whole artifact's content: a set of named entries, read plainly. Raises NotCanonical for text that
    is anything else, nothing at all included."""
    return canonical.entries(text)


def text(value) -> str:
    """A value as the text YAML 1.2 writes it. A title is text whatever arrived: true is "true", 12 is "12"."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, datetime.date):
        return value.isoformat()
    return str(value)
