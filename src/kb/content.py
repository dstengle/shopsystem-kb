"""Artifact content crossing the contract as canonical YAML text, read as YAML 1.2."""
import datetime

from kb import canonical


def dumps(value: dict) -> str:
    """Canonical text: block style, keys in the order given, prose as literal blocks."""
    return canonical.dump(value)


def loads(text: str) -> dict:
    """Read content plainly, by the same check every file kb writes passes. Raises canonical.NotCanonical."""
    return canonical.load(text) or {}


def entries(text: str) -> dict:
    """A whole artifact's content: a set of named entries, read plainly. Raises canonical.NotCanonical for text that
    is anything else, nothing at all included."""
    return canonical.entries(text)


def title(value) -> str | None:
    """A title as text: text as it is, and a number, true or false as YAML 1.2 writes it. None for anything a title
    is never written as: nothing, a list or a mapping."""
    if isinstance(value, (str, bool, int, float)):
        return text(value)
    return None


def text(value) -> str:
    """A value as the text YAML 1.2 writes it. A title is text whatever arrived: true is "true", 12 is "12"."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, datetime.date):
        return value.isoformat()
    return str(value)
