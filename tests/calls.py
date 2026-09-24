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


def define(client, type_content):
    """Define a type: a Create of type `schema`."""
    response = client.Create(kb_pb2.CreateRequest(
        type="schema", content=dumps(type_content), actor=CLIENT,
        message=f"Define {type_content['title']}",
    ))
    assert not response.faults, response.faults
    return response


def create(client, type_name, content, message="Create an artifact"):
    response = client.Create(kb_pb2.CreateRequest(
        type=type_name, content=dumps(content), actor=CLIENT, message=message,
    ))
    assert not response.faults, response.faults
    return response


def read(client, artifact_id):
    return client.Read(kb_pb2.ReadRequest(locator=kb_pb2.Locator(id=artifact_id)))
