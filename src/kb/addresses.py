"""A server's address, `host:port`, as the operator's `--listen` and a connection's `address` give it, read once into
a value: the host as written, the port a number."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Address:
    """Where a server listens or is reached: a host, as written, and a port."""
    host: str
    port: int

    def __str__(self) -> str:
        return f"{self.host}:{self.port}"


def address(text: str) -> Address:
    """`host:port` as a value; the port is what follows the last colon."""
    host, _, port = text.rpartition(":")
    return Address(host, int(port))
