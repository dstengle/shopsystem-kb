"""A directory read as a set for import into a store: each file's errors, and the files that would be skipped because
they lead to one, each with the chain of files that leads there. Each file that reads as an artifact at its place in
the export layout (kb.offers) is put in one draft over the store, so files are checked against the types the
directory brings and the store's together, as a set is. A file read through a type file that has an error, or that
leads to one, is not checked but left to be skipped. The type that describes types is the store's own: a copy of it is
compared, never drafted. The examination writes nothing."""
from dataclasses import dataclass, field

from kb import (
    canonical, comparing, composition, definitions, file_refusals, links, naming, names, offers, rules, settled, skipping,
    validation, values,
)
from kb.draft import Draft
from kb.offers import Offered
from kb.port import Port
from kb.roots import Named
from kb.values import ArtifactId, Refused

METASCHEMA_ID = skipping.METASCHEMA_ID


@dataclass(frozen=True)
class Checked:
    """What the check, or an import, answers: the faults that refused it, and every file's errors, each naming the
    file, and the files that would be skipped."""
    faults: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    skipped: list = field(default_factory=list)


def checked(store: Port, directory: Named) -> Checked:
    """Every file read, the artifacts among them drafted as one set, each checked."""
    return examined(store, offers.offered(directory))


def examined(store: Port, offered: list[Offered]) -> Checked:
    """The files offered, the artifacts among them drafted as one set, then each checked: the types first, each after
    the types it is read through, so a file read through a broken type file is left to be skipped rather than
    checked. The versions of one type are drafted in the order of their numbers, so the draft leaves the type standing
    at the highest. Each file's errors are kept on it."""
    draft = Draft(store)
    for each in sorted(offered, key=lambda each: each.number or 0):
        if each.artifact is not None and each.id != METASCHEMA_ID:
            draft.put(each.id, each.artifact)
    by_name = {each.name: each for each in offered if each.name is not None}
    unread = {each.id for each in by_name.values() if each.artifact is None}
    drafted = _drafted(draft, by_name)
    for name in in_order(by_name):
        each = by_name[name]
        each.errors += [_of(each.file, fault) for fault in _faults(store, draft, each, by_name, unread, drafted)]
    for each in comparing.compared(store, [each for each in offered if each.id != METASCHEMA_ID]).differing:
        each.errors.append(file_refusals.differs(each.file, str(each.id)))
    return Checked(
        errors=[fault for each in offered for fault in each.errors], skipped=skipping.skipped(store, draft, offered, by_name),
    )


def in_order(by_name: dict[ArtifactId, Offered]) -> list[ArtifactId]:
    """The names of the files offered, the types first, each after the types it is read through, then the rest, each
    in the order of names, the versions of one type by their numbers."""
    def key(name: ArtifactId) -> tuple:
        return names.order(by_name[name].id), by_name[name].number or 0

    ordered: list[ArtifactId] = []

    def visit(name: ArtifactId, seen: frozenset) -> None:
        if name in ordered or name in seen:
            return
        for under in sorted(skipping.beneath(by_name[name], by_name), key=key):
            visit(under, seen | {name})
        ordered.append(name)
    for name in sorted((name for name in by_name if by_name[name].typed), key=key):
        visit(name, frozenset())
    return ordered + sorted((name for name in by_name if not by_name[name].typed), key=key)


def _drafted(draft: Draft, by_name: dict) -> dict[ArtifactId, tuple]:
    """Each file's artifact as it would land, its items named and its entries ordered (kb.naming), put in the draft in
    its place, each file after the types it is read through, with the faults of the names it gives. A file whose type
    version is not held is left as it is."""
    drafted = {}
    for name in in_order(by_name):
        each = by_name[name]
        if each.artifact is None or each.id == METASCHEMA_ID or skipping.held_back(each, by_name):
            continue
        try:
            drafted[name] = naming.imported(draft, each.id, each.artifact)
        except Refused:
            continue
        draft.put(each.id, drafted[name][0])
    return drafted


def _faults(store: Port, draft: Draft, each: Offered, by_name: dict, unread: set, drafted: dict) -> list:
    """What is wrong with a file that reads as an artifact: a copy of the type that describes types that differs from
    the store's; or, unless it is read through a type file that is broken or leads to one, its kind, the version of
    its type it names, which the directory or the store must hold, its form, its content and its links against that
    version, whatever its type stands at, and for a type, the type as a type. A link to a file that could not be read
    is no error: that file does not land, and its IRI is left a placeholder."""
    if each.artifact is None:
        return []
    if each.id == METASCHEMA_ID:
        return [] if each.text == canonical.dump(store.artifact(METASCHEMA_ID)) else [file_refusals.not_canonical(
            each.file, "the type that describes types is the store's own, and this copy differs from it",
        )]
    if skipping.held_back(each, by_name):
        return []
    kind = composition.artifact_kind(each.artifact)
    if not draft.holds(values.type_of(kind)):
        return [file_refusals.no_type_offered(each.file, kind.name)]
    named = composition.conforming(each.artifact)
    version = composition.kept(values.type_of(kind), named.number, draft)
    if version is None:
        return [file_refusals.no_version_offered(each.file, str(named))]
    landing, misnamed = drafted.get(each.name, (each.artifact, ()))
    schema, content = version.content["schema"], settled.checked(landing)
    found = [
        *_form(draft, each, schema), *misnamed, *naming.placed(draft, each.id, values.type_of(kind)),
        *_fit(draft, each, content, schema, unread),
    ]
    if not found and each.typed:
        found = definitions.faults(each.id, content, draft)
    return found


def _form(draft: Draft, each: Offered, schema: dict) -> list:
    """Whether the file's text is the text kb writes for its artifact, its entries in the order its type declares."""
    try:
        written = canonical.dump(settled.order(each.artifact, composition.declared(schema, draft)))
    except canonical.NotCanonical as fault:
        return [file_refusals.not_canonical(each.file, str(fault))]
    return [] if written == each.text else [file_refusals.not_canonical(each.file, "its text is not the text kb writes")]


def _fit(draft: Draft, each: Offered, content: dict, schema: dict, unread: set) -> list:
    """Every fault of the content against its type, as an import's set is checked, a link into a part its held target
    lacks waiting, but for a link to a file that could not be read."""
    try:
        found = validation.validate(each.file, content, schema, draft, imported=True)
    except Refused as refused:
        return list(refused.faults)
    leading = {link.place for link in links.carried(content, schema, draft) if _named(link.target) in unread}
    return [fault for fault in found if not (fault.rule == rules.REF and fault.place in leading)]


def _named(target) -> ArtifactId | None:
    """The artifact a link's value names, or None where it names none."""
    try:
        return values.target(target).id if isinstance(target, str) else None
    except Refused:
        return None


def _of(file: str, fault):
    """A fault said of the file it was found in."""
    fault.artifact = file
    return fault
