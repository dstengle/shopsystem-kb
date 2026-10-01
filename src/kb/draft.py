"""The store as a set's changes would leave it, read like the store: artifacts put here stand over the ones the store
holds, artifacts removed here are no longer held, and nothing is written. It answers the corpus's reads (holds,
artifact), the links into an artifact and what the store held before the set, over the port."""
from kb import composition, links, names
from kb.port import Linking, Port
from kb.values import TYPE_KIND, ArtifactId


class Draft:
    def __init__(self, store: Port):
        self._store = store
        self._pending: dict[ArtifactId, dict] = {}
        self._removed: set[ArtifactId] = set()

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
        return self._store.artifact(artifact_id)

    def before(self, artifact_id: ArtifactId) -> dict | None:
        """The artifact as the store held it before the set, None when it held none."""
        return self._store.artifact(artifact_id) if self._store.holds(artifact_id) else None

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

    def stale(self) -> list[ArtifactId]:
        """The artifacts the store holds and the draft leaves as they are whose links are read through a type the
        draft changed or removed, so that what the store keeps of their links is not what they carry now."""
        changed = {each for each in set(self._pending) | self._removed if each.kind == TYPE_KIND}
        if not changed:
            return []
        types = sorted(set(self._store.ids(TYPE_KIND)) | changed, key=names.order)
        touched = set(self._pending) | self._removed
        return [
            each for kind in composition.reading(changed, types, self)
            for each in self._store.ids(kind) if each not in touched
        ]
