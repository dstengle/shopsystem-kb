"""Who makes a change and why: the actor, the signature, and the conversions of a writer's, a reader's and a
starter's; refuses one that does not sign."""
from dataclasses import dataclass

from kb import rules
from kb.contract import kb_pb2
from kb.values import Refused


@dataclass(frozen=True)
class Actor:
    role: str
    execution: str


@dataclass(frozen=True)
class Signed:
    """Who made a change, and the message they gave for it."""
    actor: Actor
    message: str


def actor(request: kb_pb2.Actor) -> Actor:
    return Actor(request.role, request.execution)


def _entry(reason: str) -> str:
    return f"every entry in the history {reason}"


def _unsigned(request: kb_pb2.Actor, message: str) -> list[kb_pb2.Fault]:
    faults = []
    if not request.role.strip():
        faults.append(kb_pb2.Fault(rule=rules.ACTOR, message=_entry("names the role that made it")))
    if not message.strip():
        faults.append(kb_pb2.Fault(rule=rules.MESSAGE, message=_entry("says why it was made")))
    return faults


def signed(request: kb_pb2.Actor, message: str) -> Signed:
    """Who makes a change and why, who must name a role and a message; both faults when both fail."""
    faults = _unsigned(request, message)
    if faults:
        raise Refused(faults)
    return Signed(actor(request), message)


def reader(request: kb_pb2.Actor, message: str) -> Signed:
    """Who records what a piece of work read, who must sign and name the piece of work; every fault found."""
    faults = _unsigned(request, message)
    if not request.execution:
        faults.append(kb_pb2.Fault(rule=rules.ACTOR, message="a snapshot records what a named piece of work read"))
    if faults:
        raise Refused(faults)
    return Signed(actor(request), message)


def starter(request: kb_pb2.Actor) -> Actor:
    """The actor who starts a store, who must name a role."""
    if not request.role:
        raise Refused([kb_pb2.Fault(rule=rules.ACTOR, message="a store can only be started under a role")])
    return actor(request)
