"""A caller beside kb's container, for the image check: kb's own image with this program as its entry point, under
`KB_ROOT=/kb-connection`, where a compose config puts the connection `kb/server.yaml`. Every call goes through
`kb.client.connect()` and so over the network to the server the connection names.

    python caller.py change        reads the seeded decision, defines the note type, creates a note, prints its id
    python caller.py read <id>     reads the artifact named, prints its id and title

It exits 0 when each call answers as it should, and 1, naming the call, when one does not.
"""
import sys

from kb.client import connect
from kb.content import dumps
from kb.contract import kb_pb2

SEEDED = "decision/price-reviews-happen-weekly"
NOTE_TYPE = {
    "version": 1,
    "schema": {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]},
}
CALLER = kb_pb2.Signature(role="caller", message="The image check's caller")


def answered(call: str, response):
    """The response's result, or the program ended naming the call and its refusal."""
    if response.WhichOneof("outcome") == "refusal":
        sys.exit(f"{call} refused: {list(response.refusal.faults)}")
    return response.result


def read(client, artifact_id: str):
    """A summary read of the artifact named."""
    return answered(f"Read {artifact_id}", client.Read(kb_pb2.ReadRequest(
        locator=kb_pb2.Locator(id=artifact_id), summary=kb_pb2.ReadRequest.Summary(),
    )))


def create(client, kind: str, title: str, content: dict) -> str:
    """A Create of the kind given, answering the name kb gave it."""
    return answered(f"Create {kind}", client.Create(kb_pb2.CreateRequest(
        kind=kind, title=title, content=dumps(content), signature=CALLER,
    ))).id


def change(client) -> None:
    """The seeded decision read, a type defined, and an artifact of it created, all through the server."""
    seeded = read(client, SEEDED)
    if seeded.title != "Price reviews happen weekly":
        sys.exit(f"Read {SEEDED} answered the title {seeded.title!r}")
    create(client, "schema", "Note", NOTE_TYPE)
    print(create(client, "note", "Served from a container", {}))


def main(argv: list[str]) -> None:
    client = connect()
    where = client.where()
    if not where.address:
        sys.exit(f"the client found no connection to a server: {where}")
    if argv[0] == "change":
        change(client)
    else:
        found = read(client, argv[1])
        print(f"{found.id}\t{found.title}")


if __name__ == "__main__":
    main(sys.argv[1:])
