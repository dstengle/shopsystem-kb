"""Each rpc's request as the values its one domain call takes, built from the conversions in kb.values. A request that
does not convert is refused here, before anything else sees it. In a set, or among the names a snapshot is given, an
entry that does not convert stands in its place as a Refusal, so the faults come back in the order of the entries."""
from dataclasses import dataclass
from datetime import datetime

from kb import rules, signatures, values
from kb.contract import kb_pb2
from kb.signatures import Actor, Signed
from kb.values import ArtifactId, Content, Kind, Locator, Refused, Root


@dataclass(frozen=True)
class Refusal:
    """An entry that did not convert, and its faults."""
    faults: tuple


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


@dataclass(frozen=True)
class Reading:
    locator: Locator
    level: str
    depth: int
    section: str


@dataclass(frozen=True)
class JournalFilter:
    artifact: ArtifactId | None
    role: str
    execution: str
    since: datetime | None
    batch: str


@dataclass(frozen=True)
class Searching:
    kind: Kind | None
    text: str
    sections: bool
    fields: bool


@dataclass(frozen=True)
class Walk:
    locator: Locator
    kind: Kind | None
    depth: int
    via: str
    inward: bool


@dataclass(frozen=True)
class Listing:
    kind: Kind
    fields: dict
    ids: bool


def starting(request: kb_pb2.InitRequest) -> tuple[Actor, Root]:
    """Who starts a store, then where; the first refusal only."""
    return signatures.starter(request.actor), values.root(request.root)


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


def reading(request: kb_pb2.ReadRequest) -> Reading:
    level = {kb_pb2.ReadRequest.WHOLE: "whole", kb_pb2.ReadRequest.SECTION: "section"}.get(request.level, "summary")
    return Reading(values.locator(request.locator), level, request.depth, request.section)


def journal(request: kb_pb2.JournalRequest) -> JournalFilter:
    """The journal's filters; both faults when the artifact and the time both fail."""
    artifact, since, faults = None, None, []
    try:
        artifact = values.artifact_id(request.artifact) if request.artifact else None
    except Refused as refused:
        faults += refused.faults
    try:
        since = values.since(request.since) if request.since else None
    except Refused as refused:
        faults += refused.faults
    if faults:
        raise Refused(faults)
    return JournalFilter(artifact, request.role, request.execution, since, request.batch)


def searching(request: kb_pb2.SearchRequest) -> Searching:
    kind = values.kind(request.type) if request.type else None
    scope = request.scope
    return Searching(kind, request.text, scope != kb_pb2.SearchRequest.FIELDS, scope != kb_pb2.SearchRequest.SECTIONS)


def walk(request: kb_pb2.RefsRequest) -> Walk:
    """The walk's start and its narrowing by type; both faults when both fail."""
    locator, kind, faults = None, None, []
    try:
        locator = values.locator(request.locator)
    except Refused as refused:
        faults += refused.faults
    try:
        kind = values.kind(request.type) if request.type else None
    except Refused as refused:
        faults += refused.faults
    if faults:
        raise Refused(faults)
    return Walk(locator, kind, request.depth, request.via, request.direction == kb_pb2.RefsRequest.IN)


def listing(request: kb_pb2.ListRequest) -> Listing:
    return Listing(values.kind(request.type), dict(request.fields), request.form == kb_pb2.ListRequest.IDS)


def snapshot(request: kb_pb2.SnapshotRequest) -> tuple[list, Signed]:
    """A snapshot request as the domain takes it: the reader's signature first, refused alone when it does not sign;
    then each name, converted or standing as its refusal."""
    signed = signatures.reader(_signature(request.actor, request.message))
    return _names(request.artifacts), signed


def _names(requested) -> list:
    """Each name a snapshot is given, converted or standing as its refusal."""
    converted = []
    for name in requested:
        try:
            converted.append(values.artifact_id(name))
        except Refused as refused:
            converted.append(Refusal(tuple(refused.faults)))
    return converted
