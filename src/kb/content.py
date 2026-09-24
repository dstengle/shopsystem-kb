"""Artifact content crossing the contract as canonical YAML text, read as YAML 1.2."""
from kb import canonical


def dumps(value: dict) -> str:
    """Canonical text: block style, keys in the order given, prose as literal blocks."""
    return canonical.dump(value)


def loads(text: str) -> dict:
    """Read content plainly, by the same check every file kb writes passes. Raises canonical.NotCanonical."""
    return canonical.load(text) or {}
