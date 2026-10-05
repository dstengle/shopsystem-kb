"""Each change's request, alone or in a set, as the values its one domain call takes, built from the conversions in
kb.values and kb.signatures: who makes it and why first, refused alone when it does not say; then each change,
converted or standing in its place as a Refusal, so the faults come back in the order of the changes."""
from collections import Counter
from dataclasses import dataclass

from kb import rules, signatures, values
from kb.contract import kb_pb2
from kb.requests import Refusal
from kb.signatures import Signed
from kb.values import ArtifactId, Content, Kind, Locator, Refused


@dataclass(frozen=True)
class Create:
    """A new artifact: its kind, its title, the name the title gives (None when it gives none, the title's faults
    saying why), the name its faults are said of until it has one, its content, and the key it carries in a set,
    empty for none."""
    kind: Kind
    title: str
    name: ArtifactId | None
    at: str
    title_faults: tuple
    content: Content
    key: str = ""


@dataclass(frozen=True)
class Replace:
    """A replacement, and the revision the client read its artifact at, None when it said none."""
    locator: Locator
    content: Content
    expected: int | None = None


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
    return _one(request.signature, lambda: _create(request.kind, request.title, request.content))


def replacing(request: kb_pb2.ReplaceRequest) -> tuple[list, Signed]:
    """A Replace as the domain takes it: a set of one, signed."""
    return _one(request.signature, lambda: _replace(request.locator, request.content, request.revision))


def adding(request: kb_pb2.AddRequest) -> tuple[list, Signed]:
    """An Add as the domain takes it: a set of one, signed."""
    return _one(request.signature, lambda: _add(request.locator, request.content, request.revision))


def removing(request: kb_pb2.RemoveRequest) -> tuple[list, Signed]:
    """A Remove as the domain takes it: a set of one, signed."""
    return _one(request.signature, lambda: _remove(request.locator, request.revision))


def creating_many(request: kb_pb2.BatchCreateRequest) -> tuple[list, Signed]:
    """A BatchCreate as the domain takes it: a set of creates, signed; a key two or more of its creates carry, whether
    or not they convert, refused beside every other fault of the set, after them."""
    converted, signed = _many(request.signature, [
        lambda item=item: _create(item.kind, item.title, item.content, item.key) for item in request.items
    ])
    twice = _carried_twice([item.key for item in request.items])
    return converted + ([Refusal(twice)] if twice else []), signed


def _carried_twice(keys: list[str]) -> tuple:
    """One fault for each key, as it converts, that more than one create carries."""
    carried = Counter(key for key in map(_key_or_none, keys) if key)
    return tuple(
        kb_pb2.Fault(rule=rules.REF, message=f"a key names one create in the set; {key!r} is carried by more than one")
        for key, count in carried.items() if count > 1
    )


def _key_or_none(text: str) -> str | None:
    """A key as it converts, None when it does not, its create refused for it."""
    try:
        return values.key(text)
    except Refused:
        return None


def replacing_many(request: kb_pb2.BatchReplaceRequest) -> tuple[list, Signed]:
    """A BatchReplace as the domain takes it: a set of replacements, signed."""
    return _many(request.signature, [
        lambda item=item: _replace(item.locator, item.content, item.revision) for item in request.items
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


def _create(kind_name: str, title: str, content: str, key: str = "") -> Create:
    kind = values.kind(kind_name)
    name, at, title_faults = values.named(kind, title)
    return Create(kind, title, name, at, title_faults, values.content(content), values.key(key))


def _replace(requested: kb_pb2.Locator, content: str, revision: int = 0) -> Replace:
    locator = values.locator(requested)
    return Replace(locator, values.content(content, at_root=not locator.place), values.expected(revision))


def _add(requested: kb_pb2.Locator, content: str, revision: int = 0) -> Add:
    return Add(values.locator(requested), values.item(content), values.expected(revision))


def _remove(requested: kb_pb2.Locator, revision: int = 0) -> Remove:
    return Remove(values.locator(requested), values.expected(revision))
