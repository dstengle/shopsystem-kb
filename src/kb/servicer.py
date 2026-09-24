"""The contract's servicer: every rpc, over one store. Hosted in-process today; grpc.server can host it later."""
from kb import canonical, journal, validation
from kb.content import ContentFault, loads, dumps
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
        entry = journal.write(
            store.dir, actor=request.actor, op="create", artifact="schema/schema", path="",
            revision=1, schema_version=1, written=path, message="initialise store",
        )
        store.commit([store.dir / "store.yaml", path, entry], request.actor.role, "initialise store")
        return kb_pb2.InitResponse()

    def Create(self, request, context):
        artifact_id = f"{request.type}/{slug(request.title)}"
        try:
            content = loads(request.content)
        except ContentFault as fault:
            return kb_pb2.CreateResponse(faults=[kb_pb2.Fault(artifact=artifact_id, rule="content", message=str(fault))])
        faults = _title_faults(artifact_id, request.title) + _identity_faults(artifact_id, content)
        if faults:
            return kb_pb2.CreateResponse(faults=faults)
        schema = self._store.schema(request.type)
        faults = validation.validate(artifact_id, {"title": request.title, **content}, schema["schema"])
        if faults:
            return kb_pb2.CreateResponse(faults=faults)
        for collection in schema["schema"].get("parts", {}):
            for item in content.get(collection, []):
                item["id"] = slug(item["title"])
        artifact = {
            **content,
            "id": artifact_id, "type": request.type,
            "schema_version": schema["version"], "revision": 1, "title": request.title,
        }
        path = self._store.save(canonical.order(artifact, schema["schema"]))
        self._store.commit([path], request.actor.role, request.message)
        return kb_pb2.CreateResponse(id=artifact_id, revision=1)

    def Read(self, request, context):
        if not self._store.path(request.locator.id).is_file():
            return kb_pb2.ReadResponse(faults=[kb_pb2.Fault(
                artifact=request.locator.id, rule="not-found",
                message=f"the store holds nothing by the name {request.locator.id!r}",
            )])
        artifact = self._store.load(request.locator.id)
        schema = self._store.schema(artifact["type"])["schema"]
        response = kb_pb2.ReadResponse(
            id=artifact["id"], type=artifact["type"],
            schema_version=artifact["schema_version"], revision=artifact["revision"],
            title=artifact["title"],
            content=dumps(_summary_fields(artifact, schema)),
        )
        for field in _reference_fields(schema):
            for target_id in _as_list(artifact.get(field)):
                response.references.append(self._stub(field, target_id))
        for collection in schema.get("parts", {}):
            for item in artifact.get(collection, []):
                response.parts.append(kb_pb2.PartStub(collection=collection, id=item["id"], title=item["title"]))
        for (type_name, field), count in self._inbound(artifact["id"]).items():
            response.inbound.append(kb_pb2.InboundCount(type=type_name, field=field, count=count))
        return response

    def _stub(self, field, target_id):
        target = self._store.load(target_id)
        schema = self._store.schema(target["type"])["schema"]
        return kb_pb2.Stub(
            field=field, id=target["id"], type=target["type"], title=target["title"],
            fields=dumps(_summary_fields(target, schema)),
        )

    def _inbound(self, artifact_id):
        """How many artifacts point at this one, by their type and the field they use."""
        counts = {}
        for other in self._store.artifacts():
            schema = self._store.schema(other["type"])["schema"]
            for field in _reference_fields(schema):
                if artifact_id in _as_list(other.get(field)):
                    key = (other["type"], field)
                    counts[key] = counts.get(key, 0) + 1
        return counts


def _title_faults(artifact_id, title):
    """A title is required, and must leave something to make a name from."""
    if not title:
        return [kb_pb2.Fault(artifact=artifact_id, path="title", rule="title",
                             message="an artifact cannot be created without a title")]
    if not slug(title):
        return [kb_pb2.Fault(artifact=artifact_id, path="title", rule="title",
                             message=f"a title must leave something to make a name from; {title!r} leaves nothing")]
    return []


def _identity_faults(artifact_id, content):
    """Content holds only what the type declares; the identity keys are the store's, the title travels beside."""
    faults = []
    for key in canonical.IDENTITY:
        if key not in content:
            continue
        if key == "title":
            message = f"a title is given alongside the content, never inside it; the content carried the title {content[key]!r}"
        else:
            message = f"content holds only what the type declares; {key} is settled by the store, and the content carried {key}: {content[key]!r}"
        faults.append(kb_pb2.Fault(artifact=artifact_id, path=key, rule="identity", message=message))
    return faults


def _summary_fields(artifact, schema):
    return {name: artifact[name] for name in schema.get("summary", []) if name in artifact}


def _reference_fields(schema):
    return [name for name, field in schema.get("properties", {}).items() if "ref" in field]


def _as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]
