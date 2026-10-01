"""The storage port: what kb asks of whatever keeps a store, below kb's own rules. kb-internal, never published.

Above the port stay names, content checks, sections and items, signatures, faults and the contract. Below it an
adapter keeps the artifacts, their content at every revision, the links both ways, the search rows and the history,
and lands a set of changes whole or not at all. An adapter knows nothing of kinds or types: a link says which kinds
it may land on, and the kind of an artifact is the first part of its name.

The port refuses with the exceptions named here. None of them is published, and kb translates them above the port.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import ContextManager, Protocol

from kb.values import ArtifactId, Kind


@dataclass(frozen=True)
class Link:
    """A link a change hands with an artifact's content: the field holding it, its place in the artifact, the artifact
    it lands on, the place of the part inside that artifact it lands on (empty for the artifact itself), and the kinds
    it may land on. An implicit link is kb's own bookkeeping: it holds what it lands on in place, and refuses its
    removal like any link, but no read of links, counts or walks shows it."""
    field: str
    place: str
    target: ArtifactId
    part: str
    kinds: tuple[str, ...]
    implicit: bool = False


@dataclass(frozen=True)
class Linking:
    """A link as the store holds it: the artifact holding it, the field, its place there, and where it lands."""
    source: ArtifactId
    field: str
    place: str
    target: ArtifactId
    part: str


@dataclass(frozen=True)
class Change:
    """One change of a set: the artifact, its whole content after the change (None for a removal), its links and the
    places of the parts it holds, the revision the change read it at (0 when it was not held), the revision it
    leaves it at, and the types it was checked and its links read through that the set does not change, each with
    the revision it was read at. The adapter lands none of the set when any of those has since moved. `searched` are
    the rows the artifact is found by, as kb gives them (search.searchable): each `(what, label, words)`, what being
    "section" or "field", in order; the adapter keeps them in place of those it held, and answers `search` from them."""
    artifact: ArtifactId
    content: dict | None
    links: tuple[Link, ...] = ()
    parts: tuple[str, ...] = ()
    read: int = 0
    revision: int = 0
    through: tuple[tuple[ArtifactId, int], ...] = ()
    searched: tuple[tuple[str, str, str], ...] = ()

    @property
    def op(self) -> str:
        if self.content is None:
            return "remove"
        return "create" if self.read == 0 else "replace"


@dataclass(frozen=True)
class Relink:
    """The links of an artifact a set leaves as it is, read again because a type they are read through changed: the
    artifact, its links now, the revision they were read at, and the types they were read through that the set does
    not change, each with the revision it was read at. It leaves no new revision, and its links are not held to
    landing, since what the artifact holds was not checked again. The adapter lands none of the set when the artifact
    or any of those types has since moved."""
    artifact: ArtifactId
    links: tuple[Link, ...]
    read: int
    through: tuple[tuple[ArtifactId, int], ...] = ()


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
    """A change read its artifact, or a type it was read through, at a revision that has since moved; an artifact of
    a kind whose links the set reads anew is held that the set does not change or restate; or an entry's id is
    already held."""


class Linked(Refusal):
    """The set removes an artifact, or drops a part, that something outside the set links into; each such link."""

    def __init__(self, links: list[Linking]):
        super().__init__(links)
        self.links = links


class Unlanded(Refusal):
    """A link the set hands lands on nothing the set leaves held, or on an artifact of a kind it may not land on."""

    def __init__(self, links: list[Linking]):
        super().__init__(links)
        self.links = links


class Busy(Exception):
    """Another change held the store's write lock longer than the store waits for it; nothing is written, and the same
    change may be made again."""


class Unreadable(Exception):
    """The database cannot be opened or read, or the SQLite this process runs cannot keep a store."""


class EarlierKb(Unreadable):
    """The store was made by an earlier version of kb, in a form this kb cannot read; it carries where the store is."""


class Port(Protocol):
    """Reads answer from the store as it stands; `land` changes it. Names come back in `names.order`."""

    def at_one_moment(self) -> ContextManager[None]:
        """A block whose reads all see the store as it stood when the first of them was made, whatever lands meanwhile."""

    def holds(self, artifact_id: ArtifactId) -> bool: ...

    def artifact(self, artifact_id: ArtifactId) -> dict:
        """The artifact now. KeyError when it is not held."""

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

    def land(self, changes: list[Change], entries: list[Entry], relinks: list[Relink] = (),
             kinds: tuple[Kind, ...] = ()) -> None:
        """The changes, in order, the links restated, and the entries, as one set, or nothing. `kinds` are those whose
        every artifact's links the set reads anew: an artifact of one held that the set neither changes nor restates
        is Conflict. Raises Conflict, Linked or Unlanded; and Busy, as `exclusive` does, when another change holds the
        write lock longer than the store waits for it."""
