"""Each change's request, alone or in a set, as the values its one domain call takes, built from the conversions in
kb.values and kb.signatures: who makes it and why first, refused alone when it does not say; then each change,
converted or standing in its place as a Refusal, so the faults come back in the order of the changes. An IRI two
creates of a set carry is refused on each create after the first, whether or not either converts."""
from dataclasses import dataclass

from kb import content_values, refusals, rules, signatures, values
from kb.content_values import Content
from kb.contract import kb_pb2
from kb.requests import Refusal
from kb.signatures import Signed
from kb.values import ArtifactId, Locator, Refused, Version


@dataclass(frozen=True)
class Create:
    """A new artifact: the IRI its client chose, the type version it conforms to, its title and the title's faults,
    its content, and the fault of an IRI a create before it in its set carries."""
    name: ArtifactId
    version: Version
    title: str
    title_faults: tuple
    content: Content
    carried: tuple = ()


@dataclass(frozen=True)
class Replace:
    """A replacement, the revision the client read its artifact at, None when it said none, and the version of its
    type it names for its artifact to move to, None when it names none."""
    locator: Locator
    content: Content
    expected: int | None = None
    version: Version | None = None


@dataclass(frozen=True)
class Add:
    """An item added, and the revision the client read its artifact at, None when it said none."""
    locator: Locator
    item: Content
    expected: int | None = None


@dataclass(frozen=True)
class Remove:
    """A removal, and the revision the client read its artifact at, None when it said none."""
    locator: Locator
    expected: int | None = None


def creating(request: kb_pb2.CreateRequest) -> tuple[list, Signed]:
    """A Create as the domain takes it: a set of one, signed."""
    return _one(request.signature, lambda: _create(request.id, request.type, request.title, request.content))


def replacing(request: kb_pb2.ReplaceRequest) -> tuple[list, Signed]:
    """A Replace as the domain takes it: a set of one, signed."""
    return _one(
        request.signature, lambda: _replace(request.locator, request.content, request.revision, request.type),
    )


def adding(request: kb_pb2.AddRequest) -> tuple[list, Signed]:
    """An Add as the domain takes it: a set of one, signed."""
    return _one(request.signature, lambda: _add(request.locator, request.content, request.revision))


def removing(request: kb_pb2.RemoveRequest) -> tuple[list, Signed]:
    """A Remove as the domain takes it: a set of one, signed."""
    return _one(request.signature, lambda: _remove(request.locator, request.revision))


def creating_many(request: kb_pb2.BatchCreateRequest) -> tuple[list, Signed]:
    """A BatchCreate as the domain takes it: a set of creates, signed, each saying whether a create before it carries
    its IRI."""
    return _many(request.signature, [
        lambda item=item, again=again: _create(item.id, item.type, item.title, item.content, again)
        for item, again in zip(request.items, _carried_again([item.id for item in request.items]))
    ])


def replacing_many(request: kb_pb2.BatchReplaceRequest) -> tuple[list, Signed]:
    """A BatchReplace as the domain takes it: a set of replacements, signed."""
    return _many(request.signature, [
        lambda item=item: _replace(item.locator, item.content, item.revision, item.type) for item in request.items
    ])


def adding_many(request: kb_pb2.BatchAddRequest) -> tuple[list, Signed]:
    """An BatchAdd as the domain takes it: a set of items added, signed."""
    return _many(request.signature, [
        lambda item=item: _add(item.locator, item.content, item.revision) for item in request.items
    ])


def removing_many(request: kb_pb2.BatchRemoveRequest) -> tuple[list, Signed]:
    """A BatchRemove as the domain takes it: a set of removals, signed."""
    return _many(request.signature, [
        lambda item=item: _remove(item.locator, item.revision) for item in request.items
    ])


def _many(signature: kb_pb2.Signature, conversions: list) -> tuple[list, Signed]:
    """A set: who makes it and why first, refused alone when it does not say; then a set holding nothing is refused;
    then each change, converted or standing as its refusal."""
    signed = signatures.signed(signature)
    if not conversions:
        raise Refused([kb_pb2.Fault(rule=rules.OPERATIONS, message="a set must hold at least one change")])
    return _each(conversions), signed


def _one(signature: kb_pb2.Signature, convert) -> tuple[list, Signed]:
    """One change: who makes it and why first, refused alone when it does not say; then the change, converted or
    standing as its refusal."""
    signed = signatures.signed(signature)
    return _each([convert]), signed


def _each(conversions) -> list:
    """Each conversion's change, or its refusal in its place."""
    converted = []
    for convert in conversions:
        try:
            converted.append(convert())
        except Refused as refused:
            converted.append(Refusal(tuple(refused.faults)))
    return converted


def _carried_again(iris: list[str]) -> list[bool]:
    """For each create of a set, whether a create before it carries the IRI it gives."""
    return [iri in iris[:index] for index, iri in enumerate(iris)]


def _create(iri: str, type_version: str, title: str, content: str, again: bool = False) -> Create:
    """A create's IRI and type version, both faults when both fail, then the rest; an IRI a create before it carries
    (`again`) refused once it is one, beside the create's other faults and before them."""
    name, version, carried, faults = None, None, (), []
    try:
        name = values.artifact_id(iri)
        carried = (refusals.carried_twice(name),) if again else ()
    except Refused as refused:
        faults += refused.faults
    try:
        version = values.version(type_version)
    except Refused as refused:
        faults += refused.faults
    if faults:
        raise Refused([*carried, *faults])
    return Create(name, version, title, values.titled(title, iri), content_values.content(content), carried)


def _replace(requested: kb_pb2.Locator, content: str, revision: int = 0, type_version: str = "") -> Replace:
    """A replacement, the version of its type it names read as a create's is; one naming none names no version."""
    locator = values.locator(requested)
    version = values.named(type_version)
    return Replace(locator, content_values.content(content, at_root=not locator.place), values.expected(revision), version)


def _add(requested: kb_pb2.Locator, content: str, revision: int = 0) -> Add:
    return Add(values.locator(requested), content_values.item(content), values.expected(revision))


def _remove(requested: kb_pb2.Locator, revision: int = 0) -> Remove:
    return Remove(values.locator(requested), values.expected(revision))
