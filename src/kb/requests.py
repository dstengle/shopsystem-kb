"""Each rpc's request but the changes (kb.changes) as the values its one domain call takes, built from the
conversions in kb.values. A request that does not convert is refused here, before anything else sees it. Among the
names a snapshot is given, or the changes of a set, an entry that does not convert stands in its place as a Refusal, so
the faults come back in the order of the entries."""
from dataclasses import dataclass
from datetime import datetime

from kb import signatures, values
from kb.contract import kb_pb2
from kb.signatures import Signed
from kb.values import ArtifactId, Kind, Locator, Refused


@dataclass(frozen=True)
class Refusal:
    """An entry that did not convert, and its faults."""
    faults: tuple


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


def reading(request: kb_pb2.ReadRequest) -> Reading:
    """The level asked for, a summary when none is: a whole read's depth, a section read's title."""
    level = request.WhichOneof("level") or "summary"
    return Reading(values.locator(request.locator), level, request.whole.depth, request.section.title)


def history(request: kb_pb2.HistoryRequest) -> JournalFilter:
    """The history's filters; both faults when the artifact and the time both fail."""
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
    kind = values.kind(request.kind) if request.kind else None
    scope = request.scope
    return Searching(kind, request.text, scope != kb_pb2.SearchRequest.FIELDS, scope != kb_pb2.SearchRequest.SECTIONS)


def following(request: kb_pb2.FollowRequest) -> Walk:
    """The walk's start and its narrowing by kind; both faults when both fail."""
    locator, kind, faults = None, None, []
    try:
        locator = values.locator(request.locator)
    except Refused as refused:
        faults += refused.faults
    try:
        kind = values.kind(request.kind) if request.kind else None
    except Refused as refused:
        faults += refused.faults
    if faults:
        raise Refused(faults)
    return Walk(locator, kind, request.depth, request.via, request.direction == kb_pb2.FollowRequest.IN)


def listing(request: kb_pb2.ListRequest) -> Listing:
    return Listing(values.kind(request.kind), dict(request.fields), request.form == kb_pb2.ListRequest.IDS)


def snapshot(request: kb_pb2.SnapshotRequest) -> tuple[list, Signed]:
    """A snapshot request as the domain takes it: the reader's signature first, refused alone when it does not sign;
    the piece of work it records is the signature's; then each name, converted or standing as its refusal."""
    signed = signatures.reader(request.signature)
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
