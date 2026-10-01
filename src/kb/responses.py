"""An rpc's or an operator's command's response, made from what its call gave or the faults it was refused for: a
response with an outcome holds the result or a refusal, never both; any other carries its faults beside what it
gives. A change's result, and a set's, are made here from what the set landed."""
from kb import write
from kb.contract import kb_pb2


def _has_outcome(response) -> bool:
    descriptor = getattr(response, "DESCRIPTOR", None)
    return descriptor is not None and "outcome" in descriptor.oneofs_by_name


def answered(response, given):
    """The response of this type to a call that gave what it was asked for: the result in its outcome, or, for a
    response with none, what the call gave, which is that response."""
    return response(result=given) if _has_outcome(response) else given


def refused(response, faults):
    """The response of this type to a call refused for these faults: the refusal in its outcome, or its faults."""
    if _has_outcome(response):
        return response(refusal=kb_pb2.Refusal(faults=faults))
    return response(faults=faults)


def created(result: write.Result) -> kb_pb2.Created:
    return kb_pb2.Created(id=str(result.artifact_id), revision=result.revision)


def replaced(result: write.Result) -> kb_pb2.Replaced:
    return kb_pb2.Replaced(id=str(result.artifact_id), revision=result.revision)


def added(result: write.Result) -> kb_pb2.Added:
    """The item added, by the name kb gave it, and the artifact's version now."""
    return kb_pb2.Added(id=result.item, revision=result.revision)


def removed(result: write.Result) -> kb_pb2.Removed:
    return kb_pb2.Removed(id=str(result.artifact_id), revision=result.revision)


def landed(result, set_landed: write.Landed, each):
    """A set's result of this type: the set's name, and each change's own result, in the order of the set."""
    return result(batch=set_landed.batch, results=[each(change) for change in set_landed.results])
