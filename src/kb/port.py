"""The storage port: what kb asks of whatever keeps a store, below kb's own rules. kb-internal, never published.

Above the port stay names, content checks, sections and items, signatures, faults and the contract. Below it an
adapter keeps the artifacts, their content at every revision, the links both ways, the search rows and the history,
and lands a set of changes whole or not at all. An adapter keeps the versions of a type it is handed, each
as made, and knows nothing of what a type declares: a change says the kind of its artifact, its type's IRI, and a link
says which kinds it may land on, the held type its target sits under, read when the target is not held, what in its
artifact holds it, by name, and whether the store already held that very link, waiting (`told`), read when its
held target lacks the part it names.

The port refuses with the exceptions named here. None of them is published, and kb translates them above the port.
"""
from datetime import datetime
from pathlib import Path
from typing import ContextManager, Protocol

from kb.port_values import Candidate, Change, Entry, Linking, TypeVersion
from kb.values import ArtifactId, Below, Kind, Version


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
    """A link the set hands lands on an artifact of a kind it may not land on, on a part its artifact lacks that it
    did not already wait on, or on an IRI the set leaves not held with no held type it may land on carried."""

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

    def ids(self, kind: Kind | None = None, fields: dict[str, str] | None = None,
            path: Below | None = None) -> list[ArtifactId]:
        """Every artifact held, or those of one kind whose fields each hold the value given, compared as the text
        YAML 1.2 writes the value as. With a path, only those it selects (`names.selects`), each by its IRI's path
        below its own kind's, the IRI the change that landed it gave as its kind; and with a path and no kind, of
        every kind but the kind of types (`values.TYPE_KIND`)."""

    def links_in(self, artifact_id: ArtifactId, field: str = "", kind: Kind | None = None) -> list[Linking]:
        """The links landing on an artifact or a part inside it, narrowed to a field and a kind of source."""

    def inbound(self, artifact_id: ArtifactId) -> dict[tuple[str, str], int]:
        """How many artifacts link into an artifact or its parts, by the kind of the source and the field."""

    def waiting(self, source: ArtifactId | None = None) -> list[Linking]:
        """Every link that lands on nothing held, or those of the one artifact named: one whose target is not held,
        or into a part its held target lacks; never an implicit one. By the name it points at, whatever part of it,
        then the artifact holding it, then as handed."""

    def search(self, words: list[str], kind: Kind | None = None, sections: bool = True,
               fields: bool = True) -> list[Candidate]:
        """Every section and every text field holding any word given, as search.tokens folds words."""

    def history(self, artifact: ArtifactId | None = None, role: str = "", execution: str = "",
                since: datetime | None = None, batch: str = "") -> list[dict]:
        """The entries, narrowed by each filter given: those of one artifact in the order they landed, whatever else
        is asked, and every other read by moment, then the order they landed."""

    def entry_ids(self, at: datetime) -> list[str]:
        """The ids of the entries stamped at a moment."""

    def landed_last(self) -> str:
        """The id of the entry that landed last, by the order entries landed in, whatever their moments; empty when
        none has landed."""

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
        the set leaves it: one to a held artifact by that artifact's kind and parts, but that one the artifact
        already held waiting, and says so (`Link.waits`), still lands into a part its target lacks; one to an IRI
        not held by the type it carries (`Link.under`). Raises Conflict, Linked or Unlanded; and Busy, as `exclusive` does, when
        another change holds the write lock longer than the store waits for it."""
