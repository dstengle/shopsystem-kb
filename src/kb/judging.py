"""The links of the files an import's check checked against their types, judged last, a file with an error's too,
as the landing judges them: against the store with only the files that would land, never against the check's draft,
which holds the files that would not, so a link to a file that does not land is a link to an IRI not held. One that
waits is no error; one under no type is its file's error, beside any other the file has; one to an IRI not held
whose nearest type, of those the directory brings, is one no version of which lands leads its file, when it has no
error, to be skipped for that type's version files, whatever type above would let the link wait
(decision/an-iri-belongs-to-its-nearest-type). It writes nothing."""
from kb import composition, links, refusals, settled, skipping, validation, values
from kb.draft import Draft
from kb.offers import Offered
from kb.port import Port
from kb.values import ArtifactId, Refused


def unlanded(store: Port, offered: list[Offered], by_name: dict, read: list[tuple[Offered, dict]]) -> dict:
    """The links of each file checked against its type (`read`, each with its artifact as it would land, in the order
    files are read in) judged as the landing judges them, against the store with only the files that would land, so
    a link to a file that does not land is a link to an IRI not held: it waits under a type the store holds or of
    which a version lands; under a type no version of which lands, whether or not a type above would let it wait
    (`_lost`), it leads its file, when it has no error, to that type's version files, which are given here for the
    file, by its name; under no type at all it is the file's error, beside any other the file has."""
    landing = Draft(store)
    for each, artifact in read:
        if not each.errors:
            landing.put(each.id, artifact)
    lost, waiting = skipping.lost(store, offered, by_name), {}
    for each, artifact in read:
        led = [(link, _under(link.target, lost, landing)) for link in _links(each, artifact, landing)]
        if not each.errors:
            under = [under for _, under in led if under is not None] + _lost(artifact, lost, landing)
            waiting[each.file] = [file for type_id in dict.fromkeys(under) for file in lost[type_id]]
        each.errors += [refusals.unlanded(each.file, link.place, link.target) for link, under in led if under is None]
    return waiting


def _lost(artifact: dict, lost: dict, landing: Draft) -> list[ArtifactId]:
    """The types no version of which lands that a file with no error links under, at an IRI what would land does not
    hold, in the order of its links: the nearest type the directory brings there decides
    (decision/an-iri-belongs-to-its-nearest-type), so such a link never waits under a type above that one."""
    carried = links.carried(settled.checked(artifact), composition.conformed(artifact, landing)["schema"], landing)
    found = [_under(link.target, lost, landing) for link in carried if not _held(link.target, landing)]
    return [under for under in found if under is not None]


def _held(target, landing: Draft) -> bool:
    """Whether a link's value names an artifact that what would land holds; one that names nothing is held nowhere."""
    try:
        return landing.holds(values.target(target).id)
    except values.Refused:
        return False


def _links(each: Offered, artifact: dict, landing: Draft) -> list:
    """The links of a checked file that neither land nor wait in what would land, those JSON Schema's errors leave
    unread passed over; none for a file the version of whose type is not held or whose content cannot be read."""
    try:
        schema, content = composition.conformed(artifact, landing)["schema"], settled.checked(artifact)
        errors = validation.misshapen(content, schema, landing) if each.errors else ()
    except Refused:
        return []
    return validation.unlanded(content, schema, landing, imported=True, errors=errors)


def _under(target: str, lost: dict, landing):
    """The type a link leads its file to, as `skipping.under` gives it; None for a value that names nothing."""
    try:
        return skipping.under(values.target(target).id, lost, landing)
    except values.Refused:
        return None
