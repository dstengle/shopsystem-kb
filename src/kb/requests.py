"""Each rpc's request as the values its one domain call takes, built from the conversions in kb.values. A request that
does not convert is refused here, before anything else sees it. In a set, or among the names a snapshot is given, an
entry that does not convert stands in its place as a Refusal, so the faults come back in the order of the entries."""
from dataclasses import dataclass
from datetime import datetime

from kb import names, values
from kb.contract import kb_pb2
from kb.values import Actor, ArtifactId, Content, Kind, Locator, Refused, Root


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
    return values.starter(request.actor), values.root(request.root)


def operations(requested) -> list:
    """Every operation of a set, each converted or standing as its refusal."""
    converted = []
    for operation in requested:
        try:
            converted.append(_operation(operation))
        except Refused as refused:
            converted.append(Refusal(tuple(refused.faults)))
    return converted


def _operation(operation: kb_pb2.Operation):
    which = operation.WhichOneof("operation")
    if which == "create":
        return _create(operation.create)
    if which == "append":
        return Add(values.locator(operation.append.locator), values.item(operation.append.content))
    if which == "delete":
        return Remove(values.locator(operation.delete.locator))
    locator = values.locator(operation.write.locator)
    return Replace(locator, values.content(operation.write.content, at_root=not locator.place))


def _create(creation: kb_pb2.Creation) -> Create:
    kind = values.kind(creation.type)
    try:
        name, title_faults = values.named(kind, creation.title), ()
    except Refused as refused:
        name, title_faults = None, tuple(refused.faults)
    at = names.written(kind.name, names.slug(creation.title))
    return Create(kind, creation.title, name, at, title_faults, values.content(creation.content))


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


def snapshotted(requested) -> list:
    """Each name a snapshot is given, converted or standing as its refusal."""
    converted = []
    for name in requested:
        try:
            converted.append(values.artifact_id(name))
        except Refused as refused:
            converted.append(Refusal(tuple(refused.faults)))
    return converted
