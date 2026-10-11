"""The values the storage port takes and gives (kb.port): the link, the change, the entry, the type version, the search
candidate and the read values, with the small helpers that judge them (`told`, `held_waiting`). kb-internal, never
published. See kb.port for what an adapter does with them.
"""
from dataclasses import dataclass
from datetime import datetime

from kb.values import ArtifactId, Kind, Version


@dataclass(frozen=True)
class Link:
    """A link a change hands with an artifact's content: the field holding it, its place in the artifact, the artifact
    it lands on, the place of the part inside that artifact it lands on (empty for the artifact itself), and the kinds
    it may land on. An implicit link is kb's own bookkeeping: it holds what it lands on in place, and refuses its
    removal like any link, but no read of links, counts or walks shows it. `under` is the held type kb found the
    target's IRI to sit under, held or not, None for one under no held type; it is read only when the target is not
    held as the link lands, as one removed since the link was drafted is not: a link to an IRI not held lands only
    when the adapter holds that type and its IRI is among `kinds`, nothing but the link's target kept for it, and an
    implicit link never does. `waits` says kb found the store already holding this very link for the artifact,
    landing on nothing held (decision/a-link-that-waits-keeps-waiting); it is read only when the link names a part
    its held target lacks, and the link then lands only when the adapter held it so before the set (`told`).
    `holder` is the thing in the artifact whose field holds the link, as kb names it: empty for the artifact itself,
    the place of an item by its name, or by where it stands when it has none; the adapter keeps it, reads nothing in it."""
    field: str
    place: str
    target: ArtifactId
    part: str
    kinds: tuple[str, ...]
    implicit: bool = False
    under: ArtifactId | None = None
    waits: bool = False
    holder: str | None = ""


@dataclass(frozen=True)
class Linking:
    """A link as the store holds it: the artifact holding it, the field, its place there, where it lands, and
    what in the artifact holds it, as `Link.holder` said."""
    source: ArtifactId
    field: str
    place: str
    target: ArtifactId
    part: str
    holder: str | None = ""


def told(links) -> list[tuple | None]:
    """What tells each link of one artifact, given in the order the artifact carries them, from every other it
    holds: its field, what holds that field (`holder`), the IRI it names and the part, and how many links before it
    are the same in all four. Where it stands in a list is no part of it, so two links of one artifact, before and
    after a change, are the very same link when these are. None for a link handed with no holder, which is the same
    as no other."""
    seen, found = {}, []
    for each in links:
        key = (each.field, each.holder, each.target, each.part)
        seen[key] = seen.get(key, -1) + 1
        found.append(None if each.holder is None else (*key, seen[key]))
    return found


def held_waiting(links) -> frozenset:
    """The waiting links the store holds for one artifact, each as `told` gives it, but one told from nothing."""
    return frozenset(told(links)) - {None}


@dataclass(frozen=True)
class Versioned:
    """What a change to a type says of the version it leaves the type standing at: the version, and the title the
    version is made with. Its content and its revision are the change's."""
    version: Version
    title: str


@dataclass(frozen=True)
class TypeVersion:
    """A version of a type as the store holds it: the version, and the content, the revision and the title it was
    made with."""
    version: Version
    content: dict
    revision: int
    title: str


@dataclass(frozen=True)
class Change:
    """One change of a set: the artifact, its whole content after the change (None for a removal), its links and the
    places of the parts it holds, the revision the change read it at (0 when it was not held), the revision it
    leaves it at, and the types it was checked and its links read through that the set does not change, each with
    the revision it was read at, beside any IRI kb read as holding nothing, at revision 0. The adapter lands none of
    the set when any of those has since moved or is no longer held, or the IRI now holds something. `searched` are
    the rows the artifact is found by, as kb gives them (search.searchable): each `(what, label, words)`, what being
    "section" or "field", in order; the adapter keeps them in place of those it held, and answers `search` from them.
    `kind` is the kind of the artifact a change leaves, None for a removal. `version` is given by a change that
    leaves a type held: the adapter keeps that version, read by `type_version`, beside the versions of the type it
    already keeps, each as it was made, and lands it with the set or not at all; a removal takes with it, in its
    set's landing, every version kept of what it removes."""
    artifact: ArtifactId
    content: dict | None
    links: tuple[Link, ...] = ()
    parts: tuple[str, ...] = ()
    read: int = 0
    revision: int = 0
    through: tuple[tuple[ArtifactId, int], ...] = ()
    searched: tuple[tuple[str, str, str], ...] = ()
    kind: Kind | None = None
    version: Versioned | None = None

    @property
    def op(self) -> str:
        if self.content is None:
            return "remove"
        return "create" if self.read == 0 else "replace"


@dataclass(frozen=True)
class Entry:
    """One entry of the history, as journal.py names it: its id, its moment and its seq among the entries stamped at
    that moment, what it is filtered by, and the record itself."""
    id: str
    at: datetime
    seq: int
    record: dict
    artifact: str = ""
    role: str = ""
    execution: str = ""
    batch: str = ""


@dataclass(frozen=True)
class Candidate:
    """A search row holding a word searched for: the artifact, and the title of the section or the name of the field
    the row is."""
    artifact: ArtifactId
    section: str
    field: str
