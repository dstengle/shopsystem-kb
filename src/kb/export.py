"""The store written out as canonical files at one moment, never over anything: each artifact at the place its IRI
gives, `<dir>/<host>/<segment>/.../<segment>.yaml`, and a type as its versions, every one the store holds and no
other, each at the type's place and its number, `<dir>/<host>/.../<segment>@<n>.yaml` (export-and-import-a-store).
Each artifact's entries are written in the order the version of its type it conforms to declares; its content,
revision and type version are written as the store holds them, a type's version with the content, the revision and
the title it was made with."""
from dataclasses import dataclass, field

from kb import canonical, composition, file_refusals, names, settled
from kb.port import Port
from kb.port_values import TypeVersion
from kb.roots import Named
from kb.values import Kind, Refused, Version


@dataclass(frozen=True)
class Exported:
    """What an export answers: the faults that refused it, none when it was written."""
    faults: list = field(default_factory=list)


def written(store: Port, into: Named) -> None:
    """Every artifact the store holds and every version it holds of every type, all read at one moment, then written
    as canonical text into the directory, which is made, with any directory above it, when it does not exist. Raises
    Refused, before the store is read and writing nothing, when it is not a directory or holds anything."""
    _empty(into)
    with store.at_one_moment():
        files = {place: _ordered(store, artifact) for place, artifact in _held(store)}
    into.path.mkdir(parents=True, exist_ok=True)
    for (*folders, filename), artifact in files.items():
        (into.path.joinpath(*folders)).mkdir(parents=True, exist_ok=True)
        with into.path.joinpath(*folders, filename).open("x", encoding="utf-8") as file:
            file.write(canonical.dump(artifact))


def _held(store: Port):
    """Each file's place with what it gives: every version held of a type at the type's place and the version's
    number, any other artifact at its own."""
    for name in store.ids():
        artifact = store.artifact(name)
        if settled.typed(artifact):
            yield from _versions(store, name)
        else:
            yield names.place(name), artifact


def _versions(store: Port, name):
    """The place of every version the store holds of a type, with the version as its file gives it."""
    for number in store.versions(name):
        yield names.place(name, number), _version(store.type_version(Version(Kind(str(name)), number)), name)


def _version(made: TypeVersion, name) -> dict:
    """A version of a type as its file gives it: what that version was made with, its content, its revision and its
    title, under the type's IRI."""
    return settled.given(made.content, str(name), made.content["type"], made.revision, made.title)


def _ordered(store: Port, artifact: dict) -> dict:
    """The artifact, its entries in the order the version of its type it conforms to declares."""
    return settled.order(artifact, composition.declared(composition.conformed(artifact, store)["schema"], store))


def _empty(into: Named) -> None:
    """Refuse what is not a directory, and a directory that holds anything: an export never writes over what is
    there."""
    if into.path.exists() and not into.path.is_dir():
        raise Refused([file_refusals.not_an_export_directory(into.named)])
    if into.path.is_dir() and any(into.path.iterdir()):
        raise Refused([file_refusals.export_would_overwrite(into.named)])
