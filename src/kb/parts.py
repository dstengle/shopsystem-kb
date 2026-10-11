"""The read of a node of an artifact: the artifact itself, or the part its place names, with what that node's type
declares and the links it carries."""
from typing import NamedTuple

from kb import composition, links, names, places
from kb.port import Port
from kb.values import Locator


class Read(NamedTuple):
    """What a read gives: the artifact, the node of it read (the artifact itself, or the part its place names), what
    that node's type declares, the links the node carries, in its own fields and in its items at every depth, and
    how a link says that node holds it (`links.Link.holder`)."""
    found: dict
    node: dict
    declared: dict
    links: list
    holder: str


def node(found: dict, locator: Locator) -> dict:
    """What of an artifact a read gives: the part its place names, when it names one, otherwise the artifact."""
    names_part = locator.place and places.holds_part(found, locator.place)
    return places.node(found, locator) if names_part else found


def read(store: Port, found: dict, locator: Locator) -> Read:
    schema = composition.artifact_schema(found, store)["schema"]
    declared, read_node = composition.declared(schema, store), node(found, locator)
    if read_node is found:
        return Read(found, found, declared, links.carried(found, schema, store), "")
    declared = composition.declared_at(declared, locator.place, store)
    inside = links.inside(found, schema, store, read_node)
    return Read(found, read_node, declared, inside, names.placed(locator.place))


def glance(read: Read) -> dict:
    """The node at a glance: an artifact's summary fields, or a part's name and title."""
    if read.node is read.found:
        return {name: read.found[name] for name in read.declared["summary"] if name in read.found}
    return {key: read.node[key] for key in ("id", "title") if key in read.node}
