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


def actor(signature: kb_pb2.Signature) -> Actor:
    return Actor(signature.role, signature.execution)


def _entry(reason: str) -> str:
    return f"every entry in the history {reason}"


def _unsigned(signature: kb_pb2.Signature) -> list[kb_pb2.Fault]:
    faults = []
    if not signature.role.strip():
        faults.append(kb_pb2.Fault(rule=rules.ACTOR, message=_entry("names the role that made it")))
    if not signature.message.strip():
        faults.append(kb_pb2.Fault(rule=rules.MESSAGE, message=_entry("says why it was made")))
    return faults


def signed(signature: kb_pb2.Signature) -> Signed:
    """Who makes a change and why, who must name a role and a message; both faults when both fail."""
    faults = _unsigned(signature)
    if faults:
        raise Refused(faults)
    return Signed(actor(signature), signature.message)


def reader(signature: kb_pb2.Signature) -> Signed:
    """Who records what a piece of work read, who must sign and name the piece of work; every fault found."""
    faults = _unsigned(signature)
    if not signature.execution:
        faults.append(kb_pb2.Fault(rule=rules.ACTOR, message="a snapshot records what a named piece of work read"))
    if faults:
        raise Refused(faults)
    return Signed(actor(signature), signature.message)


def starter(role: str, execution: str) -> Actor:
    """The actor who starts a store, as `kb.init` is given it, who must name a role; role and execution are text."""
    if not isinstance(role, str) or not isinstance(execution, str) or not role:
        raise Refused([kb_pb2.Fault(rule=rules.ACTOR, message="a store can only be started under a role")])
    return Actor(role, execution)
