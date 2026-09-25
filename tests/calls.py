"""How the steps call the contract: one helper per rpc, plus the types the Backgrounds define."""
import copy

from kb.content import dumps
from kb.contract import kb_pb2

CLIENT = kb_pb2.Actor(role="client")

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


TAG_TYPE = {
    "title": "Tag",
    "version": 1,
    "schema": {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]},
}


def tagged_decision_type():
    """The decision type, whose artifacts may also carry tags."""
    decision_type = copy.deepcopy(DECISION_TYPE)
    decision_type["schema"]["properties"]["tags"] = {
        "type": "array",
        "items": {"type": "string"},
        "ref": {"targets": ["tag"], "cardinality": "many", "parts": False, "on_delete": "refuse"},
    }
    return decision_type


def request(client, type_name, title, content, message="Create an artifact", actor=CLIENT):
    """A Create as the client sends it: the title beside the content. Returns the response, faults and all."""
    return client.Create(kb_pb2.CreateRequest(
        type=type_name, title=title, content=dumps(content), actor=actor, message=message,
    ))


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
    level = kb_pb2.ReadRequest.SUMMARY
    if whole:
        level = kb_pb2.ReadRequest.WHOLE
    if section:
        level = kb_pb2.ReadRequest.SECTION
    return client.Read(kb_pb2.ReadRequest(
        locator=kb_pb2.Locator(id=artifact_id), level=level, depth=depth, section=section,
    ))


def apply(client, operations, message="Make several changes"):
    """An Apply of the operations in order, under the client's role. Returns the response, faults and all."""
    return client.Apply(kb_pb2.ApplyRequest(operations=operations, actor=CLIENT, message=message))


def creation(type_name, title, content):
    """A Create inside a set: the title beside the content, the role and message the set's."""
    return kb_pb2.Operation(create=kb_pb2.Creation(type=type_name, title=title, content=dumps(content)))


def replacement(artifact_id, content):
    """A Write of a whole artifact inside a set."""
    return kb_pb2.Operation(write=kb_pb2.Replacement(locator=kb_pb2.Locator(id=artifact_id), content=dumps(content)))


def write(client, artifact_id, content, message="Change an artifact", actor=CLIENT, path=""):
    """A Write of a whole artifact, or of the node at path inside it, under the client's role unless another actor is
    given. Returns the response, faults and all."""
    return client.Write(kb_pb2.WriteRequest(
        locator=kb_pb2.Locator(id=artifact_id, path=path), content=dumps(content), actor=actor, message=message,
    ))


def journal(client, artifact=""):
    """The journal's entries, those about one artifact when it is named."""
    return client.Journal(kb_pb2.JournalRequest(artifact=artifact))

def search(client, text):
    """A search of the prose for the text."""
    return client.Search(kb_pb2.SearchRequest(text=text))


def refs(client, artifact_id, depth, inward=False, via="", type_name=""):
    """The links out of an artifact, or into it when inward, followed as many steps as depth says, through the field
    via names and to artifacts of the kind type_name names when either is given."""
    direction = kb_pb2.RefsRequest.IN if inward else kb_pb2.RefsRequest.OUT
    return client.Refs(kb_pb2.RefsRequest(
        locator=kb_pb2.Locator(id=artifact_id), depth=depth, direction=direction, via=via, type=type_name,
    ))


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
    return client.List(kb_pb2.ListRequest(type=type_name, fields=fields or {}, form=form))


def everything_under(directory):
    """Every file below a directory, with its bytes, so a step can tell whether anything was written."""
    return {path: path.read_bytes() for path in sorted(directory.rglob("*")) if path.is_file()}
