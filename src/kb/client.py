"""Transports. In-process: an object with the stub's method names that calls the servicer directly."""
from pathlib import Path

from kb.servicer import KbServicer


class InProcessClient:
    """Same method names, requests and responses as kb_pb2_grpc.KbStub, with no channel between."""

    def __init__(self, servicer: KbServicer):
        self._servicer = servicer

    def Init(self, request, timeout=None):
        return self._servicer.Init(request, None)

    def Create(self, request, timeout=None):
        return self._servicer.Create(request, None)

    def Read(self, request, timeout=None):
        return self._servicer.Read(request, None)


def connect(root) -> InProcessClient:
    """A client over the store at <root>/kb/, in this process."""
    return InProcessClient(KbServicer(Path(root)))
