"""kb's served-store double for a client's own tests, published: `served` puts a store behind kb's own server, the one
`kb serve` runs, in the test's own process on 127.0.0.1 at a port the system picks, and writes the connection to it
where the test says, so the test reaches the store the way a served store is reached, without anyone running
`kb serve`. When the block ends, however it ends, the server is stopped and the connection removed."""
from contextlib import ExitStack, contextmanager
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterator

from kb import canonical, server, store
from kb.addresses import Address

__all__ = ["served"]

HOST = "127.0.0.1"


@contextmanager
def served(store_root, connection_dir, *, clock: Callable[[], datetime] | None = None) -> Iterator[str]:
    """The store at store_root served on 127.0.0.1 at a free port for as long as the block runs, `kb/server.yaml`
    under connection_dir naming that address, and the address yielded as `host:port`. Each change made through the
    server is stamped with the moment clock gives, read at each stamp; with no clock, with the machine's. On exit the
    server is stopped, the store let go, and the connection removed, with the `kb/` directory holding it when the
    double made it and nothing else is left in it."""
    with ExitStack() as serving:
        hosting = server.started(Path(store_root), Address(HOST, 0), clock)
        serving.callback(hosting.stop)
        serving.enter_context(_connection(Path(connection_dir), hosting.address))
        yield str(hosting.address)


@contextmanager
def _connection(directory: Path, at: Address) -> Iterator[None]:
    """The connection to the server at the address, written under directory for as long as the block runs."""
    place = directory / store.CONNECTION.parent
    made = not place.exists()
    place.mkdir(parents=True, exist_ok=True)
    try:
        (directory / store.CONNECTION).write_text(canonical.dump({"address": str(at)}), encoding="utf-8")
        yield
    finally:
        (directory / store.CONNECTION).unlink(missing_ok=True)
        if made and not any(place.iterdir()):
            place.rmdir()
