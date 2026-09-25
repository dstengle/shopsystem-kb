"""Search over the prose, every section at every depth of every artifact, and over the fields, the title and every
field that holds text, ranked by how often the words searched for occur in a body or a value. A word matches a whole
word, whatever its case."""
import re
from typing import NamedTuple

from kb.canonical import IDENTITY

WIDTH = 60


class Hit(NamedTuple):
    artifact: str
    section: str
    field: str
    snippet: str
    count: int


def rank(artifacts, text: str, sections: bool = True, fields: bool = False) -> list[Hit]:
    """Every section whose body, and every field whose value, holds a word of the text, as asked, most occurrences
    first; ties in the order the store and the artifact hold them, an artifact's sections before its fields."""
    words = re.findall(r"\w+", text.lower())
    if not words:
        return []
    pattern = re.compile(r"\b(?:" + "|".join(re.escape(word) for word in words) + r")\b", re.IGNORECASE)
    hits = []
    for artifact in artifacts:
        if sections:
            for section in _sections(artifact.get("sections", [])):
                found = list(pattern.finditer(section["body"]))
                if found:
                    hits.append(Hit(artifact["id"], section["title"], "", _snippet(section["body"], found[0]), len(found)))
        if fields:
            for name, value in _fields(artifact):
                found = list(pattern.finditer(value))
                if found:
                    hits.append(Hit(artifact["id"], "", name, _snippet(value, found[0]), len(found)))
    return sorted(hits, key=lambda hit: -hit.count)


def _fields(artifact: dict):
    """The title, then every other field that holds text, in the order the artifact holds them."""
    yield "title", artifact["title"]
    for name, value in artifact.items():
        if name not in IDENTITY and name != "sections" and isinstance(value, str):
            yield name, value


def _sections(sections: list):
    for section in sections:
        yield section
        yield from _sections(section.get("sections", []))


def _snippet(body: str, found: re.Match) -> str:
    """The words around the first match, on one line, marked where they were cut."""
    start, end = max(found.start() - WIDTH, 0), min(found.end() + WIDTH, len(body))
    text = " ".join(body[start:end].split())
    return ("…" if start else "") + text + ("…" if body[end:].strip() else "")
