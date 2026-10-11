"""A file offered for import compared with what the store holds at its IRI: the canonical text of the file's artifact
as it would land, its items named and its entries ordered (kb.naming), against the canonical text of the artifact the
store holds there, or, for a type's version, of the version the store keeps at that number, each without its revision.
The same text is identical, which an import passes over; any other is a difference, a mapping's entries in another
order and a value of another kind among them. Nothing here reads a file, checks one against its type or writes."""
from kb import canonical, composition, naming, settled
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
    """Whether a file's artifact as it would land is written as the one held is, whatever revision each stands at."""
    return landing is not None and held is not None and _written(landing) == _written(held)


def _written(artifact: dict) -> str:
    """The canonical text of an artifact without its revision: what kb would write of it, so a mapping's entries in
    another order, or a value of another kind that counts as equal, is another text."""
    return canonical.dump({key: value for key, value in artifact.items() if key != "revision"})


def _as_landing(draft: Draft, each: Offered) -> dict | None:
    """A file's artifact as it would land in the store as it stands; None when the store holds no such version of its
    type, so nothing it holds was read through it."""
    try:
        return naming.imported(draft, each.id, each.artifact)[0]
    except Refused:
        return None


def _held(store: Port, each: Offered) -> dict | None:
    """What the store holds where a file's artifact would land, as an export writes it: the artifact at its IRI, or,
    for a type's version, the version kept at its number, with the title it was made with; None when it holds none."""
    if not store.holds(each.id):
        return None
    if not each.typed:
        return _ordered(store, store.artifact(each.id))
    kept = composition.kept(each.id, each.number, store)
    return kept and _ordered(store, {**kept.content, "title": kept.title})


def _ordered(store: Port, artifact: dict) -> dict:
    """An artifact the store holds, its entries in the order the version of its type it conforms to declares."""
    return settled.order(artifact, composition.declared(composition.conformed(artifact, store)["schema"], store))
