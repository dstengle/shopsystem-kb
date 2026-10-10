"""A type read through what it is built on: the schemas of its composition, base first, the type version a kb:
reference names, read as that version was made whatever its type stands at now, the type a kind names, the nearest
held type an IRI sits under, and the kind an artifact is of. kb's own keywords are read through the composition, so a
type built on a base carries the base's first."""
from typing import NamedTuple

from referencing.exceptions import NoSuchResource

from kb import names, port, refusals, settled, values


def composition(schema: dict, corpus) -> list[dict]:
    """The schema and every schema it is built on, base first: its allOf members in order, a whole type it names by
    $ref followed to that type's schema, and last the schema itself. kb's keywords are read through this list."""
    built_on = []
    for member in schema.get("allOf", []):
        built_on += composition(member, corpus)
    ref = schema.get("$ref")
    referred = reference(ref) if isinstance(ref, str) else None
    if referred is not None and referred.whole:
        built_on += composition(type_schema(ref, corpus), corpus)
    return [*built_on, schema]


class Reference(NamedTuple):
    """What a kb: reference names: the type and the number of its version, the type None when it names no type
    version at all, and whether it is to the whole type rather than to a shape inside it."""
    type_id: values.ArtifactId | None
    whole: bool
    number: int = 0


def reference(ref: str) -> Reference | None:
    """What a kb: reference names, the type version's IRI read as kb's grammar reads one. None for a reference that
    is not kb's."""
    referred = names.referred(ref)
    if referred is None:
        return None
    name, fragment = referred
    found = names.version(name)
    if found is None:
        return Reference(None, not fragment)
    return Reference(values.ArtifactId(found[0]), not fragment, found[1])


def kept(type_id: values.ArtifactId, number: int, corpus) -> port.TypeVersion | None:
    """The version of a type the corpus keeps, as the type's IRI and the number name it; None when it keeps none, or
    when no type is held at the IRI (a version kept for a type since removed is not proof the type is held)."""
    if not (corpus.holds(type_id) and settled.typed(corpus.artifact(type_id))):
        return None
    try:
        return corpus.type_version(values.Version(values.Kind(str(type_id)), number))
    except KeyError:
        return None


def current(type_id: values.ArtifactId, corpus) -> port.TypeVersion:
    """The version a type stands at, read through the versions the corpus keeps. KeyError when no type is held at
    the IRI."""
    found = corpus.artifact(type_id)
    if not settled.typed(found):
        raise KeyError(str(type_id))
    return corpus.type_version(values.Version(values.Kind(str(type_id)), found["version"]))


def held(referred: Reference, corpus) -> bool:
    """Whether the corpus holds the type version a kb: reference names: a type at its IRI, and that version of it
    kept, whichever version the type stands at."""
    if referred.type_id is None:
        return False
    return kept(referred.type_id, referred.number, corpus) is not None


def type_schema(uri: str, corpus) -> dict:
    """The JSON Schema of the type version a kb: URI names, as that version was made. NoSuchResource if it names
    none the corpus holds."""
    referred = reference(uri)
    if referred is None or not held(referred, corpus):
        raise NoSuchResource(ref=uri)
    return kept(referred.type_id, referred.number, corpus).content["schema"]


def declared(schema: dict, corpus) -> dict:
    """kb's own keywords as a type declares them together with everything it is built on, base first: its fields
    (`properties`), its collections (`parts`) and the fields shown at a glance (`summary`). A type naming a field or
    a collection its base names too has its own."""
    whole = {"properties": {}, "parts": {}, "summary": []}
    for part in composition(schema, corpus):
        whole["properties"].update(part.get("properties", {}))
        whole["parts"].update(part.get("parts", {}))
        whole["summary"] += [name for name in part.get("summary", []) if name not in whole["summary"]]
    return whole


def kind_type(kind: values.Kind, corpus) -> values.ArtifactId:
    """The type a kind names. Raises Refused when the corpus holds none, or holds there an artifact that is not a
    type, since a kind must name a type the store holds, wherever it is given."""
    type_id = values.type_of(kind)
    if not (corpus.holds(type_id) and settled.typed(corpus.artifact(type_id))):
        raise values.Refused([refusals.no_type(kind.name)])
    return type_id


def version_schema(version: values.Version, corpus) -> dict:
    """The version of a type a create or a replacement names, as the corpus keeps it, its JSON Schema under
    `schema`, whatever version the type stands at now. Raises Refused when the corpus holds no such version."""
    found = kept(values.type_of(version.kind), version.number, corpus)
    if found is None:
        raise values.Refused([refusals.no_version(str(version))])
    return found.content


def conforming(artifact: dict) -> values.Version:
    """The version of its type an artifact conforms to, as the artifact names it."""
    return values.Version(artifact_kind(artifact), settled.version(artifact))


def conformed(artifact: dict, corpus) -> dict:
    """The version of its type an artifact conforms to, as the corpus keeps it. Raises Refused when the corpus holds
    no such version."""
    return version_schema(conforming(artifact), corpus)


def moves_to(artifact: dict, version: values.Version, corpus) -> bool:
    """Whether an artifact may move to a version: one the corpus keeps, of the artifact's own type, and not earlier
    than the one it conforms to."""
    stands = conforming(artifact)
    if version.kind != stands.kind or version.number < stands.number:
        return False
    return kept(values.type_of(version.kind), version.number, corpus) is not None


def nearest_type(artifact_id: values.ArtifactId, corpus) -> values.ArtifactId | None:
    """The type an IRI belongs to: the nearest IRI it sits under that the corpus holds a type at. None when it sits
    under no held type."""
    for above in names.above(artifact_id):
        type_id = values.ArtifactId(above)
        if corpus.holds(type_id) and settled.typed(corpus.artifact(type_id)):
            return type_id
    return None


def kind_of(artifact_id: values.ArtifactId, corpus) -> values.Kind:
    """The kind of an artifact the corpus holds, as the type version it conforms to says."""
    return artifact_kind(corpus.artifact(artifact_id))


def artifact_kind(artifact: dict) -> values.Kind:
    """The kind of an artifact, as the type version it conforms to says."""
    return values.Kind(settled.kind(artifact))


def artifact_schema(artifact: dict, corpus) -> dict:
    """The version of its type an artifact conforms to, as the corpus keeps it, its JSON Schema under `schema`: what
    a read shows of it and takes for a link. Raises Refused when the corpus keeps no such version."""
    return conformed(artifact, corpus)


def latest_schema(artifact: dict, corpus) -> dict:
    """The version its kind's type stands at now, whichever version the artifact conforms to: what an export and an
    import read an artifact through. Raises Refused when the corpus holds no such type."""
    return kind_schema(artifact_kind(artifact), corpus)


def kind_schema(kind: values.Kind, corpus) -> dict:
    """The type a kind names, as the corpus holds it, its JSON Schema under `schema`. Raises Refused when the corpus
    holds none."""
    return current(kind_type(kind, corpus), corpus).content


def read_through(kind: values.Kind, schema, corpus) -> list[values.ArtifactId]:
    """The types an artifact of a kind is checked and its links read through, given the schema of the version of its
    type it is read through: its kind's type, and every type a kb: reference names, in that schema or in the version
    of a type one names, each followed at the version named, never the one its type stands at; each type once, a
    reference to a version the corpus does not keep passed over."""
    found, followed = [values.type_of(kind)], set()

    def visit(node) -> None:
        for named in references(node):
            at = (named.type_id, named.number)
            version = None if at in followed else kept(*at, corpus)
            followed.add(at)
            if version is not None:
                found.extend(each for each in [named.type_id] if each not in found)
                visit(version.content.get("schema"))
    visit(schema)
    return found


def references(node):
    """Every type version a kb: reference anywhere in a schema names."""
    if isinstance(node, dict):
        for key, value in node.items():
            named = reference(value) if key == "$ref" and isinstance(value, str) else None
            if named is not None and named.type_id is not None:
                yield named
            yield from references(value)
    elif isinstance(node, list):
        for value in node:
            yield from references(value)


def referred(node):
    """Every type a kb: reference anywhere in a schema names."""
    return (named.type_id for named in references(node))
