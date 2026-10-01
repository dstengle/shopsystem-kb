"""A directory read as a set for import into a store: each file's errors, and the files that would be skipped because
they lead to one, each with the chain of files that leads there. Each file that reads as an artifact at its place in
the export layout (kb.offers) is put in one draft over the store, so files are checked against the types the
directory brings and the store's together, as a set is. A file read through a type file that has an error, or that
leads to one, is not checked but left to be skipped. The type that describes types is the store's own: a copy of it is
compared, never drafted. The check writes nothing; the import lands what checks clean, or with errors skipped
everything that leads to none, into a freshly started store as one set, through the write pipeline (kb.write)."""
from collections import deque
from dataclasses import dataclass, field

from kb import (
    canonical, composition, definitions, links, names, offers, refusals, rules, settled, validation, values, write,
)
from kb.draft import Draft
from kb.edits import Import
from kb.offers import Offered
from kb.port import Port
from kb.signatures import Signed
from kb.values import TYPE_KIND, ArtifactId, Directory, Refused

METASCHEMA_ID = values.type_of(TYPE_KIND)


@dataclass(frozen=True)
class Skipped:
    """A file that would be skipped, and the files from it to the broken one it leads to, itself first."""
    file: str
    chain: tuple[str, ...]


@dataclass(frozen=True)
class Checked:
    """What the check, or an import, answers: the faults that refused it, and every file's errors, each naming the
    file, and the files that would be skipped."""
    faults: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    skipped: list = field(default_factory=list)


def checked(store: Port, directory: Directory) -> Checked:
    """Every file read, the artifacts among them drafted as one set, each checked."""
    return _examined(store, offers.offered(directory))


def _examined(store: Port, offered: list[Offered]) -> Checked:
    """The files offered, the artifacts among them drafted as one set, then each checked: the types first, each after
    the types it is read through, so a file read through a broken type file is left to be skipped rather than
    checked. Each file's errors are kept on it."""
    draft = Draft(store)
    for each in offered:
        if each.artifact is not None and each.name != METASCHEMA_ID:
            draft.put(each.name, each.artifact)
    by_name = {each.name: each for each in offered if each.name is not None}
    unread = {name for name, each in by_name.items() if each.artifact is None}
    for name in in_order(by_name):
        each = by_name[name]
        each.errors += [_of(each.file, fault) for fault in _faults(store, draft, each, by_name, unread)]
    return Checked(
        errors=[fault for each in offered for fault in each.errors], skipped=_skipped(draft, offered, by_name),
    )


def imported(store: Port, directory: Directory, signed: Signed, skip_errors: bool) -> Checked:
    """The directory checked, then every artifact in it landed as one set under the signature, each type ahead of the
    artifacts of its kind; the store's own type that describes types is kept. A directory with errors is refused with
    the check's report, and nothing is written; or, with errors skipped, every artifact lands but the broken files
    and the files that would be skipped, and the report says which they are and why."""
    _fresh(store)
    offered = offers.offered(directory)
    report = _examined(store, offered)
    if report.errors and not skip_errors:
        return Checked([refusals.check_failed(len(report.errors))], report.errors, report.skipped)
    landing = _landing(offered, report)
    if not landing:
        return Checked([refusals.nothing_lands()], report.errors, report.skipped)
    write.land(store, [Import(name, landing[name].artifact) for name in in_order(landing)], signed)
    return report


def _fresh(store: Port) -> None:
    """Refuse a store that holds any artifact besides the type that describes types: import never merges."""
    held = [name for name in store.ids() if name != METASCHEMA_ID]
    if held:
        raise Refused([refusals.not_fresh(len(held))])


def _landing(offered: list[Offered], report: Checked) -> dict[ArtifactId, Offered]:
    """The files that land, by name: every artifact but the type that describes types, a file with an error and a
    file that would be skipped."""
    left_out = {skipped.file for skipped in report.skipped}
    return {
        each.name: each for each in offered
        if each.name not in (None, METASCHEMA_ID) and not each.errors and each.file not in left_out
    }


def in_order(by_name: dict[ArtifactId, Offered]) -> list[ArtifactId]:
    """The names of the files offered, the types first, each after the types it is read through, then the rest, each
    in the order of names."""
    ordered: list[ArtifactId] = []

    def visit(name: ArtifactId, seen: frozenset) -> None:
        if name in ordered or name in seen:
            return
        for under in sorted(_beneath(by_name[name], by_name), key=names.order):
            visit(under, seen | {name})
        ordered.append(name)
    for name in sorted((name for name in by_name if name.kind == TYPE_KIND), key=names.order):
        visit(name, frozenset())
    return ordered + sorted((name for name in by_name if name.kind != TYPE_KIND), key=names.order)


def _faults(store: Port, draft: Draft, each: Offered, by_name: dict, unread: set) -> list:
    """What is wrong with a file that reads as an artifact: a copy of the type that describes types that differs from
    the store's; or, unless it is read through a type file that is broken or leads to one, its kind, its form, its
    content and its links against its type, and for a type, the type as a type. A link to a file that could not be
    read is left to the skipping."""
    if each.artifact is None:
        return []
    if each.name == METASCHEMA_ID:
        return [] if each.text == canonical.dump(store.artifact(METASCHEMA_ID)) else [refusals.not_canonical(
            each.file, "the type that describes types is the store's own, and this copy differs from it",
        )]
    if _held_back(each, by_name):
        return []
    if not draft.holds(values.type_of(each.name.kind)):
        return [refusals.no_type_offered(each.file, each.name.kind.name)]
    schema = composition.kind_schema(each.name.kind, draft)["schema"]
    content = settled.checked(each.artifact)
    found = [*_form(draft, each, schema), *_fit(draft, each, content, schema, unread)]
    if not found and each.name.kind == TYPE_KIND:
        found = definitions.faults(each.name, content, draft)
    return found


def _form(draft: Draft, each: Offered, schema: dict) -> list:
    """Whether the file's text is the text kb writes for its artifact, its entries in the order its type declares."""
    try:
        written = canonical.dump(settled.order(each.artifact, composition.declared(schema, draft)))
    except canonical.NotCanonical as fault:
        return [refusals.not_canonical(each.file, str(fault))]
    return [] if written == each.text else [refusals.not_canonical(each.file, "its text is not the text kb writes")]


def _fit(draft: Draft, each: Offered, content: dict, schema: dict, unread: set) -> list:
    """Every fault of the content against its type, as a set is checked, but for a link to a file that could not be
    read."""
    try:
        found = validation.validate(each.file, content, schema, draft)
    except Refused as refused:
        return list(refused.faults)
    leading = {link.place for link in links.carried(content, schema, draft) if _named(link.target) in unread}
    return [fault for fault in found if not (fault.rule == rules.REF and fault.path in leading)]


def _named(target) -> ArtifactId | None:
    """The artifact a link's value names, or None where it names none."""
    try:
        return values.target(target).id if isinstance(target, str) else None
    except Refused:
        return None


def _skipped(draft: Draft, offered: list[Offered], by_name: dict) -> list[Skipped]:
    """Each file without an error that leads to a broken one by its links, its implicit link to its type file or, for a
    type, what it is built on or refers to, with the shortest chain of files that leads there. The type that describes
    types is the store's own, led to by none."""
    files = {name: each.file for name, each in by_name.items() if name != METASCHEMA_ID}
    broken = {each.file for each in offered if each.errors}
    leads = {
        each.file: [files[target] for target in _leads_to(draft, each, by_name) if target in files]
        for each in offered if each.name in files and each.file not in broken
    }
    chains = [(file, _chain(file, leads, broken)) for file in leads]
    return [Skipped(file, chain) for file, chain in chains if chain is not None]


def _leads_to(draft: Draft, each: Offered, by_name: dict) -> list[ArtifactId]:
    """Where an artifact leads: the type files it is read through, then, unless one of them is broken or leads to a
    broken one, every link it carries, read through its type."""
    beneath = _beneath(each, by_name)
    if _held_back(each, by_name):
        return beneath
    return [*beneath, *(link.target for link in links.handed(each.name, each.artifact, draft))]


def _beneath(each: Offered, by_name: dict) -> list[ArtifactId]:
    """The type files the directory brings that a file is read through: its type's, other than the store's own type
    of types, and, for a type, those its schema is built on or refers to by a kb: reference."""
    found = [values.type_of(each.name.kind)]
    if each.name.kind == TYPE_KIND and isinstance(each.artifact, dict):
        found += composition.referred(each.artifact.get("schema"))
    return [name for name in dict.fromkeys(found) if name != METASCHEMA_ID and name in by_name]


def _held_back(each: Offered, by_name: dict, seen: frozenset = frozenset()) -> bool:
    """Whether a type file a file is read through has an error, or is itself read through one that leads to one."""
    seen = seen | {each.name}
    return any(
        by_name[under].errors or _held_back(by_name[under], by_name, seen)
        for under in _beneath(each, by_name) if under not in seen
    )


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


def _of(file: str, fault):
    """A fault said of the file it was found in."""
    fault.artifact = file
    return fault
