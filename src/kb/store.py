"""The store on disk: <root>/kb/, one canonical YAML file per artifact, itself a git repository."""
import os
import subprocess
from pathlib import Path

from kb import canonical, values
from kb.contract import CONTRACT_VERSION, kb_pb2
from kb.values import ArtifactId, Kind


class Unreadable(Exception):
    """A stored file that cannot be read. Carries the fault that names it."""

    def __init__(self, fault: kb_pb2.Fault):
        super().__init__(fault.message)
        self.fault = fault


class Store:
    def __init__(self, root):
        self.root = Path(root)
        self.dir = self.root / "kb"

    def path(self, artifact_id: ArtifactId) -> Path:
        return values.path(self.dir, artifact_id)

    def start(self) -> None:
        """Make the store directory, its git repository, and its marker file."""
        self.dir.mkdir(parents=True)
        _git("init", "-q", "-b", "main", str(self.dir))
        (self.dir / "store.yaml").write_text(canonical.dump({"contract": CONTRACT_VERSION}))

    def save(self, artifact_id: ArtifactId, text: str) -> Path:
        """Write canonical text to a temp file and rename it into place."""
        path = self.path(artifact_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_name(path.name + ".tmp")
        temp.write_text(text)
        temp.replace(path)
        return path

    def holds(self, artifact_id: ArtifactId) -> bool:
        return self.path(artifact_id).is_file()

    def load(self, artifact_id: ArtifactId) -> dict:
        """The artifact as stored. A file that cannot be read raises Unreadable, naming the file."""
        path = self.path(artifact_id)
        try:
            return canonical.load(path.read_text())
        except canonical.NotCanonical as error:
            raise Unreadable(kb_pb2.Fault(
                artifact=str(artifact_id), rule="unreadable",
                message=f"the stored file {path.relative_to(self.dir)} cannot be read: {error}",
            )) from None

    def schema(self, kind: Kind) -> dict:
        """The schema artifact of a kind; its JSON Schema is under `schema`."""
        return self.load(ArtifactId(Kind("schema"), kind.name))

    def commit(self, paths: list, role: str, message: str) -> None:
        """One commit of the given files, message from the request, author from the actor."""
        relative = [str(Path(path).relative_to(self.dir)) for path in paths]
        _git("-C", str(self.dir), "add", "--", *relative)
        env = {
            **os.environ,
            "GIT_AUTHOR_NAME": role, "GIT_AUTHOR_EMAIL": f"{role}@kb",
            "GIT_COMMITTER_NAME": role, "GIT_COMMITTER_EMAIL": f"{role}@kb",
        }
        _git("-C", str(self.dir), "-c", "commit.gpgsign=false", "commit", "-q", "-m", message, "--", *relative, env=env)

    def ids(self) -> list[ArtifactId]:
        """The name of every artifact in the store, schemas included, in path order."""
        return [ArtifactId(Kind(path.parent.name), path.stem) for path in sorted(self.dir.glob("*/*.yaml"))]

    def artifacts(self):
        """Every artifact in the store, schemas included, in path order. A file that cannot be read raises Unreadable."""
        for artifact_id in self.ids():
            yield self.load(artifact_id)


class Draft:
    """The store as a set of changes would leave it: artifacts put here stand over the stored ones, and nothing is
    written. Read like the store: holds, load, schema."""

    def __init__(self, store: Store):
        self._store = store
        self._pending: dict[ArtifactId, dict] = {}

    def put(self, artifact_id: ArtifactId, artifact: dict) -> None:
        self._pending[artifact_id] = artifact

    def holds(self, artifact_id: ArtifactId) -> bool:
        return artifact_id in self._pending or self._store.holds(artifact_id)

    def load(self, artifact_id: ArtifactId) -> dict:
        if artifact_id in self._pending:
            return self._pending[artifact_id]
        return self._store.load(artifact_id)

    def schema(self, kind: Kind) -> dict:
        return self.load(ArtifactId(Kind("schema"), kind.name))


def _git(*args, env=None):
    subprocess.run(["git", *args], check=True, capture_output=True, text=True, env=env)
