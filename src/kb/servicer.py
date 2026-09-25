"""The contract's servicer: every rpc, over one store. Hosted in-process today; grpc.server can host it later.

Each rpc first turns what the request carries into checked values (kb.values); nothing past that point sees a
string that came from the request.
"""
import copy
from datetime import datetime
from typing import NamedTuple

from kb import canonical, journal, search, validation, values
from kb.content import dumps, text
from kb.contract import kb_pb2, kb_pb2_grpc
from kb.metaschema import METASCHEMA
from kb.store import Draft, Store, Unreadable
from kb.values import ArtifactId, Kind

METASCHEMA_ID = ArtifactId(Kind("schema"), "schema")


class Change(NamedTuple):
    """What one operation did, to which artifact, at which place in it, and, for an item added, the item's name."""
    op: str
    artifact_id: ArtifactId
    path: str = ""
    item: str = ""


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

    def Append(self, request, context):
        addition = kb_pb2.Addition(locator=request.locator, content=request.content)
        landed = self._land([kb_pb2.Operation(append=addition)], request.actor, request.message)
        if landed.faults:
            return kb_pb2.AppendResponse(faults=landed.faults)
        return kb_pb2.AppendResponse(id=landed.results[0].item, revision=landed.results[0].revision)

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
        for change in touched:
            try:
                texts.append((change, canonical.dump(draft.load(change.artifact_id))))
            except canonical.NotCanonical as fault:
                faults.append(kb_pb2.Fault(artifact=str(change.artifact_id), rule="content", message=str(fault)))
        if faults:
            return kb_pb2.ApplyResponse(faults=faults)
        written, results, batch = [], [], ""
        for seq, (change, text) in enumerate(texts, start=1):
            artifact = draft.load(change.artifact_id)
            path = self._store.save(change.artifact_id, text)
            entry = journal.write(
                self._store.dir, actor=actor, op=change.op, artifact=str(change.artifact_id), path=change.path,
                revision=artifact["revision"], schema_version=artifact["schema_version"],
                written=path, message=message, seq=seq, batch=batch,
            )
            batch = batch or entry.stem
            written += [path, entry]
            results.append(kb_pb2.Result(id=str(change.artifact_id), revision=artifact["revision"], item=change.item))
        self._store.commit(written, actor.role, message)
        return kb_pb2.ApplyResponse(batch=batch, results=results)

    def _apply(self, draft: Draft, operation: kb_pb2.Operation) -> Change:
        """One operation applied to the draft. Returns what it did; raises values.Refused."""
        which = operation.WhichOneof("operation")
        if which == "create":
            return Change("create", self._create(draft, operation.create))
        if which == "append":
            return self._append(draft, operation.append)
        return Change("write", self._replace(draft, operation.write))

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
        if not draft.holds(locator.id):
            raise values.Refused([_not_found(locator.id)])
        content = values.content(str(locator.id), replacement.content, at_root=not locator.place)
        current = draft.load(locator.id)
        if locator.place:
            content = _placed(current, locator, content)
        _revise(draft, locator.id, current, content)
        return locator.id

    def _append(self, draft: Draft, addition: kb_pb2.Addition) -> Change:
        """One item put at the end of a collection the artifact's type declares, and named there."""
        locator = values.locator(addition.locator)
        if not draft.holds(locator.id):
            raise values.Refused([_not_found(locator.id)])
        item = values.item(str(locator.id), addition.content)
        collection = "/".join(locator.place)
        if collection not in draft.schema(locator.id.kind)["schema"].get("parts", {}):
            raise values.Refused([kb_pb2.Fault(
                artifact=str(locator.id), path=collection, rule="not-found",
                message=f"{str(locator.id)!r} holds no collection called {collection!r}",
            )])
        current = draft.load(locator.id)
        content = _content_of(current)
        content.setdefault(collection, []).append(item)
        _revise(draft, locator.id, current, content)
        return Change("append", locator.id, f"{collection}/{item['id']}", item["id"])

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
            if request.level == kb_pb2.ReadRequest.SECTION:
                return self._section(locator, request.section)
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

    def _section(self, locator, title: str):
        """The first section with that title, at any depth, in the order the artifact holds them, and nothing else."""
        artifact = self._store.load(locator.id)
        found = _find_section(artifact.get("sections", []), title)
        if found is None:
            return kb_pb2.ReadResponse(faults=[kb_pb2.Fault(
                artifact=str(locator.id), path="sections", rule="not-found",
                message=f"{str(locator.id)!r} holds no section titled {title!r}",
            )])
        return kb_pb2.ReadResponse(
            id=artifact["id"], type=artifact["type"],
            schema_version=artifact["schema_version"], revision=artifact["revision"],
            title=artifact["title"], content=dumps(found),
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
        """Every artifact checked against the current version of its type, and listed as stale when it was last
        checked against an older one; a file that cannot be read is reported and the check goes on."""
        violations, stale = [], []
        for artifact_id in self._store.ids():
            try:
                artifact = self._store.load(artifact_id)
                schema = self._store.schema(artifact_id.kind)
            except Unreadable as unreadable:
                violations.append(unreadable.fault)
                continue
            if artifact["schema_version"] < schema["version"]:
                stale.append(kb_pb2.Stale(
                    artifact=str(artifact_id), schema_version=artifact["schema_version"], current=schema["version"],
                ))
            content = {key: value for key, value in artifact.items() if key not in canonical.IDENTITY[:4]}
            violations += validation.validate(str(artifact_id), content, schema["schema"], self._store)
        return kb_pb2.ValidateResponse(violations=violations, stale=stale)

    def Journal(self, request, context):
        """The journal's entries, oldest first, narrowed by each of artifact, role, piece of work and time given."""
        faults = []
        try:
            artifact = str(values.artifact_id(request.artifact)) if request.artifact else ""
        except values.Refused as refused:
            faults += refused.faults
        try:
            since = values.since(request.since) if request.since else None
        except values.Refused as refused:
            faults += refused.faults
        if faults:
            return kb_pb2.JournalResponse(faults=faults)
        return kb_pb2.JournalResponse(entries=[
            _entry(entry) for entry in journal.entries(self._store.dir)
            if (not artifact or entry.get("artifact") == artifact)
            and (not request.role or entry["actor"]["role"] == request.role)
            and (not request.execution or entry["actor"]["execution"] == request.execution)
            and (since is None or datetime.fromisoformat(entry["at"]) >= since)
        ])

    def Search(self, request, context):
        """Every section whose prose, or field whose value, holds a word searched for, as the scope asks, among the
        artifacts of one kind when a type is given, with a stub of its artifact, most often first."""
        try:
            kind = values.kind(request.type) if request.type else None
        except values.Refused as refused:
            return kb_pb2.SearchResponse(faults=refused.faults)
        artifacts = (artifact for artifact in self._store.artifacts() if kind is None or artifact["type"] == kind.name)
        scope = request.scope
        hits = search.rank(
            artifacts, request.text,
            sections=scope != kb_pb2.SearchRequest.FIELDS, fields=scope != kb_pb2.SearchRequest.SECTIONS,
        )
        return kb_pb2.SearchResponse(matches=[
            kb_pb2.Match(
                stub=self._stub("", values.artifact_id(hit.artifact)), section=hit.section, field=hit.field,
                snippet=hit.snippet,
            )
            for hit in hits
        ])

    def Refs(self, request, context):
        """What an artifact's links reach, out of it or into it, a step at a time out to the depth asked: each artifact
        once, by the shortest route, the one asked about never. A via or a type narrows every step."""
        faults = []
        try:
            locator = values.locator(request.locator)
        except values.Refused as refused:
            faults += refused.faults
        try:
            kind = values.kind(request.type) if request.type else None
        except values.Refused as refused:
            faults += refused.faults
        if faults:
            return kb_pb2.RefsResponse(faults=faults)
        if not self._store.holds(locator.id):
            return kb_pb2.RefsResponse(faults=[_not_found(locator.id)])
        step = self._inward if request.direction == kb_pb2.RefsRequest.IN else self._outward
        reached, seen, frontier = [], {str(locator.id)}, [(locator.id, [])]
        for _ in range(request.depth):
            following = []
            for artifact_id, route in frontier:
                for field, other_id in step(artifact_id):
                    if str(other_id) in seen or (request.via and field != request.via):
                        continue
                    if kind is not None and other_id.kind != kind:
                        continue
                    seen.add(str(other_id))
                    taken = [*route, kb_pb2.Hop(field=field, id=str(other_id))]
                    reached.append(kb_pb2.Reached(stub=self._stub(field, other_id), route=taken))
                    following.append((other_id, taken))
            frontier = following
        return kb_pb2.RefsResponse(reached=reached)

    def _outward(self, artifact_id: ArtifactId) -> list[tuple[str, ArtifactId]]:
        """Each link out of an artifact, as the field and the name it points at."""
        artifact = self._store.load(artifact_id)
        schema = self._store.schema(artifact_id.kind)["schema"]
        return [(field, values.artifact_id(target)) for field, _, target in validation.links(artifact, schema, self._store)]

    def _inward(self, artifact_id: ArtifactId) -> list[tuple[str, ArtifactId]]:
        """Each link into an artifact or a part inside it, as the field that points there and the artifact that holds
        that field, in path order."""
        found = []
        for other_id in self._store.ids():
            other = self._store.load(other_id)
            schema = self._store.schema(other_id.kind)["schema"]
            for field, _, target in validation.links(other, schema, self._store):
                if _points_at(target, artifact_id):
                    found.append((field, other_id))
        return found

    def List(self, request, context):
        """Every artifact of a kind whose fields hold the values asked for, in path order, as stubs or names."""
        try:
            kind = values.kind(request.type)
        except values.Refused as refused:
            return kb_pb2.ListResponse(faults=refused.faults)
        matched = [
            artifact_id for artifact_id in self._store.ids()
            if artifact_id.kind == kind and _holds(self._store.load(artifact_id), request.fields)
        ]
        if request.form == kb_pb2.ListRequest.IDS:
            return kb_pb2.ListResponse(ids=[str(artifact_id) for artifact_id in matched])
        return kb_pb2.ListResponse(stubs=[self._stub("", artifact_id) for artifact_id in matched])

    def Snapshot(self, request, context):
        """One journal entry listing each artifact named with its version now and the fingerprint of its file, under
        the actor and the message given, in a commit of its own."""
        named, faults = [], []
        for name in request.artifacts:
            try:
                artifact_id = values.artifact_id(name)
            except values.Refused as refused:
                faults += refused.faults
                continue
            if not self._store.holds(artifact_id):
                faults.append(_not_found(artifact_id))
                continue
            named.append(artifact_id)
        if faults:
            return kb_pb2.SnapshotResponse(faults=faults)
        read = [
            {
                "artifact": str(artifact_id), "revision": self._store.load(artifact_id)["revision"],
                "digest": journal.digest(self._store.path(artifact_id)),
            }
            for artifact_id in named
        ]
        entry = journal.snapshot(self._store.dir, actor=request.actor, read=read, message=request.message)
        self._store.commit([entry], request.actor.role, request.message)
        return kb_pb2.SnapshotResponse(entry=entry.stem)

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


def _points_at(target: str, artifact_id: ArtifactId) -> bool:
    """Whether a link lands on the artifact or on a part inside it."""
    return target.partition("#")[0] == str(artifact_id)


def _holds(artifact: dict, fields) -> bool:
    """Whether each field named holds the value given, compared as the text the value is written as."""
    return all(field in artifact and text(artifact[field]) == value for field, value in fields.items())


def _entry(entry: dict) -> kb_pb2.Entry:
    """An entry as the contract carries it. A snapshot's entry has no artifact, place, version or fingerprint of its
    own, only what was read."""
    return kb_pb2.Entry(
        id=entry["id"], at=entry["at"], actor=kb_pb2.Actor(**entry["actor"]), op=entry["op"],
        artifact=entry.get("artifact", ""), path=entry.get("path", ""), revision=entry.get("revision", 0),
        schema_version=entry.get("schema_version", 0), digest=entry.get("digest", ""), message=entry["message"],
        batch=entry["batch"], read=[kb_pb2.Snapshotted(**read) for read in entry.get("read", [])],
    )


def _revise(draft: Draft, artifact_id: ArtifactId, current: dict, content: dict) -> None:
    """The artifact's next version put in the draft: the content checked against the current version of its type,
    its items named, its version up by one, its title kept. Raises values.Refused with every fault."""
    schema = draft.schema(artifact_id.kind)
    faults = validation.validate(str(artifact_id), {"title": current["title"], **content}, schema["schema"], draft)
    if faults:
        raise values.Refused(faults)
    _name_items(schema["schema"], content, keep_named=True)
    artifact = {
        **content,
        "id": current["id"], "type": current["type"],
        "schema_version": schema["version"], "revision": current["revision"] + 1, "title": current["title"],
    }
    draft.put(artifact_id, canonical.order(artifact, schema["schema"]))


def _content_of(artifact: dict) -> dict:
    """A copy of what an artifact holds but its identity keys, to be changed without changing it."""
    return copy.deepcopy({key: value for key, value in artifact.items() if key not in canonical.IDENTITY})


def _placed(artifact: dict, locator: values.Locator, node: dict) -> dict:
    """The artifact's content with the node at the locator's place replaced by the one given. A place is pairs of a
    list and an item in it, a section named by its title's name and a part by its id, and may end in a field."""
    content = _content_of(artifact)
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


def _find_section(sections: list, title: str) -> dict | None:
    """The first section titled so, looking at each section before the sections inside it."""
    for section in sections:
        if section["title"] == title:
            return section
        found = _find_section(section.get("sections", []), title)
        if found is not None:
            return found
    return None


def _node_name(collection: str, item: dict) -> str:
    """How a place names an item: a section by its title's name, a part by its id."""
    return values.slug(item["title"]) if collection == "sections" else item.get("id")


def _name_items(schema: dict, content: dict, keep_named: bool) -> None:
    """Every item of every part collection given its name: from its title when it carries one, otherwise from its
    place in the collection, counted from 1, with a number added as an artifact's name has when an item beside it
    already has that name. On a write an item already carrying a name is the item of that name, moved or changed
    where it stands, and keeps it; a name is minted once and never worked out again."""
    for collection in schema.get("parts", {}):
        items = content.get(collection, [])
        taken = {item["id"] for item in items if keep_named and "id" in item}
        for place, item in enumerate(items, start=1):
            if keep_named and "id" in item:
                continue
            item["id"] = _numbered(values.slug(item["title"]) if "title" in item else str(place), taken.__contains__)
            taken.add(item["id"])


def _not_found(artifact_id: ArtifactId) -> kb_pb2.Fault:
    return kb_pb2.Fault(
        artifact=str(artifact_id), rule="not-found", message=f"the store holds nothing by the name {str(artifact_id)!r}",
    )


def _unclaimed(draft: Draft, named: ArtifactId) -> ArtifactId:
    """The name a title gives, or, when the store or an earlier change in the set already holds it, that name with
    -2, -3 and so on added: the first that nothing holds. What already holds a name keeps it."""
    return ArtifactId(named.kind, _numbered(named.slug, lambda slug: draft.holds(ArtifactId(named.kind, slug))))


def _numbered(name: str, taken) -> str:
    """The name, or, when taken says it is taken, that name with -2, -3 and so on added: the first it does not."""
    candidate, number = name, 1
    while taken(candidate):
        number += 1
        candidate = f"{name}-{number}"
    return candidate


def _summary_fields(artifact, schema):
    return {name: artifact[name] for name in schema.get("summary", []) if name in artifact}

