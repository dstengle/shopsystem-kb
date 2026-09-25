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

class Locator(_message.Message):
    __slots__ = ("id", "path")
    ID_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    id: str
    path: str
    def __init__(self, id: _Optional[str] = ..., path: _Optional[str] = ...) -> None: ...

class Fault(_message.Message):
    __slots__ = ("artifact", "path", "rule", "message")
    ARTIFACT_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    RULE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    artifact: str
    path: str
    rule: str
    message: str
    def __init__(self, artifact: _Optional[str] = ..., path: _Optional[str] = ..., rule: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

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
    __slots__ = ("type", "content", "actor", "message", "title")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    ACTOR_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    type: str
    content: str
    actor: Actor
    message: str
    title: str
    def __init__(self, type: _Optional[str] = ..., content: _Optional[str] = ..., actor: _Optional[_Union[Actor, _Mapping]] = ..., message: _Optional[str] = ..., title: _Optional[str] = ...) -> None: ...

class CreateResponse(_message.Message):
    __slots__ = ("id", "revision", "faults")
    ID_FIELD_NUMBER: _ClassVar[int]
    REVISION_FIELD_NUMBER: _ClassVar[int]
    FAULTS_FIELD_NUMBER: _ClassVar[int]
    id: str
    revision: int
    faults: _containers.RepeatedCompositeFieldContainer[Fault]
    def __init__(self, id: _Optional[str] = ..., revision: _Optional[int] = ..., faults: _Optional[_Iterable[_Union[Fault, _Mapping]]] = ...) -> None: ...

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
    __slots__ = ("field", "id", "type", "title", "fields")
    FIELD_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    field: str
    id: str
    type: str
    title: str
    fields: str
    def __init__(self, field: _Optional[str] = ..., id: _Optional[str] = ..., type: _Optional[str] = ..., title: _Optional[str] = ..., fields: _Optional[str] = ...) -> None: ...

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
    __slots__ = ("type", "field", "count")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    FIELD_FIELD_NUMBER: _ClassVar[int]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    type: str
    field: str
    count: int
    def __init__(self, type: _Optional[str] = ..., field: _Optional[str] = ..., count: _Optional[int] = ...) -> None: ...

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

class WriteRequest(_message.Message):
    __slots__ = ("locator", "content", "actor", "message")
    LOCATOR_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    ACTOR_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    locator: Locator
    content: str
    actor: Actor
    message: str
    def __init__(self, locator: _Optional[_Union[Locator, _Mapping]] = ..., content: _Optional[str] = ..., actor: _Optional[_Union[Actor, _Mapping]] = ..., message: _Optional[str] = ...) -> None: ...

class WriteResponse(_message.Message):
    __slots__ = ("revision", "faults")
    REVISION_FIELD_NUMBER: _ClassVar[int]
    FAULTS_FIELD_NUMBER: _ClassVar[int]
    revision: int
    faults: _containers.RepeatedCompositeFieldContainer[Fault]
    def __init__(self, revision: _Optional[int] = ..., faults: _Optional[_Iterable[_Union[Fault, _Mapping]]] = ...) -> None: ...

class Operation(_message.Message):
    __slots__ = ("create", "write")
    CREATE_FIELD_NUMBER: _ClassVar[int]
    WRITE_FIELD_NUMBER: _ClassVar[int]
    create: Creation
    write: Replacement
    def __init__(self, create: _Optional[_Union[Creation, _Mapping]] = ..., write: _Optional[_Union[Replacement, _Mapping]] = ...) -> None: ...

class Creation(_message.Message):
    __slots__ = ("type", "title", "content")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    type: str
    title: str
    content: str
    def __init__(self, type: _Optional[str] = ..., title: _Optional[str] = ..., content: _Optional[str] = ...) -> None: ...

class Replacement(_message.Message):
    __slots__ = ("locator", "content")
    LOCATOR_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    locator: Locator
    content: str
    def __init__(self, locator: _Optional[_Union[Locator, _Mapping]] = ..., content: _Optional[str] = ...) -> None: ...

class ApplyRequest(_message.Message):
    __slots__ = ("operations", "actor", "message")
    OPERATIONS_FIELD_NUMBER: _ClassVar[int]
    ACTOR_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    operations: _containers.RepeatedCompositeFieldContainer[Operation]
    actor: Actor
    message: str
    def __init__(self, operations: _Optional[_Iterable[_Union[Operation, _Mapping]]] = ..., actor: _Optional[_Union[Actor, _Mapping]] = ..., message: _Optional[str] = ...) -> None: ...

class ApplyResponse(_message.Message):
    __slots__ = ("batch", "results", "faults")
    BATCH_FIELD_NUMBER: _ClassVar[int]
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    FAULTS_FIELD_NUMBER: _ClassVar[int]
    batch: str
    results: _containers.RepeatedCompositeFieldContainer[Result]
    faults: _containers.RepeatedCompositeFieldContainer[Fault]
    def __init__(self, batch: _Optional[str] = ..., results: _Optional[_Iterable[_Union[Result, _Mapping]]] = ..., faults: _Optional[_Iterable[_Union[Fault, _Mapping]]] = ...) -> None: ...

class Result(_message.Message):
    __slots__ = ("id", "revision")
    ID_FIELD_NUMBER: _ClassVar[int]
    REVISION_FIELD_NUMBER: _ClassVar[int]
    id: str
    revision: int
    def __init__(self, id: _Optional[str] = ..., revision: _Optional[int] = ...) -> None: ...

class JournalRequest(_message.Message):
    __slots__ = ("artifact", "role", "execution", "since")
    ARTIFACT_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_FIELD_NUMBER: _ClassVar[int]
    SINCE_FIELD_NUMBER: _ClassVar[int]
    artifact: str
    role: str
    execution: str
    since: str
    def __init__(self, artifact: _Optional[str] = ..., role: _Optional[str] = ..., execution: _Optional[str] = ..., since: _Optional[str] = ...) -> None: ...

class Entry(_message.Message):
    __slots__ = ("id", "at", "actor", "op", "artifact", "path", "revision", "schema_version", "digest", "message", "batch")
    ID_FIELD_NUMBER: _ClassVar[int]
    AT_FIELD_NUMBER: _ClassVar[int]
    ACTOR_FIELD_NUMBER: _ClassVar[int]
    OP_FIELD_NUMBER: _ClassVar[int]
    ARTIFACT_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    REVISION_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_VERSION_FIELD_NUMBER: _ClassVar[int]
    DIGEST_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    BATCH_FIELD_NUMBER: _ClassVar[int]
    id: str
    at: str
    actor: Actor
    op: str
    artifact: str
    path: str
    revision: int
    schema_version: int
    digest: str
    message: str
    batch: str
    def __init__(self, id: _Optional[str] = ..., at: _Optional[str] = ..., actor: _Optional[_Union[Actor, _Mapping]] = ..., op: _Optional[str] = ..., artifact: _Optional[str] = ..., path: _Optional[str] = ..., revision: _Optional[int] = ..., schema_version: _Optional[int] = ..., digest: _Optional[str] = ..., message: _Optional[str] = ..., batch: _Optional[str] = ...) -> None: ...

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
