"""THROWAWAY. Every adapter module that imports runs the whole suite. SPIKE_ADAPTERS=sqlite_adapter narrows it.

An adapter module exposes `open_store(name: str, workdir: pathlib.Path) -> Store`: the store called `name` under
`workdir`, made empty on first open; opening the same name again gives another handle on the same data (the
concurrency tests hold two)."""
import importlib
import os
import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

ADAPTERS = [a for a in os.environ.get("SPIKE_ADAPTERS", "sqlite_adapter,terminus_adapter").split(",") if a]


def _available():
    found = []
    for name in ADAPTERS:
        try:
            importlib.import_module(name)
            found.append(name)
        except ImportError:
            pass
    return found


@pytest.fixture(params=_available())
def opener(request, tmp_path):
    """open(name="main") -> a handle on the store of that name, isolated to this test."""
    module = importlib.import_module(request.param)
    prefix = uuid.uuid4().hex[:10]
    return lambda name="main": module.open_store(f"t{prefix}{name}", tmp_path)


@pytest.fixture
def store(opener):
    from model import ALL, SIG
    s = opener()
    for kind in ALL:
        s.define(kind, SIG)
    return s
