from google.protobuf.internal import containers as _containers
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
    __slots__ = ("locator",)
    LOCATOR_FIELD_NUMBER: _ClassVar[int]
    locator: Locator
    def __init__(self, locator: _Optional[_Union[Locator, _Mapping]] = ...) -> None: ...

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
