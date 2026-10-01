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
    the revision it was read at. The adapter lands none of the set when any of those has since moved."""
    artifact: ArtifactId
    content: dict | None
    links: tuple[Link, ...] = ()
    parts: tuple[str, ...] = ()
    read: int = 0
    revision: int = 0
    through: tuple[tuple[ArtifactId, int], ...] = ()

    @property
    def op(self) -> str:
        if self.content is None:
            return "remove"
        return "create" if self.read == 0 else "replace"


@dataclass(frozen=True)
class Relink:
    """The links of an artifact a set leaves as it is, read again because a type they are read through changed: the
    artifact, its links now, and the revision they were read at. It leaves no new revision, and its links are not
    held to landing, since what the artifact holds was not checked again."""
    artifact: ArtifactId
    links: tuple[Link, ...]
    read: int


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


@dataclass(frozen=True)
class Reached:
    """An artifact a traversal reached, and the route to it: each step's field and the artifact it reached."""
    artifact: ArtifactId
    route: tuple[tuple[str, ArtifactId], ...]


class Refusal(Exception):
    """A set the port will not land; nothing of it is written."""


class Conflict(Refusal):
    """A change read its artifact, or a type it was read through, at a revision that has since moved, or an entry's
    id is already held."""


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


class Unreadable(Exception):
    """The database cannot be opened or read, or the SQLite this process runs cannot keep a store."""


class Port(Protocol):
    """Reads answer from the store as it stands; `land` changes it. Names come back in `names.order`."""

    def at_one_moment(self) -> ContextManager[None]:
        """A block whose reads all see the store as it stood when the first of them was made, whatever lands meanwhile."""

    def holds(self, artifact_id: ArtifactId) -> bool: ...

    def artifact(self, artifact_id: ArtifactId, as_of: str = "") -> dict:
        """The artifact now, or as it stood once the set named `as_of` landed. KeyError when it was not held."""

    def ids(self, kind: Kind | None = None, fields: dict[str, str] | None = None) -> list[ArtifactId]:
        """Every artifact held, or those of one kind whose fields each hold the value given, compared as the text
        YAML 1.2 writes the value as."""

    def links_out(self, artifact_id: ArtifactId, place: str = "") -> list[Linking]:
        """The links an artifact holds, or those at a place in it or inside that place, in the order handed."""

    def links_in(self, artifact_id: ArtifactId, field: str = "", kind: Kind | None = None) -> list[Linking]:
        """The links landing on an artifact or a part inside it, narrowed to a field and a kind of source."""

    def inbound(self, artifact_id: ArtifactId) -> dict[tuple[str, str], int]:
        """How many artifacts link into an artifact or its parts, by the kind of the source and the field."""

    def traverse(self, artifact_id: ArtifactId, inward: bool, depth: int, field: str = "",
                 kind: Kind | None = None) -> list[Reached]:
        """What links reach from an artifact, out or in, a step at a time to the depth: each artifact once, by its
        shortest route, never the start; a field or a kind narrows every step."""

    def search(self, words: list[str], kind: Kind | None = None, sections: bool = True,
               fields: bool = True) -> list[Candidate]:
        """Every section and every text field holding any word given, as search.tokens folds words."""

    def history(self, artifact: ArtifactId | None = None, role: str = "", execution: str = "",
                since: datetime | None = None, batch: str = "") -> list[dict]:
        """The entries, oldest first by moment then seq, narrowed by each filter given."""

    def entry_ids(self, at: datetime) -> list[str]:
        """The ids of the entries stamped at a moment."""

    def land(self, changes: list[Change], entries: list[Entry], relinks: list[Relink] = ()) -> None:
        """The changes, in order, the links restated, and the entries, as one set, or nothing. Raises Conflict,
        Linked or Unlanded."""
