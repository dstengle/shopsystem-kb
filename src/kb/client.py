"""Transports. In-process: an object with the stub's method names that calls the servicer directly."""
import os
from pathlib import Path

from kb import discovery
from kb.contract import kb_pb2
from kb.servicer import KbServicer


class InProcessClient:
    """Same method names, requests and responses as kb_pb2_grpc.KbStub, with no channel between.

    Readied without finding a store. Each call but Init finds its store as it is made, from the root the client
    was given or, with none, the way git finds a repository; a call that finds none answers with that fault and
    touches nothing. Init takes its root from the request and finds nothing.
    """

    def __init__(self, root: Path | None = None):
        self._root = root

    def _servicer(self) -> tuple[KbServicer | None, kb_pb2.Fault | None]:
        if self._root is not None:
            return KbServicer(self._root), None
        root, refusal = discovery.locate(Path.cwd(), os.environ)
        if refusal is not None:
            return None, refusal
        return KbServicer(root), None

    def Init(self, request, timeout=None):
        return KbServicer(Path(request.root)).Init(request, None)

    def Create(self, request, timeout=None):
        servicer, refusal = self._servicer()
        if refusal is not None:
            return kb_pb2.CreateResponse(faults=[refusal])
        return servicer.Create(request, None)

    def Read(self, request, timeout=None):
        servicer, refusal = self._servicer()
        if refusal is not None:
            return kb_pb2.ReadResponse(faults=[refusal])
        return servicer.Read(request, None)

    def Validate(self, request, timeout=None):
        servicer, refusal = self._servicer()
        if refusal is not None:
            return kb_pb2.ValidateResponse(faults=[refusal])
        return servicer.Validate(request, None)


def connect(root=None) -> InProcessClient:
    """A client over the store at <root>/kb/, in this process; with no root, over whichever store each call finds."""
    return InProcessClient(Path(root) if root is not None else None)
