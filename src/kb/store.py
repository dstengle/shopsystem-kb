"""The store on disk: <root>/kb/, one canonical YAML file per artifact, itself a git repository; and finding it, the
way git finds a repository: upward from the working directory, or named by KB_ROOT."""
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from kb import canonical, refusals, values
from kb.contract import CONTRACT_VERSION, kb_pb2
from kb.values import ArtifactId, Kind, Refused, Root, Signed

MARKER = Path("kb") / "store.yaml"


@dataclass(frozen=True)
class Damaged:
    """What loading a stored file that cannot be read gives in place of the artifact: the fault that names the file."""
    fault: kb_pb2.Fault


def readable(loaded: dict | Damaged) -> dict:
    """The artifact loaded; a file that cannot be read refuses the call with the fault naming it. The one place a
    damaged file becomes a refusal."""
    if isinstance(loaded, Damaged):
        raise Refused([loaded.fault])
    return loaded


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
        (self.dir / "store.yaml").write_text(canonical.dump({"contract": CONTRACT_VERSION}), encoding="utf-8")

    def save(self, artifact_id: ArtifactId, text: str) -> Path:
        """Write canonical text to a temp file and rename it into place."""
        path = self.path(artifact_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_name(path.name + ".tmp")
        temp.write_text(text, encoding="utf-8")
        temp.replace(path)
        return path

    def remove(self, artifact_id: ArtifactId) -> Path:
        """Take an artifact's file out, and return where it was."""
        path = self.path(artifact_id)
        path.unlink()
        return path

    def holds(self, artifact_id: ArtifactId) -> bool:
        return self.path(artifact_id).is_file()

    def load(self, artifact_id: ArtifactId) -> dict | Damaged:
        """The artifact as stored, or, when its file cannot be read, the fault naming the file. Never raises for what
        a file holds."""
        path = self.path(artifact_id)
        try:
            return canonical.load(path.read_text(encoding="utf-8"))
        except canonical.NotCanonical as error:
            return Damaged(refusals.unreadable(artifact_id, path.relative_to(self.dir), str(error)))

    def artifact(self, artifact_id: ArtifactId) -> dict:
        """The artifact as stored, for a reader that cannot go on without it. Raises Refused for a damaged file."""
        return readable(self.load(artifact_id))

    def schema(self, kind: Kind) -> dict:
        """The schema artifact of a kind; its JSON Schema is under `schema`. Raises Refused for a damaged file."""
        return self.artifact(ArtifactId(Kind("schema"), kind.name))

    def commit(self, paths: list, signed: Signed) -> None:
        """One commit of the given files, under the message and the actor's role."""
        role = signed.actor.role
        relative = [str(Path(path).relative_to(self.dir)) for path in paths]
        _git("-C", str(self.dir), "add", "--", *relative)
        env = {
            **os.environ,
            "GIT_AUTHOR_NAME": role, "GIT_AUTHOR_EMAIL": f"{role}@kb",
            "GIT_COMMITTER_NAME": role, "GIT_COMMITTER_EMAIL": f"{role}@kb",
        }
        _git("-C", str(self.dir), "-c", "commit.gpgsign=false", "commit", "-q", "-m", signed.message, "--", *relative, env=env)

    def ids(self) -> list[ArtifactId]:
        """The name of every artifact in the store, schemas included, in path order."""
        return [ArtifactId(Kind(path.parent.name), path.stem) for path in sorted(self.dir.glob("*/*.yaml"))]

    def artifacts(self):
        """Every artifact in the store, schemas included, in path order. Raises Refused at a damaged file."""
        for artifact_id in self.ids():
            yield self.artifact(artifact_id)


class Draft:
    """The store as a set of changes would leave it: artifacts put here stand over the stored ones, artifacts removed
    here are no longer held, and nothing is written. Read like the store: holds, load, schema, ids."""

    def __init__(self, store: Store):
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

    def ids(self) -> list[ArtifactId]:
        """The name of every artifact the draft holds, in the order their paths would sort."""
        held = (set(self._store.ids()) | set(self._pending)) - self._removed
        return sorted(held, key=lambda artifact_id: f"{artifact_id}.yaml")

    def load(self, artifact_id: ArtifactId) -> dict | Damaged:
        if artifact_id in self._pending:
            return self._pending[artifact_id]
        return self._store.load(artifact_id)

    def artifact(self, artifact_id: ArtifactId) -> dict:
        return readable(self.load(artifact_id))

    def schema(self, kind: Kind) -> dict:
        return self.artifact(ArtifactId(Kind("schema"), kind.name))


def vacant(root: Root) -> None:
    """Refuse a root a store cannot be started in: one that is not there, is not a directory, has anything called kb
    inside it, or is inside a store."""
    if not root.path.exists():
        raise Refused([kb_pb2.Fault(
            rule="root", message=f"a store is started in a directory that exists; {root.named!r} does not",
        )])
    if not root.path.is_dir():
        raise Refused([kb_pb2.Fault(
            rule="root", message=f"a store is started in a directory, and {root.named!r} is not one",
        )])
    if (root.path / "kb").exists():
        raise Refused([kb_pb2.Fault(
            rule="root", message=f"a store is never started over another; {root.named!r} already has a store inside it",
        )])
    above = find_above(root.path.resolve().parent)
    if above is not None:
        raise Refused([kb_pb2.Fault(
            rule="root", message=f"stores do not nest; {root.named!r} is inside the store at {str(above)!r}",
        )])


def find_above(start: Path) -> Path | None:
    """The nearest directory at or above `start` with a store inside it, or None."""
    for directory in (start, *start.parents):
        if (directory / MARKER).is_file():
            return directory
    return None


def locate(cwd: Path, env: Mapping[str, str]) -> tuple[Path | None, kb_pb2.Fault | None]:
    """The store a call goes to, or the fault that refuses it. Nothing is guessed at."""
    above = find_above(cwd)
    if "KB_ROOT" not in env:
        if above is None:
            return None, kb_pb2.Fault(
                rule="store", message=f"no store was found, neither above {cwd} nor named outright",
            )
        return above, None
    named = Path(env["KB_ROOT"])
    if not (named / MARKER).is_file():
        return None, kb_pb2.Fault(
            rule="store", message=f"KB_ROOT names a directory that holds no store: {named}",
        )
    if above is not None and above.resolve() != named.resolve():
        return None, kb_pb2.Fault(
            rule="store",
            message=f"KB_ROOT names a store other than the one {cwd} is working in: KB_ROOT is {named}, "
                    f"the working directory is inside {above}; neither is guessed at",
        )
    return named, None


QUIET = ("-c", "maintenance.auto=false", "-c", "gc.auto=0")


def _git(*args, env=None):
    """git, with its automatic maintenance off, so nothing runs on in the store after a call returns."""
    subprocess.run(["git", *QUIET, *args], check=True, capture_output=True, text=True, env=env)
