"""A store started in the client's own process, off the wire: `init`, which `kb` publishes, and the operator's
`kb init` calls, and `NotStarted`, what it raises when it refuses. It runs inside the servicer's one boundary: its
values made first, then one call into the domain, and any refusal or escaping exception its faults."""
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

from kb import signatures, values, write
from kb.servicer import boundary, guarded


class NotStarted(Exception):
    """No store was started, and nothing was made: `faults` says why, each a Fault of the contract."""

    def __init__(self, faults):
        self.faults = list(faults)
        super().__init__("; ".join(f"{fault.rule}: {fault.message}" for fault in self.faults))


@dataclass
class Started:
    """What starting a store answers: the faults that refused it, none when it was started."""
    faults: list = field(default_factory=list)


@dataclass(frozen=True)
class Starting:
    """A start as it is asked for: the root as named, and who starts it."""
    root: str
    role: str
    execution: str


class _Starter:
    def __init__(self, clock):
        self._clock = guarded(clock)

    @boundary(Started, opens=False)
    def start(self, request: Starting):
        """Who starts the store, then where, the first refusal only; then the store started there."""
        actor = signatures.starter(request.role, request.execution)
        write.start(values.root(request.root), actor, self._clock)
        return Started()


def init(root, role: str, *, execution: str = "", clock: Callable[[], datetime] | None = None) -> None:
    """A new store at <root>/kb/, started under the role, for the piece of work when one is named, its first entry
    in the history stamped with the moment the clock gives, or the machine's with none; the clock is the one
    `kb.client.connect` takes. The root is an absolute or relative path. Raises NotStarted, making nothing, when no
    store can be started there."""
    started = _Starter(clock).start(Starting(os.fspath(root), role, execution))
    if started.faults:
        raise NotStarted(started.faults)
