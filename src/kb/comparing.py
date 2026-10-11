"""A file offered for import compared with what the store holds at its IRI: the canonical text of the file's artifact
as it would land, its items named and its entries ordered (kb.naming), against the canonical text of the artifact the
store holds there, or, for a type's version, of the version the store keeps at that number, each without its revision.
The same text is identical, which an import passes over; any other is a difference, a mapping's entries in another
order and a value of another kind among them, and so is a type's version the store does not keep that the type it
holds could not gain. One comparison serves the check and the import. Nothing here reads a file, checks one against
its type, makes a fault or writes."""
from dataclasses import dataclass, field

from kb import canonical, composition, naming, settled
from kb.draft import Draft
from kb.offers import Offered
from kb.port import Port
from kb.values import ArtifactId, Refused


@dataclass(frozen=True)
class Compared:
    """Files compared with the store: the names of those it holds identically, and those that differ from what it
    holds, in the order they were given. A file in neither brings what the store does not hold."""
    identical: set[ArtifactId] = field(default_factory=set)
    differing: list[Offered] = field(default_factory=list)


def compared(store: Port, offered: list[Offered]) -> Compared:
    """The files, among those that read as artifacts, the store holds identically, and those that differ from what it
    holds where they would land."""
    draft, found = Draft(store), Compared()
    for each in offered:
        if each.artifact is None or not store.holds(each.id):
            continue
        if _differs(draft, store, each):
            found.differing.append(each)
        elif _held(store, each) is not None:
            found.identical.add(each.name)
    return found


def _differs(draft: Draft, store: Port, each: Offered) -> bool:
    """Whether a file whose IRI the store holds something at differs from it: it is not written as what is held there
    is, or it is a type's version the store does not keep and its type could not gain."""
    held = _held(store, each)
    return _out_of_step(store, each) if held is None else _as_landing(draft, each) != _written(held)


def _written(artifact: dict) -> str:
    """The canonical text of an artifact without its revision: what kb would write of it, so a mapping's entries in
    another order, or a value of another kind that counts as equal, is another text."""
    return canonical.dump({key: value for key, value in artifact.items() if key != "revision"})


def _as_landing(draft: Draft, each: Offered) -> str | None:
    """The text of a file's artifact as it would land in the store as it stands; None when the store holds no such
    version of its type, so nothing it holds was read through it, or when kb could not write it."""
    try:
        return _written(naming.imported(draft, each.id, each.artifact)[0])
    except (Refused, canonical.NotCanonical):
        return None


def _held(store: Port, each: Offered) -> dict | None:
    """What the store holds where a file's artifact would land, as an export writes it: the artifact at its IRI, or,
    for a type's version, the version kept at its number, with the title it was made with; None when it keeps none."""
    if not each.typed:
        return _ordered(store, store.artifact(each.id))
    kept = composition.kept(each.id, each.number, store)
    return kept and _ordered(store, {**kept.content, "title": kept.title})


def _ordered(store: Port, artifact: dict) -> dict:
    """An artifact the store holds, its entries in the order the version of its type it conforms to declares."""
    return settled.order(artifact, composition.declared(composition.conformed(artifact, store)["schema"], store))


def _out_of_step(store: Port, each: Offered) -> bool:
    """Whether a type's version the store does not keep is one the store could not gain: what it holds at the IRI is
    no type, or its type stands at a higher version, or at a revision the file's is not above."""
    standing = store.artifact(each.id)
    if not settled.typed(standing):
        return True
    return each.number < standing["version"] or each.artifact["revision"] <= standing["revision"]
