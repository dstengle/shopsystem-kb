"""Each change's request, alone or in a set, as the values its one domain call takes, built from the conversions in
kb.values and kb.signatures: who makes it and why first, refused alone when it does not say; then each change,
converted or standing in its place as a Refusal, so the faults come back in the order of the changes."""
from dataclasses import dataclass

from kb import rules, signatures, values
from kb.contract import kb_pb2
from kb.requests import Refusal
from kb.signatures import Signed
from kb.values import ArtifactId, Content, Kind, Locator, Refused


@dataclass(frozen=True)
class Create:
    """A new artifact: its kind, its title, the name the title gives (None when it gives none, the title's faults
    saying why), the name its faults are said of until it has one, and its content."""
    kind: Kind
    title: str
    name: ArtifactId | None
    at: str
    title_faults: tuple
    content: Content


@dataclass(frozen=True)
class Replace:
    locator: Locator
    content: Content


@dataclass(frozen=True)
class Add:
    locator: Locator
    item: Content


@dataclass(frozen=True)
class Remove:
    locator: Locator


def _signature(actor: kb_pb2.Actor, message: str) -> kb_pb2.Signature:
    """An actor and a message, as a request that still carries them apart gives them, read as one signature."""
    return kb_pb2.Signature(role=actor.role, execution=actor.execution, message=message)


def change(requested, actor: kb_pb2.Actor, message: str) -> tuple[list, Signed]:
    """A set request as the domain takes it: who makes it and why first, refused alone when it does not say; then
    a set holding nothing is refused; then each operation, converted or standing as its refusal."""
    signed = signatures.signed(_signature(actor, message))
    if not requested:
        raise Refused([kb_pb2.Fault(rule=rules.OPERATIONS, message="a set must hold at least one change")])
    return operations(requested), signed


def creating(request: kb_pb2.CreateRequest) -> tuple[list, Signed]:
    """A Create as the domain takes it: a set of one, signed."""
    return _one(request.signature, lambda: _create(request.kind, request.title, request.content))


def replacing(request: kb_pb2.ReplaceRequest) -> tuple[list, Signed]:
    """A Replace as the domain takes it: a set of one, signed."""
    return _one(request.signature, lambda: _replace(request.locator, request.content))


def adding(request: kb_pb2.AddRequest) -> tuple[list, Signed]:
    """An Add as the domain takes it: a set of one, signed."""
    return _one(request.signature, lambda: _add(request.locator, request.content))


def removing(request: kb_pb2.RemoveRequest) -> tuple[list, Signed]:
    """A Remove as the domain takes it: a set of one, signed."""
    return _one(request.signature, lambda: _remove(request.locator))


def _one(signature: kb_pb2.Signature, convert) -> tuple[list, Signed]:
    """One change: who makes it and why first, refused alone when it does not say; then the change, converted or
    standing as its refusal."""
    signed = signatures.signed(signature)
    return _each([convert]), signed


def operations(requested) -> list:
    """Every operation of a set, each converted or standing as its refusal."""
    return _each([lambda operation=operation: _operation(operation) for operation in requested])


def _each(conversions) -> list:
    """Each conversion's change, or its refusal in its place."""
    converted = []
    for convert in conversions:
        try:
            converted.append(convert())
        except Refused as refused:
            converted.append(Refusal(tuple(refused.faults)))
    return converted


def _operation(operation: kb_pb2.Operation):
    which = operation.WhichOneof("operation")
    if which == "create":
        return _create(operation.create.type, operation.create.title, operation.create.content)
    if which == "append":
        return _add(operation.append.locator, operation.append.content)
    if which == "delete":
        return _remove(operation.delete.locator)
    return _replace(operation.write.locator, operation.write.content)


def _create(kind_name: str, title: str, content: str) -> Create:
    kind = values.kind(kind_name)
    name, at, title_faults = values.named(kind, title)
    return Create(kind, title, name, at, title_faults, values.content(content))


def _replace(requested: kb_pb2.Locator, content: str) -> Replace:
    locator = values.locator(requested)
    return Replace(locator, values.content(content, at_root=not locator.place))


def _add(requested: kb_pb2.Locator, content: str) -> Add:
    return Add(values.locator(requested), values.item(content))


def _remove(requested: kb_pb2.Locator) -> Remove:
    return Remove(values.locator(requested))
