"""Each rpc's request but the changes (kb.changes) as the values its one domain call takes, built from the
conversions in kb.values. A request that does not convert is refused here, before anything else sees it. Among the
names a snapshot is given, an entry that does not convert stands in its place as a Refusal, so
the faults come back in the order of the entries."""
from dataclasses import dataclass
from datetime import datetime

from kb import signatures, values
from kb.contract import kb_pb2
from kb.signatures import Signed
from kb.values import ArtifactId, Below, Kind, Locator, Refused


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
    version: values.Version | None = None


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
    path: Below | None = None


@dataclass(frozen=True)
class Listing:
    kind: Kind | None
    fields: dict
    ids: bool
    path: Below | None = None


def reading(request: kb_pb2.ReadRequest) -> Reading:
    """The level asked for, a summary when none is: a whole read's depth, a section read's title. A locator naming a
    type's version is a read of that version, its locator the type's."""
    level = request.WhichOneof("level") or "summary"
    locator, version = values.read(request.locator)
    return Reading(locator, level, request.whole.depth, request.section.title, version)


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
    """The walk's start and its narrowing by kind and by a path below the type, each when given; every fault when
    more than one fails."""
    faults = []
    locator = _converted(values.locator, request.locator, faults, always=True)
    kind = _converted(values.kind, request.kind, faults)
    path = _converted(values.below, request.path, faults)
    if faults:
        raise Refused(faults)
    return Walk(locator, kind, request.depth, request.via, request.direction == kb_pb2.FollowRequest.IN, path)


def listing(request: kb_pb2.ListRequest) -> Listing:
    """The list's kind, taken when one is given or no path is, so a list by neither is refused for its kind, and its
    path below the type when one is given; both faults when both fail."""
    faults = []
    kind = _converted(values.kind, request.kind, faults, always=not request.path)
    path = _converted(values.below, request.path, faults)
    if faults:
        raise Refused(faults)
    return Listing(kind, dict(request.fields), request.form == kb_pb2.ListRequest.IDS, path)


def _converted(convert, text: str, faults: list, always: bool = False):
    """A request's text converted when it is given, or always; None when it is not, or when it does not convert,
    its faults then added to those given."""
    if not (text or always):
        return None
    try:
        return convert(text)
    except Refused as refused:
        faults += refused.faults
        return None


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
