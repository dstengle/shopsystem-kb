"""The git repositories a step makes beside a store, always under the test's tmp_path, and how one stands: the steps
that name a repository in the environment the way git does for a hook, and observe it was left alone, know git; kb's
own steps never do otherwise. Every git run here has an environment cleared of git's own variables, whatever a Given
has set, so it reaches only the directory it names."""
import os
import subprocess
from pathlib import Path

IDENTITY = ("-c", "user.name=steps", "-c", "user.email=steps@example.com", "-c", "commit.gpgsign=false")


def git(directory: Path, *args: str) -> str:
    """git run in `directory` alone, its output."""
    clean = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    return subprocess.run(
        ["git", "-C", str(directory), *IDENTITY, *args], env=clean, capture_output=True, text=True, check=True,
    ).stdout


NOTES = {"NOTES.md": b"# Notes kept beside the shop\n"}


def made(directory: Path, files: dict[str, bytes] = NOTES) -> Path:
    """A git repository at `directory`, made there with one commit of files of its own and nothing staged."""
    directory.mkdir(parents=True, exist_ok=True)
    git(directory, "init", "-q", "-b", "main")
    for name, data in files.items():
        (directory / name).parent.mkdir(parents=True, exist_ok=True)
        (directory / name).write_bytes(data)
    git(directory, "add", "--", *files)
    git(directory, "commit", "-q", "-m", "Files of its own")
    return directory


def hooked(directory: Path) -> dict[str, str]:
    """The environment git gives a program it runs from a hook in the repository at `directory`, naming it: its git
    directory, and the index a commit's hooks are given."""
    return {"GIT_DIR": str(directory / ".git"), "GIT_INDEX_FILE": str(directory / ".git" / "index")}


def standing(directory: Path) -> tuple[str, str]:
    """How the repository at `directory` stands: its history, and what it has made ready for its next commit. What
    is not yet tracked is not ready for a commit, so a store started inside the repository's directory is not part
    of how it stands."""
    return git(directory, "log", "--format=%H %s"), git(directory, "status", "--porcelain", "--untracked-files=no")
