"""The store as a set's changes would leave it, read like the store: artifacts put here stand over the ones the store
holds, artifacts removed here are no longer held, and nothing is written. It answers the corpus's reads (holds,
artifact) and the links into an artifact, over the port: those of what it put read through the version each conforms
to, the store's standing for everything else, a type it changed restating none. A type it reads from the store is kept as first read, so
every check of a set reads one version of it, and the revision it was read at is what the set hands the port."""
from kb import composition, links, names, settled
from kb.port import Linking, Port, TypeVersion
from kb.values import ArtifactId, Kind, Version, type_of


class Draft:
    def __init__(self, store: Port):
        self._store = store
        self._pending: dict[ArtifactId, dict] = {}
        self._removed: set[ArtifactId] = set()
        self._types: dict[ArtifactId, dict] = {}
        self._numbers: dict[ArtifactId, int] = {}
        self._made: dict[ArtifactId, dict[int, dict]] = {}
        self._gone: set[ArtifactId] = set()

    def put(self, artifact_id: ArtifactId, artifact: dict) -> None:
        """An artifact as the draft leaves it; a type is kept too as the version of it this makes, under its number,
        whatever the draft puts there after."""
        self._removed.discard(artifact_id)
        self._pending[artifact_id] = artifact
        if settled.typed(artifact) and type(artifact.get("version")) is int:
            self._made.setdefault(artifact_id, {})[artifact["version"]] = artifact

    def remove(self, artifact_id: ArtifactId) -> None:
        """An artifact taken out, and with a type every version of it, the store's and those the draft made."""
        self._removed.add(artifact_id)
        self._gone.add(artifact_id)
        self._made.pop(artifact_id, None)

    def ids(self, kind: Kind) -> list[ArtifactId]:
        """Every artifact of a kind the draft holds, in the order of their names."""
        put = {each for each, artifact in self._pending.items() if settled.kind(artifact) == kind.name}
        return sorted((put | set(self._store.ids(kind))) - self._removed, key=names.order)

    def versions(self, type_id: ArtifactId) -> list[int]:
        """The number of every version of a type the draft leaves held, lowest first: those the store keeps, unless
        the draft removed the type, and those the draft made since."""
        if type_id in self._removed:
            return []
        kept = [] if type_id in self._gone else self._store.versions(type_id)
        return sorted({*kept, *self._made.get(type_id, {})})

    def holds(self, artifact_id: ArtifactId) -> bool:
        if artifact_id in self._removed:
            return False
        return artifact_id in self._pending or self._store.holds(artifact_id)

    def artifact(self, artifact_id: ArtifactId) -> dict:
        if artifact_id in self._pending:
            return self._pending[artifact_id]
        if artifact_id in self._types:
            return self._types[artifact_id]
        found = self._store.artifact(artifact_id)
        if settled.typed(found):
            self._types[artifact_id] = found
        return found

    def type_version(self, version: Version) -> TypeVersion:
        """A version of a type as the draft leaves it: the type the draft put, when it stands at that version, or
        as the draft made it at that version before; any other version, and every version of a type the draft did
        not put, as the store keeps it, a type's kept as first read. KeyError when the draft removed the type, or
        neither it nor the store holds that version; a type removed and put again holds only what was made since."""
        type_id = ArtifactId(version.kind.name)
        if type_id in self._removed:
            raise KeyError(str(version))
        put = self._pending.get(type_id)
        if put is None:
            found = self._store.type_version(version)
            self._types.setdefault(type_id, found.content)
            return found
        if put.get("version") == version.number:
            return TypeVersion(version, put, put["revision"], put["title"])
        made = self._made.get(type_id, {}).get(version.number)
        if made is not None:
            return TypeVersion(version, made, made["revision"], made["title"])
        if type_id in self._gone:
            raise KeyError(str(version))
        return self._store.type_version(version)

    def numbered(self, type_id: ArtifactId) -> int:
        """The number the next version of a type is made at, and counted as made: 1 for a type the draft does not
        hold, else the number after the last counted here, or after the one the type stands at."""
        last = (self._numbers.get(type_id) or self.artifact(type_id)["version"]) if self.holds(type_id) else 0
        self._numbers[type_id] = last + 1
        return last + 1

    def as_read(self, type_ids: list[ArtifactId]) -> tuple[tuple[ArtifactId, int], ...]:
        """Each type given, once, that the draft read from the store and leaves as it is, with the revision it was
        read at."""
        return tuple(
            (each, self._types[each]["revision"]) for each in dict.fromkeys(type_ids)
            if each in self._types and each not in self._pending and each not in self._removed
        )

    def links_in(self, target: ArtifactId) -> list[Linking]:
        """Every link into an artifact or a part inside it from an artifact the draft holds, in the order of their
        names, each artifact's in the order it carries them: the store's, as each artifact's own version of its type
        declares them whatever the draft did to that type, but for what the draft changed, which is read here as the
        draft leaves it, one whose own version of its type the draft does not keep carrying none."""
        read_here = set(self._pending) | self._removed
        held = [each for each in self._store.links_in(target) if each.source not in read_here]
        sources = [
            (source, artifact, self._own(artifact)) for source, artifact in self._pending.items()
            if source not in self._removed
        ]
        drafted = [
            Linking(source, link.field, link.place, link.target, link.part)
            for source, artifact, own in sources if own is not None
            for link in links.handed(source, artifact, self, own)
            if link.target == target and not link.implicit
        ]
        return sorted(held + drafted, key=lambda each: names.order(each.source))

    def _own(self, artifact: dict) -> dict | None:
        """The version of its type an artifact the draft put conforms to, as the draft keeps it; None when it keeps
        none."""
        version = composition.conforming(artifact)
        found = composition.kept(type_of(version.kind), version.number, self)
        return found and found.content
