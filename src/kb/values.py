"""The boundary: every value a request carries is turned here into a checked value, or refused with a fault.
Storage takes only these values, never a string that came from a request."""
from dataclasses import dataclass
from datetime import datetime, timezone

from kb import names, rules
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


def below(text: str) -> Below:
    """A path below a type as a request names it: segments of kb's grammar joined by single slashes."""
    segments = names.path(text)
    if segments is None:
        raise Refused([kb_pb2.Fault(rule=rules.LOCATOR, message=(
            f"a path below a type is plain segments joined by single slashes, as pricing or pricing/discounts; {text!r} is not"
        ))])
    return Below(segments)


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
