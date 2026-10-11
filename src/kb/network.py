"""The network transport: an rpc called, with the request as it was asked, on the server at the address a
connection names, over a channel made for that call alone, and its response as the server gave it; a server that
cannot be reached, never there, gone since, or something at the address that never answers as one, the rpc's own
response refused with `unreachable`, naming the address. The channel gives up connecting after CONNECTING; a call
sets no deadline of its own. A message may be of any size, either way. An rpc that answers with a stream is called
the same way (`streamed`), its channel kept for as long as the stream is read."""
import sys
from contextlib import contextmanager

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


def streamed(address: Address, rpc: str, request, response):
    """The server's stream for the rpc, each message as the server sends it, over a channel of its own that is kept
    until the stream ends or its reader closes it or lets it go, which tells the server to stop; no deadline is set
    on its length. A server that cannot be reached, or is lost partway, ends the stream with one more message of the
    rpc's type, refused: the stream's only message when none had come, its last otherwise."""
    with _kept(address) as channel:
        try:
            yield from getattr(kb_pb2_grpc.KbStub(channel), rpc)(request)
        except grpc.RpcError:
            yield responses.refused(response, [refusals.unreachable(str(address))])


@contextmanager
def _kept(address: Address):
    """A channel to the address, closed when the block ends, unless it ends because the program is ending: closing a
    channel with a call still open waits on a thread of grpc's, which runs no longer by then, so the program would
    never end; the channel is left to go with the process."""
    channel = grpc.insecure_channel(str(address), options=_OPTIONS)
    try:
        yield channel
    finally:
        if not sys.is_finalizing():
            channel.close()
