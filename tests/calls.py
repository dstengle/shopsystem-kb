"""How the steps call the contract: one helper per rpc, plus the types the Backgrounds define."""
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


def request(client, type_name, title, content, message="Create an artifact"):
    """A Create as the client sends it: the title beside the content. Returns the response, faults and all."""
    return client.Create(kb_pb2.CreateRequest(
        type=type_name, title=title, content=dumps(content), actor=CLIENT, message=message,
    ))


def create(client, type_name, content, message="Create an artifact"):
    """Create from a dict written the way a user writes a file, title inside; the title is lifted out and sent beside."""
    content = dict(content)
    title = content.pop("title", "")
    response = request(client, type_name, title, content, message)
    assert not response.faults, response.faults
    return response


def define(client, type_content):
    """Define a type: a Create of type `schema`."""
    return create(client, "schema", type_content, message=f"Define {type_content['title']}")


def read(client, artifact_id):
    return client.Read(kb_pb2.ReadRequest(locator=kb_pb2.Locator(id=artifact_id)))


def apply(client, operations, message="Make several changes"):
    """An Apply of the operations in order, under the client's role. Returns the response, faults and all."""
    return client.Apply(kb_pb2.ApplyRequest(operations=operations, actor=CLIENT, message=message))


def creation(type_name, title, content):
    """A Create inside a set: the title beside the content, the role and message the set's."""
    return kb_pb2.Operation(create=kb_pb2.Creation(type=type_name, title=title, content=dumps(content)))


def replacement(artifact_id, content):
    """A Write of a whole artifact inside a set."""
    return kb_pb2.Operation(write=kb_pb2.Replacement(locator=kb_pb2.Locator(id=artifact_id), content=dumps(content)))


def write(client, artifact_id, content, message="Change an artifact"):
    """A Write of a whole artifact under the client's role. Returns the response, faults and all."""
    return client.Write(kb_pb2.WriteRequest(
        locator=kb_pb2.Locator(id=artifact_id), content=dumps(content), actor=CLIENT, message=message,
    ))
