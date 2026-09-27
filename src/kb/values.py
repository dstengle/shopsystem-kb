"""The boundary: every value a request carries is turned here into a checked value, or refused with a fault.

Storage takes only these values, never a string that came from a request.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from kb import canonical, names, rules, settled
from kb.content import entries, loads
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
        return names.written(self.kind.name, self.slug)


TYPE_KIND = Kind(names.TYPES)


def type_of(kind: Kind) -> ArtifactId:
    """The name of the type the artifacts of a kind are of."""
    return ArtifactId(TYPE_KIND, kind.name)


@dataclass(frozen=True)
class Locator:
    id: ArtifactId
    place: tuple[str, ...]


def kind(text: str) -> Kind:
    if not names.plain(text):
        raise Refused([kb_pb2.Fault(
            rule=rules.KIND,
            message=f"a kind is a plain name of lower-case letters, digits and single hyphens, never a path; {text!r} is not",
        )])
    return Kind(text)


def artifact_id(text: str) -> ArtifactId:
    kind_name, slug = names.parted(text)
    if not (names.plain(kind_name) and names.plain(slug)):
        raise Refused([_not_a_plain_name(text)])
    return ArtifactId(Kind(kind_name), slug)


def locator(request: kb_pb2.Locator) -> Locator:
    """A locator's name and its place, each checked; both faults when both fail."""
    return _located(request.id, request.path)


def target(text: str) -> Locator:
    """A link as a field holds it: a name, or a name and, after `#`, a place inside that artifact. Checked as a
    locator is."""
    return _located(*names.linked(text))


def _located(name: str, path: str) -> Locator:
    faults = []
    try:
        converted = artifact_id(name)
    except Refused as refused:
        faults += refused.faults
    place = names.steps(path)
    if not all(names.plain(part) for part in place):
        faults.append(kb_pb2.Fault(
            artifact=name, path=path, rule=rules.LOCATOR,
            message=f"a place inside an artifact is named by parts of the same plain alphabet, or a collection and an item in it; {path!r} is not",
        ))
    if faults:
        raise Refused(faults)
    return Locator(converted, place)


def since(text: str) -> datetime:
    """A time as a request names it: ISO 8601, a date alone meaning its midnight, in UTC unless it says otherwise."""
    try:
        moment = datetime.fromisoformat(text)
    except ValueError:
        raise Refused([kb_pb2.Fault(
            rule=rules.SINCE, message=f"a time is written in ISO 8601, as 2026-09-22 or 2026-09-22T09:00:00Z; {text!r} is not",
        )]) from None
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def named(kind: Kind, title: str) -> tuple[ArtifactId | None, str, tuple]:
    """The name kb gives an artifact of this kind from its title, and the name its faults are said of; None, with the
    title's faults, when it gives none. A title is required and must leave a name."""
    slug = names.slug(title)
    at = names.written(kind.name, slug)
    if not title:
        message = "an artifact cannot be created without a title"
    elif not slug:
        message = _leaves_nothing(title)
    else:
        return ArtifactId(kind, slug), at, ()
    return None, at, (kb_pb2.Fault(artifact=at, path="title", rule=rules.TITLE, message=message),)


def _leaves_nothing(title: str) -> str:
    return f"a title must leave something to make a name from; {title!r} leaves nothing"


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
        tree = entries(text) if at_root else loads(text)
    except canonical.NotCanonical as fault:
        return Content(None, ((fault.path, rules.CONTENT, str(fault)),))
    if not at_root:
        return Content(tree)
    problems = []
    for key in settled.IDENTITY:
        if key not in tree:
            continue
        if key == "title":
            message = f"a title is given alongside the content, never inside it; the content carried the title {tree[key]!r}"
        else:
            message = f"content holds only what the type declares; {key} is settled by the store, and the content carried {key}: {tree[key]!r}"
        problems.append((key, rules.IDENTITY, message))
    return Content(tree, tuple(problems))


def item(text: str) -> Content:
    """An item read plainly, never carrying its own name, which kb gives, and with its title, which its name is made
    from, as text. Only a set of named entries can carry a name or a title; an item of any other shape is left for
    its type to refuse."""
    read = content(text, at_root=False)
    if read.problems or not isinstance(read.tree, dict):
        return read
    if "id" in read.tree:
        return Content(read.tree, (("id", rules.IDENTITY,
            f"content holds only what the type declares; an item's id is settled by the store, and the content carried id: {read.tree['id']!r}"),))
    return _titled(read.tree)


def _titled(tree: dict) -> Content:
    """An item whose title, when it has one, is text whatever it was written as, as an artifact's is, and leaves a
    name to be made from it."""
    title = names.title(tree.get("title"))
    if title is None:
        return Content(tree)
    if not names.slug(title):
        return Content(tree, (("title", rules.TITLE, _leaves_nothing(title)),))
    return Content({**tree, "title": title})


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


def _unsigned(request: kb_pb2.Actor, message: str) -> list[kb_pb2.Fault]:
    return [kb_pb2.Fault(rule=rule, message=f"every entry in the history {reason}") for rule, reason, missing in (
        (rules.ACTOR, "names the role that made it", not request.role.strip()),
        (rules.MESSAGE, "says why it was made", not message.strip()),
    ) if missing]


def signed(request: kb_pb2.Actor, message: str) -> Signed:
    """Who makes a change and why, who must name a role and a message; both faults when both fail."""
    faults = _unsigned(request, message)
    if faults:
        raise Refused(faults)
    return Signed(actor(request), message)


def reader(request: kb_pb2.Actor, message: str) -> Signed:
    """Who records what a piece of work read, who must sign and name the piece of work; every fault found."""
    faults = _unsigned(request, message)
    if not request.execution:
        faults.append(kb_pb2.Fault(rule=rules.ACTOR, message="a snapshot records what a named piece of work read"))
    if faults:
        raise Refused(faults)
    return Signed(actor(request), message)


def starter(request: kb_pb2.Actor) -> Actor:
    """The actor who starts a store, who must name a role."""
    if not request.role:
        raise Refused([kb_pb2.Fault(rule=rules.ACTOR, message="a store can only be started under a role")])
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
            rule=rules.ROOT,
            message="a store is started in a directory that was named and that exists; no directory was named",
        )])
    return Root(Path(text), text)


def _not_a_plain_name(text: str) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=text, rule=rules.LOCATOR,
        message=f"a name is a kind and a plain name of lower-case letters, digits and single hyphens, never a path; {text!r} is not",
    )
