"""An rpc's or an operator's command's response, made from what its call gave or the faults it was refused for: a
response with an outcome holds the result or a refusal, never both; any other carries its faults beside what it
gives."""
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
