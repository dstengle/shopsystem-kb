"""The storage port: what kb asks of whatever keeps a store, below kb's own rules. kb-internal, never published.

Above the port stay names, content checks, sections and items, signatures, faults and the contract. Below it an
adapter keeps the artifacts, their content at every revision, the links both ways, the search rows and the history,
and lands a set of changes whole or not at all. An adapter keeps the versions of a type it is handed, each
as made, and knows nothing of what a type declares: a change says the kind of its artifact, its type's IRI, and a link
says which kinds it may land on and, for a target kb found not held, the held type that target sits under.

The port refuses with the exceptions named here. None of them is published, and kb translates them above the port.
"""
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import ContextManager, Protocol

from kb.values import ArtifactId, Kind, Version


@dataclass(frozen=True)
class Link:
    """A link a change hands with an artifact's content: the field holding it, its place in the artifact, the artifact
    it lands on, the place of the part inside that artifact it lands on (empty for the artifact itself), and the kinds
    it may land on. An implicit link is kb's own bookkeeping: it holds what it lands on in place, and refuses its
    removal like any link, but no read of links, counts or walks shows it. `under` is the held type kb found the
    target's IRI to sit under when it found the target not held, None for a target it found held: a link to an IRI
    not held lands only when the adapter holds that type and its IRI is among `kinds`, nothing but the link's target
    kept for it, and an implicit link never does."""
    field: str
    place: str
    target: ArtifactId
    part: str
    kinds: tuple[str, ...]
    implicit: bool = False
    under: ArtifactId | None = None


@dataclass(frozen=True)
class Linking:
    """A link as the store holds it: the artifact holding it, the field, its place there, and where it lands."""
    source: ArtifactId
    field: str
    place: str
    target: ArtifactId
    part: str


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
    the revision it was read at. The adapter lands none of the set when any of those has since moved or is no longer
    held. `searched` are
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


class Refusal(Exception):
    """A set the port will not land; nothing of it is written."""


class Conflict(Refusal):
    """A change read its artifact, or a type it was read through, at a revision that has since moved, a type since
    removed standing at none; or an entry's id is already held."""


class Linked(Refusal):
    """The set removes an artifact, or drops a part, that something outside the set links into; each such link."""

    def __init__(self, links: list[Linking]):
        super().__init__(links)
        self.links = links


class Unlanded(Refusal):
    """A link the set hands lands on an artifact of a kind it may not land on, on a part its artifact lacks, or on an
    IRI the set leaves not held with no held type it may land on carried."""

    def __init__(self, links: list[Linking]):
        super().__init__(links)
        self.links = links


class Busy(Exception):
    """Another change held the store's write lock longer than the store waits for it; nothing is written, and the same
    change may be made again."""


class Unreadable(Exception):
    """The database cannot be opened or read, or the SQLite this process runs cannot keep a store."""


class Port(Protocol):
    """Reads answer from the store as it stands; `land` changes it. Names come back in `names.order`."""

    def at_one_moment(self) -> ContextManager[None]:
        """A block whose reads all see the store as it stood when the first of them was made, whatever lands meanwhile."""

    def holds(self, artifact_id: ArtifactId) -> bool: ...

    def artifact(self, artifact_id: ArtifactId) -> dict:
        """The artifact now. KeyError when it is not held."""

    def type_version(self, version: Version) -> TypeVersion:
        """The version of a type held at the version's IRI, as it was made. KeyError when none is held there. A
        version is no artifact: `holds`, `artifact` and `ids` answer nothing of it."""

    def versions(self, type_id: ArtifactId) -> list[int]:
        """The number of every version held of the type at an IRI, lowest first; none where no version is held."""

    def ids(self, kind: Kind | None = None, fields: dict[str, str] | None = None) -> list[ArtifactId]:
        """Every artifact held, or those of one kind whose fields each hold the value given, compared as the text
        YAML 1.2 writes the value as."""

    def links_in(self, artifact_id: ArtifactId, field: str = "", kind: Kind | None = None) -> list[Linking]:
        """The links landing on an artifact or a part inside it, narrowed to a field and a kind of source."""

    def inbound(self, artifact_id: ArtifactId) -> dict[tuple[str, str], int]:
        """How many artifacts link into an artifact or its parts, by the kind of the source and the field."""

    def search(self, words: list[str], kind: Kind | None = None, sections: bool = True,
               fields: bool = True) -> list[Candidate]:
        """Every section and every text field holding any word given, as search.tokens folds words."""

    def history(self, artifact: ArtifactId | None = None, role: str = "", execution: str = "",
                since: datetime | None = None, batch: str = "") -> list[dict]:
        """The entries, narrowed by each filter given: those of one artifact in the order they landed, whatever else
        is asked, and every other read by moment, then the order they landed."""

    def entry_ids(self, at: datetime) -> list[str]:
        """The ids of the entries stamped at a moment."""

    def exclusive(self) -> ContextManager[None]:
        """A block holding the store's write lock from its start to its end: its reads see every set landed before it,
        no other set lands until it ends, and what `land` lands in it is kept when the block ends without raising.
        A refusal of `land` inside it takes back only that set, and the lock is still held. A block opened inside one
        that holds the lock runs within it. Raises Busy, nothing
        written, when another change holds the write lock longer than the store waits for it."""

    def copied(self, path: Path, form: int) -> None:
        """The store copied whole, as it stood at one moment, into a new file at path, which says it holds a store of
        the form given; the copy neither takes nor waits for the write lock. Raises FileExistsError, writing nothing,
        when anything is at path; a copy that fails leaves nothing there."""

    def land(self, changes: list[Change], entries: list[Entry]) -> None:
        """The changes, in order, and the entries, as one set, or nothing. Every link is checked against the store as
        the set leaves it: one to a held artifact by that artifact's kind and parts, one to an IRI not held by the
        type it carries (`Link.under`). Raises Conflict, Linked or Unlanded; and Busy, as `exclusive` does, when
        another change holds the write lock longer than the store waits for it."""
