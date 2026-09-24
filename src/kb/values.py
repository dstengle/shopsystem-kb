"""The boundary: every value a request carries is turned here into a checked value, or refused with a fault.

Storage takes only these values, never a string that came from a request, and `path` is the one place a file
path is made from a name.
"""
import re
from dataclasses import dataclass
from pathlib import Path

from kb.contract import kb_pb2

PLAIN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


class Refused(ValueError):
    """A request value that does not convert. Carries every fault found."""

    def __init__(self, faults: list[kb_pb2.Fault]):
        super().__init__(faults)
        self.faults = faults


@dataclass(frozen=True)
class Kind:
    name: str


@dataclass(frozen=True)
class ArtifactId:
    kind: Kind
    slug: str

    def __str__(self) -> str:
        return f"{self.kind.name}/{self.slug}"


@dataclass(frozen=True)
class Locator:
    id: ArtifactId
    place: tuple[str, ...]


def kind(text: str) -> Kind:
    if not PLAIN.fullmatch(text):
        raise Refused([kb_pb2.Fault(
            rule="kind",
            message=f"a kind is a plain name of lower-case letters, digits and single hyphens, never a path; {text!r} is not",
        )])
    return Kind(text)


def artifact_id(text: str) -> ArtifactId:
    kind_name, _, slug = text.partition("/")
    if not (PLAIN.fullmatch(kind_name) and PLAIN.fullmatch(slug)):
        raise Refused([_not_a_plain_name(text)])
    return ArtifactId(Kind(kind_name), slug)


def locator(request: kb_pb2.Locator) -> Locator:
    """A locator's name and its place, each checked; both faults when both fail."""
    faults = []
    try:
        converted = artifact_id(request.id)
    except Refused as refused:
        faults += refused.faults
    place = tuple(request.path.split("/")) if request.path else ()
    if not all(PLAIN.fullmatch(part) for part in place):
        faults.append(kb_pb2.Fault(
            artifact=request.id, path=request.path, rule="locator",
            message=f"a place inside an artifact is named by parts of the same plain alphabet, or a collection and an item in it; {request.path!r} is not",
        ))
    if faults:
        raise Refused(faults)
    return Locator(converted, place)


def named(kind: Kind, title: str) -> ArtifactId:
    """The name kb gives an artifact of this kind from its title. A title is required and must leave a name."""
    at = f"{kind.name}/{slug(title)}"
    if not title:
        raise Refused([kb_pb2.Fault(artifact=at, path="title", rule="title",
                                    message="an artifact cannot be created without a title")])
    if not slug(title):
        raise Refused([kb_pb2.Fault(artifact=at, path="title", rule="title",
                                    message=f"a title must leave something to make a name from; {title!r} leaves nothing")])
    return ArtifactId(kind, slug(title))


def slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def path(store_dir: Path, artifact_id: ArtifactId) -> Path:
    """The one function that makes a file path from a name."""
    if not isinstance(artifact_id, ArtifactId):
        raise TypeError(f"a path is made only from a checked name, not {artifact_id!r}")
    return store_dir / artifact_id.kind.name / f"{artifact_id.slug}.yaml"


def _not_a_plain_name(text: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=text, rule="locator",
        message=f"a name is a kind and a plain name of lower-case letters, digits and single hyphens, never a path; {text!r} is not",
    )
