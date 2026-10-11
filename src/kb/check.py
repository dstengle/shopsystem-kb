"""The check of the whole store, read through the port: every artifact against the version of its type it
conforms to, the stale listed beside the violations, and the placeholders apart from both."""
from kb import composition, fault_order, links, query, rules, settled, validation
from kb.contract import kb_pb2
from kb.port import Port


def everything(store: Port) -> kb_pb2.Checked:
    """Every artifact checked against the version of its type it conforms to, and listed as stale when its type
    stands at a later one; each version of a type read once. The placeholders are those the client is given when it
    asks for them, made of the waiting links read once, and a link among them is no violation."""
    violations, stale, schemas, standing = [], [], {}, {}
    waiting = store.waiting()
    lacking = _lacking(waiting, store)
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
        found = validation.validate(str(artifact_id), settled.checked(artifact), schema, store)
        if artifact_id in lacking:
            carried = links.handed(artifact_id, artifact, store, schemas[conforming])
            found = _but_waiting(found, carried, lacking[artifact_id])
        violations += fault_order.ordered(found, settled.checked(artifact), composition.declared(schema, store))
    return kb_pb2.Checked(violations=violations, stale=stale, placeholders=query.placeholders_of(waiting).placeholders)


def _lacking(waiting: list, store: Port) -> dict:
    """The waiting links that point into a part the artifact held at their IRI lacks, by the artifact holding each,
    as the link's place there, the IRI and the part. Such a link was written while nothing was held at that IRI,
    waits as a placeholder does, and is listed with them."""
    found = {}
    for each in waiting:
        if store.holds(each.target):
            found.setdefault(each.source, set()).add((each.place, each.target, each.part))
    return found


def _but_waiting(found: list, carried: list, lacking: set) -> list:
    """An artifact's faults less the one a write would refuse each of its waiting links for: a `ref` fault at a place
    where the artifact, as it reads now, carries the very link that waits there, its IRI and part the same. A fault
    for any other link at that place, or of any other rule, stays."""
    waits = {link.place for link in carried if (link.place, link.target, link.part) in lacking}
    return [fault for fault in found if fault.rule != rules.REF or fault.place not in waits]
