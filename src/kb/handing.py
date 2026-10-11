"""Each change of a drafted set as the port takes it: the type it is checked against (`typed`), its entries in the
order that type declares and the version it records (`versioned`), its canonical text (`serialised`), and the change
handed over (`handed`), read at the revision given, with the rows it is found by, its links and the places of its parts
for the last change the set makes to an artifact, each link an import brings carrying the import's mark and no other
change's any, and the revisions of the types it was read through."""
import dataclasses

from kb import canonical, composition, links, names, places, port_values, refusals, search, settled, values
from kb.draft import Draft
from kb.edits import Change
from kb.values import Refused


def typed(draft: Draft, change: Change) -> dict:
    """The type a change is checked against: the version of its type its artifact conforms to as the change left it
    (the one a create or a replacement names, the one an import's file names, else the one it conformed to), whatever
    its type stands at; or, for an artifact the set later removes when it leaves no such type, as the change acted on
    it. Raises Refused when an artifact the set leaves has no type."""
    kind = composition.artifact_kind(change.left)
    if not draft.holds(change.artifact_id) and not draft.holds(values.type_of(kind)):
        return change.acted
    return composition.conformed(change.left, draft)


def versioned(draft: Draft, change: Change, last: bool) -> Change:
    """A change recording the version of the type it was checked against, its entries in the order that type
    declares; the last the set makes to an artifact put in the draft so. An import keeps the version it was written
    against."""
    if change.left is None or change.op == "import":
        return change
    schema = typed(draft, change)
    version = names.versioned(settled.kind(change.left), schema["version"])
    left = settled.order({**change.left, "type": version}, composition.declared(schema["schema"], draft))
    if last:
        draft.put(change.artifact_id, left)
    return change._replace(type=version, left=left)


def serialised(changes: list[Change]) -> list[str | None]:
    """Each change's canonical text as the change left its artifact, None for a removal; refused if any cannot be
    written."""
    texts, found = [], []
    for change in changes:
        try:
            texts.append(None if change.left is None else canonical.dump(change.left))
        except canonical.NotCanonical as fault:
            found.append(refusals.unwritable(change.artifact_id, str(fault), fault.path))
    if found:
        raise Refused(found)
    return texts


def handed(draft: Draft, change: Change, read: int, last: bool) -> port_values.Change:
    """A change as the port takes it, read at the revision given:
    its content as it left the artifact with the rows it is found by, and, for the last change the set makes to that
    artifact, its links and the places of its parts as the set leaves them, read through the type it was checked
    against, each marked as an import's when the change is one (`port_values.Link.imported`), with the revisions of
    the types that version is read through, each kb: reference followed at the version it names, that the set leaves
    as they are; every change that leaves a type with those of the types the version it makes reads."""
    if change.left is None:
        return port_values.Change(change.artifact_id, None, read=read, revision=change.revision)
    searched, kind = tuple(search.searchable(change.left)), composition.artifact_kind(change.left)
    version = _stands_at(change.left) if kind == values.TYPE_KIND else None
    made = _read_by_the_version_made(draft, change)
    if not last:
        return port_values.Change(
            change.artifact_id, change.left, read=read, revision=change.revision, through=draft.as_read(made),
            searched=searched, kind=kind, version=version,
        )
    schema, waited = typed(draft, change), draft.waited(change.artifact_id)
    carried = links.handed(change.artifact_id, change.left, draft, schema, waited)
    return port_values.Change(
        change.artifact_id, change.left, tuple(_marked(carried) if change.op == "import" else carried),
        tuple(places.parts(change.left)), read, change.revision,
        draft.as_read([*composition.read_through(kind, schema["schema"], draft), *made]), searched, kind, version,
    )


def _marked(carried: list[port_values.Link]) -> list[port_values.Link]:
    """The links an import brings, each but kb's own implicit one carrying the import's mark, which lets one into a
    part its held target lacks land and wait (decision/a-link-that-waits-keeps-waiting)."""
    return [link if link.implicit else dataclasses.replace(link, imported=True) for link in carried]


def _read_by_the_version_made(draft: Draft, change: Change) -> list:
    """The other types the version of a type a change makes refers to a shape of or is built on, each kb: reference
    followed at the version it names: were one removed before the set lands, that version would read a version no
    longer held. None for a change that leaves no type."""
    if composition.artifact_kind(change.left) != values.TYPE_KIND:
        return []
    return composition.read_through(values.TYPE_KIND, change.left.get("schema"), draft)[1:]


def _stands_at(held: dict) -> port_values.Versioned:
    """The version a type's change makes as the port takes it: of the kind its IRI names, the number and the title
    it holds."""
    return port_values.Versioned(values.Version(values.Kind(held["id"]), held["version"]), held["title"])
