"""A server's address, `host:port`, as the operator's `--listen` and a connection's `address` give it, read once into
a value: the host as written, never empty, and the port a number from 0 to 65535, 0 asking the system for one."""
from dataclasses import dataclass

LAST_PORT = 65535


@dataclass(frozen=True)
class Address:
    """Where a server listens or is reached: a host, as written, and a port."""
    host: str
    port: int

    def __str__(self) -> str:
        return f"{self.host}:{self.port}"


def address(text: str) -> Address:
    """`host:port` as a value; the port is what follows the last colon. Raises ValueError when the text is not a
    host and a port from 0 to LAST_PORT."""
    host, _, port = text.rpartition(":")
    if not host or not (port.isascii() and port.isdigit()) or int(port) > LAST_PORT:
        raise ValueError(f"it is not a host and a port from 0 to {LAST_PORT}")
    return Address(host, int(port))
