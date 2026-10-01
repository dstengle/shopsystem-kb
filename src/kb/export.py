"""The store written out as canonical files at one moment, never over anything: each artifact at
`<dir>/<kind>/<slug>.yaml`, so a type, of kind `schema`, at `<dir>/schema/<kind>.yaml` (export-and-import-a-store)."""
from dataclasses import dataclass, field

from kb import canonical, rules
from kb.contract import kb_pb2
from kb.port import Port
from kb.values import Directory, Refused


@dataclass(frozen=True)
class Exported:
    """What an export answers: the faults that refused it, none when it was written."""
    faults: list = field(default_factory=list)


def written(store: Port, into: Directory) -> None:
    """Every artifact the store holds, all read at one moment, then written as canonical text into the directory,
    which is made when it does not exist. Raises Refused, writing nothing, when the directory holds anything."""
    with store.at_one_moment():
        artifacts = {name: store.artifact(name) for name in store.ids()}
    _empty(into)
    into.path.mkdir(exist_ok=True)
    for name, artifact in artifacts.items():
        folder = into.path / name.kind.name
        folder.mkdir(exist_ok=True)
        with (folder / f"{name.slug}.yaml").open("x", encoding="utf-8") as file:
            file.write(canonical.dump(artifact))



def _empty(into: Directory) -> None:
    """Refuse a directory that holds anything: an export never writes over what is there."""
    if into.path.is_dir() and any(into.path.iterdir()):
        raise Refused([kb_pb2.Fault(
            rule=rules.ROOT, message=f"an export never overwrites; {into.named!r} already holds something",
        )])
