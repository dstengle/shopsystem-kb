"""Artifact content crossing the contract as canonical YAML text, read as YAML 1.2."""
from ruamel.yaml import events

from kb import canonical


class ContentFault(ValueError):
    """Content that cannot be read plainly. The message is the fault's."""


def dumps(value: dict) -> str:
    """Canonical text: block style, keys in the order given, prose as literal blocks."""
    return canonical.dump(value)


def loads(text: str) -> dict:
    """Read content plainly: no tags, exactly one document."""
    parsed = list(canonical.events(text))
    if any(getattr(event, "tag", None) is not None for event in parsed):
        raise ContentFault("content is read plainly as written and carries no tags")
    if sum(isinstance(event, events.DocumentStartEvent) for event in parsed) > 1:
        raise ContentFault("content holds exactly one document")
    return canonical.load(text) or {}
