"""The store written out as canonical files at one moment, never over anything: each artifact at the place its IRI
gives, `<dir>/<host>/<segment>/.../<segment>.yaml`, and a type as its versions, every one the store holds and no
other, each at the type's place and its number, `<dir>/<host>/.../<segment>@<n>.yaml` (export-and-import-a-store).
Each artifact's entries are written in the order the version of its type it conforms to declares; its content,
revision and type version are written as the store holds them, a type's version with the content, the revision and
the title it was made with."""
from dataclasses import dataclass, field
from typing import Iterator, NamedTuple

from kb import canonical, composition, file_refusals, names, settled
from kb.port import Port
from kb.port_values import TypeVersion
from kb.roots import Named
from kb.values import Kind, Refused, Version


@dataclass(frozen=True)
class Exported:
    """What an export answers: the faults that refused it, none when it was written."""
    faults: list = field(default_factory=list)


class File(NamedTuple):
    """One file of an export: its place below the export's directory, as `names.placing` writes it, and its
    canonical text."""
    place: str
    text: str


class Position(NamedTuple):
    """The position in the history an export's files reflect: the id of the entry landed last at their moment,
    empty when none has landed (decision/journal-position-is-an-entry)."""
    entry: str


def taken(store: Port) -> Iterator[File | Position]:
    """The store's files, each read as it is asked for, then the position they reflect. The caller holds the store
    at one moment from before the first is asked for until the position is given."""
    yield from files(store)
    yield Position(store.landed_last())


def files(store: Port) -> Iterator[File]:
    """Every artifact the store holds and every version it holds of every type, each at its place as canonical
    text, read as it is asked for."""
    for name in store.ids():
        artifact = store.artifact(name)
        if settled.typed(artifact):
            yield from _versions(store, name)
        else:
            yield File(names.placing(name), canonical.dump(_ordered(store, artifact)))


def written(store: Port, into: Named) -> None:
    """Those files, all read at one moment, then written into the directory, which is made, with any directory above
    it, when it does not exist. Raises Refused, before the store is read and writing nothing, when it is not a
    directory or holds anything."""
    _empty(into)
    with store.at_one_moment():
        read = list(files(store))
    into.path.mkdir(parents=True, exist_ok=True)
    for file in read:
        (into.path / file.place).parent.mkdir(parents=True, exist_ok=True)
        with (into.path / file.place).open("x", encoding="utf-8") as made:
            made.write(file.text)


def _versions(store: Port, name) -> Iterator[File]:
    """Every version the store holds of a type, each at the type's place and the version's number, as its file
    gives it."""
    for number in store.versions(name):
        made = _version(store.type_version(Version(Kind(str(name)), number)), name)
        yield File(names.placing(name, number), canonical.dump(_ordered(store, made)))


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
