"""The store on disk: <root>/kb/, one canonical YAML file per artifact, itself a git repository."""
import os
import subprocess
from pathlib import Path

from kb import canonical, values
from kb.contract import CONTRACT_VERSION
from kb.values import ArtifactId, Kind


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

    def save(self, artifact_id: ArtifactId, artifact: dict) -> Path:
        """Serialize canonically to a temp file and rename into place."""
        path = self.path(artifact_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_name(path.name + ".tmp")
        temp.write_text(canonical.dump(artifact))
        temp.replace(path)
        return path

    def holds(self, artifact_id: ArtifactId) -> bool:
        return self.path(artifact_id).is_file()

    def load(self, artifact_id: ArtifactId) -> dict:
        return canonical.load(self.path(artifact_id).read_text())

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

    def artifacts(self):
        """Every artifact in the store, schemas included, in path order."""
        for path in sorted(self.dir.glob("*/*.yaml")):
            yield canonical.load(path.read_text())


def _git(*args, env=None):
    subprocess.run(["git", *args], check=True, capture_output=True, text=True, env=env)
