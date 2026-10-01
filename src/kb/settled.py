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


def order(artifact: dict, schema: dict) -> dict:
    """Identity keys first, then fields in schema order, then sections, then part collections in schema order. What
    is not written in the shape its type gives it, which a set may leave before a later change in it fixes it, is
    left as it was written."""
    parts = schema.get("parts", {})
    ordered = {key: artifact[key] for key in IDENTITY}
    for name in schema.get("properties", {}):
        if name in artifact and name not in ordered:
            ordered[name] = artifact[name]
    for name, value in artifact.items():
        if name not in ordered and name != "sections" and name not in parts:
            ordered[name] = value
    if "sections" in artifact:
        ordered["sections"] = _listed(artifact["sections"], _section)
    for name in parts:
        if name in artifact:
            ordered[name] = _listed(artifact[name], lambda item, name=name: _item(item, parts[name]["items"]))
    return ordered


def _listed(found, each):
    """Each entry of a list put in order, a value that is not a list as it was."""
    return [each(entry) for entry in found] if isinstance(found, list) else found


def _section(section) -> dict:
    """A section's title, body and sections first, then anything else it carries as it was written."""
    if not isinstance(section, dict):
        return section
    ordered = {key: section[key] for key in ("title", "body") if key in section}
    if "sections" in section:
        ordered["sections"] = _listed(section["sections"], _section)
    return {**ordered, **{key: value for key, value in section.items() if key not in ordered}}


def _item(item, item_schema: dict) -> dict:
    """An item's id first, then its fields in the item schema's order; an item that is not a set of named entries as
    it was written."""
    if not isinstance(item, dict):
        return item
    ordered = {"id": item["id"]} if "id" in item else {}
    for name in item_schema.get("properties", {}):
        if name in item and name not in ordered:
            ordered[name] = item[name]
    for name, value in item.items():
        if name not in ordered:
            ordered[name] = value
    return ordered
