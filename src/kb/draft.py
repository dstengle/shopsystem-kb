"""The store as a set's changes would leave it, read like the store: artifacts put here stand over the ones the store
holds, artifacts removed here are no longer held, and nothing is written. It answers the corpus's reads (holds,
artifact) and the links into an artifact, over the port. A type it reads from the store is kept as first read, so
every check of a set reads one version of it, and the revision it was read at is what the set hands the port."""
from kb import composition, links, names
from kb.port import Linking, Port
from kb.values import TYPE_KIND, ArtifactId, Kind


class Draft:
    def __init__(self, store: Port):
        self._store = store
        self._pending: dict[ArtifactId, dict] = {}
        self._removed: set[ArtifactId] = set()
        self._types: dict[ArtifactId, dict] = {}

    def put(self, artifact_id: ArtifactId, artifact: dict) -> None:
        self._removed.discard(artifact_id)
        self._pending[artifact_id] = artifact

    def remove(self, artifact_id: ArtifactId) -> None:
        self._removed.add(artifact_id)

    def holds(self, artifact_id: ArtifactId) -> bool:
        if artifact_id in self._removed:
            return False
        return artifact_id in self._pending or self._store.holds(artifact_id)

    def artifact(self, artifact_id: ArtifactId) -> dict:
        if artifact_id in self._pending:
            return self._pending[artifact_id]
        if artifact_id.kind != TYPE_KIND:
            return self._store.artifact(artifact_id)
        if artifact_id not in self._types:
            self._types[artifact_id] = self._store.artifact(artifact_id)
        return self._types[artifact_id]

    def as_read(self, type_ids: list[ArtifactId]) -> tuple[tuple[ArtifactId, int], ...]:
        """Each type given that the draft read from the store and leaves as it is, with the revision it was read at."""
        return tuple(
            (each, self._types[each]["revision"]) for each in type_ids
            if each in self._types and each not in self._pending and each not in self._removed
        )

    def links_in(self, target: ArtifactId) -> list[Linking]:
        """Every link into an artifact or a part inside it from an artifact the draft holds, in the order of their
        names, each artifact's in the order it carries them: the store's, but for what the draft changed and what it
        reads through a type it changed, which are read here as the draft leaves them."""
        stale = self.stale()
        read_here = set(self._pending) | self._removed | set(stale)
        held = [each for each in self._store.links_in(target) if each.source not in read_here]
        sources = [(source, artifact) for source, artifact in self._pending.items() if source not in self._removed]
        drafted = [
            Linking(source, link.field, link.place, link.target, link.part)
            for source, artifact in sources + [(source, self._store.artifact(source)) for source in stale]
            for link in links.handed(source, artifact, self) if link.target == target and not link.implicit
        ]
        return sorted(held + drafted, key=lambda each: names.order(each.source))

    def reread(self) -> list[Kind]:
        """The kinds whose artifacts' links are read through a type the draft changed or removed."""
        changed = {each for each in set(self._pending) | self._removed if each.kind == TYPE_KIND}
        if not changed:
            return []
        types = sorted(set(self._store.ids(TYPE_KIND)) | changed, key=names.order)
        return list(composition.reading(changed, types, self))

    def stale(self) -> list[ArtifactId]:
        """The artifacts the store holds and the draft leaves as they are whose links are read through a type the
        draft changed or removed, so that what the store keeps of their links is not what they carry now."""
        touched = set(self._pending) | self._removed
        return [each for kind in self.reread() for each in self._store.ids(kind) if each not in touched]
