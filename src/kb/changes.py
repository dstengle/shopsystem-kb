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
    locator: Locator
    content: Content


@dataclass(frozen=True)
class Add:
    locator: Locator
    item: Content


@dataclass(frozen=True)
class Remove:
    locator: Locator


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


def creating_many(request: kb_pb2.CreateManyRequest) -> tuple[list, Signed]:
    """A CreateMany as the domain takes it: a set of creates, signed, refused when two of its creates carry one key."""
    converted, signed = _many(request.signature, [
        lambda item=item: _create(item.kind, item.title, item.content, item.key) for item in request.items
    ])
    _keyed_once(converted)
    return converted, signed


def _keyed_once(converted: list) -> None:
    """Refuse a set in which more than one create carries the same key, one fault for each such key."""
    carried = Counter(each.key for each in converted if isinstance(each, Create) and each.key)
    twice = [key for key, count in carried.items() if count > 1]
    if twice:
        raise Refused([
            kb_pb2.Fault(
                rule=rules.REF, message=f"a key names one create in the set; {key!r} is carried by more than one",
            )
            for key in twice
        ])


def replacing_many(request: kb_pb2.ReplaceManyRequest) -> tuple[list, Signed]:
    """A ReplaceMany as the domain takes it: a set of replacements, signed."""
    return _many(request.signature, [lambda item=item: _replace(item.locator, item.content) for item in request.items])


def adding_many(request: kb_pb2.AddManyRequest) -> tuple[list, Signed]:
    """An AddMany as the domain takes it: a set of items added, signed."""
    return _many(request.signature, [lambda item=item: _add(item.locator, item.content) for item in request.items])


def removing_many(request: kb_pb2.RemoveManyRequest) -> tuple[list, Signed]:
    """A RemoveMany as the domain takes it: a set of removals, signed."""
    return _many(request.signature, [lambda item=item: _remove(item.locator) for item in request.items])


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


def _replace(requested: kb_pb2.Locator, content: str) -> Replace:
    locator = values.locator(requested)
    return Replace(locator, values.content(content, at_root=not locator.place))


def _add(requested: kb_pb2.Locator, content: str) -> Add:
    return Add(values.locator(requested), values.item(content))


def _remove(requested: kb_pb2.Locator) -> Remove:
    return Remove(values.locator(requested))
