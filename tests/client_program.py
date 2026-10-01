"""A client in a program of its own, for `at_once.py`: it makes one change, the rpc's request read from the file
`request` in the gate directory, over the store at the root it is given, and writes the response to stdout. Its
clock, the first time it is asked, leaves the file `waiting` in the gate directory and waits until the file `go` is
there.

    python client_program.py <root> <gate> <rpc>
"""
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from kb import client
from kb.contract import kb_pb2

PATIENCE = 30.0


def gated(gate: Path):
    def clock() -> datetime:
        (gate / "waiting").touch()
        deadline = time.monotonic() + PATIENCE
        while not (gate / "go").exists():
            if time.monotonic() > deadline:
                raise TimeoutError("the change was never let go")
            time.sleep(0.005)
        return datetime.now(timezone.utc)
    return clock


def main(root: str, gate: str, rpc: str) -> None:
    request = getattr(kb_pb2, f"{rpc}Request").FromString((Path(gate) / "request").read_bytes())
    response = getattr(client.connect(root, clock=gated(Path(gate))), rpc)(request)
    sys.stdout.buffer.write(response.SerializeToString())


if __name__ == "__main__":
    main(*sys.argv[1:])
