"""THROWAWAY. The port kb would own: what any storage adapter must do, below kb's own rules.

kb keeps above the port: minting slugs from titles, naming items, reading or writing one node or section of a
document, the signature rules, and the public contract. Each adapter keeps below it: persistence, the links index,
integrity, transactions, concurrency, history, search and export.

The neutral type model (a "kind") is a plain dict:

    {"name": "note", "version": 1, "base": None | "<kind name>",
     "fields": {"<name>": {"type": "string" | "text" | "number" | "boolean" | "link",
                           "required": bool, "many": bool,
                           # links only:
                           "targets": ["<kind name>", ...], "parts": bool}},
     "collections": {"<name>": {"fields": {...}, "collections": {...}}},
     "sections": ["<title>", ...]}

- A kind with a base carries every field, collection and required section of its base, the base's first. A link
  whose targets name a base also accepts documents of any kind built on it.
- "text" is prose: searched. "string" is a plain value: filtered on, not searched.
- A document's content holds its fields, its "sections" (a list of {"title", "body", "sections"}) and its
  collections (lists of items, each item a dict with an "id" unique in its collection, and its own fields and
  collections). The required section titles must appear first, in order; further sections may follow.
- A link's value is a document id, "kind/slug", or, when the field allows parts, a place inside one:
  "kind/slug#collection/item-id" or deeper "kind/slug#collection/item-id/collection/item-id".
- A required field must be present and not None. Unknown fields are refused.

A document as read: {"id": "kind/slug", "kind": str, "title": str, "revision": int, "content": dict}.
A signature: {"role": str, "execution": str, "message": str}.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterator, Protocol


@dataclass
class Fault:
    rule: str          # one of RULES
    doc: str = ""      # the document (or kind) the fault is about
    path: str = ""     # the place in it, when there is one
    message: str = ""


RULES = {
    "kind",        # a kind the store holds no type for, or a kind that is not well formed
    "shape",       # content that does not fit its kind: unknown field, wrong type, missing required field or section
    "ref",         # a link that does not land: no such document or part, or a document of a kind the field refuses
    "not-found",   # a document the store holds nothing under
    "conflict",    # an expected revision that no longer holds
    "linked",      # removing a document, or a part of one (by replacing it without the part), something links to
    "in-use",      # removing or narrowing a kind while documents of it exist
    "version",     # a kind changed without its version moving on
    "set",         # a set that is malformed: a key captured twice or never captured
}


class Refused(Exception):
    """A change or query refused; nothing was written."""

    def __init__(self, faults: list[Fault]):
        super().__init__("; ".join(f"{f.rule}: {f.doc} {f.path} {f.message}".strip() for f in faults))
        self.faults = faults

    @property
    def rules(self) -> set[str]:
        return {f.rule for f in self.faults}


@dataclass
class Committed:
    commit: str                                   # an id that `read(at=)`, `list(at=)` and `history` understand
    results: list[dict] = field(default_factory=list)   # per change in order: {"id": str, "revision": int}


@dataclass
class Link:
    source: str   # the document holding the link
    field: str    # the link field
    place: str    # where the field sits in the source: "about", "steps/draft/uses", "tags/1"
    target: str   # the value as stored: "kind/slug" or "kind/slug#collection/item"


@dataclass
class Reached:
    id: str
    route: list[tuple[str, str]]   # (field, id) per step from the start


@dataclass
class Hit:
    id: str
    score: float
    snippet: str


@dataclass
class Entry:
    commit: str
    at: str                 # ISO 8601 UTC
    role: str
    execution: str
    message: str
    changes: list[tuple[str, str, int]]   # (op, id, revision) in the order of the set


class Store(Protocol):
    # Types
    def define(self, kind: dict, sig: dict) -> None:
        """Create a kind, or replace it with a higher version (refused 'version' otherwise). A replacement that
        would leave held documents unfit is accepted; `check` reports them. Refused 'kind' when the kind is not
        well formed: a base or link target naming no kind, or a kind based on itself."""

    def remove_kind(self, name: str, sig: dict) -> None:
        """Refused 'in-use' while any document of that kind, or of a kind based on it, exists."""

    def kinds(self) -> list[str]: ...

    # Changes
    def commit(self, changes: list[dict], sig: dict, expect: dict[str, int] | None = None) -> Committed:
        """Every change lands, in order, as one commit, or none does. A change is one of:
            {"op": "create", "kind": str, "slug": str, "title": str, "content": dict, "key": str?}
            {"op": "replace", "id": str, "content": dict}
            {"op": "remove", "id": str}
        A create's id is "kind/slug", or, when that is taken (by the store or an earlier create in the set),
        "kind/slug-2", "-3" and so on. Where content holds a link, {"ref": "<key>"} stands for the id minted for
        the create in this set carrying that key; creates may refer to each other in any order. Each change is
        checked against the store as the whole set leaves it: two new documents may link to each other.
        `expect` maps ids to the revision the caller read; any that moved refuses the set with 'conflict'.
        A replace or remove of a document whose revision moved between the adapter's read and its write is also
        refused 'conflict' (never a lost update). Revision starts at 1 and goes up by 1 per change to the doc.
        Refused with every fault found: 'kind', 'shape', 'ref', 'not-found', 'conflict', 'linked', 'set'."""

    # Reads
    def read(self, id: str, at: str | None = None) -> dict:
        """The document now, or as it stood after commit `at`. Refused 'not-found'."""

    def list(self, kind: str, where: dict[str, Any] | None = None, at: str | None = None) -> list[str]:
        """Ids of documents of that kind (and of kinds based on it), sorted, whose top-level fields equal every
        value in `where`. Refused 'kind'."""

    def links_out(self, id: str, place: str | None = None, field: str | None = None,
                  kind: str | None = None) -> list[Link]:
        """Links the document carries, anywhere in it, or only within the item at `place`
        ("collection/item-id/..."), narrowed to one field and to targets of one kind. Sorted by place."""

    def links_in(self, id: str, field: str | None = None, kind: str | None = None) -> list[Link]:
        """Links that land on the document or on any part inside it, narrowed to one field and to sources of one
        kind. Sorted by (source, place)."""

    def inbound_counts(self, id: str) -> dict[tuple[str, str], int]:
        """How many links land on the document or its parts, by (source kind, field)."""

    def traverse(self, id: str, direction: str, depth: int, field: str | None = None,
                 kind: str | None = None) -> list[Reached]:
        """Documents reached following links out ('out') or in ('in') up to `depth` steps, each once, by its
        shortest route, never the start; a field or kind narrows every step. Nearest first, then by id."""

    def search(self, text: str, kind: str | None = None) -> list[Hit]:
        """Documents whose title, text fields or section bodies hold every word, best first."""

    def history(self, id: str | None = None, role: str | None = None, execution: str | None = None,
                since: str | None = None) -> list[Entry]:
        """Commits, oldest first, narrowed to those touching a document, made under a role, for a piece of work,
        or at or after an ISO 8601 moment."""

    def check(self) -> list[Fault]:
        """Every document that no longer fits its kind or whose links do not land ('shape', 'ref')."""

    # Moving a corpus
    def export(self) -> Iterator[dict]:
        """Every kind ({"kind": <kind dict>}) then every document as `read` gives it, in a stable order."""

    def import_(self, items: list[dict], sig: dict) -> None:
        """Into an empty store: what `export` gave, ids and titles kept, revisions restarting at 1."""


class Factory(Protocol):
    def __call__(self) -> Store:
        """A new, empty, isolated store."""
