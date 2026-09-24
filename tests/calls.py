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
