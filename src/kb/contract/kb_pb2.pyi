from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Actor(_message.Message):
    __slots__ = ("role", "execution")
    ROLE_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_FIELD_NUMBER: _ClassVar[int]
    role: str
    execution: str
    def __init__(self, role: _Optional[str] = ..., execution: _Optional[str] = ...) -> None: ...

class Signature(_message.Message):
    __slots__ = ("role", "execution", "message")
    ROLE_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    role: str
    execution: str
    message: str
    def __init__(self, role: _Optional[str] = ..., execution: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

class Locator(_message.Message):
    __slots__ = ("id", "place")
    ID_FIELD_NUMBER: _ClassVar[int]
    PLACE_FIELD_NUMBER: _ClassVar[int]
    id: str
    place: str
    def __init__(self, id: _Optional[str] = ..., place: _Optional[str] = ...) -> None: ...

class Fault(_message.Message):
    __slots__ = ("artifact", "place", "rule", "message")
    ARTIFACT_FIELD_NUMBER: _ClassVar[int]
    PLACE_FIELD_NUMBER: _ClassVar[int]
    RULE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    artifact: str
    place: str
    rule: str
    message: str
    def __init__(self, artifact: _Optional[str] = ..., place: _Optional[str] = ..., rule: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

class Refusal(_message.Message):
    __slots__ = ("faults",)
    FAULTS_FIELD_NUMBER: _ClassVar[int]
    faults: _containers.RepeatedCompositeFieldContainer[Fault]
    def __init__(self, faults: _Optional[_Iterable[_Union[Fault, _Mapping]]] = ...) -> None: ...

class InitRequest(_message.Message):
    __slots__ = ("root", "actor")
    ROOT_FIELD_NUMBER: _ClassVar[int]
    ACTOR_FIELD_NUMBER: _ClassVar[int]
    root: str
    actor: Actor
    def __init__(self, root: _Optional[str] = ..., actor: _Optional[_Union[Actor, _Mapping]] = ...) -> None: ...

class InitResponse(_message.Message):
    __slots__ = ("faults",)
    FAULTS_FIELD_NUMBER: _ClassVar[int]
    faults: _containers.RepeatedCompositeFieldContainer[Fault]
    def __init__(self, faults: _Optional[_Iterable[_Union[Fault, _Mapping]]] = ...) -> None: ...

class CreateRequest(_message.Message):
    __slots__ = ("kind", "title", "content", "signature")
    KIND_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    SIGNATURE_FIELD_NUMBER: _ClassVar[int]
    kind: str
    title: str
    content: str
    signature: Signature
    def __init__(self, kind: _Optional[str] = ..., title: _Optional[str] = ..., content: _Optional[str] = ..., signature: _Optional[_Union[Signature, _Mapping]] = ...) -> None: ...

class Created(_message.Message):
    __slots__ = ("id", "revision")
    ID_FIELD_NUMBER: _ClassVar[int]
    REVISION_FIELD_NUMBER: _ClassVar[int]
    id: str
    revision: int
    def __init__(self, id: _Optional[str] = ..., revision: _Optional[int] = ...) -> None: ...

class CreateResponse(_message.Message):
    __slots__ = ("result", "refusal")
    RESULT_FIELD_NUMBER: _ClassVar[int]
    REFUSAL_FIELD_NUMBER: _ClassVar[int]
    result: Created
    refusal: Refusal
    def __init__(self, result: _Optional[_Union[Created, _Mapping]] = ..., refusal: _Optional[_Union[Refusal, _Mapping]] = ...) -> None: ...

class ReadRequest(_message.Message):
    __slots__ = ("locator", "level", "depth", "section")
    class Level(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        SUMMARY: _ClassVar[ReadRequest.Level]
        WHOLE: _ClassVar[ReadRequest.Level]
        SECTION: _ClassVar[ReadRequest.Level]
    SUMMARY: ReadRequest.Level
    WHOLE: ReadRequest.Level
    SECTION: ReadRequest.Level
    LOCATOR_FIELD_NUMBER: _ClassVar[int]
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    DEPTH_FIELD_NUMBER: _ClassVar[int]
    SECTION_FIELD_NUMBER: _ClassVar[int]
    locator: Locator
    level: ReadRequest.Level
    depth: int
    section: str
    def __init__(self, locator: _Optional[_Union[Locator, _Mapping]] = ..., level: _Optional[_Union[ReadRequest.Level, str]] = ..., depth: _Optional[int] = ..., section: _Optional[str] = ...) -> None: ...

class ReadResponse(_message.Message):
    __slots__ = ("id", "type", "schema_version", "revision", "title", "content", "references", "parts", "inbound", "faults")
    ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_VERSION_FIELD_NUMBER: _ClassVar[int]
    REVISION_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    REFERENCES_FIELD_NUMBER: _ClassVar[int]
    PARTS_FIELD_NUMBER: _ClassVar[int]
    INBOUND_FIELD_NUMBER: _ClassVar[int]
    FAULTS_FIELD_NUMBER: _ClassVar[int]
    id: str
    type: str
    schema_version: int
    revision: int
    title: str
    content: str
    references: _containers.RepeatedCompositeFieldContainer[Stub]
    parts: _containers.RepeatedCompositeFieldContainer[PartStub]
    inbound: _containers.RepeatedCompositeFieldContainer[InboundCount]
    faults: _containers.RepeatedCompositeFieldContainer[Fault]
    def __init__(self, id: _Optional[str] = ..., type: _Optional[str] = ..., schema_version: _Optional[int] = ..., revision: _Optional[int] = ..., title: _Optional[str] = ..., content: _Optional[str] = ..., references: _Optional[_Iterable[_Union[Stub, _Mapping]]] = ..., parts: _Optional[_Iterable[_Union[PartStub, _Mapping]]] = ..., inbound: _Optional[_Iterable[_Union[InboundCount, _Mapping]]] = ..., faults: _Optional[_Iterable[_Union[Fault, _Mapping]]] = ...) -> None: ...

class Stub(_message.Message):
    __slots__ = ("field", "id", "kind", "title", "fields")
    FIELD_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    KIND_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    field: str
    id: str
    kind: str
    title: str
    fields: str
    def __init__(self, field: _Optional[str] = ..., id: _Optional[str] = ..., kind: _Optional[str] = ..., title: _Optional[str] = ..., fields: _Optional[str] = ...) -> None: ...

class PartStub(_message.Message):
    __slots__ = ("collection", "id", "title")
    COLLECTION_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    collection: str
    id: str
    title: str
    def __init__(self, collection: _Optional[str] = ..., id: _Optional[str] = ..., title: _Optional[str] = ...) -> None: ...

class InboundCount(_message.Message):
    __slots__ = ("kind", "field", "count")
    KIND_FIELD_NUMBER: _ClassVar[int]
    FIELD_FIELD_NUMBER: _ClassVar[int]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    kind: str
    field: str
    count: int
    def __init__(self, kind: _Optional[str] = ..., field: _Optional[str] = ..., count: _Optional[int] = ...) -> None: ...

class ValidateRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ValidateResponse(_message.Message):
    __slots__ = ("violations", "faults", "stale")
    VIOLATIONS_FIELD_NUMBER: _ClassVar[int]
    FAULTS_FIELD_NUMBER: _ClassVar[int]
    STALE_FIELD_NUMBER: _ClassVar[int]
    violations: _containers.RepeatedCompositeFieldContainer[Fault]
    faults: _containers.RepeatedCompositeFieldContainer[Fault]
    stale: _containers.RepeatedCompositeFieldContainer[Stale]
    def __init__(self, violations: _Optional[_Iterable[_Union[Fault, _Mapping]]] = ..., faults: _Optional[_Iterable[_Union[Fault, _Mapping]]] = ..., stale: _Optional[_Iterable[_Union[Stale, _Mapping]]] = ...) -> None: ...

class Stale(_message.Message):
    __slots__ = ("artifact", "schema_version", "current")
    ARTIFACT_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_VERSION_FIELD_NUMBER: _ClassVar[int]
    CURRENT_FIELD_NUMBER: _ClassVar[int]
    artifact: str
    schema_version: int
    current: int
    def __init__(self, artifact: _Optional[str] = ..., schema_version: _Optional[int] = ..., current: _Optional[int] = ...) -> None: ...

class ReplaceRequest(_message.Message):
    __slots__ = ("locator", "content", "signature", "revision")
    LOCATOR_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    SIGNATURE_FIELD_NUMBER: _ClassVar[int]
    REVISION_FIELD_NUMBER: _ClassVar[int]
    locator: Locator
    content: str
    signature: Signature
    revision: int
    def __init__(self, locator: _Optional[_Union[Locator, _Mapping]] = ..., content: _Optional[str] = ..., signature: _Optional[_Union[Signature, _Mapping]] = ..., revision: _Optional[int] = ...) -> None: ...

class Replaced(_message.Message):
    __slots__ = ("revision", "id")
    REVISION_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    revision: int
    id: str
    def __init__(self, revision: _Optional[int] = ..., id: _Optional[str] = ...) -> None: ...

class ReplaceResponse(_message.Message):
    __slots__ = ("result", "refusal")
    RESULT_FIELD_NUMBER: _ClassVar[int]
    REFUSAL_FIELD_NUMBER: _ClassVar[int]
    result: Replaced
    refusal: Refusal
    def __init__(self, result: _Optional[_Union[Replaced, _Mapping]] = ..., refusal: _Optional[_Union[Refusal, _Mapping]] = ...) -> None: ...

class JournalRequest(_message.Message):
    __slots__ = ("artifact", "role", "execution", "since", "batch")
    ARTIFACT_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_FIELD_NUMBER: _ClassVar[int]
    SINCE_FIELD_NUMBER: _ClassVar[int]
    BATCH_FIELD_NUMBER: _ClassVar[int]
    artifact: str
    role: str
    execution: str
    since: str
    batch: str
    def __init__(self, artifact: _Optional[str] = ..., role: _Optional[str] = ..., execution: _Optional[str] = ..., since: _Optional[str] = ..., batch: _Optional[str] = ...) -> None: ...

class Entry(_message.Message):
    __slots__ = ("id", "at", "actor", "op", "artifact", "place", "revision", "schema_version", "digest", "message", "batch", "read")
    ID_FIELD_NUMBER: _ClassVar[int]
    AT_FIELD_NUMBER: _ClassVar[int]
    ACTOR_FIELD_NUMBER: _ClassVar[int]
    OP_FIELD_NUMBER: _ClassVar[int]
    ARTIFACT_FIELD_NUMBER: _ClassVar[int]
    PLACE_FIELD_NUMBER: _ClassVar[int]
    REVISION_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_VERSION_FIELD_NUMBER: _ClassVar[int]
    DIGEST_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    BATCH_FIELD_NUMBER: _ClassVar[int]
    READ_FIELD_NUMBER: _ClassVar[int]
    id: str
    at: str
    actor: Actor
    op: str
    artifact: str
    place: str
    revision: int
    schema_version: int
    digest: str
    message: str
    batch: str
    read: _containers.RepeatedCompositeFieldContainer[Snapshotted]
    def __init__(self, id: _Optional[str] = ..., at: _Optional[str] = ..., actor: _Optional[_Union[Actor, _Mapping]] = ..., op: _Optional[str] = ..., artifact: _Optional[str] = ..., place: _Optional[str] = ..., revision: _Optional[int] = ..., schema_version: _Optional[int] = ..., digest: _Optional[str] = ..., message: _Optional[str] = ..., batch: _Optional[str] = ..., read: _Optional[_Iterable[_Union[Snapshotted, _Mapping]]] = ...) -> None: ...

class Snapshotted(_message.Message):
    __slots__ = ("artifact", "revision", "digest")
    ARTIFACT_FIELD_NUMBER: _ClassVar[int]
    REVISION_FIELD_NUMBER: _ClassVar[int]
    DIGEST_FIELD_NUMBER: _ClassVar[int]
    artifact: str
    revision: int
    digest: str
    def __init__(self, artifact: _Optional[str] = ..., revision: _Optional[int] = ..., digest: _Optional[str] = ...) -> None: ...

class JournalResponse(_message.Message):
    __slots__ = ("entries", "faults")
    ENTRIES_FIELD_NUMBER: _ClassVar[int]
    FAULTS_FIELD_NUMBER: _ClassVar[int]
    entries: _containers.RepeatedCompositeFieldContainer[Entry]
    faults: _containers.RepeatedCompositeFieldContainer[Fault]
    def __init__(self, entries: _Optional[_Iterable[_Union[Entry, _Mapping]]] = ..., faults: _Optional[_Iterable[_Union[Fault, _Mapping]]] = ...) -> None: ...

class SearchRequest(_message.Message):
    __slots__ = ("text", "type", "scope")
    class Scope(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        SECTIONS: _ClassVar[SearchRequest.Scope]
        FIELDS: _ClassVar[SearchRequest.Scope]
        ALL: _ClassVar[SearchRequest.Scope]
    SECTIONS: SearchRequest.Scope
    FIELDS: SearchRequest.Scope
    ALL: SearchRequest.Scope
    TEXT_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    text: str
    type: str
    scope: SearchRequest.Scope
    def __init__(self, text: _Optional[str] = ..., type: _Optional[str] = ..., scope: _Optional[_Union[SearchRequest.Scope, str]] = ...) -> None: ...

class Match(_message.Message):
    __slots__ = ("stub", "section", "snippet", "field")
    STUB_FIELD_NUMBER: _ClassVar[int]
    SECTION_FIELD_NUMBER: _ClassVar[int]
    SNIPPET_FIELD_NUMBER: _ClassVar[int]
    FIELD_FIELD_NUMBER: _ClassVar[int]
    stub: Stub
    section: str
    snippet: str
    field: str
    def __init__(self, stub: _Optional[_Union[Stub, _Mapping]] = ..., section: _Optional[str] = ..., snippet: _Optional[str] = ..., field: _Optional[str] = ...) -> None: ...

class SearchResponse(_message.Message):
    __slots__ = ("matches", "faults")
    MATCHES_FIELD_NUMBER: _ClassVar[int]
    FAULTS_FIELD_NUMBER: _ClassVar[int]
    matches: _containers.RepeatedCompositeFieldContainer[Match]
    faults: _containers.RepeatedCompositeFieldContainer[Fault]
    def __init__(self, matches: _Optional[_Iterable[_Union[Match, _Mapping]]] = ..., faults: _Optional[_Iterable[_Union[Fault, _Mapping]]] = ...) -> None: ...

class RefsRequest(_message.Message):
    __slots__ = ("locator", "depth", "direction", "via", "type")
    class Direction(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        OUT: _ClassVar[RefsRequest.Direction]
        IN: _ClassVar[RefsRequest.Direction]
    OUT: RefsRequest.Direction
    IN: RefsRequest.Direction
    LOCATOR_FIELD_NUMBER: _ClassVar[int]
    DEPTH_FIELD_NUMBER: _ClassVar[int]
    DIRECTION_FIELD_NUMBER: _ClassVar[int]
    VIA_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    locator: Locator
    depth: int
    direction: RefsRequest.Direction
    via: str
    type: str
    def __init__(self, locator: _Optional[_Union[Locator, _Mapping]] = ..., depth: _Optional[int] = ..., direction: _Optional[_Union[RefsRequest.Direction, str]] = ..., via: _Optional[str] = ..., type: _Optional[str] = ...) -> None: ...

class Hop(_message.Message):
    __slots__ = ("field", "id")
    FIELD_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    field: str
    id: str
    def __init__(self, field: _Optional[str] = ..., id: _Optional[str] = ...) -> None: ...

class Reached(_message.Message):
    __slots__ = ("stub", "route")
    STUB_FIELD_NUMBER: _ClassVar[int]
    ROUTE_FIELD_NUMBER: _ClassVar[int]
    stub: Stub
    route: _containers.RepeatedCompositeFieldContainer[Hop]
    def __init__(self, stub: _Optional[_Union[Stub, _Mapping]] = ..., route: _Optional[_Iterable[_Union[Hop, _Mapping]]] = ...) -> None: ...

class RefsResponse(_message.Message):
    __slots__ = ("reached", "faults")
    REACHED_FIELD_NUMBER: _ClassVar[int]
    FAULTS_FIELD_NUMBER: _ClassVar[int]
    reached: _containers.RepeatedCompositeFieldContainer[Reached]
    faults: _containers.RepeatedCompositeFieldContainer[Fault]
    def __init__(self, reached: _Optional[_Iterable[_Union[Reached, _Mapping]]] = ..., faults: _Optional[_Iterable[_Union[Fault, _Mapping]]] = ...) -> None: ...

class ListRequest(_message.Message):
    __slots__ = ("type", "fields", "form")
    class Form(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        STUBS: _ClassVar[ListRequest.Form]
        IDS: _ClassVar[ListRequest.Form]
    STUBS: ListRequest.Form
    IDS: ListRequest.Form
    class FieldsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    TYPE_FIELD_NUMBER: _ClassVar[int]
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    FORM_FIELD_NUMBER: _ClassVar[int]
    type: str
    fields: _containers.ScalarMap[str, str]
    form: ListRequest.Form
    def __init__(self, type: _Optional[str] = ..., fields: _Optional[_Mapping[str, str]] = ..., form: _Optional[_Union[ListRequest.Form, str]] = ...) -> None: ...

class ListResponse(_message.Message):
    __slots__ = ("stubs", "ids", "faults")
    STUBS_FIELD_NUMBER: _ClassVar[int]
    IDS_FIELD_NUMBER: _ClassVar[int]
    FAULTS_FIELD_NUMBER: _ClassVar[int]
    stubs: _containers.RepeatedCompositeFieldContainer[Stub]
    ids: _containers.RepeatedScalarFieldContainer[str]
    faults: _containers.RepeatedCompositeFieldContainer[Fault]
    def __init__(self, stubs: _Optional[_Iterable[_Union[Stub, _Mapping]]] = ..., ids: _Optional[_Iterable[str]] = ..., faults: _Optional[_Iterable[_Union[Fault, _Mapping]]] = ...) -> None: ...

class SnapshotRequest(_message.Message):
    __slots__ = ("actor", "artifacts", "message")
    ACTOR_FIELD_NUMBER: _ClassVar[int]
    ARTIFACTS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    actor: Actor
    artifacts: _containers.RepeatedScalarFieldContainer[str]
    message: str
    def __init__(self, actor: _Optional[_Union[Actor, _Mapping]] = ..., artifacts: _Optional[_Iterable[str]] = ..., message: _Optional[str] = ...) -> None: ...

class SnapshotResponse(_message.Message):
    __slots__ = ("entry", "faults")
    ENTRY_FIELD_NUMBER: _ClassVar[int]
    FAULTS_FIELD_NUMBER: _ClassVar[int]
    entry: str
    faults: _containers.RepeatedCompositeFieldContainer[Fault]
    def __init__(self, entry: _Optional[str] = ..., faults: _Optional[_Iterable[_Union[Fault, _Mapping]]] = ...) -> None: ...

class AddRequest(_message.Message):
    __slots__ = ("locator", "content", "signature", "revision")
    LOCATOR_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    SIGNATURE_FIELD_NUMBER: _ClassVar[int]
    REVISION_FIELD_NUMBER: _ClassVar[int]
    locator: Locator
    content: str
    signature: Signature
    revision: int
    def __init__(self, locator: _Optional[_Union[Locator, _Mapping]] = ..., content: _Optional[str] = ..., signature: _Optional[_Union[Signature, _Mapping]] = ..., revision: _Optional[int] = ...) -> None: ...

class Added(_message.Message):
    __slots__ = ("id", "revision", "artifact")
    ID_FIELD_NUMBER: _ClassVar[int]
    REVISION_FIELD_NUMBER: _ClassVar[int]
    ARTIFACT_FIELD_NUMBER: _ClassVar[int]
    id: str
    revision: int
    artifact: str
    def __init__(self, id: _Optional[str] = ..., revision: _Optional[int] = ..., artifact: _Optional[str] = ...) -> None: ...

class AddResponse(_message.Message):
    __slots__ = ("result", "refusal")
    RESULT_FIELD_NUMBER: _ClassVar[int]
    REFUSAL_FIELD_NUMBER: _ClassVar[int]
    result: Added
    refusal: Refusal
    def __init__(self, result: _Optional[_Union[Added, _Mapping]] = ..., refusal: _Optional[_Union[Refusal, _Mapping]] = ...) -> None: ...

class RemoveRequest(_message.Message):
    __slots__ = ("locator", "signature", "revision")
    LOCATOR_FIELD_NUMBER: _ClassVar[int]
    SIGNATURE_FIELD_NUMBER: _ClassVar[int]
    REVISION_FIELD_NUMBER: _ClassVar[int]
    locator: Locator
    signature: Signature
    revision: int
    def __init__(self, locator: _Optional[_Union[Locator, _Mapping]] = ..., signature: _Optional[_Union[Signature, _Mapping]] = ..., revision: _Optional[int] = ...) -> None: ...

class Removed(_message.Message):
    __slots__ = ("revision", "id")
    REVISION_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    revision: int
    id: str
    def __init__(self, revision: _Optional[int] = ..., id: _Optional[str] = ...) -> None: ...

class RemoveResponse(_message.Message):
    __slots__ = ("result", "refusal")
    RESULT_FIELD_NUMBER: _ClassVar[int]
    REFUSAL_FIELD_NUMBER: _ClassVar[int]
    result: Removed
    refusal: Refusal
    def __init__(self, result: _Optional[_Union[Removed, _Mapping]] = ..., refusal: _Optional[_Union[Refusal, _Mapping]] = ...) -> None: ...

class CreateItem(_message.Message):
    __slots__ = ("kind", "title", "content", "key")
    KIND_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    kind: str
    title: str
    content: str
    key: str
    def __init__(self, kind: _Optional[str] = ..., title: _Optional[str] = ..., content: _Optional[str] = ..., key: _Optional[str] = ...) -> None: ...

class CreateManyRequest(_message.Message):
    __slots__ = ("items", "signature")
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    SIGNATURE_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[CreateItem]
    signature: Signature
    def __init__(self, items: _Optional[_Iterable[_Union[CreateItem, _Mapping]]] = ..., signature: _Optional[_Union[Signature, _Mapping]] = ...) -> None: ...

class CreatedMany(_message.Message):
    __slots__ = ("batch", "results")
    BATCH_FIELD_NUMBER: _ClassVar[int]
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    batch: str
    results: _containers.RepeatedCompositeFieldContainer[Created]
    def __init__(self, batch: _Optional[str] = ..., results: _Optional[_Iterable[_Union[Created, _Mapping]]] = ...) -> None: ...

class CreateManyResponse(_message.Message):
    __slots__ = ("result", "refusal")
    RESULT_FIELD_NUMBER: _ClassVar[int]
    REFUSAL_FIELD_NUMBER: _ClassVar[int]
    result: CreatedMany
    refusal: Refusal
    def __init__(self, result: _Optional[_Union[CreatedMany, _Mapping]] = ..., refusal: _Optional[_Union[Refusal, _Mapping]] = ...) -> None: ...

class ReplaceItem(_message.Message):
    __slots__ = ("locator", "content", "revision")
    LOCATOR_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    REVISION_FIELD_NUMBER: _ClassVar[int]
    locator: Locator
    content: str
    revision: int
    def __init__(self, locator: _Optional[_Union[Locator, _Mapping]] = ..., content: _Optional[str] = ..., revision: _Optional[int] = ...) -> None: ...

class ReplaceManyRequest(_message.Message):
    __slots__ = ("items", "signature")
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    SIGNATURE_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[ReplaceItem]
    signature: Signature
    def __init__(self, items: _Optional[_Iterable[_Union[ReplaceItem, _Mapping]]] = ..., signature: _Optional[_Union[Signature, _Mapping]] = ...) -> None: ...

class ReplacedMany(_message.Message):
    __slots__ = ("batch", "results")
    BATCH_FIELD_NUMBER: _ClassVar[int]
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    batch: str
    results: _containers.RepeatedCompositeFieldContainer[Replaced]
    def __init__(self, batch: _Optional[str] = ..., results: _Optional[_Iterable[_Union[Replaced, _Mapping]]] = ...) -> None: ...

class ReplaceManyResponse(_message.Message):
    __slots__ = ("result", "refusal")
    RESULT_FIELD_NUMBER: _ClassVar[int]
    REFUSAL_FIELD_NUMBER: _ClassVar[int]
    result: ReplacedMany
    refusal: Refusal
    def __init__(self, result: _Optional[_Union[ReplacedMany, _Mapping]] = ..., refusal: _Optional[_Union[Refusal, _Mapping]] = ...) -> None: ...

class AddItem(_message.Message):
    __slots__ = ("locator", "content", "revision")
    LOCATOR_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    REVISION_FIELD_NUMBER: _ClassVar[int]
    locator: Locator
    content: str
    revision: int
    def __init__(self, locator: _Optional[_Union[Locator, _Mapping]] = ..., content: _Optional[str] = ..., revision: _Optional[int] = ...) -> None: ...

class AddManyRequest(_message.Message):
    __slots__ = ("items", "signature")
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    SIGNATURE_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[AddItem]
    signature: Signature
    def __init__(self, items: _Optional[_Iterable[_Union[AddItem, _Mapping]]] = ..., signature: _Optional[_Union[Signature, _Mapping]] = ...) -> None: ...

class AddedMany(_message.Message):
    __slots__ = ("batch", "results")
    BATCH_FIELD_NUMBER: _ClassVar[int]
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    batch: str
    results: _containers.RepeatedCompositeFieldContainer[Added]
    def __init__(self, batch: _Optional[str] = ..., results: _Optional[_Iterable[_Union[Added, _Mapping]]] = ...) -> None: ...

class AddManyResponse(_message.Message):
    __slots__ = ("result", "refusal")
    RESULT_FIELD_NUMBER: _ClassVar[int]
    REFUSAL_FIELD_NUMBER: _ClassVar[int]
    result: AddedMany
    refusal: Refusal
    def __init__(self, result: _Optional[_Union[AddedMany, _Mapping]] = ..., refusal: _Optional[_Union[Refusal, _Mapping]] = ...) -> None: ...

class RemoveItem(_message.Message):
    __slots__ = ("locator", "revision")
    LOCATOR_FIELD_NUMBER: _ClassVar[int]
    REVISION_FIELD_NUMBER: _ClassVar[int]
    locator: Locator
    revision: int
    def __init__(self, locator: _Optional[_Union[Locator, _Mapping]] = ..., revision: _Optional[int] = ...) -> None: ...

class RemoveManyRequest(_message.Message):
    __slots__ = ("items", "signature")
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    SIGNATURE_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[RemoveItem]
    signature: Signature
    def __init__(self, items: _Optional[_Iterable[_Union[RemoveItem, _Mapping]]] = ..., signature: _Optional[_Union[Signature, _Mapping]] = ...) -> None: ...

class RemovedMany(_message.Message):
    __slots__ = ("batch", "results")
    BATCH_FIELD_NUMBER: _ClassVar[int]
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    batch: str
    results: _containers.RepeatedCompositeFieldContainer[Removed]
    def __init__(self, batch: _Optional[str] = ..., results: _Optional[_Iterable[_Union[Removed, _Mapping]]] = ...) -> None: ...

class RemoveManyResponse(_message.Message):
    __slots__ = ("result", "refusal")
    RESULT_FIELD_NUMBER: _ClassVar[int]
    REFUSAL_FIELD_NUMBER: _ClassVar[int]
    result: RemovedMany
    refusal: Refusal
    def __init__(self, result: _Optional[_Union[RemovedMany, _Mapping]] = ..., refusal: _Optional[_Union[Refusal, _Mapping]] = ...) -> None: ...
