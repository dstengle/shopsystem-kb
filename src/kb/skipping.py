"""The files an import would skip: those that lead to a file with an error, each with the shortest chain of files that
leads there, and the relation they are led by: the type version files a file is read through (`beneath`), and whether
one of those has an error or is itself read through one that leads to one (`held_back`). Worked out from the files
offered, their errors and the store; it writes nothing."""
from collections import deque
from dataclasses import dataclass

from kb import composition, links, names, values
from kb.draft import Draft
from kb.offers import Offered
from kb.port import Port
from kb.values import TYPE_KIND, ArtifactId

METASCHEMA_ID = values.type_of(TYPE_KIND)


@dataclass(frozen=True)
class Skipped:
    """A file that would be skipped, and the files from it to the broken one it leads to, itself first."""
    file: str
    chain: tuple[str, ...]



def skipped(store: Port, draft: Draft, offered: list[Offered], by_name: dict) -> list[Skipped]:
    """Each file without an error that leads to a broken one, with the shortest chain of files that leads there: by
    its implicit link to its type version's file, for a type by a version it is built on or refers to, or by a link to
    an IRI under a type no version of which would land. A link to an artifact's file is not followed: a file that
    does not land leaves its IRI a placeholder. The type that describes types is the store's own, led to by none."""
    files = {name: each.file for name, each in by_name.items() if each.id != METASCHEMA_ID}
    broken = {each.file for each in offered if each.errors}
    sound = [each for each in offered if each.name in files and each.file not in broken]
    through = {each.file: [files[name] for name in beneath(each, by_name)] for each in sound}
    lost = _lost(store, files, by_name, broken | {file for file in through if _chain(file, through, broken)})
    leads = {each.file: through[each.file] + _waiting_under(draft, each, by_name, lost) for each in sound}
    chains = [(file, _chain(file, leads, broken)) for file in leads]
    return [Skipped(file, chain) for file, chain in chains if chain is not None]
def _lost(store: Port, files: dict, by_name: dict, left_out: set) -> dict[ArtifactId, list[str]]:
    """The types no version of which would land, each with its versions' files in the order of their numbers: those
    the store does not hold whose every version file is broken or leads to a broken one. Worked out from the files
    that would land and the store, never from the check's draft, which holds the broken versions too."""
    versions: dict[ArtifactId, list[str]] = {}
    for name in sorted((name for name in files if by_name[name].typed), key=lambda name: by_name[name].number or 0):
        versions.setdefault(by_name[name].id, []).append(files[name])
    return {
        type_id: held for type_id, held in versions.items()
        if not store.holds(type_id) and all(file in left_out for file in held)
    }
def _waiting_under(draft: Draft, each: Offered, by_name: dict, lost: dict) -> list[str]:
    """The files a file leads to by its links: for each link to an IRI under a type no version of which would land,
    where no placeholder can wait, that type's version files. The links are read through the version of its type the
    file names, so not at all when that version's file is broken or leads to a broken one."""
    if held_back(each, by_name):
        return []
    handed = links.handed(each.id, each.artifact, draft, composition.conformed(each.artifact, draft))
    return [file for link in handed if not link.implicit for file in lost.get(link.under, [])]
def _chain(start: str, leads: dict, broken: set) -> tuple[str, ...] | None:
    """The shortest chain of files from one to a broken file, or None when it leads to none."""
    chains, waiting = {start: (start,)}, deque([start])
    while waiting:
        at = waiting.popleft()
        for to in leads.get(at, []):
            if to in chains:
                continue
            chains[to] = (*chains[at], to)
            if to in broken:
                return chains[to]
            waiting.append(to)
    return None
def beneath(each: Offered, by_name: dict) -> list[ArtifactId]:
    """The names of the type version files the directory brings that a file is read through: that of the version of
    its type it conforms to, other than the store's own type of types, and, for a type, of each version its schema is
    built on or refers to by a kb: reference, at the number the reference names. No other version of those types."""
    if each.artifact is None:
        return []
    found = [str(composition.conforming(each.artifact))]
    if each.typed:
        referred = composition.references(each.artifact.get("schema"))
        found += [names.versioned(str(to.type_id), to.number) for to in referred]
    read_through = dict.fromkeys(ArtifactId(name) for name in found)
    return [name for name in read_through if name in by_name and by_name[name].id != METASCHEMA_ID]


def held_back(each: Offered, by_name: dict, seen: frozenset = frozenset()) -> bool:
    """Whether a type file a file is read through has an error, or is itself read through one that leads to one."""
    seen = seen | {each.name}
    return any(
        by_name[under].errors or held_back(by_name[under], by_name, seen)
        for under in beneath(each, by_name) if under not in seen
    )
