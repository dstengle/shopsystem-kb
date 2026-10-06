"""The network transport: an rpc called, with the request as it was asked, on the server at the address a
connection names, over a channel made for that call alone, and its response as the server gave it; a server that
cannot be reached, never there, gone since, or something at the address that never answers as one, the rpc's own
response refused with `unreachable`, naming the address. The channel gives up connecting after CONNECTING; a call
sets no deadline of its own."""
import grpc

from kb import refusals, responses
from kb.addresses import Address
from kb.contract import kb_pb2_grpc

CONNECTING = 5  # seconds a channel tries to connect, and to hear the server's first word, before it gives up
_OPTIONS = [("grpc.min_reconnect_backoff_ms", CONNECTING * 1000)]


def called(address: Address, rpc: str, request, response):
    """The server's response to the rpc, or a response of the rpc's type refused because the server cannot be
    reached."""
    with grpc.insecure_channel(str(address), options=_OPTIONS) as channel:
        try:
            return getattr(kb_pb2_grpc.KbStub(channel), rpc)(request)
        except grpc.RpcError:
            return responses.refused(response, [refusals.unreachable(str(address))])
