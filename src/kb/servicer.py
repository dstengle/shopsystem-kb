"""The contract's servicer: every rpc, over one store. Hosted in-process today; grpc.server can host it later."""
from kb import canonical, validation
from kb.content import loads
from kb.contract import kb_pb2, kb_pb2_grpc
from kb.metaschema import METASCHEMA
from kb.store import Store, slug


class KbServicer(kb_pb2_grpc.KbServicer):
    def __init__(self, root):
        self._store = Store(root)

    def Init(self, request, context):
        store = Store(request.root)
        store.start()
        metaschema = {"id": "schema/schema", "type": "schema", "schema_version": 1, "revision": 1, **METASCHEMA}
        path = store.save(canonical.order(metaschema, METASCHEMA["schema"]))
        store.commit([store.dir / "store.yaml", path], "kb", "Start the store")
        return kb_pb2.InitResponse()

    def Create(self, request, context):
        content = loads(request.content)
        schema = self._store.schema(request.type)
        artifact_id = f"{request.type}/{slug(content['title'])}"
        faults = validation.validate(artifact_id, content, schema["schema"])
        if faults:
            return kb_pb2.CreateResponse(faults=faults)
        for collection in schema["schema"].get("parts", {}):
            for item in content.get(collection, []):
                item["id"] = slug(item["title"])
        artifact = {
            "id": artifact_id, "type": request.type,
            "schema_version": schema["version"], "revision": 1,
            **content,
        }
        path = self._store.save(canonical.order(artifact, schema["schema"]))
        self._store.commit([path], request.actor.role, request.message)
        return kb_pb2.CreateResponse(id=artifact_id, revision=1)

    def Read(self, request, context):
        artifact = self._store.load(request.locator.id)
        schema = self._store.schema(artifact["type"])["schema"]
        response = kb_pb2.ReadResponse(
            id=artifact["id"], type=artifact["type"],
            schema_version=artifact["schema_version"], revision=artifact["revision"],
            title=artifact["title"],
        )
        for collection in schema.get("parts", {}):
            for item in artifact.get(collection, []):
                response.parts.append(kb_pb2.PartStub(collection=collection, id=item["id"], title=item["title"]))
        return response
