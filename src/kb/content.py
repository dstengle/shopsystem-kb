"""Artifact content crossing the contract as canonical YAML text."""
from kb import canonical


def dumps(value: dict) -> str:
    """Canonical text: block style, keys in the order given, multi-line strings as literal blocks."""
    return canonical.dump(value)


def loads(text: str) -> dict:
    return canonical.load(text) or {}
