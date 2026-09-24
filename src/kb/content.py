"""Artifact content crossing the contract as canonical YAML text."""
import yaml

from kb import canonical


class ContentFault(ValueError):
    """Content that cannot be read plainly. The message is the fault's."""


def dumps(value: dict) -> str:
    """Canonical text: block style, keys in the order given, prose as literal blocks."""
    return canonical.dump(value)


def loads(text: str) -> dict:
    """Read content plainly: no tags, exactly one document."""
    if any(isinstance(token, yaml.TagToken) for token in yaml.scan(text)):
        raise ContentFault("content is read plainly as written and carries no tags")
    documents = list(yaml.safe_load_all(text))
    if len(documents) > 1:
        raise ContentFault("content holds exactly one document")
    return (documents[0] if documents else None) or {}
