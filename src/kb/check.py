"""The check of the whole store, read through the port: every artifact against the current version of its type, the
stale listed beside the violations."""
from kb import composition, settled, validation
from kb.contract import kb_pb2
from kb.port import Port


def everything(store: Port) -> kb_pb2.Checked:
    """Every artifact checked against the current version of its type, and listed as stale when it was last
    checked against an older one; each kind's type composed once."""
    violations, stale, schemas = [], [], {}
    for artifact_id in store.ids():
        artifact = store.artifact(artifact_id)
        if artifact_id.kind not in schemas:
            schemas[artifact_id.kind] = composition.kind_schema(artifact_id.kind, store)
        schema = schemas[artifact_id.kind]
        if artifact["schema_version"] < schema["version"]:
            stale.append(kb_pb2.Stale(
                artifact=str(artifact_id), schema_version=artifact["schema_version"], current=schema["version"],
            ))
        violations += validation.validate(str(artifact_id), settled.checked(artifact), schema["schema"], store)
    return kb_pb2.Checked(violations=violations, stale=stale)
