"""The contract's servicer: every rpc, over one store. Hosted in-process today; grpc.server can host it later.

Each rpc first turns what the request carries into checked values (kb.values); nothing past that point sees a
string that came from the request.
"""
import copy

from kb import canonical, journal, search, validation, values
from kb.content import dumps
from kb.contract import kb_pb2, kb_pb2_grpc
from kb.metaschema import METASCHEMA
from kb.store import Draft, Store, Unreadable
from kb.values import ArtifactId, Kind

METASCHEMA_ID = ArtifactId(Kind("schema"), "schema")


class KbServicer(kb_pb2_grpc.KbServicer):
    def __init__(self, root=None):
        """Over the store at root; with none, a servicer that can only start a store, taking its root from the request."""
        self._store = Store(root) if root is not None else None

    def Init(self, request, context):
        if not request.actor.role:
            return kb_pb2.InitResponse(faults=[kb_pb2.Fault(
                rule="actor", message="a store can only be started under a role",
            )])
        try:
            store = Store(values.root(request.root))
        except values.Refused as refused:
            return kb_pb2.InitResponse(faults=refused.faults)
        store.start()
        metaschema = {"id": str(METASCHEMA_ID), "type": "schema", "schema_version": 1, "revision": 1, **METASCHEMA}
        path = store.save(METASCHEMA_ID, canonical.dump(canonical.order(metaschema, METASCHEMA["schema"])))
        entry = journal.write(
            store.dir, actor=request.actor, op="create", artifact=str(METASCHEMA_ID), path="",
            revision=1, schema_version=1, written=path, message="initialise store",
        )
        store.commit([store.dir / "store.yaml", path, entry], request.actor.role, "initialise store")
        return kb_pb2.InitResponse()

    def Create(self, request, context):
        creation = kb_pb2.Creation(type=request.type, title=request.title, content=request.content)
        landed = self._land([kb_pb2.Operation(create=creation)], request.actor, request.message)
        if landed.faults:
            return kb_pb2.CreateResponse(faults=landed.faults)
        return kb_pb2.CreateResponse(id=landed.results[0].id, revision=landed.results[0].revision)

    def Write(self, request, context):
        replacement = kb_pb2.Replacement(locator=request.locator, content=request.content)
        landed = self._land([kb_pb2.Operation(write=replacement)], request.actor, request.message)
        if landed.faults:
            return kb_pb2.WriteResponse(faults=landed.faults)
        return kb_pb2.WriteResponse(revision=landed.results[0].revision)

    def Apply(self, request, context):
        return self._land(request.operations, request.actor, request.message)

    def _land(self, operations, actor, message) -> kb_pb2.ApplyResponse:
        """The write path. Each operation is applied in order to a draft of the store and checked there, against the
        store as the operations before it left it; only when every one passes is anything written, each artifact
        saved, one journal entry per operation naming the set, and one commit.

        A fault anywhere refuses the whole set with every fault found, and nothing is written.
        """
        draft = Draft(self._store)
        touched, faults = [], []
        for operation in operations:
            try:
                touched.append(self._apply(draft, operation))
            except values.Refused as refused:
                faults += refused.faults
        if faults:
            return kb_pb2.ApplyResponse(faults=faults)
        texts = []
        for op, artifact_id in touched:
            try:
                texts.append((op, artifact_id, canonical.dump(draft.load(artifact_id))))
            except canonical.NotCanonical as fault:
                faults.append(kb_pb2.Fault(artifact=str(artifact_id), rule="content", message=str(fault)))
        if faults:
            return kb_pb2.ApplyResponse(faults=faults)
        written, results, batch = [], [], ""
        for seq, (op, artifact_id, text) in enumerate(texts, start=1):
            artifact = draft.load(artifact_id)
            path = self._store.save(artifact_id, text)
            entry = journal.write(
                self._store.dir, actor=actor, op=op, artifact=str(artifact_id), path="",
                revision=artifact["revision"], schema_version=artifact["schema_version"],
                written=path, message=message, seq=seq, batch=batch,
            )
            batch = batch or entry.stem
            written += [path, entry]
            results.append(kb_pb2.Result(id=str(artifact_id), revision=artifact["revision"]))
        self._store.commit(written, actor.role, message)
        return kb_pb2.ApplyResponse(batch=batch, results=results)

    def _apply(self, draft: Draft, operation: kb_pb2.Operation) -> tuple[str, ArtifactId]:
        """One operation applied to the draft. Returns what it did and to which artifact; raises values.Refused."""
        if operation.WhichOneof("operation") == "create":
            return "create", self._create(draft, operation.create)
        return "write", self._replace(draft, operation.write)

    def _create(self, draft: Draft, creation: kb_pb2.Creation) -> ArtifactId:
        kind = values.kind(creation.type)
        if not draft.holds(ArtifactId(Kind("schema"), kind.name)):
            raise values.Refused([kb_pb2.Fault(
                rule="kind", message=f"a kind must name a type the store holds; the store holds no type called {kind.name!r}",
            )])
        at = f"{kind.name}/{values.slug(creation.title)}"
        faults = []
        try:
            artifact_id = _unclaimed(draft, values.named(kind, creation.title))
            at = str(artifact_id)
        except values.Refused as refused:
            faults += refused.faults
        try:
            content = values.content(at, creation.content)
        except values.Refused as refused:
            faults += refused.faults
        if faults:
            raise values.Refused(faults)
        schema = draft.schema(kind)
        faults = validation.validate(at, {"title": creation.title, **content}, schema["schema"], draft)
        if faults:
            raise values.Refused(faults)
        _name_items(schema["schema"], content, keep_named=False)
        artifact = {
            **content,
            "id": str(artifact_id), "type": kind.name,
            "schema_version": schema["version"], "revision": 1, "title": creation.title,
        }
        draft.put(artifact_id, canonical.order(artifact, schema["schema"]))
        return artifact_id

    def _replace(self, draft: Draft, replacement: kb_pb2.Replacement) -> ArtifactId:
        locator = values.locator(replacement.locator)
        content = values.content(str(locator.id), replacement.content, at_root=not locator.place)
        current = draft.load(locator.id)
        if locator.place:
            content = _placed(current, locator, content)
        schema = draft.schema(locator.id.kind)
        faults = validation.validate(str(locator.id), {"title": current["title"], **content}, schema["schema"], draft)
        if faults:
            raise values.Refused(faults)
        _name_items(schema["schema"], content, keep_named=True)
        artifact = {
            **content,
            "id": current["id"], "type": current["type"],
            "schema_version": schema["version"], "revision": current["revision"] + 1, "title": current["title"],
        }
        draft.put(locator.id, canonical.order(artifact, schema["schema"]))
        return locator.id

    def Read(self, request, context):
        try:
            locator = values.locator(request.locator)
        except values.Refused as refused:
            return kb_pb2.ReadResponse(faults=refused.faults)
        if not self._store.holds(locator.id):
            return kb_pb2.ReadResponse(faults=[_not_found(locator.id)])
        try:
            if request.level == kb_pb2.ReadRequest.WHOLE:
                return self._whole(locator, request.depth)
            return self._summary(locator)
        except Unreadable as unreadable:
            return kb_pb2.ReadResponse(faults=[unreadable.fault])

    def _whole(self, locator, depth: int):
        artifact = self._resolved(locator.id, depth, {str(locator.id)})
        return kb_pb2.ReadResponse(
            id=artifact["id"], type=artifact["type"],
            schema_version=artifact["schema_version"], revision=artifact["revision"],
            title=artifact["title"],
            content=dumps({key: value for key, value in artifact.items() if key not in canonical.IDENTITY}),
        )

    def _resolved(self, artifact_id: ArtifactId, depth: int, on_path: set) -> dict:
        """The artifact as stored, each link followed depth steps with the target, itself resolved, in place of its
        name. A target on the path already being filled in stays a name, so a loop ends."""
        artifact = self._store.load(artifact_id)
        if depth < 1:
            return artifact
        def fill(target):
            if target in on_path:
                return target
            return self._resolved(values.artifact_id(target), depth - 1, on_path | {target})
        resolved = dict(artifact)
        for field in validation.references(self._store.schema(artifact_id.kind)["schema"], self._store):
            value = artifact.get(field)
            if isinstance(value, list):
                resolved[field] = [fill(target) for target in value]
            elif value is not None:
                resolved[field] = fill(value)
        return resolved

    def _summary(self, locator):
        artifact = self._store.load(locator.id)
        schema = self._store.schema(locator.id.kind)["schema"]
        response = kb_pb2.ReadResponse(
            id=artifact["id"], type=artifact["type"],
            schema_version=artifact["schema_version"], revision=artifact["revision"],
            title=artifact["title"],
            content=dumps(_summary_fields(artifact, schema)),
        )
        for field, _, target in validation.links(artifact, schema, self._store):
            response.references.append(self._stub(field, values.artifact_id(target)))
        for collection in schema.get("parts", {}):
            for item in artifact.get(collection, []):
                response.parts.append(kb_pb2.PartStub(collection=collection, id=item["id"], title=item["title"]))
        for (type_name, field), count in self._inbound(str(locator.id)).items():
            response.inbound.append(kb_pb2.InboundCount(type=type_name, field=field, count=count))
        return response

    def Validate(self, request, context):
        """Every artifact checked against its type; a file that cannot be read is reported and the check goes on."""
        violations = []
        for artifact_id in self._store.ids():
            try:
                artifact = self._store.load(artifact_id)
                schema = self._store.schema(artifact_id.kind)["schema"]
            except Unreadable as unreadable:
                violations.append(unreadable.fault)
                continue
            content = {key: value for key, value in artifact.items() if key not in canonical.IDENTITY[:4]}
            violations += validation.validate(str(artifact_id), content, schema, self._store)
        return kb_pb2.ValidateResponse(violations=violations)

    def Journal(self, request, context):
        """The journal's entries, oldest first, those about one artifact when the request names it."""
        try:
            artifact = str(values.artifact_id(request.artifact)) if request.artifact else ""
        except values.Refused as refused:
            return kb_pb2.JournalResponse(faults=refused.faults)
        return kb_pb2.JournalResponse(entries=[
            _entry(entry) for entry in journal.entries(self._store.dir)
            if not artifact or entry["artifact"] == artifact
        ])

    def Search(self, request, context):
        """Every section whose prose holds a word searched for, with a stub of its artifact, most often first."""
        return kb_pb2.SearchResponse(matches=[
            kb_pb2.Match(stub=self._stub("", values.artifact_id(hit.artifact)), section=hit.section, snippet=hit.snippet)
            for hit in search.rank(self._store.artifacts(), request.text)
        ])

    def Refs(self, request, context):
        """What an artifact's links reach, a step at a time out to the depth asked: each artifact once, by the
        shortest route, the one asked about never."""
        try:
            locator = values.locator(request.locator)
        except values.Refused as refused:
            return kb_pb2.RefsResponse(faults=refused.faults)
        if not self._store.holds(locator.id):
            return kb_pb2.RefsResponse(faults=[_not_found(locator.id)])
        reached, seen, frontier = [], {str(locator.id)}, [(locator.id, [])]
        for _ in range(request.depth):
            following = []
            for artifact_id, route in frontier:
                artifact = self._store.load(artifact_id)
                schema = self._store.schema(artifact_id.kind)["schema"]
                for field, _, target in validation.links(artifact, schema, self._store):
                    if target in seen:
                        continue
                    seen.add(target)
                    target_id = values.artifact_id(target)
                    taken = [*route, kb_pb2.Hop(field=field, id=target)]
                    reached.append(kb_pb2.Reached(stub=self._stub(field, target_id), route=taken))
                    following.append((target_id, taken))
            frontier = following
        return kb_pb2.RefsResponse(reached=reached)

    def _stub(self, field, target_id: ArtifactId):
        target = self._store.load(target_id)
        schema = self._store.schema(target_id.kind)["schema"]
        return kb_pb2.Stub(
            field=field, id=target["id"], type=target["type"], title=target["title"],
            fields=dumps(_summary_fields(target, schema)),
        )

    def _inbound(self, artifact_id: str):
        """How many artifacts point at this one, by their type and the field they use."""
        counts = {}
        for other in self._store.artifacts():
            schema = self._store.schema(values.kind(other["type"]))["schema"]
            pointing = {field for field, _, target in validation.links(other, schema, self._store) if target == artifact_id}
            for field in pointing:
                counts[(other["type"], field)] = counts.get((other["type"], field), 0) + 1
        return counts


def _entry(entry: dict) -> kb_pb2.Entry:
    return kb_pb2.Entry(
        id=entry["id"], at=entry["at"], actor=kb_pb2.Actor(**entry["actor"]), op=entry["op"],
        artifact=entry["artifact"], path=entry["path"], revision=entry["revision"],
        schema_version=entry["schema_version"], digest=entry["digest"], message=entry["message"], batch=entry["batch"],
    )


def _placed(artifact: dict, locator: values.Locator, node: dict) -> dict:
    """The artifact's content with the node at the locator's place replaced by the one given. A place is pairs of a
    list and an item in it, a section named by its title's name and a part by its id, and may end in a field."""
    content = copy.deepcopy({key: value for key, value in artifact.items() if key not in canonical.IDENTITY})
    holder, steps = content, list(locator.place)
    while len(steps) > 1:
        collection, name = steps.pop(0), steps.pop(0)
        items = holder.get(collection, [])
        index = next((index for index, item in enumerate(items) if _node_name(collection, item) == name), None)
        if index is None:
            raise values.Refused([kb_pb2.Fault(
                artifact=str(locator.id), path="/".join(locator.place), rule="not-found",
                message=f"{str(locator.id)!r} holds nothing at {'/'.join(locator.place)!r}",
            )])
        if not steps:
            items[index] = node if collection == "sections" else {"id": name, **node}
            return content
        holder = items[index]
    holder[steps[0]] = node
    return content


def _node_name(collection: str, item: dict) -> str:
    """How a place names an item: a section by its title's name, a part by its id."""
    return values.slug(item["title"]) if collection == "sections" else item.get("id")


def _name_items(schema: dict, content: dict, keep_named: bool) -> None:
    """Every item of every part collection given its name: from its title when it carries one, otherwise from its
    place in the collection, counted from 1. On a write an item already carrying a name is the item of that name,
    moved or changed where it stands, and keeps it; a name is minted once and never worked out again."""
    for collection in schema.get("parts", {}):
        for place, item in enumerate(content.get(collection, []), start=1):
            if keep_named and "id" in item:
                continue
            item["id"] = values.slug(item["title"]) if "title" in item else str(place)


def _not_found(artifact_id: ArtifactId) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(artifact_id), rule="not-found", message=f"the store holds nothing by the name {str(artifact_id)!r}",
    )


def _unclaimed(draft: Draft, named: ArtifactId) -> ArtifactId:
    """The name a title gives, or, when the store or an earlier change in the set already holds it, that name with
    -2, -3 and so on added: the first that nothing holds. What already holds a name keeps it."""
    candidate, number = named, 1
    while draft.holds(candidate):
        number += 1
        candidate = ArtifactId(named.kind, f"{named.slug}-{number}")
    return candidate


def _summary_fields(artifact, schema):
    return {name: artifact[name] for name in schema.get("summary", []) if name in artifact}

