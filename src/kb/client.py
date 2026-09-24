"""Transports. In-process: an object with the stub's method names that calls the servicer directly."""
import os
from pathlib import Path

from kb import discovery
from kb.contract import kb_pb2
from kb.servicer import KbServicer


class InProcessClient:
    """Same method names, requests and responses as kb_pb2_grpc.KbStub, with no channel between.

    Built over a refusal instead of a servicer, every call answers with that fault and touches nothing.
    """

    def __init__(self, servicer: KbServicer | None, refusal: kb_pb2.Fault | None = None):
        self._servicer = servicer
        self._refusal = refusal

    def Init(self, request, timeout=None):
        return self._servicer.Init(request, None)

    def Create(self, request, timeout=None):
        if self._refusal:
            return kb_pb2.CreateResponse(faults=[self._refusal])
        return self._servicer.Create(request, None)

    def Read(self, request, timeout=None):
        if self._refusal:
            return kb_pb2.ReadResponse(faults=[self._refusal])
        return self._servicer.Read(request, None)


def connect(root=None) -> InProcessClient:
    """A client over the store at <root>/kb/, in this process.

    With no root, over the store found the way git finds a repository: above the working directory, or
    named by KB_ROOT; none found, or the two disagreeing, and the client refuses every call.
    """
    if root is not None:
        return InProcessClient(KbServicer(Path(root)))
    root, refusal = discovery.locate(Path.cwd(), os.environ)
    if refusal is not None:
        return InProcessClient(None, refusal)
    return InProcessClient(KbServicer(root))
