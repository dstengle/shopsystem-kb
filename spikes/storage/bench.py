"""THROWAWAY. Per-call cost at scale, for one adapter: `python bench.py sqlite_adapter 3000 30000`.

The graph: tags, decisions (each linking to 2 tags and, for most, the decision before it), work items (each linking
to 2 decisions). About 3 links per document. Then a transcript-like burst: 10,000 small entries, each linking to one
work item, landed in sets of 100. Every timing is the median of 20 calls unless it says otherwise."""
import importlib
import statistics
import sys
import tempfile
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from model import ALL, SIG, create, replace, sections  # noqa: E402

ENTRY = {"name": "entry", "version": 1, "base": None,
         "fields": {"about": {"type": "link", "targets": ["work-item"], "many": False, "parts": False,
                              "required": True},
                    "body": {"type": "text", "required": False, "many": False}},
         "collections": {}, "sections": []}
WORDS = "restocking shelves pricing weekly review supplier till opening closing inventory".split()


def timed(call, runs=20):
    samples = []
    for _ in range(runs):
        start = time.perf_counter()
        call()
        samples.append(time.perf_counter() - start)
    return statistics.median(samples) * 1000


def build(store, n):
    tags = max(10, n // 30)
    decisions = n * 2 // 3 - tags
    items = n - tags - decisions
    started = time.perf_counter()
    for start in range(0, tags, 500):
        store.commit([create("tag", f"t{i}", f"Tag {i}", {}) for i in range(start, min(tags, start + 500))], SIG)
    for start in range(0, decisions, 500):
        store.commit([create("decision", f"d{i}", f"Decision {i}", {
            "sections": sections(purpose=f"{WORDS[i % 10]} {WORDS[(i * 7) % 10]}", rationale=f"Because {i}."),
            "tags": [f"tag/t{i % tags}", f"tag/t{(i * 3 + 1) % tags}"],
            **({"supersedes": f"decision/d{i - 1}"} if i % 10 else {}),
        }) for i in range(start, min(decisions, start + 500))], SIG)
    for start in range(0, items, 500):
        store.commit([create("work-item", f"w{i}", f"Work {i}", {
            "decisions": [f"decision/d{i % decisions}", f"decision/d{(i * 5 + 2) % decisions}"],
        }) for i in range(start, min(items, start + 500))], SIG)
    return time.perf_counter() - started, decisions, items


def run(adapter, n):
    module = importlib.import_module(adapter)
    store = module.open_store(f"bench{uuid.uuid4().hex[:8]}", Path(tempfile.mkdtemp()))
    for kind in ALL + [ENTRY]:
        store.define(kind, SIG)
    load, decisions, items = build(store, n)
    hot = f"decision/d{decisions // 2}"
    tag = "tag/t3"
    row = {"adapter": adapter, "docs": n, "load s": round(load, 1)}
    row["read ms"] = timed(lambda: store.read(hot))
    row["glance ms"] = timed(lambda: (store.read(hot), store.inbound_counts(hot)))
    row["links in (tag) ms"] = timed(lambda: store.links_in(tag))
    row["traverse out 3 ms"] = timed(lambda: store.traverse(f"work-item/w{items // 2}", "out", 3))
    row["traverse in 3 ms"] = timed(lambda: store.traverse(hot, "in", 3))
    row["list filtered ms"] = timed(lambda: store.list("decision", {"status": "none"}))
    row["search ms"] = timed(lambda: store.search("restocking"))
    row["search hits"] = len(store.search("restocking"))
    counter = iter(range(10**6))
    row["create ms"] = timed(lambda: store.commit([create("tag", f"x{next(counter)}", "X", {})], SIG))
    current = store.read(hot)
    row["replace ms"] = timed(lambda: store.commit([replace(hot, current["content"])], SIG), runs=10)
    batch = iter(range(10**6))
    row["set of 100 ms"] = timed(lambda: store.commit(
        [create("tag", f"y{next(batch)}", "Y", {}) for _ in range(100)], SIG), runs=5)
    started = time.perf_counter()
    for start in range(0, 10_000, 100):
        store.commit([create("entry", f"e{i}", f"Entry {i}", {
            "about": f"work-item/w{i % items}", "body": f"{WORDS[i % 10]} happened"}) for i in range(start, start + 100)],
            SIG)
    row["10k entries s"] = round(time.perf_counter() - started, 1)
    started = time.perf_counter()
    exported = sum(1 for _ in store.export())
    row["export s"] = round(time.perf_counter() - started, 1)
    row["exported"] = exported
    return row


if __name__ == "__main__":
    adapter, sizes = sys.argv[1], [int(s) for s in sys.argv[2:]] or [3000, 30000]
    for n in sizes:
        row = run(adapter, n)
        print(" | ".join(f"{k}: {v:.2f}" if isinstance(v, float) and "ms" in k else f"{k}: {v}" for k, v in row.items()),
              flush=True)
