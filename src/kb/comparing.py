"""A file offered for import compared with what the store holds at its IRI: the file's artifact as it would land, its
items named and its entries ordered (kb.naming), against the artifact the store holds there, or, for a type's version,
against the version the store keeps at that number, by everything the file gives but its revision. An identical one
is what an import passes over. Nothing here reads a file, checks one against its type or writes."""
from kb import composition, naming
from kb.draft import Draft
from kb.offers import Offered
from kb.port import Port
from kb.values import ArtifactId, Refused


def identical(store: Port, offered: list[Offered]) -> set[ArtifactId]:
    """The names of the files, among those that read as artifacts, that the store holds identically."""
    draft = Draft(store)
    return {
        each.name for each in offered
        if each.artifact is not None and _same(_as_landing(draft, each), _held(store, each))
    }


def _same(landing: dict | None, held: dict | None) -> bool:
    """Whether a file's artifact as it would land is the one held, whatever revision each stands at."""
    return landing is not None and held is not None and _compared(landing) == _compared(held)


def _compared(artifact: dict) -> dict:
    return {key: value for key, value in artifact.items() if key != "revision"}


def _as_landing(draft: Draft, each: Offered) -> dict | None:
    """A file's artifact as it would land in the store as it stands; None when the store holds no such version of its
    type, so nothing it holds was read through it."""
    try:
        return naming.imported(draft, each.id, each.artifact)[0]
    except Refused:
        return None


def _held(store: Port, each: Offered) -> dict | None:
    """What the store holds where a file's artifact would land: the artifact at its IRI, or, for a type's version,
    the version kept at its number, with the title it was made with; None when it holds none."""
    if not store.holds(each.id):
        return None
    if not each.typed:
        return store.artifact(each.id)
    kept = composition.kept(each.id, each.number, store)
    return kept and {**kept.content, "title": kept.title}
