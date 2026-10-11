"""A directory's files as they are offered for import: which files are read, and each read as YAML 1.2 and as an
artifact at its place in the export layout. A store's history and the files that mark and keep it, at the directory's
top, are passed over, unread: an old store's `.git/`, `journal/` and marker, a current store's marker, database
and the lock a server of it held, and the place kb starts a store in out of sight (`store.STAGING`); and, wherever it
lies below the directory, the one place a start was told it made, with everything under it. A name that names no
directory is refused. Nothing here checks an artifact against a type."""
from pathlib import Path
from dataclasses import dataclass, field

from kb import canonical, file_refusals, names, served, settled, store
from kb.roots import Named
from kb.values import ArtifactId, Refused

HISTORY = (".git", "journal", store.STAGING)
KEPT = (
    store.MARKER.name, store.DATABASE.name, *(f"{store.DATABASE.name}-{side}" for side in ("wal", "shm")),
    served.LOCK.name,
)


@dataclass
class Offered:
    """One file as read: its place, the name the layout gives it (None where the layout puts no artifact): the IRI
    of the artifact, or, for a type's version, of that version, so the versions of one type are told apart; the
    number of the version a type's place gives (None for any other artifact's), its text and, when it reads as an
    artifact at its place, that artifact; and its errors."""
    file: str
    name: ArtifactId | None
    number: int | None = None
    text: str = ""
    artifact: dict | None = None
    errors: list = field(default_factory=list)

    @property
    def id(self) -> ArtifactId | None:
        """The IRI of the artifact the file holds: the name, but for a type's version, the type's."""
        if self.name is None or self.number is None:
            return self.name
        return ArtifactId(names.version(str(self.name))[0])

    @property
    def typed(self) -> bool:
        """Whether the file's place is a type version's."""
        return self.number is not None


def offered(directory: Named, passed_over: Path | None = None) -> list[Offered]:
    """Every file below the directory, read, in the order of the places the layout gives them; those under the place
    passed over, if one is given, are not. Raises Refused when the name names no directory."""
    if not directory.path.is_dir():
        raise Refused([file_refusals.not_an_import_directory(directory.named)])
    return [_offered(directory, steps) for steps in _files(directory, passed_over)]


def _files(directory: Named, passed_over: Path | None) -> list[tuple[str, ...]]:
    """The place of every file below the directory, as steps, sorted; a store's history and the files that mark and
    keep it, at its top, and whatever lies under the place passed over, passed over."""
    found = [path.relative_to(directory.path).parts for path in directory.path.rglob("*") if path.is_file()]
    return sorted(
        steps for steps in found
        if not (len(steps) == 1 and steps[0] in KEPT) and not (len(steps) > 1 and steps[0] in HISTORY)
        and not _under(directory.path.joinpath(*steps), passed_over)
    )


def _under(file: Path, place: Path | None) -> bool:
    return place is not None and place.resolve() in file.resolve().parents


def _offered(directory: Named, steps: tuple[str, ...]) -> Offered:
    """A file read as YAML 1.2, and as an artifact at the place the layout gives its IRI, and a type's version."""
    file, written = "/".join(steps), names.filed(steps)
    offered = Offered(file, *((_named(*written), written[1]) if written is not None else (None, None)))
    try:
        offered.text = directory.path.joinpath(*steps).read_bytes().decode("utf-8")
        loaded = canonical.load(offered.text)
    except OSError as error:
        offered.errors.append(file_refusals.unreadable_file(file, f"it cannot be opened: {error.strerror or error}"))
        return offered
    except UnicodeDecodeError:
        offered.errors.append(file_refusals.unreadable_file(file, "it is not text in UTF-8"))
        return offered
    except canonical.NotCanonical as fault:
        offered.errors.append(file_refusals.unreadable_file(file, str(fault)))
        return offered
    problem = _misplaced(offered, loaded)
    if problem is not None:
        offered.errors.append(file_refusals.not_canonical(file, problem))
    else:
        offered.artifact = loaded
    return offered


def _named(iri: str, number: int | None) -> ArtifactId:
    """The name a file's IRI and version number give it: the IRI, or the version's."""
    return ArtifactId(iri if number is None else names.versioned(iri, number))


def _misplaced(offered: Offered, loaded) -> str | None:
    """Why what a file holds is not an artifact at its place, or None when it is: its IRI the one its place gives,
    and a type's version the one its place gives, at a type version's place, and no other artifact there."""
    if offered.name is None:
        return ("an artifact is filed as <host>/<segment>/.../<segment>.yaml, a type's version as "
                "<host>/.../<segment>@<n>.yaml, and nothing else is offered for import")
    if not isinstance(loaded, dict) or not settled.identified(loaded):
        return f"an artifact opens with {', '.join(settled.IDENTITY)}, in that order, and this file does not"
    if loaded["id"] != str(offered.id):
        return f"its place names {str(offered.id)!r}, and it holds {loaded['id']!r}"
    if settled.typed(loaded) != offered.typed or (offered.typed and loaded.get("version") != offered.number):
        return "a type is filed at its version's place, <segment>@<n>.yaml, and nothing else is"
    return None
