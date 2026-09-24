"""Search over the prose: every section at every depth, of every artifact, ranked by how often the words searched
for occur in its body. A word matches a whole word, whatever its case."""
import re
from typing import NamedTuple

WIDTH = 60


class Hit(NamedTuple):
    artifact: str
    section: str
    snippet: str
    count: int


def rank(artifacts, text: str) -> list[Hit]:
    """Every section whose body holds a word of the text, most occurrences first; ties in the order the store and
    the artifact hold them."""
    words = re.findall(r"\w+", text.lower())
    if not words:
        return []
    pattern = re.compile(r"\b(?:" + "|".join(re.escape(word) for word in words) + r")\b", re.IGNORECASE)
    hits = []
    for artifact in artifacts:
        for section in _sections(artifact.get("sections", [])):
            found = list(pattern.finditer(section["body"]))
            if found:
                hits.append(Hit(artifact["id"], section["title"], _snippet(section["body"], found[0]), len(found)))
    return sorted(hits, key=lambda hit: -hit.count)


def _sections(sections: list):
    for section in sections:
        yield section
        yield from _sections(section.get("sections", []))


def _snippet(body: str, found: re.Match) -> str:
    """The words around the first match, on one line, marked where they were cut."""
    start, end = max(found.start() - WIDTH, 0), min(found.end() + WIDTH, len(body))
    text = " ".join(body[start:end].split())
    return ("…" if start else "") + text + ("…" if body[end:].strip() else "")
