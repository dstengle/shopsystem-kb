"""The boundary: every value a request carries is turned here into a checked value, or refused with a fault.
Storage takes only these values, never a string that came from a request."""
from dataclasses import dataclass
from datetime import datetime, timezone

from kb import canonical, names, rules, settled
from kb.content import loads
from kb.contract import kb_pb2


class Refused(ValueError):
    """A request value that does not convert. Carries every fault found."""

    def __init__(self, faults: list[kb_pb2.Fault]):
        super().__init__(faults)
        self.faults = faults


@dataclass(frozen=True)
class Kind:
    """A kind, named by its type's IRI."""
    name: str


@dataclass(frozen=True)
class ArtifactId:
    """An artifact, named by its IRI."""
    iri: str

    def __str__(self) -> str:
        return self.iri


@dataclass(frozen=True)
class Version:
    """A version of a type: the kind it is of, and its number."""
    kind: Kind
    number: int

    def __str__(self) -> str:
        return names.versioned(self.kind.name, self.number)


@dataclass(frozen=True)
class Below:
    """A path below a type: the segments an artifact's IRI holds after its type's, or the first of them."""
    segments: tuple[str, ...]


TYPE_KIND = Kind(names.TYPES)


def type_of(kind: Kind) -> ArtifactId:
    """The type the artifacts of a kind are of, held at the kind's IRI."""
    return ArtifactId(kind.name)


@dataclass(frozen=True)
class Locator:
    id: ArtifactId
    place: tuple[str, ...]


def kind(text: str) -> Kind:
    """A kind as a request names it: its type's IRI, of kb's grammar."""
    if not names.iri(text):
        raise Refused([kb_pb2.Fault(
            rule=rules.LOCATOR, message=f"a kind is named by its type's IRI, an IRI of kb's grammar; {text!r} is not",
        )])
    return Kind(text)


def artifact_id(text: str) -> ArtifactId:
    """An artifact's IRI as a request names it, of kb's grammar, which holds neither a version nor a place."""
    if not names.iri(text):
        raise Refused([kb_pb2.Fault(artifact=text, rule=rules.LOCATOR, message=(
            f"a name is an IRI of kb's grammar, https://, a host and plain segments, never a path; {text!r} is not"
        ))])
    return ArtifactId(text)


def version(text: str) -> Version:
    """A type version's IRI as a request names it: a type's IRI, `@` and the version's number."""
    found = names.version(text)
    if found is None:
        raise Refused([kb_pb2.Fault(artifact=text, rule=rules.LOCATOR,
            message=f"a version of a type is named by the type's IRI, @ and its number; {text!r} is not")])
    return Version(Kind(found[0]), found[1])


def named(text: str) -> Version | None:
    """The version of its type a change names; None when it names none, as an empty name says."""
    return version(text) if text else None


def read(request: kb_pb2.Locator) -> tuple[Locator, Version | None]:
    """What a read names: an artifact and a place in it, or, when its name is a type version's IRI, the type's
    locator and that version."""
    found = names.version(request.id)
    if found is None:
        return locator(request), None
    return _located(found[0], request.place), Version(Kind(found[0]), found[1])


def locator(request: kb_pb2.Locator) -> Locator:
    """A locator's name and its place, each checked; both faults when both fail."""
    return _located(request.id, request.place)


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
            artifact=name, place=path, rule=rules.LOCATOR,
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
    return in_utc(moment)


def in_utc(moment: datetime) -> datetime:
    """The one reading of a moment: in UTC unless it says otherwise, and given in UTC."""
    return (moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)


def titled(title: str, at: str) -> tuple:
    """The faults of an artifact's title, said of the IRI given: a title is required."""
    if title:
        return ()
    return (kb_pb2.Fault(artifact=at, place="title", rule=rules.TITLE,
                         message="an artifact cannot be created without a title"),)


def expected(revision: int) -> int | None:
    """The revision a change says the client read its artifact at; None when it says none, as 0 says."""
    return revision or None


def _leaves_nothing(title: str) -> str:
    return f"a title must leave something to make a name from; {title!r} leaves nothing"


@dataclass(frozen=True)
class Content:
    """Content as a request carries it: the tree read from it, and, when it cannot be taken, what is wrong with it,
    each as a place, a rule and a message, to be said of whichever artifact the content turns out to be for."""
    tree: object
    problems: tuple[tuple[str, str, str], ...] = ()

    def refusal(self, artifact: str) -> list[kb_pb2.Fault]:
        return [kb_pb2.Fault(artifact=artifact, place=path, rule=rule, message=message)
                for path, rule, message in self.problems]


def content(text: str, at_root: bool = True) -> Content:
    """Content read plainly, and, for a whole artifact, holding only what a type declares. The identity keys belong
    to an artifact's root, so a node inside it, a section with its title, is not held to them. Every problem found."""
    try:
        tree = canonical.entries(text) if at_root else loads(text)
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
