"""A directory's files as they are offered for import: which files are read, and each read as YAML 1.2 and as an
artifact at its place in the export layout. A store's history and the files that mark and keep it, at the directory's
top, are passed over, unread: an old store's `.git/`, `journal/` and marker, and a current store's marker and
database. A name that names no directory is refused. Nothing here checks an artifact against a type."""
from dataclasses import dataclass, field

from kb import canonical, names, refusals, settled, store, values
from kb.values import ArtifactId, Directory, Refused

HISTORY = (".git", "journal")
KEPT = (store.MARKER.name, store.DATABASE.name, *(f"{store.DATABASE.name}-{side}" for side in ("wal", "shm")))


@dataclass
class Offered:
    """One file as read: its place, the name the layout gives it (None where the layout puts no artifact), its text
    and, when it reads as an artifact at its place, that artifact; and its errors."""
    file: str
    name: ArtifactId | None
    text: str = ""
    artifact: dict | None = None
    errors: list = field(default_factory=list)


def offered(directory: Directory) -> list[Offered]:
    """Every file below the directory, read, in the order of the places the layout gives them. Raises Refused when
    the name names no directory."""
    if not directory.path.is_dir():
        raise Refused([refusals.not_an_import_directory(directory.named)])
    return [_offered(directory, steps) for steps in _files(directory)]


def _files(directory: Directory) -> list[tuple[str, ...]]:
    """The place of every file below the directory, as steps, sorted; a store's history and the files that mark and
    keep it, at its top, passed over."""
    found = [path.relative_to(directory.path).parts for path in directory.path.rglob("*") if path.is_file()]
    return sorted(
        steps for steps in found
        if not (len(steps) == 1 and steps[0] in KEPT) and not (len(steps) > 1 and steps[0] in HISTORY)
    )


def _offered(directory: Directory, steps: tuple[str, ...]) -> Offered:
    """A file read as YAML 1.2, and as an artifact at the place the layout gives its name and kind."""
    file, written = "/".join(steps), names.filed(steps)
    offered = Offered(file, values.artifact_id(written) if written is not None else None)
    try:
        offered.text = directory.path.joinpath(*steps).read_bytes().decode("utf-8")
        loaded = canonical.load(offered.text)
    except OSError as error:
        offered.errors.append(refusals.unreadable_file(file, f"it cannot be opened: {error.strerror or error}"))
        return offered
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
