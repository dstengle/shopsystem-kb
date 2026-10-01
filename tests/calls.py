"""How the steps call the contract: one helper per rpc, the types the Backgrounds define, and the one reading of a
moment a step names."""
import copy
import re
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import kb
from kb.content import dumps
from kb.contract import kb_pb2

CLIENT = kb_pb2.Actor(role="client")

READING = re.compile(r"(?P<day>\d{4}-\d{2}-\d{2}) at (?P<time>\d{2}:\d{2})(?P<zone>.*)")
ZONES = {
    "": timezone.utc,
    " UTC": timezone.utc,
    ", five hours ahead of UTC": timezone(timedelta(hours=5)),
    ", with no zone": None,
}

DECISION_TYPE = {
    "title": "Decision",
    "version": 1,
    "schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "supersedes": {
                "type": "string",
                "ref": {"targets": ["decision"], "cardinality": "one", "parts": False, "on_delete": "refuse"},
            },
        },
        "required": ["title"],
        "sections": [{"title": "Purpose"}, {"title": "Rationale"}],
        "parts": {
            "options": {
                "items": {
                    "type": "object",
                    "properties": {"title": {"type": "string"}, "body": {"type": "string"}},
                    "required": ["title"],
                }
            }
        },
        "summary": ["supersedes"],
    },
}

WORK_ITEM_TYPE = {
    "title": "Work item",
    "version": 1,
    "schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "decisions": {
                "type": "array",
                "items": {"type": "string"},
                "ref": {"targets": ["decision"], "cardinality": "many", "parts": False, "on_delete": "refuse"},
            },
        },
        "required": ["title"],
        "summary": ["decisions"],
    },
}

NOTE_TYPE = {
    "title": "Note",
    "version": 1,
    "schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "about": {
                "type": "string",
                "ref": {"targets": ["decision"], "cardinality": "one", "parts": True, "on_delete": "refuse"},
            },
        },
        "required": ["title"],
    },
}


TAG_TYPE = {
    "title": "Tag",
    "version": 1,
    "schema": {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]},
}


def moment(reading):
    """The moment a step reads, as "2026-09-23 at 14:30" with the zone it names after, UTC when it names none, or
    with none at all when it says "with no zone"."""
    found = READING.fullmatch(reading)
    assert found, reading
    return datetime.fromisoformat(f"{found['day']}T{found['time']}").replace(tzinfo=ZONES[found["zone"]])


def tagged_decision_type():
    """The decision type, whose artifacts may also carry tags."""
    decision_type = copy.deepcopy(DECISION_TYPE)
    decision_type["schema"]["properties"]["tags"] = {
        "type": "array",
        "items": {"type": "string"},
        "ref": {"targets": ["tag"], "cardinality": "many", "parts": False, "on_delete": "refuse"},
    }
    return decision_type


def start_a_store(root, clock=None):
    """A store started at root through `kb.init`, under the client's role, its first entry stamped by the clock when
    one is given."""
    kb.init(root, CLIENT.role, clock=clock)


def starting(root, role=CLIENT.role, clock=None):
    """A store asked to be started at root through `kb.init`, under the client's role unless another is given,
    stamped by the clock when one is given, answered as a step reads it: `faults`, every fault `kb.NotStarted`
    carried, none when the store was started."""
    try:
        kb.init(root, role, clock=clock)
    except kb.NotStarted as refused:
        return SimpleNamespace(faults=refused.faults)
    return SimpleNamespace(faults=[])


class Answer:
    """A response as a step reads it: whether it is a refusal, the fields of its result, and the faults of its
    refusal, none when it gave a result; a field of a refused call reads as unset. The response itself is
    `response`. A response that is neither a result nor a refusal is never read as either."""

    def __init__(self, response):
        assert response.WhichOneof("outcome") is not None, f"neither a result nor a refusal: {response!r}"
        self.response = response

    @property
    def refused(self):
        return self.response.WhichOneof("outcome") == "refusal"

    @property
    def faults(self):
        return list(self.response.refusal.faults)

    def __getattr__(self, name):
        return getattr(self.response.result, name)

    def __eq__(self, other):
        """Two answers are equal when their responses are."""
        return isinstance(other, Answer) and self.response == other.response

    __hash__ = None


def answer(response):
    """A response, its result or its refusal, as a step reads it."""
    return Answer(response)


def signature(message, actor=CLIENT):
    """The signature of a change: the actor's role and piece of work, and the message."""
    return kb_pb2.Signature(role=actor.role, execution=actor.execution, message=message)


def creating(type_name, title, content, message="Create an artifact", actor=CLIENT):
    """A CreateRequest: the title beside the content, which is canonical text already when it is a string."""
    text = content if isinstance(content, str) else dumps(content)
    return kb_pb2.CreateRequest(kind=type_name, title=title, content=text, signature=signature(message, actor))


def replacing(artifact_id, content, message="Change an artifact", actor=CLIENT, path="", revision=0):
    """A ReplaceRequest for a whole artifact, or for the node at path inside it, saying the revision the client read
    the artifact at when revision is given."""
    text = content if isinstance(content, str) else dumps(content)
    return kb_pb2.ReplaceRequest(
        locator=kb_pb2.Locator(id=artifact_id, place=path), content=text, signature=signature(message, actor),
        revision=revision,
    )


def adding(artifact_id, collection, content, message="Add an item", actor=CLIENT, revision=0):
    """An AddRequest for one item to the collection named inside an artifact, saying the revision the client read the
    artifact at when revision is given."""
    return kb_pb2.AddRequest(
        locator=kb_pb2.Locator(id=artifact_id, place=collection), content=dumps(content),
        signature=signature(message, actor), revision=revision,
    )


def removing(artifact_id, message="Remove an artifact", actor=CLIENT, revision=0):
    """A RemoveRequest for a whole artifact, saying the revision the client read it at when revision is given."""
    return kb_pb2.RemoveRequest(
        locator=kb_pb2.Locator(id=artifact_id), signature=signature(message, actor), revision=revision,
    )


def request(client, type_name, title, content, message="Create an artifact", actor=CLIENT):
    """A Create as the client sends it: the title beside the content. Returns the answer, faults and all."""
    return answer(client.Create(creating(type_name, title, content, message, actor)))


def create(client, type_name, content, message="Create an artifact", actor=CLIENT):
    """Create from a dict written the way a user writes a file, title inside; the title is lifted out and sent beside."""
    content = dict(content)
    title = content.pop("title", "")
    response = request(client, type_name, title, content, message, actor)
    assert not response.faults, response.faults
    return response


def define(client, type_content):
    """Define a type: a Create of type `schema`."""
    return create(client, "schema", type_content, message=f"Define {type_content['title']}")


def read(client, artifact_id, whole=False, depth=0, section=""):
    """A summary read, a whole read following the links as many steps as depth says, or a read of the section
    with the title given."""
    asked = kb_pb2.ReadRequest(locator=kb_pb2.Locator(id=artifact_id), summary=kb_pb2.ReadRequest.Summary())
    if whole:
        asked.whole.depth = depth
    if section:
        asked.section.title = section
    return answer(client.Read(asked))


def created(type_name, title, content, key=""):
    """A create inside a CreateMany: the title beside the content, and the key it carries, if any."""
    return kb_pb2.CreateItem(kind=type_name, title=title, content=dumps(content), key=key)


def replaced(artifact_id, content, revision=0):
    """A replacement of a whole artifact inside a ReplaceMany, saying the revision the client read it at when revision
    is given."""
    return kb_pb2.ReplaceItem(locator=kb_pb2.Locator(id=artifact_id), content=dumps(content), revision=revision)


def create_many(client, items, message="Make several changes", actor=CLIENT):
    """A CreateMany of the creates in order, under the client's role unless another actor is given. Returns the
    answer, faults and all."""
    return answer(client.CreateMany(kb_pb2.CreateManyRequest(items=items, signature=signature(message, actor))))


def replace_many(client, items, message="Make several changes", actor=CLIENT):
    """A ReplaceMany of the replacements in order, under the client's role unless another actor is given. Returns the
    answer, faults and all."""
    return answer(client.ReplaceMany(kb_pb2.ReplaceManyRequest(items=items, signature=signature(message, actor))))


def added(artifact_id, collection, content, revision=0):
    """One item for the collection named inside an artifact, inside an AddMany, saying the revision the client read
    the artifact at when revision is given."""
    return kb_pb2.AddItem(
        locator=kb_pb2.Locator(id=artifact_id, place=collection), content=dumps(content), revision=revision,
    )


def removed(artifact_id, revision=0):
    """A removal of a whole artifact inside a RemoveMany, saying the revision the client read it at when revision is
    given."""
    return kb_pb2.RemoveItem(locator=kb_pb2.Locator(id=artifact_id), revision=revision)


def add_many(client, items, message="Make several changes", actor=CLIENT):
    """An AddMany of the additions in order, under the client's role unless another actor is given. Returns the
    answer, faults and all."""
    return answer(client.AddMany(kb_pb2.AddManyRequest(items=items, signature=signature(message, actor))))


def remove_many(client, items, message="Make several changes", actor=CLIENT):
    """A RemoveMany of the removals in order, under the client's role unless another actor is given. Returns the
    answer, faults and all."""
    return answer(client.RemoveMany(kb_pb2.RemoveManyRequest(items=items, signature=signature(message, actor))))


def replace(client, artifact_id, content, message="Change an artifact", actor=CLIENT, path="", revision=0):
    """A Replace of a whole artifact, or of the node at path inside it, under the client's role unless another actor
    is given, saying the revision the client read it at when revision is given. Returns the answer, faults and
    all."""
    return answer(client.Replace(replacing(artifact_id, content, message, actor, path, revision)))


def add(client, artifact_id, collection, content, message="Add an item", actor=CLIENT, revision=0):
    """An Add of one item to the collection named inside an artifact, under the client's role unless another actor is
    given, saying the revision the client read the artifact at when revision is given. Returns the answer, faults and
    all."""
    return answer(client.Add(adding(artifact_id, collection, content, message, actor, revision)))


def remove(client, artifact_id, message="Remove an artifact", actor=CLIENT, revision=0):
    """A Remove of a whole artifact, under the client's role unless another actor is given, saying the revision the
    client read it at when revision is given. Returns the answer, faults and all."""
    return answer(client.Remove(removing(artifact_id, message, actor, revision)))


def journal(client, artifact="", role="", execution="", since="", batch=""):
    """The history's entries, narrowed to those about one artifact, made by one role, for one piece of work, at or
    after a time, or landed in one set, by whichever are given."""
    request = kb_pb2.HistoryRequest(artifact=artifact)
    for name, value in (("role", role), ("execution", execution), ("since", since), ("batch", batch)):
        if value:
            setattr(request, name, value)
    return answer(client.History(request))


def snapshot(client, execution, artifacts, message="Say what was read", role="agent"):
    """A snapshot of the artifacts named, as they stand now, for the piece of work named, under the role given."""
    return answer(client.Snapshot(kb_pb2.SnapshotRequest(
        signature=kb_pb2.Signature(role=role, execution=execution, message=message), artifacts=artifacts,
    )))


def search(client, text, type_name="", everywhere=False):
    """A search of the prose for the text, or of the fields and the prose when everywhere, among artifacts of one kind
    when type_name is given."""
    request = kb_pb2.SearchRequest(text=text)
    if type_name:
        request.kind = type_name
    if everywhere:
        request.scope = kb_pb2.SearchRequest.ALL
    return answer(client.Search(request))


def refs(client, artifact_id, depth, inward=False, via="", type_name="", place=""):
    """The links out of an artifact, or out of the place inside it place names, or into it when inward, followed as
    many steps as depth says, through the field via names and to artifacts of the kind type_name names when either is
    given."""
    direction = kb_pb2.FollowRequest.IN if inward else kb_pb2.FollowRequest.OUT
    return answer(client.Follow(kb_pb2.FollowRequest(
        locator=kb_pb2.Locator(id=artifact_id, place=place), depth=depth, direction=direction, via=via, kind=type_name,
    )))


PROCESS_TYPE = {
    "title": "Process",
    "version": 1,
    "schema": {
        "type": "object",
        "properties": {"title": {"type": "string"}},
        "required": ["title"],
        "parts": {
            "steps": {
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "body": {"type": "string"},
                        "branches": {"type": "array", "items": {"type": "string"}},
                        "uses": {
                            "type": "string",
                            "ref": {"targets": ["step"], "cardinality": "one", "parts": False, "on_delete": "refuse"},
                        },
                        "settings": {"type": "object"},
                    },
                    "required": ["title"],
                }
            }
        },
    },
}


def listing(client, type_name, fields=None, ids_only=False):
    """The artifacts of a kind, those whose fields hold the values given, as stubs or as names only."""
    form = kb_pb2.ListRequest.IDS if ids_only else kb_pb2.ListRequest.STUBS
    return answer(client.List(kb_pb2.ListRequest(kind=type_name, fields=fields or {}, form=form)))


def check(client):
    """The check of the whole store: its violations and the stale, or the refusal."""
    return answer(client.Check(kb_pb2.CheckRequest()))


def next_version(client, kind, type_content, sections=None):
    """Write the type of a kind back at its next version, the sections it requires replaced when sections are given,
    so what the store holds of that kind falls behind it. Returns the Replace's answer."""
    schema = copy.deepcopy(type_content["schema"])
    if sections is not None:
        schema["sections"] = [{"title": title} for title in sections]
    return replace(client, f"schema/{kind}", {"version": type_content["version"] + 1, "schema": schema},
                 message=f"Revise {type_content['title']}")


class MovingClock:
    """A clock for a dated scenario: it reads `at`, moving on a second at each reading so no two entries share a
    moment; a step sets `at` to make a change on another day. `today` is the day the scenario named."""

    def __init__(self, day):
        self.today = datetime.fromisoformat(f"{day}T09:00:00+00:00")
        self.at = self.today

    def __call__(self):
        self.at += timedelta(seconds=1)
        return self.at
