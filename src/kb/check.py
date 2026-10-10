"""The check of the whole store, read through the port: every artifact against the version of its type it
conforms to, the stale listed beside the violations."""
from kb import composition, fault_order, settled, validation
from kb.contract import kb_pb2
from kb.port import Port


def everything(store: Port) -> kb_pb2.Checked:
    """Every artifact checked against the version of its type it conforms to, and listed as stale when its type
    stands at a later one; each version of a type read once."""
    violations, stale, schemas, standing = [], [], {}, {}
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
        violations += fault_order.ordered(found, settled.checked(artifact), composition.declared(schema, store))
    return kb_pb2.Checked(violations=violations, stale=stale)
