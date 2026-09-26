"""The boundary: every value a request carries is turned here into a checked value, or refused with a fault.

Storage takes only these values, never a string that came from a request, and `path` is the one place a file
path is made from a name.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from kb import canonical, names
from kb.content import loads
from kb.contract import kb_pb2

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
    if not names.plain(text):
        raise Refused([kb_pb2.Fault(
            rule="kind",
            message=f"a kind is a plain name of lower-case letters, digits and single hyphens, never a path; {text!r} is not",
        )])
    return Kind(text)


def artifact_id(text: str) -> ArtifactId:
    kind_name, _, slug = text.partition("/")
    if not (names.plain(kind_name) and names.plain(slug)):
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
    if not all(names.plain(part) for part in place):
        faults.append(kb_pb2.Fault(
            artifact=request.id, path=request.path, rule="locator",
            message=f"a place inside an artifact is named by parts of the same plain alphabet, or a collection and an item in it; {request.path!r} is not",
        ))
    if faults:
        raise Refused(faults)
    return Locator(converted, place)


def target(text: str) -> Locator:
    """A link as a field holds it: a name, or a name and, after `#`, a place inside that artifact. Checked as a
    locator is."""
    name, _, place = text.partition("#")
    return locator(kb_pb2.Locator(id=name, path=place))


def since(text: str) -> datetime:
    """A time as a request names it: ISO 8601, a date alone meaning its midnight, in UTC unless it says otherwise."""
    try:
        moment = datetime.fromisoformat(text)
    except ValueError:
        raise Refused([kb_pb2.Fault(
            rule="since", message=f"a time is written in ISO 8601, as 2026-09-22 or 2026-09-22T09:00:00Z; {text!r} is not",
        )]) from None
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def named(kind: Kind, title: str) -> ArtifactId:
    """The name kb gives an artifact of this kind from its title. A title is required and must leave a name."""
    at = f"{kind.name}/{names.slug(title)}"
    if not title:
        raise Refused([kb_pb2.Fault(artifact=at, path="title", rule="title",
                                    message="an artifact cannot be created without a title")])
    if not names.slug(title):
        raise Refused([kb_pb2.Fault(artifact=at, path="title", rule="title",
                                    message=f"a title must leave something to make a name from; {title!r} leaves nothing")])
    return ArtifactId(kind, names.slug(title))


@dataclass(frozen=True)
class Content:
    """Content as a request carries it: the tree read from it, and, when it cannot be taken, what is wrong with it,
    each as a place, a rule and a message, to be said of whichever artifact the content turns out to be for."""
    tree: object
    problems: tuple[tuple[str, str, str], ...] = ()

    def refusal(self, artifact: str) -> list[kb_pb2.Fault]:
        return [kb_pb2.Fault(artifact=artifact, path=path, rule=rule, message=message)
                for path, rule, message in self.problems]


def content(text: str, at_root: bool = True) -> Content:
    """Content read plainly, and, for a whole artifact, holding only what a type declares. The identity keys belong
    to an artifact's root, so a node inside it, a section with its title, is not held to them. Every problem found."""
    try:
        tree = loads(text)
    except canonical.NotCanonical as fault:
        return Content(None, ((fault.path, "content", str(fault)),))
    if not at_root:
        return Content(tree)
    problems = []
    for key in canonical.IDENTITY:
        if key not in tree:
            continue
        if key == "title":
            message = f"a title is given alongside the content, never inside it; the content carried the title {tree[key]!r}"
        else:
            message = f"content holds only what the type declares; {key} is settled by the store, and the content carried {key}: {tree[key]!r}"
        problems.append((key, "identity", message))
    return Content(tree, tuple(problems))


def item(text: str) -> Content:
    """An item read plainly, never carrying its own name, which kb gives."""
    read = content(text, at_root=False)
    if read.problems or "id" not in read.tree:
        return read
    return Content(read.tree, (("id", "identity",
        f"content holds only what the type declares; an item's id is settled by the store, and the content carried id: {read.tree['id']!r}"),))


@dataclass(frozen=True)
class Actor:
    role: str
    execution: str


@dataclass(frozen=True)
class Signed:
    """Who made a change, and the message they gave for it."""
    actor: Actor
    message: str


def actor(request: kb_pb2.Actor) -> Actor:
    return Actor(request.role, request.execution)


def signed(request: kb_pb2.Actor, message: str) -> Signed:
    return Signed(actor(request), message)


def starter(request: kb_pb2.Actor) -> Actor:
    """The actor who starts a store, who must name a role."""
    if not request.role:
        raise Refused([kb_pb2.Fault(rule="actor", message="a store can only be started under a role")])
    return actor(request)


@dataclass(frozen=True)
class Root:
    """The directory a store is started in, and the name the request gave it, which a refusal quotes."""
    path: Path
    named: str


def root(text: str) -> Root:
    """The directory a store is started in, as the request names it; relative names stay relative. What stands
    there is the store's to check."""
    if not text:
        raise Refused([kb_pb2.Fault(
            rule="root",
            message="a store is started in a directory that was named and that exists; no directory was named",
        )])
    return Root(Path(text), text)


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
