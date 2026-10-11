"""A version of a type read as the artifact it was made as."""
from dataclasses import replace

from kb import composition, refusals, values
from kb.port import Port
from kb.requests import Reading
from kb.values import ArtifactId, Locator, Refused


def as_read(store: Port, reading: Reading) -> tuple[Port, Reading]:
    """The store with the version put over it as an artifact under the version's IRI, with the revision and the
    title it was made with, and the reading made of that artifact. Raises Refused when the store keeps no such
    version."""
    version = reading.version
    held = composition.kept(values.type_of(version.kind), version.number, store)
    if held is None:
        raise Refused([refusals.not_found(ArtifactId(str(version)))])
    at = ArtifactId(str(version))
    made = {**held.content, "id": str(at), "revision": held.revision, "title": held.title}
    return _Kept(store, at, made), replace(reading, locator=Locator(at, reading.locator.place), version=None)


class _Kept:
    """The store with one artifact put over it, as a version of a type is read as an artifact; all else is the store's."""

    def __init__(self, store: Port, artifact_id: ArtifactId, made: dict):
        self._store, self._id, self._made = store, artifact_id, made

    def holds(self, artifact_id: ArtifactId) -> bool:
        return artifact_id == self._id or self._store.holds(artifact_id)

    def artifact(self, artifact_id: ArtifactId) -> dict:
        return self._made if artifact_id == self._id else self._store.artifact(artifact_id)

    def __getattr__(self, name):
        return getattr(self._store, name)
