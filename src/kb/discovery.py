"""Finding the store the way git finds a repository: upward from the working directory, or named by KB_ROOT."""
from pathlib import Path
from typing import Mapping

from kb.contract import kb_pb2

MARKER = Path("kb") / "store.yaml"


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
