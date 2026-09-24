"""Finding the store the way git finds a repository: upward from the working directory."""
from pathlib import Path

MARKER = Path("kb") / "store.yaml"


def find_above(start: Path) -> Path | None:
    """The nearest directory at or above `start` with a store inside it, or None."""
    for directory in (start, *start.parents):
        if (directory / MARKER).is_file():
            return directory
    return None
