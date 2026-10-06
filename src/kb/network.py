"""The network transport: an rpc called, with the request as it was asked, on the server at the address a
connection names, over a channel made for that call alone, and its response as the server gave it."""
import grpc

from kb.addresses import Address
from kb.contract import kb_pb2_grpc


def called(address: Address, rpc: str, request):
    """The server's response to the rpc."""
    with grpc.insecure_channel(str(address)) as channel:
        return getattr(kb_pb2_grpc.KbStub(channel), rpc)(request)
