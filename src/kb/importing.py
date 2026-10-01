"""A directory read as a set for import into a store: each file's errors, and the files that would be skipped because
they lead to one, each with the chain of files that leads there. An old store's history and marker at the directory's
top are passed over, unread; every other file is read. Each file that reads as an artifact at its place in the export
layout is put in one draft over the store, so files are checked against the types the directory brings and the
store's together, as a set is. The type that describes types is the store's own: a copy of it is compared, never
drafted. Nothing is written."""
from collections import deque
from dataclasses import dataclass, field

from kb import canonical, composition, definitions, links, names, refusals, rules, settled, validation, values
from kb.draft import Draft
from kb.port import Port
from kb.values import TYPE_KIND, ArtifactId, Directory, Refused

HISTORY = (".git", "journal")
MARKER = ("store.yaml",)
METASCHEMA_ID = values.type_of(TYPE_KIND)


@dataclass(frozen=True)
class Skipped:
    """A file that would be skipped, and the files from it to the broken one it leads to, itself first."""
    file: str
    chain: tuple[str, ...]


@dataclass(frozen=True)
class Checked:
    """What the check answers: the faults that refused it; or every file's errors, each naming the file, and the files
    that would be skipped."""
    faults: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    skipped: list = field(default_factory=list)


@dataclass
class Offered:
    """One file as read: its place, the name the layout gives it (None where the layout puts no artifact), its text
    and, when it reads as an artifact at its place, that artifact; and its errors."""
    file: str
    name: ArtifactId | None
    text: str = ""
    artifact: dict | None = None
    errors: list = field(default_factory=list)


def checked(store: Port, directory: Directory) -> Checked:
    """Every file read, the artifacts among them drafted as one set, each checked; types first, so an artifact of a
    kind whose type file is broken is left to be skipped rather than checked."""
    offered = [_offered(directory, steps) for steps in _files(directory)]
    draft = Draft(store)
    for each in offered:
        if each.artifact is not None and each.name != METASCHEMA_ID:
            draft.put(each.name, each.artifact)
    by_name = {each.name: each for each in offered if each.name is not None}
    unread = {name for name, each in by_name.items() if each.artifact is None}
    for each in sorted(offered, key=lambda each: each.name is None or each.name.kind != TYPE_KIND):
        each.errors += [_of(each.file, fault) for fault in _faults(store, draft, each, by_name, unread)]
    return Checked(
        errors=[fault for each in offered for fault in each.errors], skipped=_skipped(draft, offered, by_name),
    )


def _files(directory: Directory) -> list[tuple[str, ...]]:
    """The place of every file below the directory, as steps, in the order of the names the layout gives them; an old
    store's history and marker at its top passed over."""
    found = [path.relative_to(directory.path).parts for path in directory.path.rglob("*") if path.is_file()]
    return sorted(steps for steps in found if steps != MARKER and not (len(steps) > 1 and steps[0] in HISTORY))


def _offered(directory: Directory, steps: tuple[str, ...]) -> Offered:
    """A file read as YAML 1.2, and as an artifact at the place the layout gives its name and kind."""
    file, written = "/".join(steps), names.filed(steps)
    offered = Offered(file, values.artifact_id(written) if written is not None else None)
    try:
        offered.text = directory.path.joinpath(*steps).read_bytes().decode("utf-8")
        loaded = canonical.load(offered.text)
    except UnicodeDecodeError:
        offered.errors.append(refusals.unreadable_file(file, "it is not text in UTF-8"))
        return offered
    except canonical.NotCanonical as fault:
        offered.errors.append(refusals.unreadable_file(file, str(fault)))
        return offered
    problem = _misplaced(written, loaded)
    if problem is not None:
        offered.errors.append(refusals.not_canonical(file, problem))
    else:
        offered.artifact = loaded
    return offered


def _misplaced(written: str | None, loaded) -> str | None:
    """Why what a file holds is not an artifact at its place, or None when it is."""
    if written is None:
        return "an artifact is filed as <kind>/<slug>.yaml, and nothing else is offered for import"
    if not isinstance(loaded, dict) or not settled.identified(loaded):
        return f"an artifact opens with {', '.join(settled.IDENTITY)}, in that order, and this file does not"
    kind = names.parted(written)[0]
    if (loaded["id"], loaded["type"]) != (written, kind):
        return (f"its place names {written!r}, of kind {kind!r}, and it holds {loaded['id']!r}, "
                f"of kind {loaded['type']!r}")
    return None


def _faults(store: Port, draft: Draft, each: Offered, by_name: dict, unread: set) -> list:
    """What is wrong with a file that reads as an artifact: a copy of the type that describes types that differs from
    the store's; or, of a kind whose type file is not broken, its kind, its form, its content and its links against
    its type, and for a type, the type as a type. A link to a file that could not be read is left to the skipping."""
    if each.artifact is None:
        return []
    if each.name == METASCHEMA_ID:
        return [] if each.text == canonical.dump(store.artifact(METASCHEMA_ID)) else [refusals.not_canonical(
            each.file, "the type that describes types is the store's own, and this copy differs from it",
        )]
    type_id = values.type_of(each.name.kind)
    if _type_broken(each, by_name):
        return []
    if not draft.holds(type_id):
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
    """Each file without an error that leads to a broken one by its links or its implicit link to its type file, with
    the shortest chain of files that leads there. The type that describes types is the store's own, led to by none."""
    files = {name: each.file for name, each in by_name.items() if name != METASCHEMA_ID}
    broken = {each.file for each in offered if each.errors}
    leads = {
        each.file: [files[target] for target in _leads_to(draft, each, by_name) if target in files]
        for each in offered if each.name in files and each.file not in broken
    }
    chains = [(file, _chain(file, leads, broken)) for file in leads]
    return [Skipped(file, chain) for file, chain in chains if chain is not None]


def _leads_to(draft: Draft, each: Offered, by_name: dict) -> list[ArtifactId]:
    """Where an artifact's links lead: its type, then every link, read through its type unless that type's file is
    broken."""
    if _type_broken(each, by_name):
        return [values.type_of(each.name.kind)]
    return [link.target for link in links.handed(each.name, each.artifact, draft)]


def _type_broken(each: Offered, by_name: dict) -> bool:
    """Whether the directory brings the file of an artifact's type, other than the store's own type of types, and
    that file has an error."""
    type_id = values.type_of(each.name.kind)
    return type_id != METASCHEMA_ID and type_id in by_name and bool(by_name[type_id].errors)


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
