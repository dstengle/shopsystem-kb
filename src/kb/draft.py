"""The store as a set's changes would leave it, read like the store: artifacts put here stand over the ones the store
holds, artifacts removed here are no longer held, and nothing is written. It answers the corpus's reads (holds,
artifact) and the links into an artifact, over the port."""
from kb import links, names
from kb.port import Linking, Port
from kb.values import ArtifactId


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

    def links_in(self, target: ArtifactId) -> list[Linking]:
        """Every link into an artifact or a part inside it from an artifact the draft holds, in the order of their
        names, each artifact's in the order it carries them: the store's, but for what the draft changed, and those
        of what the draft put."""
        changed = set(self._pending) | self._removed
        held = [each for each in self._store.links_in(target) if each.source not in changed]
        drafted = [
            Linking(source, link.field, link.place, link.target, link.part)
            for source, artifact in self._pending.items() if source not in self._removed
            for link in links.handed(source, artifact, self) if link.target == target
        ]
        return sorted(held + drafted, key=lambda each: names.order(each.source))
