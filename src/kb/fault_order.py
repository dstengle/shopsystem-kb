"""The order an artifact's faults are given in: its places as the artifact reads back, a place before what is inside
it, then, at one place, by the names of the rules broken. It never makes or checks a fault."""
from kb import settled
from kb.contract import kb_pb2

_TOP, _ITEM, _SECTION, _SECTIONS, _ITEMS, _PLAIN = "top", "item", "section", "sections", "items", "plain"
_ENTRIES = {_ITEM: ("id",), _SECTION: ("title", "body", "sections")}


def ordered(faults: list[kb_pb2.Fault], artifact: dict, declared: dict) -> list[kb_pb2.Fault]:
    """An artifact's faults in the order its places stand in it as it reads back (as `settled.order` writes it, with
    its type's declared fields and collections), at one place by their rules' names without regard to case, then as
    written, then by message."""
    view = settled.order(artifact, declared)
    return sorted(faults, key=lambda fault: (
        _position(fault.place, view, declared), fault.rule.lower(), fault.rule, fault.message,
    ))


def _position(place: str, view: dict, declared: dict) -> tuple:
    """Where a place stands: the rank of each step of it among its siblings. The whole artifact, which is the place
    "", is before every place inside it."""
    node, level, schema = view, _TOP, declared
    position = []
    for step in place.split("/") if place else []:
        position.append(_rank(step, node, level, schema))
        node, level, schema = _inside(step, node, level, schema)
    return tuple(position)


def _rank(step: str, node, level: str, schema: dict) -> tuple:
    """A step's rank among the entries beside it: an entry of a list by its index as a number; a name by where its
    level's entries stand, the names it does not hold standing where the type would put them and those the type does
    not declare after them, by name."""
    if level in (_SECTIONS, _ITEMS):
        return (int(step) if step.isdigit() else len(node or []), "")
    names = _sequence(node, level, schema)
    return (names.index(step) if step in names else len(names), step)


def _sequence(node, level: str, schema: dict) -> list[str]:
    """The names of a level's entries in the order they stand: those the level declares, then the others as the node
    holds them."""
    held = list(node) if isinstance(node, dict) else []
    if level == _TOP:
        fields = [name for name in schema["properties"] if name not in settled.IDENTITY]
        others = [name for name in held if name not in (*settled.IDENTITY, *fields, "sections", *schema["parts"])]
        return [*settled.IDENTITY, *fields, *others, "sections", *schema["parts"]]
    if level == _ITEM:
        return list(dict.fromkeys([*_ENTRIES[_ITEM], *schema.get("properties", {}), *held]))
    return list(dict.fromkeys([*_ENTRIES.get(level, ()), *held]))


def _inside(step: str, node, level: str, schema: dict) -> tuple:
    """The node a step leads to, the level it stands at and the schema that level is read by."""
    if level == _SECTIONS:
        return _entry(step, node), _SECTION, {}
    if level == _ITEMS:
        return _entry(step, node), _ITEM, schema
    child = node.get(step) if isinstance(node, dict) else None
    if level in (_TOP, _ITEM) and step in schema.get("parts", {}):
        return child, _ITEMS, schema["parts"][step].get("items", {})
    if level in (_TOP, _SECTION) and step == "sections":
        return child, _SECTIONS, {}
    return child, _PLAIN, {}


def _entry(step: str, node):
    """The entry of a list at an index, none when there is none."""
    return node[int(step)] if isinstance(node, list) and step.isdigit() and int(step) < len(node) else None
