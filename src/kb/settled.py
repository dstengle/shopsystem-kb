"""What the store settles for every artifact, whatever its type: the keys that say which artifact it is and what each
must be, its content without them, an artifact given them, and the order its entries are written in, as its type
declares them."""

SETTLED = {"id": str, "type": str, "schema_version": int, "revision": int, "title": str}
IDENTITY = tuple(SETTLED)


def identified(artifact: dict) -> bool:
    """Whether an artifact as written opens with the keys naming it, in their order, each what it must be."""
    if list(artifact)[:len(IDENTITY)] != list(IDENTITY):
        return False
    return all(
        isinstance(artifact[key], kind) and not isinstance(artifact[key], bool) for key, kind in SETTLED.items()
    )


def given(content: dict, artifact_id: str, kind: str, schema_version: int, revision: int, title: str) -> dict:
    """The content as an artifact: with its name, its kind, the version of its type it was checked against, its own
    version and its title."""
    return {
        **content,
        "id": artifact_id, "type": kind, "schema_version": schema_version, "revision": revision, "title": title,
    }


def content(artifact: dict) -> dict:
    """What an artifact holds but the keys the store settles."""
    return {key: value for key, value in artifact.items() if key not in IDENTITY}


def checked(artifact: dict) -> dict:
    """What of an artifact its type checks: its content, and its title, which a type may say something of."""
    return {key: value for key, value in artifact.items() if key not in IDENTITY or key == "title"}


TOP, ITEM, SECTION = "top", "item", "section"
LEVELS = (TOP, ITEM, SECTION)
SECTIONS = "sections"


def sequence(level: str, held, schema: dict) -> list[str]:
    """The names at one level of an artifact (its top, an item of a collection, a section) in the order they are
    written, given the schema declared there and the names the level holds: at the top, the identity keys, the fields
    in schema order, what else it holds as it holds it, the sections, the collections in schema order; in an item, its
    id, its fields in the item schema's order, then what else it holds; in a section, its title, body and sections,
    then what else it holds. The names declared there stand in it whether it holds them or not."""
    if level == TOP:
        fields = [name for name in schema.get("properties", {}) if name not in IDENTITY]
        parts = list(schema.get("parts", {}))
        others = [name for name in held if name not in (*IDENTITY, *fields, SECTIONS, *parts)]
        return list(dict.fromkeys([*IDENTITY, *fields, *others, SECTIONS, *parts]))
    leading = ("id", *schema.get("properties", {})) if level == ITEM else ("title", "body", SECTIONS)
    return list(dict.fromkeys([*leading, *held]))


def order(artifact: dict, schema: dict) -> dict:
    """An artifact's entries in the order `sequence` gives its top, each section's and each item's. What is not
    written in the shape its type gives it, which a set may leave before a later change in it fixes it, is left as it
    was written."""
    parts = schema.get("parts", {})
    ordered = _arranged(artifact, TOP, schema)
    if SECTIONS in artifact:
        ordered[SECTIONS] = _listed(artifact[SECTIONS], _section)
    for name in parts:
        if name in artifact:
            ordered[name] = _listed(artifact[name], lambda item, name=name: _item(item, parts[name]["items"]))
    return ordered


def _arranged(node: dict, level: str, schema: dict) -> dict:
    """A level's entries in the order `sequence` gives them."""
    return {name: node[name] for name in sequence(level, node, schema) if name in node}


def _listed(found, each):
    """Each entry of a list put in order, a value that is not a list as it was."""
    return [each(entry) for entry in found] if isinstance(found, list) else found


def _section(section) -> dict:
    """A section in order, and each of its sections; a section that is not a set of named entries as it was."""
    if not isinstance(section, dict):
        return section
    ordered = _arranged(section, SECTION, {})
    if SECTIONS in section:
        ordered[SECTIONS] = _listed(section[SECTIONS], _section)
    return ordered


def _item(item, item_schema: dict) -> dict:
    """An item in order; an item that is not a set of named entries as it was written."""
    return _arranged(item, ITEM, item_schema) if isinstance(item, dict) else item
