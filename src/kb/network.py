"""The network transport: an rpc called, with the request as it was asked, on the server at the address a
connection names, over a channel made for that call alone, and its response as the server gave it; a server that
cannot be reached, never there, gone since, or something at the address that never answers as one, the rpc's own
response refused with `unreachable`, naming the address. The channel gives up connecting after CONNECTING; a call
sets no deadline of its own. A message may be of any size, either way."""
import grpc

from kb import refusals, responses
from kb.addresses import Address
from kb.contract import kb_pb2_grpc

CONNECTING = 5  # seconds a channel tries to connect, and to hear the server's first word, before it gives up
# grpc core reads the minimum reconnect backoff as the minimum connect timeout too: an attempt to connect, the
# server's first word included, is given that long before it fails, and the call with it. `channel_ready_future`
# would say this outright, but it waits out its timeout at a port nobody listens at, where the call fails at once.
_OPTIONS = [
    ("grpc.min_reconnect_backoff_ms", CONNECTING * 1000),
    ("grpc.max_send_message_length", -1), ("grpc.max_receive_message_length", -1),  # a message of any size
]


def called(address: Address, rpc: str, request, response):
    """The server's response to the rpc, or a response of the rpc's type refused because the server cannot be
    reached."""
    with grpc.insecure_channel(str(address), options=_OPTIONS) as channel:
        try:
            return getattr(kb_pb2_grpc.KbStub(channel), rpc)(request)
        except grpc.RpcError:
            return responses.refused(response, [refusals.unreachable(str(address))])
