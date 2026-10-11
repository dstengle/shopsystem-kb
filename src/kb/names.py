"""Names: kb's IRI grammar, how an IRI is split into its host and segments, which IRIs one sits under, and a type
version's IRI read, the place an export gives an artifact and the IRI a file's place gives, how a link names a place
inside an artifact and a type version is referred to. Nothing here reads or writes. The names of items are
`item_names.py`'s."""
import re

PLAIN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_DOTTED = r"[a-z0-9]+(?:-[a-z0-9]+)*(?:\.[a-z0-9]+(?:-[a-z0-9]+)*)*"
SEGMENT = re.compile(_DOTTED)
IRI = re.compile(rf"https://(?P<host>{_DOTTED})(?P<path>(?:/{_DOTTED})+)")
VERSION = re.compile(r"(?P<iri>[^@]+)@(?P<number>[1-9][0-9]*)")
LONGEST = 512
SCHEME = "https://"
FILE = ".yaml"

VERSIONED = "@"

TYPES = "https://missingmass.io/kb/type"
TYPE_URI = "kb:"


def iri(text: str) -> bool:
    """Whether text is an IRI of kb's grammar: `https://`, a host of plain names joined by single dots, and one or
    more segments, each plain names joined by single dots; at most LONGEST characters; no `@` and no `#`."""
    return len(text) <= LONGEST and IRI.fullmatch(text) is not None


def split(iri_text: str) -> tuple[str, tuple[str, ...]]:
    """An IRI of kb's grammar read as its host and its segments."""
    host, *segments = iri_text.removeprefix(SCHEME).split("/")
    return host, tuple(segments)


def above(iri_text) -> tuple[str, ...]:
    """The IRIs an IRI sits under, nearest first: its host and each run of its segments, from the first, that leaves
    at least one out. Whole segments only, and never the IRI itself."""
    host, segments = split(str(iri_text))
    return tuple(SCHEME + "/".join((host, *segments[:count])) for count in range(len(segments) - 1, 0, -1))


def below(iri_text, type_iri) -> tuple[str, ...] | None:
    """An IRI's path below a type's IRI: the segments it holds after the type's. None for an IRI that does not sit
    under the type's, as the type's own does not."""
    under = f"{type_iri}/"
    return tuple(str(iri_text).removeprefix(under).split("/")) if str(iri_text).startswith(under) else None


def selects(segments: tuple[str, ...], iri_text, type_iri) -> bool:
    """Whether a path below the type selects an IRI of a type: the IRI's path below its type's IRI is the segments
    given or begins with them, whole segments only, so `plan` selects `plan` and `plan/a`, never `planning`."""
    found = below(iri_text, type_iri)
    return found is not None and found[:len(segments)] == tuple(segments)


def path(text: str) -> tuple[str, ...] | None:
    """A path below a type read as its segments: one or more, joined by single slashes, each a segment of kb's IRI
    grammar, with no slash at either end. None for text that is not one, empty text among it."""
    segments = tuple(text.split("/"))
    return segments if all(SEGMENT.fullmatch(each) for each in segments) else None


def version(text: str) -> tuple[str, int] | None:
    """A type version's IRI read as the type's IRI and the version's number; None for text that is not one."""
    found = VERSION.fullmatch(text)
    if found is None or not iri(found["iri"]) or len(text) > LONGEST:
        return None
    return found["iri"], int(found["number"])


def versioned(type_iri: str, number: int) -> str:
    """A type version's IRI: the type's IRI, `@` and the version's number."""
    return f"{type_iri}{VERSIONED}{number}"


def order(artifact_id) -> tuple[str, ...]:
    """The one order artifacts' IRIs are given in: as the places the export layout gives them compare, step by
    step."""
    return place(artifact_id)


def place(artifact_id, number: int | None = None) -> tuple[str, ...]:
    """The place the export layout gives an artifact, as steps below the directory: the host and the segments of its
    IRI, the last written `<segment>.yaml`, or, for a type's version, `<segment>@<n>.yaml`; the inverse of
    `filed`."""
    host, segments = split(str(artifact_id))
    last = segments[-1] if number is None else versioned(segments[-1], number)
    return (host, *segments[:-1], f"{last}{FILE}")


def placing(artifact_id, number: int | None = None) -> str:
    """That place written as one path below the directory, its steps joined by slashes."""
    return "/".join(place(artifact_id, number))


def filed(steps: tuple[str, ...]) -> tuple[str, int | None] | None:
    """The IRI of the artifact the export layout puts at a file's place, given the place's steps below the directory,
    and the version's number when the place is a type version's, None when it is not; None for a place where the
    layout puts no artifact."""
    if len(steps) < 2 or not steps[-1].endswith(FILE):
        return None
    written = SCHEME + "/".join((*steps[:-1], steps[-1].removesuffix(FILE)))
    found = version(written)
    if found is not None:
        return found
    return (written, None) if iri(written) else None


def linked(text: str) -> tuple[str, str]:
    """A link as a field holds it read as the name it points at and, after `#`, the place inside that artifact."""
    name, _, place = text.partition("#")
    return name, place


def pointing(name, place: str) -> str:
    """A link written as a field holds it, which `linked` reads back: the name it points at and, after `#`, the place
    inside that artifact, when it names one."""
    return f"{name}#{place}" if place else str(name)


def placed(steps) -> str:
    """A place inside an artifact as it is written: its steps, each a collection, an item's or a section's name, or a
    field, joined by slashes."""
    return "/".join(steps)


def steps(text: str) -> tuple[str, ...]:
    """A written place read back as its steps, none for no place, none of them yet checked."""
    return tuple(text.split("/")) if text else ()


def referred(ref: str) -> tuple[str, str] | None:
    """What a `kb:` reference names: the IRI of a type's version, and what follows it from `#` on, empty when the
    reference is to the whole type. None for a reference that is not kb's."""
    if not ref.startswith(TYPE_URI):
        return None
    name, mark, fragment = ref.removeprefix(TYPE_URI).partition("#")
    return name, mark + fragment


def plain(text: str) -> bool:
    """Whether text is a plain name: lower-case letters and digits in runs joined by single hyphens."""
    return PLAIN.fullmatch(text) is not None
