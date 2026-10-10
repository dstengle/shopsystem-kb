"""The store written out as canonical files at one moment, never over anything: each artifact at the place its IRI
gives, `<dir>/<host>/<segment>/.../<segment>.yaml`, and a type at its version's, `<dir>/<host>/.../<segment>@<n>.yaml`
(export-and-import-a-store).
Each artifact's entries are written in the order the current version of its type declares, as an import checks them;
its content, revision and type version are written as the store holds them."""
from dataclasses import dataclass, field

from kb import canonical, composition, file_refusals, names, settled
from kb.port import Port
from kb.roots import Named
from kb.values import Refused


@dataclass(frozen=True)
class Exported:
    """What an export answers: the faults that refused it, none when it was written."""
    faults: list = field(default_factory=list)


def written(store: Port, into: Named) -> None:
    """Every artifact the store holds, all read at one moment, then written as canonical text into the directory,
    which is made, with any directory above it, when it does not exist. Raises Refused, before the store is read and
    writing nothing, when it is not a directory or holds anything."""
    _empty(into)
    with store.at_one_moment():
        artifacts = {name: _ordered(store, name, store.artifact(name)) for name in store.ids()}
    into.path.mkdir(parents=True, exist_ok=True)
    for name, artifact in artifacts.items():
        *folders, filename = names.place(name, artifact.get("version") if settled.typed(artifact) else None)
        (into.path.joinpath(*folders)).mkdir(parents=True, exist_ok=True)
        with into.path.joinpath(*folders, filename).open("x", encoding="utf-8") as file:
            file.write(canonical.dump(artifact))


def _ordered(store: Port, name, artifact: dict) -> dict:
    """The artifact, its entries in the order the current version of its type declares."""
    return settled.order(artifact, composition.declared(composition.latest_schema(artifact, store)["schema"], store))


def _empty(into: Named) -> None:
    """Refuse what is not a directory, and a directory that holds anything: an export never writes over what is
    there."""
    if into.path.exists() and not into.path.is_dir():
        raise Refused([file_refusals.not_an_export_directory(into.named)])
    if into.path.is_dir() and any(into.path.iterdir()):
        raise Refused([file_refusals.export_would_overwrite(into.named)])
