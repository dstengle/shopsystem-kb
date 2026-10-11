"""How the steps call the contract: one helper per rpc, the types the Backgrounds define, the IRIs the steps name
artifacts and types by, and the one reading of a moment a step names. A kind is given to a helper by its short name,
`decision` for the type at `https://shop.example/kb/decision`, or by its type's IRI; `schema` names the type that
describes types. An artifact a step creates without stating an IRI sits under its type's IRI at the name its title
gives."""
import copy
import re
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import kb
from kb.content import dumps, loads
from kb.contract import kb_pb2

CLIENT = kb_pb2.Actor(role="client")

TYPES_AT = "https://shop.example/kb/"
TYPE_OF_TYPES = "https://missingmass.io/kb/type"
TYPES = "schema"


def type_iri(kind):
    """The IRI of the type of a kind given by its short name, or the IRI itself when it is one."""
    if kind.startswith("https://"):
        return kind
    return TYPE_OF_TYPES if kind == TYPES else TYPES_AT + kind


def version_iri(kind, number=1):
    """The IRI of a version of a kind's type."""
    return f"{type_iri(kind)}@{number}"


def iri(kind, name):
    """The IRI of an artifact of a kind, under its type's IRI at the name given; a type's, of kind `schema`, is the
    IRI of the kind it is named for."""
    return type_iri(name) if kind == TYPES else f"{type_iri(kind)}/{name}"


def slug(title):
    """The name a title gives: lower-cased, every run of anything else a hyphen, none at either end."""
    return re.sub(r"[^a-z0-9]+", "-", str(title).lower()).strip("-")


def named(kind, title):
    """The IRI an artifact of a kind a step creates sits at when the step states none: the name its title gives."""
    return iri(kind, slug(title))


def filed(name, version=None):
    """Where an export puts an artifact, below its directory: the host and path of its IRI, `.yaml`; for a type, the
    version given, its IRI followed by `@` and the version's number."""
    return name.removeprefix("https://") + (f"@{version}" if version else "") + ".yaml"


def kb_ref(kind, number=1, fragment=""):
    """A `kb:` reference to a version of a kind's type, and to a shape inside it when a fragment is given."""
    return f"kb:{version_iri(kind, number)}{fragment}"


def targets(*kinds):
    """The kinds a link field may point at, each by its type's IRI."""
    return [type_iri(kind) for kind in kinds]

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
                "ref": {"targets": targets("decision"), "cardinality": "one", "parts": False, "on_delete": "refuse"},
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

# DECISION_TYPE's fields, sections and options in that order, and a field whose two constraints are written in the
# reverse of their alphabetical order, so the order the validator finds them in and kb's order differ.
ORDERED_DECISION_TYPE = copy.deepcopy(DECISION_TYPE)
ORDERED_DECISION_TYPE["schema"]["properties"]["status"] = {"type": "string", "pattern": "^[a-z-]+$", "maxLength": 5}

# A decision written options first, then sections, then fields; the field breaks both its constraints, the second
# option's title is a number and the rationale is missing.
MISORDERED_DECISION = {
    "options": [{"title": "Go weekly"}, {"title": 7}],
    "sections": [{"title": "Purpose", "body": "Keep prices in step with costs.\n"}],
    "status": "Not-Lower-Case",
}

# The places and rules of its faults in the order the decision reads back: field, sections, options.
READING_ORDER = [
    ("status", "maxLength"), ("status", "pattern"), ("sections", "sections"), ("options/1/title", "type"),
]


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
                "ref": {"targets": targets("decision"), "cardinality": "many", "parts": False, "on_delete": "refuse"},
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
                "ref": {"targets": targets("decision"), "cardinality": "one", "parts": True, "on_delete": "refuse"},
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
        "ref": {"targets": targets("tag"), "cardinality": "many", "parts": False, "on_delete": "refuse"},
    }
    return decision_type


def start_a_store(root, clock=None):
    """A store started at root through `kb.init`, under the client's role, its first entry stamped by the clock when
    one is given."""
    kb.init(root, CLIENT.role, clock=clock)


def starting(root, role=CLIENT.role, clock=None, execution=""):
    """A store asked to be started at root through `kb.init`, under the client's role unless another is given,
    stamped by the clock when one is given, for the piece of work when one is named, answered as a step reads it:
    `faults`, every fault `kb.NotStarted` carried, none when the store was started."""
    try:
        kb.init(root, role, execution=execution, clock=clock)
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


class Stream:
    """A streamed answer as a step reads it, read to its end: `messages`, each as it came; whether it is a refusal,
    which it is when any message of it is one; the faults of those; the files given, each its place and its text, in
    the order they came; and the position the end carries. Only a stream whose last message is its one end is
    `complete`."""

    def __init__(self, stream):
        self.messages = list(stream)
        assert all(message.WhichOneof("outcome") is not None for message in self.messages), self.messages

    @property
    def refused(self):
        return any(message.WhichOneof("outcome") == "refusal" for message in self.messages)

    @property
    def faults(self):
        return [fault for message in self.messages for fault in message.refusal.faults]

    @property
    def files(self):
        return [(message.result.file.place, message.result.file.text) for message in self.messages
                if message.result.WhichOneof("part") == "file"]

    @property
    def complete(self):
        ends = [message for message in self.messages if message.result.WhichOneof("part") == "end"]
        return len(ends) == 1 and ends[0] is self.messages[-1]

    @property
    def position(self):
        assert self.complete, self.messages
        return self.messages[-1].result.end.position


def answer(response):
    """A response, its result or its refusal, as a step reads it; a streamed answer read to its end."""
    return Answer(response) if hasattr(response, "WhichOneof") else Stream(response)


def signature(message, actor=CLIENT):
    """The signature of a change: the actor's role and piece of work, and the message."""
    return kb_pb2.Signature(role=actor.role, execution=actor.execution, message=message)


def creating(type_name, title, content, message="Create an artifact", actor=CLIENT, at=None, version=1):
    """A CreateRequest: at the IRI given, or the one its title gives under its type's, conforming to the version of
    its type given, the first unless another is, the title beside the content, which is canonical text already when it
    is a string."""
    text = content if isinstance(content, str) else dumps(content)
    return kb_pb2.CreateRequest(
        id=at or named(type_name, title), type=version_iri(type_name, version), title=str(title), content=text,
        signature=signature(message, actor),
    )


def replacing(artifact_id, content, message="Change an artifact", actor=CLIENT, path="", revision=0, version=""):
    """A ReplaceRequest for a whole artifact, or for the node at path inside it, saying the revision the client read
    the artifact at when revision is given, and naming a version of its type, by its IRI, when version is given."""
    text = content if isinstance(content, str) else dumps(content)
    return kb_pb2.ReplaceRequest(
        locator=kb_pb2.Locator(id=artifact_id, place=path), content=text, signature=signature(message, actor),
        revision=revision, type=version,
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


def request(client, type_name, title, content, message="Create an artifact", actor=CLIENT, at=None, version=None):
    """A Create as the client sends it: the title beside the content, naming the version its type stands at unless
    another is given. Returns the answer, faults and all."""
    number = held_version(client, type_name) if version is None else version
    return answer(client.Create(creating(type_name, title, content, message, actor, at, number)))


def held_version(client, kind):
    """The version a kind's type stands at, as the client reads it; the first when the store holds no such type."""
    read_back = client.Read(kb_pb2.ReadRequest(locator=kb_pb2.Locator(id=type_iri(kind)), whole=kb_pb2.ReadRequest.Whole()))
    if read_back.WhichOneof("outcome") != "result":
        return 1
    return loads(read_back.result.content).get("version", 1)


def create(client, type_name, content, message="Create an artifact", actor=CLIENT, at=None):
    """Create from a dict written the way a user writes a file, title inside; the title is lifted out and sent beside."""
    content = dict(content)
    title = content.pop("title", "")
    response = request(client, type_name, title, content, message, actor, at)
    assert not response.faults, response.faults
    return response


def a_decision_type_and_a_decision(client):
    """The type for decisions defined in the store, and one decision of it created."""
    define(client, DECISION_TYPE)
    create(client, "decision", {"title": "Price reviews happen weekly", "sections": [
        {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
        {"title": "Rationale", "body": "Costs move weekly.\n"},
    ]})


def define(client, type_content, at=None):
    """Define a type: a Create of the type that describes types, at the IRI given, or the one its title gives under
    the steps' types."""
    return create(client, TYPES, type_content, message=f"Define {type_content['title']}", at=at)


def read(client, artifact_id, whole=False, depth=0, section=""):
    """A summary read, a whole read following the links as many steps as depth says, or a read of the section
    with the title given."""
    asked = kb_pb2.ReadRequest(locator=kb_pb2.Locator(id=artifact_id), summary=kb_pb2.ReadRequest.Summary())
    if whole:
        asked.whole.depth = depth
    if section:
        asked.section.title = section
    return answer(client.Read(asked))


def created(type_name, title, content, at=None, version=1):
    """A create inside a BatchCreate: at the IRI given, or the one its title gives under its type's, conforming to
    the version of its type given, the first unless another is, the title beside the content."""
    return kb_pb2.CreateItem(
        id=at or named(type_name, title), type=version_iri(type_name, version), title=str(title),
        content=dumps(content),
    )


def replaced(artifact_id, content, revision=0, version=""):
    """A replacement of a whole artifact inside a BatchReplace, saying the revision the client read it at when revision
    is given, and naming a version of its type, by its IRI, when version is given."""
    return kb_pb2.ReplaceItem(
        locator=kb_pb2.Locator(id=artifact_id), content=dumps(content), revision=revision, type=version,
    )


def create_many(client, items, message="Make several changes", actor=CLIENT):
    """A BatchCreate of the creates in order, under the client's role unless another actor is given. Returns the
    answer, faults and all."""
    return answer(client.BatchCreate(kb_pb2.BatchCreateRequest(items=items, signature=signature(message, actor))))


def replace_many(client, items, message="Make several changes", actor=CLIENT):
    """A BatchReplace of the replacements in order, under the client's role unless another actor is given. Returns the
    answer, faults and all."""
    return answer(client.BatchReplace(kb_pb2.BatchReplaceRequest(items=items, signature=signature(message, actor))))


def added(artifact_id, collection, content, revision=0):
    """One item for the collection named inside an artifact, inside an BatchAdd, saying the revision the client read
    the artifact at when revision is given."""
    return kb_pb2.AddItem(
        locator=kb_pb2.Locator(id=artifact_id, place=collection), content=dumps(content), revision=revision,
    )


def removed(artifact_id, revision=0):
    """A removal of a whole artifact inside a BatchRemove, saying the revision the client read it at when revision is
    given."""
    return kb_pb2.RemoveItem(locator=kb_pb2.Locator(id=artifact_id), revision=revision)


def add_many(client, items, message="Make several changes", actor=CLIENT):
    """An BatchAdd of the additions in order, under the client's role unless another actor is given. Returns the
    answer, faults and all."""
    return answer(client.BatchAdd(kb_pb2.BatchAddRequest(items=items, signature=signature(message, actor))))


def remove_many(client, items, message="Make several changes", actor=CLIENT):
    """A BatchRemove of the removals in order, under the client's role unless another actor is given. Returns the
    answer, faults and all."""
    return answer(client.BatchRemove(kb_pb2.BatchRemoveRequest(items=items, signature=signature(message, actor))))


def replace(client, artifact_id, content, message="Change an artifact", actor=CLIENT, path="", revision=0, version=""):
    """A Replace of a whole artifact, or of the node at path inside it, under the client's role unless another actor
    is given, saying the revision the client read it at when revision is given, and naming a version of its type, by
    its IRI, when version is given. Returns the answer, faults and all."""
    return answer(client.Replace(replacing(artifact_id, content, message, actor, path, revision, version)))


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
        request.kind = type_iri(type_name)
    if everywhere:
        request.scope = kb_pb2.SearchRequest.ALL
    return answer(client.Search(request))


def refs(client, artifact_id, depth, inward=False, via="", type_name="", place="", path=""):
    """The links out of an artifact, or out of the place inside it place names, or into it when inward, followed as
    many steps as depth says, through the field via names, to artifacts of the kind type_name names and to what the
    path below the type selects, when each is given."""
    direction = kb_pb2.FollowRequest.IN if inward else kb_pb2.FollowRequest.OUT
    return answer(client.Follow(kb_pb2.FollowRequest(
        locator=kb_pb2.Locator(id=artifact_id, place=place), depth=depth, direction=direction, via=via,
        kind=type_iri(type_name) if type_name else "", path=path,
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
                            "ref": {"targets": targets("step"), "cardinality": "one", "parts": False, "on_delete": "refuse"},
                        },
                        "settings": {"type": "object"},
                    },
                    "required": ["title"],
                }
            }
        },
    },
}


def listing(client, type_name, fields=None, ids_only=False, path=""):
    """The artifacts of a kind, or of every kind when none is named, those whose fields hold the values given and
    that the path below the type selects when one is given, as stubs or as names only."""
    form = kb_pb2.ListRequest.IDS if ids_only else kb_pb2.ListRequest.STUBS
    kind = type_iri(type_name) if type_name else ""
    return answer(client.List(kb_pb2.ListRequest(kind=kind, fields=fields or {}, form=form, path=path)))


def below_their_types(datatable):
    """A table of kinds and paths below the type read as each row's kind, by its short name, and its artifact's IRI."""
    heading, *rows = datatable
    assert heading == ["kind", "path below its type"]
    return [(slug(kind), iri(slug(kind), path)) for kind, path in rows]


def check(client):
    """The check of the whole store: its violations and the stale, or the refusal."""
    return answer(client.Check(kb_pb2.CheckRequest()))


def placeholders(client):
    """Every IRI a link points at that the store does not hold, each with the links into it, or the refusal."""
    return answer(client.Placeholders(kb_pb2.PlaceholdersRequest()))


def export(client):
    """The whole store exported through the contract, the stream read to its end."""
    return answer(client.Export(kb_pb2.ExportRequest()))


def next_version(client, kind, type_content, sections=None):
    """Write the type of a kind back at its next version, the sections it requires replaced when sections are given,
    so what the store holds of that kind falls behind it. Returns the Replace's answer."""
    schema = copy.deepcopy(type_content["schema"])
    if sections is not None:
        schema["sections"] = [{"title": title} for title in sections]
    return replace(client, type_iri(kind), {"version": type_content["version"] + 1, "schema": schema},
                 message=f"Revise {type_content['title']}")


def change_type(client, type_name, schema, message="Change a type"):
    """Write the type of a kind, or at an IRI, back with the schema given and no number: the store numbers the
    version the change makes. Returns the Replace's answer."""
    return replace(client, type_iri(type_name), {"schema": schema}, message=message)


class MovingClock:
    """A clock for a dated scenario: it reads `at`, moving on a second at each reading so no two entries share a
    moment; a step sets `at` to make a change on another day. `today` is the day the scenario named."""

    def __init__(self, day):
        self.today = datetime.fromisoformat(f"{day}T09:00:00+00:00")
        self.at = self.today

    def __call__(self):
        self.at += timedelta(seconds=1)
        return self.at
