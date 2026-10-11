"""The files an import would skip: those that lead to a file with an error, each with the shortest chain of files that
leads there, and the relations they are led by: the type version files a file is read through (`beneath`), whether
one of those has an error or is itself read through one that leads to one (`held_back`), and the types no version of
which would land (`lost`), with the one of them a link's target sits under (`under`). Worked out from the files
offered, their errors and the store; it writes nothing."""
from collections import deque
from dataclasses import dataclass

from kb import composition, names, values
from kb.offers import Offered
from kb.port import Port
from kb.values import TYPE_KIND, ArtifactId

METASCHEMA_ID = values.type_of(TYPE_KIND)


@dataclass(frozen=True)
class Skipped:
    """A file that would be skipped, and the files from it to the broken one it leads to, itself first."""
    file: str
    chain: tuple[str, ...]


def skipped(offered: list[Offered], by_name: dict, waiting: dict[str, list[str]]) -> list[Skipped]:
    """Each file without an error that leads to a broken one, with the shortest chain of files that leads there: by
    its implicit link to its type version's file, for a type by a version it is built on or refers to, or by a link to
    an IRI under a type no version of which would land, whose version files `waiting` gives for the file. A link to
    an artifact's file is not followed: a file that does not land leaves its IRI a placeholder. The type that
    describes types is the store's own, led to by none."""
    broken, through = _read_through(offered, by_name)
    leads = {file: through[file] + waiting.get(file, []) for file in through}
    chains = [(file, _chain(file, leads, broken)) for file in leads]
    return [Skipped(file, chain) for file, chain in chains if chain is not None]


def lost(store: Port, offered: list[Offered], by_name: dict) -> dict[ArtifactId, list[str]]:
    """The types no version of which would land, each with its versions' files in the order of their numbers: those
    the store does not hold whose every version file, one that cannot be read among them, is broken or leads to a
    broken one. Worked out from the files that would land and the store, never from the check's draft, which holds
    the broken versions too."""
    broken, through = _read_through(offered, by_name)
    left_out = broken | {file for file in through if _chain(file, through, broken)}
    versions: dict[ArtifactId, list[str]] = {}
    typed = [each for each in by_name.values() if each.typed and each.id != METASCHEMA_ID]
    for each in sorted(typed, key=lambda each: each.number):
        versions.setdefault(each.id, []).append(each.file)
    return {
        type_id: held for type_id, held in versions.items()
        if not store.holds(type_id) and all(file in left_out for file in held)
    }


def under(target: ArtifactId, lost: dict, landing) -> ArtifactId | None:
    """The type no version of which would land that a link's target sits under, where no placeholder can wait; None
    when a type that lands, or that the store holds, is nearer, or when it sits under no such type."""
    nearest = composition.nearest_type(target, landing)
    for above in map(ArtifactId, names.above(target)):
        if above == nearest:
            return None
        if above in lost:
            return above
    return None


def _read_through(offered: list[Offered], by_name: dict) -> tuple[set[str], dict[str, list[str]]]:
    """The files with an error, and each file without one with the type version files it is read through."""
    files = {name: each.file for name, each in by_name.items() if each.id != METASCHEMA_ID}
    broken = {each.file for each in offered if each.errors}
    sound = [each for each in offered if each.name in files and each.file not in broken]
    return broken, {each.file: [files[name] for name in beneath(each, by_name)] for each in sound}


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
