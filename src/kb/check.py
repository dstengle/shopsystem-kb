"""The check of the whole store, read through the port: every artifact against the version of its type it
conforms to, the stale listed beside the violations, and the placeholders apart from both."""
from kb import composition, fault_order, query, rules, settled, validation
from kb.contract import kb_pb2
from kb.port import Port


def everything(store: Port) -> kb_pb2.Checked:
    """Every artifact checked against the version of its type it conforms to, and listed as stale when its type
    stands at a later one; each version of a type read once. The placeholders are those the client is given when it
    asks for them, and a link among them is no violation."""
    violations, stale, schemas, standing = [], [], {}, {}
    lacking = _lacking(store)
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
        found = [fault for fault in found if (fault.rule, fault.artifact, fault.place) not in lacking]
        violations += fault_order.ordered(found, settled.checked(artifact), composition.declared(schema, store))
    return kb_pb2.Checked(violations=violations, stale=stale, placeholders=query.placeholders(store).placeholders)


def _lacking(store: Port) -> set[tuple[str, str, str]]:
    """The fault a write would refuse each link for that points into a part the artifact held at its IRI lacks, as
    its rule, the artifact holding the link and the link's place there. Such a link was written while nothing was
    held at that IRI, waits as a placeholder does, and is listed with them."""
    return {(rules.REF, str(each.source), each.place) for each in store.waiting() if store.holds(each.target)}
