"""The store written out as canonical files at one moment, never over anything: each artifact at
`<dir>/<kind>/<slug>.yaml`, so a type, of kind `schema`, at `<dir>/schema/<kind>.yaml` (export-and-import-a-store).
Each artifact's entries are written in the order the current version of its type declares, as an import checks them;
its content, revision and type version are written as the store holds them."""
from dataclasses import dataclass, field

from kb import canonical, composition, rules, settled, values
from kb.contract import kb_pb2
from kb.port import Port
from kb.values import Directory, Refused


@dataclass(frozen=True)
class Exported:
    """What an export answers: the faults that refused it, none when it was written."""
    faults: list = field(default_factory=list)


def written(store: Port, into: Directory) -> None:
    """Every artifact the store holds, all read at one moment, then written as canonical text into the directory,
    which is made, with any directory above it, when it does not exist. Raises Refused, writing nothing, when it is not a
    directory or holds anything."""
    with store.at_one_moment():
        artifacts = {name: _ordered(store, name, store.artifact(name)) for name in store.ids()}
    _empty(into)
    into.path.mkdir(parents=True, exist_ok=True)
    for name, artifact in artifacts.items():
        folder = into.path / name.kind.name
        folder.mkdir(exist_ok=True)
        with (folder / f"{name.slug}.yaml").open("x", encoding="utf-8") as file:
            file.write(canonical.dump(artifact))


def _ordered(store: Port, name, artifact: dict) -> dict:
    """The artifact, its entries in the order the current version of its type declares; as held when its kind has
    no type."""
    type_id = values.type_of(name.kind)
    if not store.holds(type_id):
        return artifact
    return settled.order(artifact, composition.declared(store.artifact(type_id)["schema"], store))


def _empty(into: Directory) -> None:
    """Refuse what is not a directory, and a directory that holds anything: an export never writes over what is
    there."""
    if into.path.exists() and not into.path.is_dir():
        raise Refused([kb_pb2.Fault(
            rule=rules.ROOT, message=f"an export is written into a directory; {into.named!r} is not a directory",
        )])
    if into.path.is_dir() and any(into.path.iterdir()):
        raise Refused([kb_pb2.Fault(
            rule=rules.ROOT, message=f"an export never overwrites; {into.named!r} already holds something",
        )])
