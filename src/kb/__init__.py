"""kb: a schema-typed, graph-oriented artifact store behind one versioned contract. A store is started in the client's
own process by `init`, which raises `NotStarted` when it refuses."""
from kb.starting import NotStarted, init

__all__ = ["NotStarted", "init"]
