"""The check of the whole store, read through the port: every artifact against the version of its type it
conforms to, the stale listed beside the violations, and the placeholders apart from both."""
from kb import composition, fault_order, port, query, settled, validation
from kb.contract import kb_pb2
from kb.port import Port


def everything(store: Port) -> kb_pb2.Checked:
    """Every artifact checked against the version of its type it conforms to, and listed as stale when its type
    stands at a later one; each version of a type read once. The placeholders are those the client is given when it
    asks for them, made of the waiting links read once, and a link among them that waits on a part its held
    target lacks is no violation, by the judgement a change to its artifact is checked with (kb.validation)."""
    violations, stale, schemas, standing = [], [], {}, {}
    waiting = store.waiting()
    held = _by_holder(waiting)
    for artifact_id in store.ids():
        artifact = store.artifact(artifact_id)
        conforming = composition.conforming(artifact)
        if conforming not in schemas:
            schemas[conforming] = composition.artifact_schema(artifact, store)
        if conforming.kind not in standing:
            standing[conforming.kind] = composition.kind_schema(conforming.kind, store)["version"]
        if conforming.number < standing[conforming.kind]:
            stale.append(kb_pb2.Stale(
                artifact=str(artifact_id), schema_version=conforming.number, current=standing[conforming.kind],
            ))
        schema = schemas[conforming]["schema"]
        waited = port.held_waiting(held.get(artifact_id, ()))
        found = validation.validate(str(artifact_id), settled.checked(artifact), schema, store, waited)
        violations += fault_order.ordered(found, settled.checked(artifact), composition.declared(schema, store))
    return kb_pb2.Checked(violations=violations, stale=stale, placeholders=query.placeholders_of(waiting).placeholders)


def _by_holder(waiting: list) -> dict:
    """The waiting links by the artifact holding each, each artifact's in the order given."""
    found = {}
    for each in waiting:
        found.setdefault(each.source, []).append(each)
    return found
