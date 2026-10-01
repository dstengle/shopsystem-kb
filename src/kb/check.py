"""The check of the whole store: every artifact against the current version of its type, the stale listed beside
the violations, and a file that cannot be read, or an artifact of a kind with no type, reported as what it is, the
check going on past it."""
from kb import composition, settled, validation
from kb.contract import kb_pb2
from kb.port import Port


def everything(store: Port) -> kb_pb2.ValidateResponse:
    """Every artifact checked against the current version of its type, and listed as stale when it was last
    checked against an older one; a file that cannot be read, or an artifact of a kind with no type, is reported and
    the check goes on."""
    violations, stale = [], []
    for artifact_id in store.ids():
        found = _with_type(store, artifact_id)
        if isinstance(found, kb_pb2.Fault):
            violations.append(found)
            continue
        artifact, schema = found
        if artifact["schema_version"] < schema["version"]:
            stale.append(kb_pb2.Stale(
                artifact=str(artifact_id), schema_version=artifact["schema_version"], current=schema["version"],
            ))
        violations += validation.validate(str(artifact_id), settled.checked(artifact), schema["schema"], store)
    return kb_pb2.ValidateResponse(violations=violations, stale=stale)


def _with_type(store: Port, artifact_id) -> tuple[dict, dict] | kb_pb2.Fault:
    """The artifact and its type as the store holds them, or the finding that stands in for checking it: that the
    store holds no type for its kind."""
    type_id = composition.named_type(artifact_id.kind, store, artifact=str(artifact_id))
    if isinstance(type_id, kb_pb2.Fault):
        return type_id
    return store.artifact(artifact_id), store.artifact(type_id)
