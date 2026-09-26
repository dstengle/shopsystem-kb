"""The check of the whole store: every artifact against the current version of its type, the stale listed beside
the violations, and a file that cannot be read reported as the file it is, the check going on past it."""
from kb import canonical, validation, values
from kb.contract import kb_pb2
from kb.store import Damaged, Store


def everything(store: Store) -> kb_pb2.ValidateResponse:
    """Every artifact checked against the current version of its type, and listed as stale when it was last
    checked against an older one; a file that cannot be read is reported and the check goes on."""
    violations, stale = [], []
    for artifact_id in store.ids():
        loaded = _with_type(store, artifact_id)
        if isinstance(loaded, Damaged):
            violations.append(loaded.fault)
            continue
        artifact, schema = loaded
        if artifact["schema_version"] < schema["version"]:
            stale.append(kb_pb2.Stale(
                artifact=str(artifact_id), schema_version=artifact["schema_version"], current=schema["version"],
            ))
        content = {key: value for key, value in artifact.items() if key not in canonical.IDENTITY[:4]}
        violations += validation.validate(str(artifact_id), content, schema["schema"], store)
    return kb_pb2.ValidateResponse(violations=violations, stale=stale)


def _with_type(store: Store, artifact_id) -> tuple[dict, dict] | Damaged:
    """The artifact and its type as stored, or the damage of the first of them whose file cannot be read."""
    artifact = store.load(artifact_id)
    if isinstance(artifact, Damaged):
        return artifact
    schema = store.load(values.type_of(artifact_id.kind))
    return schema if isinstance(schema, Damaged) else (artifact, schema)
